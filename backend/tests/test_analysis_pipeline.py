from datetime import datetime, timezone

from app.models.meeting import Meeting
from app.models.transcript import Transcript
from app.models.summary import MeetingSummary
from app.models.decision import Decision
from app.models.task import Task


def test_analyze_meeting_success(client, db_session, admin_user, monkeypatch):
    # Set AI provider to mock so it returns a standard response
    monkeypatch.setenv("AI_PROVIDER", "mock")

    # Create dummy meeting and transcript
    meeting = Meeting(
        title="Test Meeting",
        meeting_type="INTERNAL",
        host_id=admin_user.id,
        status="COMPLETED"
    )
    db_session.add(meeting)
    db_session.commit()

    transcript = Transcript(
        meeting_id=meeting.id,
        content="Rajesh will prepare the report by Friday. Priya will review it. Testing is needed.",
        source="AUTO_RECORDED"
    )
    db_session.add(transcript)
    db_session.commit()

    response = client.post(f"/api/meetings/{meeting.id}/analyze")
    assert response.status_code == 200
    data = response.json()
    
    assert data["summary"] is not None
    assert len(data["decisions"]) > 0
    assert len(data["action_items"]) > 0

    # Verify DB persistence
    summary = db_session.query(MeetingSummary).filter_by(meeting_id=meeting.id).first()
    assert summary is not None

    decisions = db_session.query(Decision).filter_by(meeting_id=meeting.id).all()
    assert len(decisions) > 0

    tasks = db_session.query(Task).filter_by(meeting_id=meeting.id).all()
    assert len(tasks) > 0
    assert tasks[0].status == "PENDING_REVIEW"


def test_analyze_meeting_no_transcript(client, db_session, admin_user):
    meeting = Meeting(
        title="No Transcript",
        meeting_type="INTERNAL",
        host_id=admin_user.id,
        status="COMPLETED"
    )
    db_session.add(meeting)
    db_session.commit()

    response = client.post(f"/api/meetings/{meeting.id}/analyze")
    assert response.status_code == 400
    assert "No transcript available" in response.json()["detail"]
