"""Dashboard routes — role-specific dashboard data."""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.audit_log import AuditLog
from app.models.meeting import Meeting
from app.models.notification import Notification
from app.models.task import Task
from app.models.user import User
from app.schemas.dashboard import AdminDashboard, EmployeeDashboard, ManagerDashboard

router = APIRouter(prefix="/api/dashboard", tags=["Dashboards"])


@router.get("/employee", response_model=EmployeeDashboard)
def employee_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get employee dashboard data."""
    today = date.today()

    my_tasks = db.query(Task).filter(
        Task.assigned_to == current_user.id,
        Task.status.notin_(["PENDING_REVIEW", "REJECTED"]),
    ).all()

    pending = [t for t in my_tasks if t.status in ("PENDING", "CONFIRMED")]
    in_progress = [t for t in my_tasks if t.status == "IN_PROGRESS"]
    completed = [t for t in my_tasks if t.status == "COMPLETED"]
    overdue = [t for t in my_tasks if t.deadline and t.deadline < today and t.status not in ("COMPLETED", "REJECTED")]

    # Upcoming deadlines (next 7 days)
    week_from_now = today + timedelta(days=7)
    upcoming = [
        {"id": t.id, "title": t.title, "deadline": str(t.deadline), "priority": t.priority}
        for t in my_tasks
        if t.deadline and today <= t.deadline <= week_from_now and t.status not in ("COMPLETED", "REJECTED")
    ]

    recent_tasks = sorted(my_tasks, key=lambda t: t.created_at, reverse=True)[:5]

    # Recent meetings
    from app.models.participant import MeetingParticipant
    participant_meetings = (
        db.query(Meeting)
        .join(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
        .filter(MeetingParticipant.user_id == current_user.id)
        .order_by(Meeting.created_at.desc())
        .limit(5)
        .all()
    )

    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .order_by(Notification.created_at.desc())
        .limit(10)
        .all()
    )

    return EmployeeDashboard(
        total_tasks=len(my_tasks),
        pending_tasks=len(pending),
        in_progress_tasks=len(in_progress),
        completed_tasks=len(completed),
        overdue_tasks=len(overdue),
        upcoming_deadlines=upcoming,
        recent_tasks=[
            {"id": t.id, "title": t.title, "status": t.status, "priority": t.priority,
             "deadline": str(t.deadline) if t.deadline else None,
             "meeting_title": t.meeting.title if t.meeting else None}
            for t in recent_tasks
        ],
        recent_meetings=[
            {"id": m.id, "title": m.title, "date": str(m.meeting_date) if m.meeting_date else None,
             "status": m.status}
            for m in participant_meetings
        ],
        notifications=[
            {"id": n.id, "message": n.message, "type": n.type, "created_at": str(n.created_at)}
            for n in notifications
        ],
    )


@router.get("/manager", response_model=ManagerDashboard)
def manager_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "MANAGER")),
):
    """Get manager dashboard data."""
    today = date.today()
    week_ago = today - timedelta(days=7)

    # Meetings
    all_meetings = db.query(Meeting).filter(Meeting.host_id == current_user.id).all()
    meetings_this_week = [
        m for m in all_meetings
        if m.created_at and m.created_at.date() >= week_ago
    ]

    # All tasks (created by this manager or from their meetings)
    meeting_ids = [m.id for m in all_meetings]
    all_tasks = db.query(Task).filter(
        (Task.created_by == current_user.id) | (Task.meeting_id.in_(meeting_ids))
    ).all()

    active = [t for t in all_tasks if t.status in ("PENDING", "IN_PROGRESS", "CONFIRMED")]
    completed = [t for t in all_tasks if t.status == "COMPLETED"]
    overdue = [t for t in all_tasks if t.deadline and t.deadline < today and t.status not in ("COMPLETED", "REJECTED")]
    pending_reviews = [t for t in all_tasks if t.status == "PENDING_REVIEW"]

    total_non_review = [t for t in all_tasks if t.status not in ("PENDING_REVIEW", "REJECTED")]
    completion_rate = (len(completed) / len(total_non_review) * 100) if total_non_review else 0

    # Tasks by status
    status_counts = {}
    for t in all_tasks:
        status_counts[t.status] = status_counts.get(t.status, 0) + 1

    # Tasks by priority
    priority_counts = {}
    for t in all_tasks:
        priority_counts[t.priority] = priority_counts.get(t.priority, 0) + 1

    # Team workload
    workload = {}
    for t in all_tasks:
        if t.assigned_to and t.assignee and t.status not in ("COMPLETED", "REJECTED"):
            name = t.assignee.name
            workload[name] = workload.get(name, 0) + 1

    team_workload = [{"name": k, "tasks": v} for k, v in workload.items()]

    # Recent meetings
    recent = sorted(all_meetings, key=lambda m: m.created_at, reverse=True)[:5]

    # --- Completion trend (last 30 days) ---
    thirty_days_ago = today - timedelta(days=29)  # inclusive today = 30 days
    # Build a dict of date -> count for completed tasks in manager scope
    completion_counts: dict[date, int] = {}
    for t in completed:
        if t.completed_at:
            d = t.completed_at.date() if hasattr(t.completed_at, 'date') else t.completed_at
            if thirty_days_ago <= d <= today:
                completion_counts[d] = completion_counts.get(d, 0) + 1

    # Build the continuous 30-day list (zero-fill missing dates)
    completion_trend = []
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        completion_trend.append({"date": d.isoformat(), "count": completion_counts.get(d, 0)})

    # --- Meeting activity trend (last 30 days) ---
    meeting_counts: dict[date, int] = {}
    for m in all_meetings:
        if m.created_at:
            d = m.created_at.date() if hasattr(m.created_at, 'date') else m.created_at
            if thirty_days_ago <= d <= today:
                meeting_counts[d] = meeting_counts.get(d, 0) + 1

    meeting_activity = []
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        meeting_activity.append({"date": d.isoformat(), "count": meeting_counts.get(d, 0)})

    return ManagerDashboard(
        total_meetings=len(all_meetings),
        meetings_this_week=len(meetings_this_week),
        active_tasks=len(active),
        completed_tasks=len(completed),
        overdue_tasks=len(overdue),
        pending_reviews=len(pending_reviews),
        completion_rate=round(completion_rate, 1),
        tasks_by_status=status_counts,
        tasks_by_priority=priority_counts,
        team_workload=team_workload,
        recent_meetings=[
            {"id": m.id, "title": m.title, "date": str(m.meeting_date) if m.meeting_date else None,
             "status": m.status, "type": m.meeting_type}
            for m in recent
        ],
        completion_trend=completion_trend,
        meeting_activity=meeting_activity,
    )


@router.get("/admin", response_model=AdminDashboard)
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    """Get admin dashboard data."""
    total_users = db.query(User).count()

    role_counts = {}
    for role in ["ADMIN", "MANAGER", "EMPLOYEE"]:
        role_counts[role] = db.query(User).filter(User.role == role).count()

    total_meetings = db.query(Meeting).count()
    total_tasks = db.query(Task).filter(Task.status != "PENDING_REVIEW").count()
    completed_tasks = db.query(Task).filter(Task.status == "COMPLETED").count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks else 0

    # Meeting types
    meetings_by_type = {}
    for mt in ["INTERNAL", "EXTERNAL"]:
        meetings_by_type[mt] = db.query(Meeting).filter(Meeting.meeting_type == mt).count()

    # Tasks by status
    tasks_by_status = {}
    for s in ["PENDING", "IN_PROGRESS", "COMPLETED", "REJECTED"]:
        tasks_by_status[s] = db.query(Task).filter(Task.status == s).count()

    # Recent activity
    recent_logs = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(10)
        .all()
    )

    # Overdue and Pending Reviews
    today = date.today()
    overdue_tasks = db.query(Task).filter(Task.deadline < today, Task.status.not_in(["COMPLETED", "REJECTED"])).count()
    pending_reviews = db.query(Task).filter(Task.status == "PENDING_REVIEW").count()

    # AI vs Manual
    ai_tasks = db.query(Task).filter(Task.source == "AI_EXTRACTED").count()
    manual_tasks = db.query(Task).filter(Task.source == "MANUAL").count()
    ai_vs_manual_tasks = {"AI_EXTRACTED": ai_tasks, "MANUAL": manual_tasks}

    # Trends (last 30 days)
    thirty_days_ago = today - timedelta(days=29)

    # User growth
    recent_users = db.query(User).filter(User.created_at >= thirty_days_ago).all()
    user_counts: dict[date, int] = {}
    for u in recent_users:
        if u.created_at:
            d = u.created_at.date() if hasattr(u.created_at, 'date') else u.created_at
            if thirty_days_ago <= d <= today:
                user_counts[d] = user_counts.get(d, 0) + 1

    user_growth_trend = []
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        user_growth_trend.append({"date": d.isoformat(), "count": user_counts.get(d, 0)})

    # System Activity (Meetings created & Tasks completed)
    recent_meetings = db.query(Meeting).filter(Meeting.created_at >= thirty_days_ago).all()
    recent_completed_tasks = db.query(Task).filter(Task.status == "COMPLETED", Task.completed_at >= thirty_days_ago).all()

    meeting_counts: dict[date, int] = {}
    task_counts: dict[date, int] = {}

    for m in recent_meetings:
        if m.created_at:
            d = m.created_at.date() if hasattr(m.created_at, 'date') else m.created_at
            if thirty_days_ago <= d <= today:
                meeting_counts[d] = meeting_counts.get(d, 0) + 1

    for t in recent_completed_tasks:
        if t.completed_at:
            d = t.completed_at.date() if hasattr(t.completed_at, 'date') else t.completed_at
            if thirty_days_ago <= d <= today:
                task_counts[d] = task_counts.get(d, 0) + 1

    system_activity_trend = []
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        system_activity_trend.append({
            "date": d.isoformat(),
            "meetings_created": meeting_counts.get(d, 0),
            "tasks_completed": task_counts.get(d, 0)
        })

    return AdminDashboard(
        total_users=total_users,
        users_by_role=role_counts,
        total_meetings=total_meetings,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        completion_rate=round(completion_rate, 1),
        recent_activity=[
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "entity_type": log.entity_type,
                "timestamp": str(log.timestamp),
            }
            for log in recent_logs
        ],
        meetings_by_type=meetings_by_type,
        tasks_by_status=tasks_by_status,
        overdue_tasks=overdue_tasks,
        pending_reviews=pending_reviews,
        user_growth_trend=user_growth_trend,
        system_activity_trend=system_activity_trend,
        ai_vs_manual_tasks=ai_vs_manual_tasks,
    )
