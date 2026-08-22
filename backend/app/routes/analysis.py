"""Analysis routes — trigger AI analysis, view results, manage action items."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.decision import Decision
from app.models.meeting import Meeting
from app.models.summary import MeetingSummary
from app.models.task import Task
from app.models.transcript import Transcript
from app.models.user import User
from app.schemas.analysis import AnalysisResponse
from app.schemas.task import ConfirmActionItemRequest, TaskResponse
from app.services.ai import get_ai_service
from app.services.audit_service import log_action
from app.services.notification_service import notify_task_assigned, notify_task_confirmed

router = APIRouter(tags=["Analysis"])


@router.post("/api/meetings/{meeting_id}/analyze", response_model=AnalysisResponse)
def analyze_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Run the AI Meeting Intelligence pipeline on a meeting's transcript."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    if not transcript:
        raise HTTPException(status_code=400, detail="No transcript available. Upload a transcript or audio first.")

    ai_service = get_ai_service()

    try:
        analysis = ai_service.analyze_transcript(transcript.content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")

    # Save/update summary
    existing_summary = db.query(MeetingSummary).filter(MeetingSummary.meeting_id == meeting_id).first()
    if existing_summary:
        existing_summary.summary = analysis.summary
        existing_summary.key_points = analysis.key_points
    else:
        summary = MeetingSummary(
            meeting_id=meeting_id,
            summary=analysis.summary,
            key_points=analysis.key_points,
        )
        db.add(summary)

    # Clear old decisions for re-analysis
    db.query(Decision).filter(Decision.meeting_id == meeting_id).delete()

    # Save decisions
    for dec in analysis.decisions:
        decision = Decision(
            meeting_id=meeting_id,
            decision_text=dec.decision,
            decision_context=dec.context,
        )
        db.add(decision)

    # Clear old PENDING_REVIEW AI-extracted tasks for re-analysis
    db.query(Task).filter(
        Task.meeting_id == meeting_id,
        Task.source == "AI_EXTRACTED",
        Task.status == "PENDING_REVIEW",
    ).delete()

    # Create new action item tasks
    from app.services.user_service import resolve_assignee
    for item in analysis.action_items:
        assigned_to = resolve_assignee(db, item.assignee_name)
        parsed_deadline = None
        if item.deadline:
            try:
                parsed_deadline = datetime.fromisoformat(item.deadline.replace('Z', '+00:00')).date()
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

    transcript.processed_at = datetime.now(timezone.utc)
    db.commit()

    log_action(db, current_user.id, "AI_ANALYSIS", "meeting", meeting_id)

    # Build response
    decisions = db.query(Decision).filter(Decision.meeting_id == meeting_id).all()
    tasks = db.query(Task).filter(
        Task.meeting_id == meeting_id, Task.source == "AI_EXTRACTED"
    ).all()

    return AnalysisResponse(
        meeting_id=meeting_id,
        summary=analysis.summary,
        key_points=analysis.key_points,
        decisions=[{"decision": d.decision_text, "context": d.decision_context} for d in decisions],
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


@router.get("/api/meetings/{meeting_id}/analysis", response_model=AnalysisResponse)
def get_analysis(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get existing AI analysis results for a meeting."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    summary = db.query(MeetingSummary).filter(MeetingSummary.meeting_id == meeting_id).first()
    decisions = db.query(Decision).filter(Decision.meeting_id == meeting_id).all()
    tasks = db.query(Task).filter(
        Task.meeting_id == meeting_id, Task.source == "AI_EXTRACTED"
    ).all()

    if not summary:
        raise HTTPException(status_code=404, detail="No analysis found. Run analysis first.")

    return AnalysisResponse(
        meeting_id=meeting_id,
        summary=summary.summary,
        key_points=summary.key_points or [],
        decisions=[{"decision": d.decision_text, "context": d.decision_context} for d in decisions],
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


@router.get("/api/meetings/{meeting_id}/action-items")
def get_action_items(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI-extracted action items for a meeting."""
    tasks = db.query(Task).filter(
        Task.meeting_id == meeting_id,
        Task.source == "AI_EXTRACTED",
    ).all()

    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "assignee_id": t.assigned_to,
            "assignee_name": t.assignee.name if t.assignee else "unresolved",
            "deadline": str(t.deadline) if t.deadline else None,
            "priority": t.priority,
            "status": t.status,
            "source_text": t.source_text,
            "confidence": t.ai_confidence,
        }
        for t in tasks
    ]


@router.post("/api/action-items/{task_id}/confirm")
def confirm_action_item(
    task_id: int,
    req: ConfirmActionItemRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Confirm an AI-extracted action item — it becomes a real task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Action item not found")

    if task.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail="Action item has already been processed")

    # Apply overrides if provided
    if req:
        if req.assigned_to is not None:
            task.assigned_to = req.assigned_to
        if req.deadline is not None:
            task.deadline = req.deadline
        if req.priority is not None:
            task.priority = req.priority
        if req.title is not None:
            task.title = req.title
        if req.description is not None:
            task.description = req.description

    task.status = "PENDING"
    db.commit()
    db.refresh(task)

    log_action(db, current_user.id, "CONFIRM_ACTION_ITEM", "task", task.id)

    # Notify assignee
    if task.assigned_to:
        notify_task_assigned(db, task.assigned_to, task.id, task.title)

    return {"status": "confirmed", "task_id": task.id}


@router.post("/api/action-items/{task_id}/reject")
def reject_action_item(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Reject an AI-extracted action item."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Action item not found")

    if task.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail="Action item has already been processed")

    task.status = "REJECTED"
    db.commit()

    log_action(db, current_user.id, "REJECT_ACTION_ITEM", "task", task.id)

    return {"status": "rejected", "task_id": task.id}


@router.put("/api/action-items/{task_id}")
def edit_action_item(
    task_id: int,
    req: ConfirmActionItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Edit an AI-extracted action item before confirming."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Action item not found")

    if task.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail="Can only edit items pending review")

    if req.assigned_to is not None:
        task.assigned_to = req.assigned_to
    if req.deadline is not None:
        task.deadline = req.deadline
    if req.priority is not None:
        task.priority = req.priority
    if req.title is not None:
        task.title = req.title
    if req.description is not None:
        task.description = req.description

    db.commit()
    db.refresh(task)

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "assigned_to": task.assigned_to,
        "deadline": str(task.deadline) if task.deadline else None,
        "priority": task.priority,
        "status": task.status,
    }
