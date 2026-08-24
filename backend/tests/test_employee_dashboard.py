from datetime import date, datetime, timedelta, timezone
import pytest

from app.models.task import Task
from app.models.meeting import Meeting

def test_employee_dashboard_empty_data(client_as, employee_user):
    client = client_as(employee_user)
    response = client.get("/api/dashboard/employee")
    assert response.status_code == 200
    data = response.json()

    assert "tasks_by_status" in data
    assert "tasks_by_priority" in data
    assert "completion_trend" in data

    assert data["tasks_by_status"] == {}
    assert data["tasks_by_priority"] == {}
    assert len(data["completion_trend"]) == 30
    assert all(entry["count"] == 0 for entry in data["completion_trend"])
    assert data["total_tasks"] == 0

def test_employee_dashboard_analytics_scoping(db_session, client_as, employee_user, manager_user):
    # Create another employee user to test scoping
    from app.models.user import User
    other_employee = User(
        name="Other Employee",
        email="other@test.com",
        password_hash="fakehash",
        role="EMPLOYEE",
        is_active=True,
    )
    db_session.add(other_employee)
    db_session.commit()
    db_session.refresh(other_employee)

    today = date.today()
    thirty_days_ago = today - timedelta(days=29)
    five_days_ago = today - timedelta(days=5)

    # 1. Task for current employee (COMPLETED recently)
    t1 = Task(
        title="My Task 1",
        assigned_to=employee_user.id,
        created_by=manager_user.id,
        priority="HIGH",
        status="COMPLETED",
        completed_at=datetime.combine(five_days_ago, datetime.min.time(), tzinfo=timezone.utc),
    )
    # 2. Task for current employee (IN_PROGRESS)
    t2 = Task(
        title="My Task 2",
        assigned_to=employee_user.id,
        created_by=manager_user.id,
        priority="URGENT",
        status="IN_PROGRESS",
    )
    # 3. Task for another employee
    t3 = Task(
        title="Other Task",
        assigned_to=other_employee.id,
        created_by=manager_user.id,
        priority="LOW",
        status="COMPLETED",
        completed_at=datetime.combine(five_days_ago, datetime.min.time(), tzinfo=timezone.utc),
    )

    db_session.add_all([t1, t2, t3])
    db_session.commit()

    client = client_as(employee_user)
    response = client.get("/api/dashboard/employee")
    assert response.status_code == 200
    data = response.json()

    # Verify tasks_by_status only includes employee's tasks
    assert data["tasks_by_status"] == {"COMPLETED": 1, "IN_PROGRESS": 1}
    assert "PENDING" not in data["tasks_by_status"]

    # Verify tasks_by_priority only includes employee's tasks
    assert data["tasks_by_priority"] == {"HIGH": 1, "URGENT": 1}

    # Verify completion_trend
    assert len(data["completion_trend"]) == 30

    # Find the entry for five_days_ago
    five_days_ago_iso = five_days_ago.isoformat()
    five_days_entry = next(entry for entry in data["completion_trend"] if entry["date"] == five_days_ago_iso)

    # It should only count t1, not t3
    assert five_days_entry["count"] == 1

    # Check another date to ensure zero-filling works
    four_days_ago_iso = (today - timedelta(days=4)).isoformat()
    four_days_entry = next(entry for entry in data["completion_trend"] if entry["date"] == four_days_ago_iso)
    assert four_days_entry["count"] == 0

    # Verify existing metrics remain correct
    assert data["total_tasks"] == 2 # total tasks for the employee not in PENDING_REVIEW or REJECTED
    assert data["in_progress_tasks"] == 1
    assert data["completed_tasks"] == 1
    assert data["pending_tasks"] == 0

def test_employee_dashboard_rbac(client_as, admin_user):
    # Only employees, managers and admins can hit their respective dashboards.
    # Actually employee_dashboard might be hit by any authenticated user because
    # get_current_user is the dependency. Let's check the dependency.
    # Wait, the route says `current_user: User = Depends(get_current_user)`.
    # It doesn't restrict by role in the route itself.
    # So if an admin hits it, they get an empty dashboard because they have no assigned tasks.
    client = client_as(admin_user)
    response = client.get("/api/dashboard/employee")
    assert response.status_code == 200
    assert response.json()["total_tasks"] == 0
