"""Dashboard schemas."""

from typing import Optional

from pydantic import BaseModel


class EmployeeDashboard(BaseModel):
    total_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0
    upcoming_deadlines: list[dict] = []
    recent_tasks: list[dict] = []
    recent_meetings: list[dict] = []
    notifications: list[dict] = []


class ManagerDashboard(BaseModel):
    total_meetings: int = 0
    meetings_this_week: int = 0
    active_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0
    pending_reviews: int = 0
    completion_rate: float = 0.0
    tasks_by_status: dict = {}
    tasks_by_priority: dict = {}
    team_workload: list[dict] = []
    recent_meetings: list[dict] = []
    completion_trend: list[dict] = []
    meeting_activity: list[dict] = []


class AdminDashboard(BaseModel):
    total_users: int = 0
    users_by_role: dict = {}
    total_meetings: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    completion_rate: float = 0.0
    recent_activity: list[dict] = []
    meetings_by_type: dict = {}
    tasks_by_status: dict = {}

    overdue_tasks: int = 0
    pending_reviews: int = 0
    user_growth_trend: list[dict] = []
    system_activity_trend: list[dict] = []
    ai_vs_manual_tasks: dict = {}