import pytest
from app.models.task import Task
from app.models.user import User

def test_employee_task_list_visibility(db_session, client_as, employee_user, manager_user):
    """Verify employees do not see PENDING_REVIEW or REJECTED tasks in GET /api/tasks."""

    # 1. Create a PENDING task
    t1 = Task(
        title="Pending Task",
        assigned_to=employee_user.id,
        created_by=manager_user.id,
        priority="MEDIUM",
        status="PENDING",
    )
    # 2. Create an IN_PROGRESS task
    t2 = Task(
        title="In Progress Task",
        assigned_to=employee_user.id,
        created_by=manager_user.id,
        priority="HIGH",
        status="IN_PROGRESS",
    )
    # 3. Create a COMPLETED task
    t3 = Task(
        title="Completed Task",
        assigned_to=employee_user.id,
        created_by=manager_user.id,
        priority="LOW",
        status="COMPLETED",
    )
    # 4. Create a PENDING_REVIEW task
    t4 = Task(
        title="Pending Review Task",
        assigned_to=employee_user.id,
        created_by=manager_user.id,
        priority="URGENT",
        status="PENDING_REVIEW",
    )
    # 5. Create a REJECTED task
    t5 = Task(
        title="Rejected Task",
        assigned_to=employee_user.id,
        created_by=manager_user.id,
        priority="LOW",
        status="REJECTED",
    )

    db_session.add_all([t1, t2, t3, t4, t5])
    db_session.commit()

    # Employee should only see PENDING, IN_PROGRESS, COMPLETED
    client = client_as(employee_user)
    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3
    task_titles = [t["title"] for t in data["tasks"]]
    assert "Pending Task" in task_titles
    assert "In Progress Task" in task_titles
    assert "Completed Task" in task_titles
    assert "Pending Review Task" not in task_titles
    assert "Rejected Task" not in task_titles

    # Manager should see all tasks, but actually manager task list doesn't filter by assignee implicitly
    # unless assigned_to is provided. But it doesn't filter out PENDING_REVIEW or REJECTED either.
    # Let's verify manager sees PENDING_REVIEW and REJECTED.
    client_mgr = client_as(manager_user)
    mgr_response = client_mgr.get("/api/tasks")
    assert mgr_response.status_code == 200
    mgr_data = mgr_response.json()
    mgr_titles = [t["title"] for t in mgr_data["tasks"]]
    assert "Pending Review Task" in mgr_titles
    assert "Rejected Task" in mgr_titles
