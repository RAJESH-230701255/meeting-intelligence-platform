"""Tests for Manager Dashboard analytics — Phase 4.1."""

from datetime import date, datetime, timedelta, timezone

from app.models.meeting import Meeting
from app.models.task import Task


class TestManagerDashboardTrends:
    """Test completion_trend and meeting_activity for the manager dashboard."""

    def test_manager_dashboard_returns_30_day_trends(self, client_as, db_session, manager_user):
        """Verify both trend arrays contain exactly 30 entries."""
        c = client_as(manager_user)
        res = c.get("/api/dashboard/manager")
        assert res.status_code == 200
        data = res.json()

        assert "completion_trend" in data
        assert "meeting_activity" in data
        assert len(data["completion_trend"]) == 30
        assert len(data["meeting_activity"]) == 30

    def test_trends_contain_date_and_count(self, client_as, db_session, manager_user):
        """Verify each trend entry has 'date' and 'count' keys."""
        c = client_as(manager_user)
        res = c.get("/api/dashboard/manager")
        data = res.json()

        for entry in data["completion_trend"]:
            assert "date" in entry
            assert "count" in entry
            # Date should be ISO format (YYYY-MM-DD)
            date.fromisoformat(entry["date"])
            assert isinstance(entry["count"], int)
            assert entry["count"] >= 0

        for entry in data["meeting_activity"]:
            assert "date" in entry
            assert "count" in entry
            date.fromisoformat(entry["date"])
            assert isinstance(entry["count"], int)
            assert entry["count"] >= 0

    def test_empty_database_returns_all_zeros(self, client_as, db_session, manager_user):
        """With no meetings or tasks, all counts should be zero."""
        c = client_as(manager_user)
        res = c.get("/api/dashboard/manager")
        data = res.json()

        for entry in data["completion_trend"]:
            assert entry["count"] == 0

        for entry in data["meeting_activity"]:
            assert entry["count"] == 0

    def test_completion_trend_counts_only_manager_tasks(
        self, client_as, db_session, manager_user, employee_user
    ):
        """Completion trend should only include tasks in the manager's scope."""
        now = datetime.now(timezone.utc)

        # Meeting owned by manager
        meeting = Meeting(
            title="Manager Meeting",
            host_id=manager_user.id,
            meeting_type="INTERNAL",
            status="COMPLETED",
        )
        db_session.add(meeting)
        db_session.commit()
        db_session.refresh(meeting)

        # Task from manager's meeting — completed today
        task_in_scope = Task(
            title="In-scope task",
            meeting_id=meeting.id,
            assigned_to=employee_user.id,
            created_by=manager_user.id,
            status="COMPLETED",
            completed_at=now,
            priority="MEDIUM",
            source="MANUAL",
        )
        db_session.add(task_in_scope)

        # Task NOT in manager's scope — different creator, no linked meeting
        other_meeting = Meeting(
            title="Other Meeting",
            host_id=employee_user.id,
            meeting_type="INTERNAL",
            status="COMPLETED",
        )
        db_session.add(other_meeting)
        db_session.commit()
        db_session.refresh(other_meeting)

        task_out_of_scope = Task(
            title="Out-of-scope task",
            meeting_id=other_meeting.id,
            assigned_to=employee_user.id,
            created_by=employee_user.id,
            status="COMPLETED",
            completed_at=now,
            priority="MEDIUM",
            source="MANUAL",
        )
        db_session.add(task_out_of_scope)
        db_session.commit()

        c = client_as(manager_user)
        res = c.get("/api/dashboard/manager")
        data = res.json()

        # Sum of all completion_trend counts should be 1 (only the in-scope task)
        total = sum(entry["count"] for entry in data["completion_trend"])
        assert total == 1

    def test_meeting_activity_counts_only_manager_meetings(
        self, client_as, db_session, manager_user, employee_user
    ):
        """Meeting activity should only count meetings hosted by the manager."""
        # Manager's meeting
        m1 = Meeting(
            title="Manager's Meeting",
            host_id=manager_user.id,
            meeting_type="INTERNAL",
            status="SCHEDULED",
        )
        db_session.add(m1)

        # Someone else's meeting
        m2 = Meeting(
            title="Other Meeting",
            host_id=employee_user.id,
            meeting_type="INTERNAL",
            status="SCHEDULED",
        )
        db_session.add(m2)
        db_session.commit()

        c = client_as(manager_user)
        res = c.get("/api/dashboard/manager")
        data = res.json()

        total = sum(entry["count"] for entry in data["meeting_activity"])
        assert total == 1

    def test_completion_trend_excludes_non_completed_tasks(
        self, client_as, db_session, manager_user, employee_user
    ):
        """Only COMPLETED tasks with completed_at should appear in the trend."""
        meeting = Meeting(
            title="Test Meeting",
            host_id=manager_user.id,
            meeting_type="INTERNAL",
            status="COMPLETED",
        )
        db_session.add(meeting)
        db_session.commit()
        db_session.refresh(meeting)

        now = datetime.now(timezone.utc)

        # PENDING task — should NOT appear in trend
        t1 = Task(
            title="Pending",
            meeting_id=meeting.id,
            created_by=manager_user.id,
            status="PENDING",
            priority="MEDIUM",
            source="MANUAL",
        )
        # PENDING_REVIEW task — should NOT appear
        t2 = Task(
            title="Pending Review",
            meeting_id=meeting.id,
            created_by=manager_user.id,
            status="PENDING_REVIEW",
            priority="MEDIUM",
            source="AI_EXTRACTED",
        )
        # REJECTED task — should NOT appear
        t3 = Task(
            title="Rejected",
            meeting_id=meeting.id,
            created_by=manager_user.id,
            status="REJECTED",
            priority="MEDIUM",
            source="AI_EXTRACTED",
        )
        # COMPLETED task — SHOULD appear
        t4 = Task(
            title="Done",
            meeting_id=meeting.id,
            created_by=manager_user.id,
            status="COMPLETED",
            completed_at=now,
            priority="HIGH",
            source="MANUAL",
        )
        db_session.add_all([t1, t2, t3, t4])
        db_session.commit()

        c = client_as(manager_user)
        res = c.get("/api/dashboard/manager")
        data = res.json()

        total = sum(entry["count"] for entry in data["completion_trend"])
        assert total == 1

    def test_trend_dates_cover_last_30_days(self, client_as, db_session, manager_user):
        """Verify the dates span exactly from 29 days ago to today."""
        c = client_as(manager_user)
        res = c.get("/api/dashboard/manager")
        data = res.json()

        today = date.today()
        thirty_days_ago = today - timedelta(days=29)

        dates = [entry["date"] for entry in data["completion_trend"]]
        assert dates[0] == thirty_days_ago.isoformat()
        assert dates[-1] == today.isoformat()
        assert len(dates) == 30

        # Same for meeting_activity
        activity_dates = [entry["date"] for entry in data["meeting_activity"]]
        assert activity_dates[0] == thirty_days_ago.isoformat()
        assert activity_dates[-1] == today.isoformat()

    def test_existing_metrics_preserved(self, client_as, db_session, manager_user):
        """All pre-existing dashboard fields should still be returned."""
        c = client_as(manager_user)
        res = c.get("/api/dashboard/manager")
        assert res.status_code == 200
        data = res.json()

        expected_fields = [
            "total_meetings",
            "meetings_this_week",
            "active_tasks",
            "completed_tasks",
            "overdue_tasks",
            "pending_reviews",
            "completion_rate",
            "tasks_by_status",
            "tasks_by_priority",
            "team_workload",
            "recent_meetings",
            "completion_trend",
            "meeting_activity",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_employee_cannot_access_manager_dashboard(
        self, client_as, db_session, employee_user
    ):
        """Employees should be denied access to the manager dashboard."""
        c = client_as(employee_user)
        res = c.get("/api/dashboard/manager")
        assert res.status_code == 403
