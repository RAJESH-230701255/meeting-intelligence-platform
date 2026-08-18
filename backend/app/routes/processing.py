"""Processing routes — server-side pipeline orchestrator for meeting intelligence.

This endpoint is the primary orchestration point for the meeting intelligence
pipeline.  It accepts an optional audio file, runs STT if needed, then
triggers AI analysis and persists all results in a single request.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_current_user, get_db, require_role
from app.models.decision import Decision
from app.models.meeting import Meeting
from app.models.summary import MeetingSummary
from app.models.task import Task
from app.models.transcript import Transcript
from app.models.user import User
from app.schemas.analysis import AnalysisResponse
from app.services.ai import get_ai_service
from app.services.audit_service import log_action
from app.services.file_processor import ALLOWED_AUDIO_EXTENSIONS, validate_file
from app.services.notification_service import notify_task_assigned
from app.services.speech import get_speech_service

settings = get_settings()
router = APIRouter(tags=["Processing"])


@router.post("/api/meetings/{meeting_id}/process", response_model=AnalysisResponse)
async def process_meeting(
    meeting_id: int,
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Orchestrate the full meeting intelligence pipeline.

    Accepts an optional audio file.  If provided the audio is saved (and
    retained), transcribed via STT, and the transcript is persisted.  Then
    AI analysis runs on the transcript producing summary, decisions, and
    action items.

    If no audio file is provided the endpoint expects a transcript to
    already exist in the database for the given meeting.

    Re-analysis behaviour:
    - Summary is upserted (overwritten).
    - Decisions are replaced.
    - Only PENDING_REVIEW + AI_EXTRACTED tasks are replaced.
    - CONFIRMED, PENDING, IN_PROGRESS, and COMPLETED tasks are NEVER touched.
    """

    # ------------------------------------------------------------------
    # 1. Validate meeting
    # ------------------------------------------------------------------
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # ------------------------------------------------------------------
    # 2. Handle audio file (optional)
    # ------------------------------------------------------------------
    if file is not None:
        content = await file.read()
        file_size = len(content)

        try:
            validate_file(
                file.filename, file_size,
                ALLOWED_AUDIO_EXTENSIONS, settings.MAX_UPLOAD_SIZE_MB,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Save audio — file is RETAINED after processing (req #1).
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file.filename)[1].lower()
        audio_filename = f"meeting_{meeting_id}_{uuid.uuid4().hex[:8]}{ext}"
        audio_path = os.path.join(settings.UPLOAD_DIR, audio_filename)

        with open(audio_path, "wb") as f:
            f.write(content)

        # Determine source type
        source_type = (
            "INTERNAL_AUDIO"
            if meeting.meeting_type == "INTERNAL"
            else "UPLOADED_AUDIO"
        )
        meeting.source_type = source_type

        # Speech-to-text
        try:
            stt_service = get_speech_service()
            transcript_text = stt_service.transcribe(audio_path)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Speech-to-text failed: {e}"
            )

        # Save / upsert transcript
        existing_transcript = (
            db.query(Transcript)
            .filter(Transcript.meeting_id == meeting_id)
            .first()
        )
        source_label = (
            "AUTO_RECORDED" if source_type == "INTERNAL_AUDIO" else "UPLOADED_AUDIO"
        )
        if existing_transcript:
            existing_transcript.content = transcript_text
            existing_transcript.source = source_label
            existing_transcript.processed_at = datetime.now(timezone.utc)
        else:
            db.add(Transcript(
                meeting_id=meeting_id,
                source=source_label,
                content=transcript_text,
                language="en",
                processed_at=datetime.now(timezone.utc),
            ))

        db.commit()
        log_action(db, current_user.id, "UPLOAD_AUDIO", "meeting", meeting_id)

    # ------------------------------------------------------------------
    # 3. Verify transcript exists
    # ------------------------------------------------------------------
    transcript = (
        db.query(Transcript)
        .filter(Transcript.meeting_id == meeting_id)
        .first()
    )
    if not transcript:
        raise HTTPException(
            status_code=400,
            detail="No transcript available. Upload audio or a transcript first.",
        )

    # ------------------------------------------------------------------
    # 4. AI Analysis
    # ------------------------------------------------------------------
    ai_service = get_ai_service()
    try:
        analysis = ai_service.analyze_transcript(transcript.content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")

    # ------------------------------------------------------------------
    # 5. Save / upsert summary
    # ------------------------------------------------------------------
    existing_summary = (
        db.query(MeetingSummary)
        .filter(MeetingSummary.meeting_id == meeting_id)
        .first()
    )
    if existing_summary:
        existing_summary.summary = analysis.summary
        existing_summary.key_points = analysis.key_points
    else:
        db.add(MeetingSummary(
            meeting_id=meeting_id,
            summary=analysis.summary,
            key_points=analysis.key_points,
        ))

    # ------------------------------------------------------------------
    # 6. Replace decisions
    # ------------------------------------------------------------------
    db.query(Decision).filter(Decision.meeting_id == meeting_id).delete()
    for dec in analysis.decisions:
        db.add(Decision(
            meeting_id=meeting_id,
            decision_text=dec.decision,
            decision_context=dec.context,
        ))

    # ------------------------------------------------------------------
    # 7. Replace ONLY PENDING_REVIEW AI-extracted tasks (req #2)
    #    CONFIRMED, PENDING, IN_PROGRESS, COMPLETED tasks are NEVER deleted.
    # ------------------------------------------------------------------
    db.query(Task).filter(
        Task.meeting_id == meeting_id,
        Task.source == "AI_EXTRACTED",
        Task.status == "PENDING_REVIEW",
    ).delete()

    for item in analysis.action_items:
        assigned_to = None
        if item.assignee_name and item.assignee_name.lower() != "unresolved":
            user = (
                db.query(User)
                .filter(User.name.ilike(f"%{item.assignee_name}%"))
                .first()
            )
            if user:
                assigned_to = user.id

        parsed_deadline = None
        if item.deadline:
            try:
                parsed_deadline = datetime.fromisoformat(
                    item.deadline.replace("Z", "+00:00")
                ).date()
            except ValueError:
                pass

        task = Task(
            meeting_id=meeting_id,
            assigned_to=assigned_to,
            created_by=current_user.id,
            title=item.title,
            description=item.description,
            deadline=parsed_deadline,
            priority=item.priority,
            status="PENDING_REVIEW",
            source_text=item.source_text,
            ai_confidence=item.confidence,
            source="AI_EXTRACTED",
        )
        db.add(task)

    # ------------------------------------------------------------------
    # 8. Commit & log
    # ------------------------------------------------------------------
    transcript.processed_at = datetime.now(timezone.utc)
    db.commit()
    log_action(db, current_user.id, "AI_ANALYSIS", "meeting", meeting_id)

    # ------------------------------------------------------------------
    # 9. Build response
    # ------------------------------------------------------------------
    decisions = db.query(Decision).filter(Decision.meeting_id == meeting_id).all()
    tasks = db.query(Task).filter(
        Task.meeting_id == meeting_id, Task.source == "AI_EXTRACTED"
    ).all()

    return AnalysisResponse(
        meeting_id=meeting_id,
        summary=analysis.summary,
        key_points=analysis.key_points,
        decisions=[
            {"decision": d.decision_text, "context": d.decision_context}
            for d in decisions
        ],
        action_items=[
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "assignee_id": t.assigned_to,
                "assignee_name": t.assignee.name if t.assignee else "unresolved",
                "deadline": str(t.deadline) if t.deadline else None,
                "priority": t.priority,
                "source_text": t.source_text,
                "confidence": t.ai_confidence,
                "status": t.status,
            }
            for t in tasks
        ],
    )
