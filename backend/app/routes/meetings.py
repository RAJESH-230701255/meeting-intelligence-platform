"""Meeting routes — CRUD, participants, start/end, audio upload."""

import os
import uuid
from datetime import datetime, timezone, date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, String, cast

from app.core.config import get_settings
from app.core.dependencies import get_current_user, get_db, require_role
from app.models.meeting import Meeting
from app.models.participant import MeetingParticipant
from app.models.transcript import Transcript
from app.models.user import User
from app.schemas.meeting import (
    AddParticipantsRequest,
    MeetingCreate,
    MeetingListResponse,
    MeetingResponse,
    MeetingUpdate,
    ParticipantInfo,
)
from app.services.audit_service import log_action
from app.services.file_processor import ALLOWED_AUDIO_EXTENSIONS, validate_file
from app.services.speech import get_speech_service
from app.services.ai import get_ai_service
from app.models.summary import MeetingSummary
from app.models.decision import Decision
from app.models.task import Task

router = APIRouter(prefix="/api/meetings", tags=["Meetings"])
settings = get_settings()


def _build_meeting_response(meeting: Meeting, db: Session) -> MeetingResponse:
    """Build a MeetingResponse with aggregated data."""
    participants = []
    for p in meeting.participants:
        user = db.query(User).filter(User.id == p.user_id).first()
        participants.append(ParticipantInfo(
            id=p.id,
            user_id=p.user_id,
            user_name=user.name if user else "Unknown",
            user_email=user.email if user else "",
            role_in_meeting=p.role_in_meeting,
            joined_at=p.joined_at,
            left_at=p.left_at,
        ))

    host = db.query(User).filter(User.id == meeting.host_id).first()
    task_count = db.query(Task).filter(Task.meeting_id == meeting.id).count()

    return MeetingResponse(
        id=meeting.id,
        title=meeting.title,
        description=meeting.description,
        meeting_type=meeting.meeting_type,
        host_id=meeting.host_id,
        host_name=host.name if host else None,
        room_id=meeting.room_id,
        meeting_date=meeting.meeting_date,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        status=meeting.status,
        source_type=meeting.source_type,
        created_at=meeting.created_at,
        participants=participants,
        has_transcript=meeting.transcript is not None,
        has_summary=meeting.summary is not None,
        task_count=task_count,
    )


@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
def create_meeting(
    req: MeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Create a new meeting."""
    room_id = str(uuid.uuid4())[:12] if req.meeting_type == "INTERNAL" else None

    meeting = Meeting(
        title=req.title,
        description=req.description,
        meeting_type=req.meeting_type,
        host_id=current_user.id,
        room_id=room_id,
        meeting_date=req.meeting_date,
        status="SCHEDULED",
    )
    db.add(meeting)
    db.flush()

    # Add host as participant
    host_participant = MeetingParticipant(
        meeting_id=meeting.id,
        user_id=current_user.id,
        role_in_meeting="HOST",
    )
    db.add(host_participant)

    # Add invited participants
    if req.participant_ids:
        for uid in req.participant_ids:
            if uid == current_user.id:
                continue
            user = db.query(User).filter(User.id == uid).first()
            if user:
                participant = MeetingParticipant(
                    meeting_id=meeting.id,
                    user_id=uid,
                    role_in_meeting="PARTICIPANT",
                )
                db.add(participant)

    db.commit()
    db.refresh(meeting)

    log_action(db, current_user.id, "CREATE_MEETING", "meeting", meeting.id)

    return _build_meeting_response(meeting, db)


@router.get("", response_model=MeetingListResponse)
def list_meetings(
    status_filter: str = None,
    meeting_type: str = None,
    search: str = None,
    person_id: int = None,
    date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List meetings visible to the current user."""
    query = db.query(Meeting)

    if current_user.role == "EMPLOYEE":
        # Employees see only meetings they participate in
        participant_meeting_ids = (
            db.query(MeetingParticipant.meeting_id)
            .filter(MeetingParticipant.user_id == current_user.id)
            .subquery()
        )
        query = query.filter(Meeting.id.in_(participant_meeting_ids))
    elif current_user.role == "MANAGER":
        # Managers see meetings they host or participate in
        participant_meeting_ids = (
            db.query(MeetingParticipant.meeting_id)
            .filter(MeetingParticipant.user_id == current_user.id)
            .subquery()
        )
        query = query.filter(
            (Meeting.host_id == current_user.id) | (Meeting.id.in_(participant_meeting_ids))
        )
    # ADMIN sees all

    if status_filter:
        query = query.filter(Meeting.status == status_filter.upper())

    if meeting_type:
        query = query.filter(Meeting.meeting_type == meeting_type.upper())

    if person_id:
        query = query.filter(Meeting.participants.any(MeetingParticipant.user_id == person_id))

    if date:
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(Meeting.meeting_date == parsed_date)
        except ValueError:
            pass

    if search:
        search_term = f"%{search}%"
        has_transcript = db.query(Transcript.id).filter(
            Transcript.meeting_id == Meeting.id,
            Transcript.content.ilike(search_term)
        ).exists()

        has_summary = db.query(MeetingSummary.id).filter(
            MeetingSummary.meeting_id == Meeting.id,
            or_(
                MeetingSummary.summary.ilike(search_term),
                cast(MeetingSummary.key_points, String).ilike(search_term)
            )
        ).exists()

        has_decision = db.query(Decision.id).filter(
            Decision.meeting_id == Meeting.id,
            or_(
                Decision.decision_text.ilike(search_term),
                Decision.decision_context.ilike(search_term)
            )
        ).exists()

        query = query.filter(
            or_(
                Meeting.title.ilike(search_term),
                Meeting.description.ilike(search_term),
                has_transcript,
                has_summary,
                has_decision
            )
        )

    meetings = query.order_by(Meeting.created_at.desc()).all()
    return MeetingListResponse(
        meetings=[_build_meeting_response(m, db) for m in meetings],
        total=len(meetings),
    )


@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific meeting by ID."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return _build_meeting_response(meeting, db)


@router.put("/{meeting_id}", response_model=MeetingResponse)
def update_meeting(
    meeting_id: int,
    updates: MeetingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Update meeting details."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.role == "MANAGER" and meeting.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the host can update this meeting")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meeting, field, value)

    db.commit()
    db.refresh(meeting)
    return _build_meeting_response(meeting, db)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Delete a meeting."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.role == "MANAGER" and meeting.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the host can delete this meeting")

    db.delete(meeting)
    db.commit()


# --- Participants ---

@router.post("/{meeting_id}/participants")
def add_participants(
    meeting_id: int,
    req: AddParticipantsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Add participants to a meeting."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    added = []
    for uid in req.user_ids:
        existing = db.query(MeetingParticipant).filter(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == uid,
        ).first()
        if existing:
            continue

        user = db.query(User).filter(User.id == uid).first()
        if not user:
            continue

        p = MeetingParticipant(
            meeting_id=meeting_id,
            user_id=uid,
            role_in_meeting="PARTICIPANT",
        )
        db.add(p)
        added.append(uid)

    db.commit()
    return {"added": added, "meeting_id": meeting_id}


@router.get("/{meeting_id}/participants")
def get_participants(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List participants in a meeting."""
    participants = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id
    ).all()

    result = []
    for p in participants:
        user = db.query(User).filter(User.id == p.user_id).first()
        result.append(ParticipantInfo(
            id=p.id,
            user_id=p.user_id,
            user_name=user.name if user else "Unknown",
            user_email=user.email if user else "",
            role_in_meeting=p.role_in_meeting,
            joined_at=p.joined_at,
            left_at=p.left_at,
        ))

    return result


# --- Start / End Meeting ---

@router.post("/{meeting_id}/start")
def start_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Start a meeting — sets status to IN_PROGRESS.

    Idempotent: if the meeting is already IN_PROGRESS the current state is
    returned without overwriting the original start_time.
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.status == "IN_PROGRESS":
        return {"status": "started", "room_id": meeting.room_id}

    meeting.status = "IN_PROGRESS"
    meeting.start_time = datetime.now(timezone.utc)
    db.commit()
    db.refresh(meeting)

    log_action(db, current_user.id, "START_MEETING", "meeting", meeting.id)

    return {"status": "started", "room_id": meeting.room_id}


@router.post("/{meeting_id}/end")
def end_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """End a meeting — sets status to COMPLETED."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    meeting.status = "COMPLETED"
    meeting.end_time = datetime.now(timezone.utc)
    db.commit()
    db.refresh(meeting)

    log_action(db, current_user.id, "END_MEETING", "meeting", meeting.id)

    return {"status": "completed", "meeting_id": meeting.id}


# --- Audio Upload ---

@router.post("/{meeting_id}/audio")
async def upload_audio(
    meeting_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Upload meeting audio for speech-to-text processing."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Read file to get size
    content = await file.read()
    file_size = len(content)

    try:
        validate_file(file.filename, file_size, ALLOWED_AUDIO_EXTENSIONS, settings.MAX_UPLOAD_SIZE_MB)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save audio file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    audio_filename = f"meeting_{meeting_id}_{uuid.uuid4().hex[:8]}{ext}"
    audio_path = os.path.join(settings.UPLOAD_DIR, audio_filename)

    with open(audio_path, "wb") as f:
        f.write(content)

    # Update meeting source type
    source_type = "INTERNAL_AUDIO" if meeting.meeting_type == "INTERNAL" else "UPLOADED_AUDIO"
    meeting.source_type = source_type

    # Speech-to-text
    try:
        stt_service = get_speech_service()
        transcript_text = stt_service.transcribe(audio_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {e}")

    # Save transcript
    existing_transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    if existing_transcript:
        existing_transcript.content = transcript_text
        existing_transcript.source = "AUTO_RECORDED" if source_type == "INTERNAL_AUDIO" else "UPLOADED_AUDIO"
        existing_transcript.processed_at = datetime.now(timezone.utc)
    else:
        transcript = Transcript(
            meeting_id=meeting_id,
            source="AUTO_RECORDED" if source_type == "INTERNAL_AUDIO" else "UPLOADED_AUDIO",
            content=transcript_text,
            language="en",
            processed_at=datetime.now(timezone.utc),
        )
        db.add(transcript)

    db.commit()

    log_action(db, current_user.id, "UPLOAD_AUDIO", "meeting", meeting_id)

    # Audio file is retained for potential re-processing or download (Phase 3).
    # No cleanup is performed here.

    return {
        "status": "processed",
        "meeting_id": meeting_id,
        "transcript_preview": transcript_text[:200] + "..." if len(transcript_text) > 200 else transcript_text,
    }


