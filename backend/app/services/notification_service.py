"""Notification service — create and manage in-app notifications."""

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: int,
    message: str,
    notification_type: str = "GENERAL",
    task_id: int = None,
) -> Notification:
    """Create a new notification for a user."""
    notification = Notification(
        user_id=user_id,
        task_id=task_id,
        type=notification_type,
        message=message,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def notify_task_assigned(db: Session, user_id: int, task_id: int, task_title: str):
    """Notify a user that a task has been assigned to them."""
    return create_notification(
        db=db,
        user_id=user_id,
        task_id=task_id,
        notification_type="TASK_ASSIGNED",
        message=f'You have been assigned a new task: "{task_title}"',
    )


def notify_task_confirmed(db: Session, user_id: int, task_id: int, task_title: str):
    """Notify user that their action item was confirmed."""
    return create_notification(
        db=db,
        user_id=user_id,
        task_id=task_id,
        notification_type="TASK_CONFIRMED",
        message=f'Action item confirmed as task: "{task_title}"',
    )


def notify_deadline_approaching(db: Session, user_id: int, task_id: int, task_title: str):
    """Notify user about approaching deadline."""
    return create_notification(
        db=db,
        user_id=user_id,
        task_id=task_id,
        notification_type="DEADLINE_APPROACHING",
        message=f'Your task deadline is tomorrow: "{task_title}"',
    )


def notify_task_overdue(db: Session, user_id: int, task_id: int, task_title: str):
    """Notify user about overdue task."""
    return create_notification(
        db=db,
        user_id=user_id,
        task_id=task_id,
        notification_type="TASK_OVERDUE",
        message=f'Your task is overdue: "{task_title}"',
    )
