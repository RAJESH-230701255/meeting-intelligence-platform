"""Task routes — CRUD, status updates, filtering."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.audit_service import log_action
from app.services.notification_service import notify_task_assigned

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


def _task_to_response(task: Task) -> TaskResponse:
    """Convert Task model to TaskResponse."""
    return TaskResponse(
        id=task.id,
        meeting_id=task.meeting_id,
        assigned_to=task.assigned_to,
        assignee_name=task.assignee.name if task.assignee else None,
        created_by=task.created_by,
        creator_name=task.creator.name if task.creator else None,
        title=task.title,
        description=task.description,
        deadline=task.deadline,
        priority=task.priority,
        status=task.status,
        source_text=task.source_text,
        ai_confidence=task.ai_confidence,
        source=task.source,
        meeting_title=task.meeting.title if task.meeting else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status_filter: str = None,
    priority: str = None,
    assigned_to: int = None,
    meeting_id: int = None,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tasks based on role and filters."""
    query = db.query(Task)

    if current_user.role == "EMPLOYEE":
        query = query.filter(Task.assigned_to == current_user.id)
        # Employees don't see PENDING_REVIEW or REJECTED
        query = query.filter(Task.status.notin_(["PENDING_REVIEW", "REJECTED"]))

    if status_filter:
        query = query.filter(Task.status == status_filter.upper())

    if priority:
        query = query.filter(Task.priority == priority.upper())

    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)

    if meeting_id:
        query = query.filter(Task.meeting_id == meeting_id)

    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    tasks = query.order_by(Task.created_at.desc()).all()
    return TaskListResponse(
        tasks=[_task_to_response(t) for t in tasks],
        total=len(tasks),
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Employees can only see their own tasks
    if current_user.role == "EMPLOYEE" and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return _task_to_response(task)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    req: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Manually create a task."""
    task = Task(
        title=req.title,
        description=req.description,
        assigned_to=req.assigned_to,
        created_by=current_user.id,
        meeting_id=req.meeting_id,
        deadline=req.deadline,
        priority=req.priority,
        status="PENDING",
        source="MANUAL",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    log_action(db, current_user.id, "CREATE_TASK", "task", task.id)

    # Notify assignee
    if task.assigned_to:
        notify_task_assigned(db, task.assigned_to, task.id, task.title)

    return _task_to_response(task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    updates: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a task. Employees can only update status of their own tasks."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role == "EMPLOYEE":
        if task.assigned_to != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        # Employees can only update status
        if updates.status:
            allowed_transitions = {
                "PENDING": ["IN_PROGRESS"],
                "IN_PROGRESS": ["COMPLETED", "PENDING"],
                "CONFIRMED": ["IN_PROGRESS", "PENDING"],
            }
            allowed = allowed_transitions.get(task.status, [])
            if updates.status not in allowed:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot change status from {task.status} to {updates.status}",
                )
            task.status = updates.status
            if updates.status == "COMPLETED":
                task.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(task)
        return _task_to_response(task)

    # Manager/Admin can update any field
    update_data = updates.model_dump(exclude_unset=True)

    old_assignee = task.assigned_to

    for field, value in update_data.items():
        setattr(task, field, value)

    if updates.status == "COMPLETED":
        task.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)

    log_action(db, current_user.id, "UPDATE_TASK", "task", task.id)

    # Notify if reassigned
    if task.assigned_to and task.assigned_to != old_assignee:
        notify_task_assigned(db, task.assigned_to, task.id, task.title)

    return _task_to_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Delete a task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
