"""Tests for Admin Dashboard analytics — Phase 4.2."""

from datetime import date, datetime, timedelta, timezone

from app.models.meeting import Meeting
from app.models.task import Task
from app.models.user import User


class TestAdminDashboardAnalytics:
    """Test new analytics in the Admin Dashboard."""

    def test_admin_receives_30_entries_for_trends(self, client_as, db_session, admin_user):
        c = client_as(admin_user)
        res = c.get("/api/dashboard/admin")
        assert res.status_code == 200
        data = res.json()

        assert "user_growth_trend" in data
        assert "system_activity_trend" in data
        assert len(data["user_growth_trend"]) == 30
        assert len(data["system_activity_trend"]) == 30

    def test_zero_filled_dates_work(self, client_as, db_session, admin_user):
        c = client_as(admin_user)
        res = c.get("/api/dashboard/admin")
        data = res.json()

        # The admin user was created today, so one day might not be 0.
        # But we can verify all entries have 'count' or 'meetings_created' etc as ints
        for entry in data["user_growth_trend"]:
            assert "date" in entry
            assert isinstance(entry["count"], int)
            assert entry["count"] >= 0

        for entry in data["system_activity_trend"]:
            assert "date" in entry
            assert isinstance(entry["meetings_created"], int)
            assert isinstance(entry["tasks_completed"], int)
            assert entry["meetings_created"] >= 0
            assert entry["tasks_completed"] >= 0

    def test_user_growth_counts_are_correct(self, client_as, db_session, admin_user):
        # Admin user is already created recently. Let's add another user manually today.
        today = date.today()
        new_user = User(
            name="Newbie",
            email="newbie@test.com",
            password_hash="fake",
            role="EMPLOYEE",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(new_user)
        db_session.commit()

        c = client_as(admin_user)
        res = c.get("/api/dashboard/admin")
        data = res.json()

        # Check total users in last 30 days includes new_user
        # (It also includes admin_user because fixtures create them on the fly for each test)
        total_growth = sum(entry["count"] for entry in data["user_growth_trend"])
        assert total_growth >= 1

    def test_meeting_and_task_activity_counts_are_correct(self, client_as, db_session, admin_user):
        # Create a meeting today
        m = Meeting(
            title="Activity Meeting",
            host_id=admin_user.id,
            meeting_type="INTERNAL",
            status="COMPLETED",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(m)
        db_session.commit()
        db_session.refresh(m)

        # Create a completed task today
        t = Task(
            title="Activity Task",
            meeting_id=m.id,
            assigned_to=admin_user.id,
            created_by=admin_user.id,
            status="COMPLETED",
            priority="HIGH",
            source="AI_EXTRACTED",
            completed_at=datetime.now(timezone.utc)
        )
        db_session.add(t)
        db_session.commit()

        c = client_as(admin_user)
        res = c.get("/api/dashboard/admin")
        data = res.json()

        total_meetings = sum(entry["meetings_created"] for entry in data["system_activity_trend"])
        total_tasks = sum(entry["tasks_completed"] for entry in data["system_activity_trend"])

        assert total_meetings >= 1
        assert total_tasks >= 1

    def test_overdue_task_count(self, client_as, db_session, admin_user):
        # Overdue task
        t_overdue = Task(
            title="Overdue",
            created_by=admin_user.id,
            status="PENDING",
            deadline=date.today() - timedelta(days=2)
        )
        db_session.add(t_overdue)
        db_session.commit()

        c = client_as(admin_user)
        res = c.get("/api/dashboard/admin")
        data = res.json()

        assert data["overdue_tasks"] >= 1

    def test_pending_ai_review_count(self, client_as, db_session, admin_user):
        t_pending_review = Task(
            title="Pending Review",
            created_by=admin_user.id,
            status="PENDING_REVIEW"
        )
        db_session.add(t_pending_review)
        db_session.commit()

        c = client_as(admin_user)
        res = c.get("/api/dashboard/admin")
        data = res.json()

        assert data["pending_reviews"] >= 1

    def test_ai_vs_manual_counts(self, client_as, db_session, admin_user):
        t_ai = Task(title="AI", created_by=admin_user.id, source="AI_EXTRACTED")
        t_manual = Task(title="Manual", created_by=admin_user.id, source="MANUAL")
        db_session.add_all([t_ai, t_manual])
        db_session.commit()

        c = client_as(admin_user)
        res = c.get("/api/dashboard/admin")
        data = res.json()

        assert "ai_vs_manual_tasks" in data
        assert "AI_EXTRACTED" in data["ai_vs_manual_tasks"]
        assert "MANUAL" in data["ai_vs_manual_tasks"]
        assert data["ai_vs_manual_tasks"]["AI_EXTRACTED"] >= 1
        assert data["ai_vs_manual_tasks"]["MANUAL"] >= 1

    def test_existing_metrics_remain_correct(self, client_as, db_session, admin_user):
        c = client_as(admin_user)
        res = c.get("/api/dashboard/admin")
        data = res.json()

        expected_fields = [
            "total_users",
            "users_by_role",
            "total_meetings",
            "total_tasks",
            "completed_tasks",
            "completion_rate",
            "meetings_by_type",
            "tasks_by_status",
            "recent_activity"
        ]
        for field in expected_fields:
            assert field in data

    def test_admin_sees_system_wide_data(self, client_as, db_session, admin_user, employee_user):
        # Create a task as an employee. The admin should still see it in system-wide stats.
        t_emp = Task(
            title="Emp Task",
            created_by=employee_user.id,
            status="PENDING_REVIEW",
            source="AI_EXTRACTED"
        )
        db_session.add(t_emp)
        db_session.commit()

        c = client_as(admin_user)
        res = c.get("/api/dashboard/admin")
        data = res.json()

        assert data["pending_reviews"] >= 1
        assert data["ai_vs_manual_tasks"]["AI_EXTRACTED"] >= 1

    def test_manager_cannot_access_admin_dashboard(self, client_as, db_session, manager_user):
        c = client_as(manager_user)
        res = c.get("/api/dashboard/admin")
        assert res.status_code == 403

    def test_employee_cannot_access_admin_dashboard(self, client_as, db_session, employee_user):
        c = client_as(employee_user)
        res = c.get("/api/dashboard/admin")
        assert res.status_code == 403

    def test_empty_data_does_not_crash(self, client_as, db_session):
        # Creating a fresh admin in an empty DB context
        u = User(name="A", email="a@a.com", password_hash="1", role="ADMIN")
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)

        c = client_as(u)
        res = c.get("/api/dashboard/admin")
        assert res.status_code == 200
        data = res.json()
        assert len(data["user_growth_trend"]) == 30
