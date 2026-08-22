"""Tests for the /api/meetings/{id}/process orchestrator endpoint.

Covers:
- Basic processing with audio upload
- Processing with existing transcript (no audio)
- Error: no transcript and no audio
- Confirmed tasks survive re-analysis (req #11)
- Full internal meeting pipeline to employee dashboard (req #12)
- External transcript workflow (req #13)
- External audio workflow (req #13)
"""

import io

from app.models.meeting import Meeting
from app.models.task import Task
from app.models.transcript import Transcript
from app.models.summary import MeetingSummary
from app.models.decision import Decision
from app.models.participant import MeetingParticipant


def test_process_with_audio_upload(client, db_session, admin_user, monkeypatch):
    """Upload audio via /process — verify transcript + summary + decisions + tasks created."""
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("SPEECH_PROVIDER", "mock")

    meeting = Meeting(
        title="Process Audio Test",
        meeting_type="INTERNAL",
        host_id=admin_user.id,
        status="COMPLETED",
    )
    db_session.add(meeting)
    db_session.commit()

    fake_audio = io.BytesIO(b"fake audio data")
    res = client.post(
        f"/api/meetings/{meeting.id}/process",
        files={"file": ("test.wav", fake_audio, "audio/wav")},
    )

    assert res.status_code == 200
    data = res.json()
    assert data["summary"] != ""
    assert len(data["action_items"]) > 0
    assert len(data["decisions"]) > 0

    # Verify DB persistence
    transcript = db_session.query(Transcript).filter_by(meeting_id=meeting.id).first()
    assert transcript is not None
    assert transcript.content != ""

    summary = db_session.query(MeetingSummary).filter_by(meeting_id=meeting.id).first()
    assert summary is not None

    tasks = db_session.query(Task).filter_by(meeting_id=meeting.id).all()
    assert len(tasks) > 0
    assert all(t.status == "PENDING_REVIEW" for t in tasks)


def test_process_with_existing_transcript(client, db_session, admin_user, monkeypatch):
    """Process with existing transcript (no audio upload) — verify analysis runs and notifications are created."""
    from app.models.user import User
    from app.models.notification import Notification
    
    monkeypatch.setenv("AI_PROVIDER", "mock")

    # Create a user named Rajesh so the mock AI assignment works
    rajesh = User(
        name="Rajesh Kumar",
        email="rajesh@test.com",
        password_hash="fakehash",
        role="EMPLOYEE",
        is_active=True,
    )
    db_session.add(rajesh)
    db_session.commit()

    meeting = Meeting(
        title="Existing Transcript Test",
        meeting_type="INTERNAL",
        host_id=admin_user.id,
        status="COMPLETED",
    )
    db_session.add(meeting)
    db_session.commit()

    transcript = Transcript(
        meeting_id=meeting.id,
        content="Rajesh will prepare the report by Friday. Testing needed.",
        source="AUTO_RECORDED",
    )
    db_session.add(transcript)
    db_session.commit()

    res = client.post(f"/api/meetings/{meeting.id}/process")
    assert res.status_code == 200
    data = res.json()
    assert data["summary"] != ""
    assert len(data["action_items"]) > 0

    # Verify that Rajesh received a notification
    notifications = db_session.query(Notification).filter_by(user_id=rajesh.id).all()
    assert len(notifications) > 0
    assert "new task" in notifications[0].message
    assert notifications[0].type == "TASK_ASSIGNED"


def test_process_no_transcript_no_audio_returns_400(client, db_session, admin_user):
    """No transcript and no audio → 400 error."""
    meeting = Meeting(
        title="Empty Meeting",
        meeting_type="INTERNAL",
        host_id=admin_user.id,
        status="COMPLETED",
    )
    db_session.add(meeting)
    db_session.commit()

    res = client.post(f"/api/meetings/{meeting.id}/process")
    assert res.status_code == 400
    assert "No transcript" in res.json()["detail"]


def test_confirmed_tasks_survive_reanalysis(client, db_session, admin_user, monkeypatch):
    """Re-analysis must NEVER delete CONFIRMED or COMPLETED tasks (req #2, #11).

    Flow:
    1. Create meeting + transcript → process → creates PENDING_REVIEW tasks
    2. Confirm one task, complete another
    3. Re-process (re-analysis)
    4. Verify: CONFIRMED and COMPLETED tasks survive unchanged
    5. Verify: old PENDING_REVIEW tasks are replaced with new ones
    """
    monkeypatch.setenv("AI_PROVIDER", "mock")

    meeting = Meeting(
        title="Re-analysis Safety Test",
        meeting_type="INTERNAL",
        host_id=admin_user.id,
        status="COMPLETED",
    )
    db_session.add(meeting)
    db_session.commit()

    transcript = Transcript(
        meeting_id=meeting.id,
        content="Rajesh will prepare the report by Friday. Testing needed.",
        source="AUTO_RECORDED",
    )
    db_session.add(transcript)
    db_session.commit()

    # --- First analysis ---
    res1 = client.post(f"/api/meetings/{meeting.id}/process")
    assert res1.status_code == 200

    initial_tasks = db_session.query(Task).filter_by(meeting_id=meeting.id).all()
    assert len(initial_tasks) > 0

    # Confirm the first task
    confirmed_task = initial_tasks[0]
    confirmed_task.status = "CONFIRMED"
    db_session.commit()
    confirmed_task_id = confirmed_task.id
    confirmed_task_title = confirmed_task.title

    # Complete a second task (if available, otherwise create one manually)
    if len(initial_tasks) > 1:
        completed_task = initial_tasks[1]
        completed_task.status = "COMPLETED"
        db_session.commit()
        completed_task_id = completed_task.id
    else:
        # Create a manual completed task for safety
        manual_task = Task(
            meeting_id=meeting.id,
            created_by=admin_user.id,
            title="Manual completed task",
            status="COMPLETED",
            priority="MEDIUM",
            source="AI_EXTRACTED",
        )
        db_session.add(manual_task)
        db_session.commit()
        completed_task_id = manual_task.id

    # Count tasks with preserved statuses before re-analysis
    preserved_count_before = db_session.query(Task).filter(
        Task.meeting_id == meeting.id,
        Task.status.in_(["CONFIRMED", "COMPLETED", "PENDING", "IN_PROGRESS"]),
    ).count()

    # --- Re-analysis ---
    res2 = client.post(f"/api/meetings/{meeting.id}/process")
    assert res2.status_code == 200

    # Verify CONFIRMED task survived
    confirmed_after = db_session.query(Task).filter_by(id=confirmed_task_id).first()
    assert confirmed_after is not None, "CONFIRMED task was deleted during re-analysis!"
    assert confirmed_after.status == "CONFIRMED"
    assert confirmed_after.title == confirmed_task_title

    # Verify COMPLETED task survived
    completed_after = db_session.query(Task).filter_by(id=completed_task_id).first()
    assert completed_after is not None, "COMPLETED task was deleted during re-analysis!"
    assert completed_after.status == "COMPLETED"

    # Verify preserved task count is unchanged
    preserved_count_after = db_session.query(Task).filter(
        Task.meeting_id == meeting.id,
        Task.status.in_(["CONFIRMED", "COMPLETED", "PENDING", "IN_PROGRESS"]),
    ).count()
    assert preserved_count_after == preserved_count_before

    # Verify new PENDING_REVIEW tasks were created (from re-analysis)
    new_pending = db_session.query(Task).filter(
        Task.meeting_id == meeting.id,
        Task.status == "PENDING_REVIEW",
    ).all()
    assert len(new_pending) > 0, "Re-analysis should create new PENDING_REVIEW tasks"


def test_full_internal_meeting_pipeline(
    client, db_session, admin_user, employee_user, client_as, monkeypatch
):
    """Full internal meeting flow: recording → STT → AI → tasks → employee dashboard (req #12).

    1. Create internal meeting with employee participant
    2. Start meeting → End meeting
    3. Upload audio + process via /process
    4. Confirm an action item (assign to employee)
    5. Verify task appears on employee dashboard
    """
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("SPEECH_PROVIDER", "mock")

    # 1. Create meeting
    create_res = client.post("/api/meetings", json={
        "title": "Full Pipeline Test",
        "description": "End-to-end internal meeting test",
        "meeting_type": "INTERNAL",
        "participant_ids": [employee_user.id],
    })
    assert create_res.status_code == 201
    meeting_id = create_res.json()["id"]

    # 2. Start → End
    start_res = client.post(f"/api/meetings/{meeting_id}/start")
    assert start_res.status_code == 200

    end_res = client.post(f"/api/meetings/{meeting_id}/end")
    assert end_res.status_code == 200

    # 3. Upload audio + process
    fake_audio = io.BytesIO(b"recorded meeting audio")
    process_res = client.post(
        f"/api/meetings/{meeting_id}/process",
        files={"file": ("meeting.webm", fake_audio, "audio/webm")},
    )
    assert process_res.status_code == 200
    data = process_res.json()
    assert data["summary"] != ""
    assert len(data["action_items"]) > 0

    # Verify transcript exists
    transcript = db_session.query(Transcript).filter_by(meeting_id=meeting_id).first()
    assert transcript is not None

    # Verify summary exists
    summary = db_session.query(MeetingSummary).filter_by(meeting_id=meeting_id).first()
    assert summary is not None

    # 4. Confirm an action item and assign to employee
    action_items_res = client.get(f"/api/meetings/{meeting_id}/action-items")
    assert action_items_res.status_code == 200
    action_items = action_items_res.json()
    assert len(action_items) > 0

    first_item_id = action_items[0]["id"]
    confirm_res = client.post(
        f"/api/action-items/{first_item_id}/confirm",
        json={"assigned_to": employee_user.id},
    )
    assert confirm_res.status_code == 200

    # 5. Switch to employee → check dashboard
    emp_client = client_as(employee_user)
    dashboard_res = emp_client.get("/api/dashboard/employee")
    assert dashboard_res.status_code == 200
    dashboard = dashboard_res.json()

    # The confirmed task should appear in employee's tasks
    assert dashboard["total_tasks"] >= 1


def test_external_transcript_flow(client, db_session, admin_user, monkeypatch):
    """External meeting with transcript file upload → process → analysis (req #13)."""
    monkeypatch.setenv("AI_PROVIDER", "mock")

    # 1. Create external meeting
    create_res = client.post("/api/meetings", json={
        "title": "External Transcript Test",
        "meeting_type": "EXTERNAL",
    })
    assert create_res.status_code == 201
    meeting_id = create_res.json()["id"]

    # 2. Upload transcript file
    transcript_content = (
        "The team discussed the project timeline. "
        "Rajesh will prepare the final report by Friday. "
        "The decision was made to extend the deadline by one week."
    )
    fake_file = io.BytesIO(transcript_content.encode("utf-8"))
    upload_res = client.post(
        f"/api/meetings/{meeting_id}/transcript/upload",
        files={"file": ("notes.txt", fake_file, "text/plain")},
    )
    assert upload_res.status_code == 200

    # 3. Process (no audio — uses existing transcript)
    process_res = client.post(f"/api/meetings/{meeting_id}/process")
    assert process_res.status_code == 200
    data = process_res.json()
    assert data["summary"] != ""
    assert len(data["action_items"]) > 0
    assert len(data["decisions"]) > 0


def test_external_audio_flow(client, db_session, admin_user, monkeypatch):
    """External meeting with audio upload via /process (req #13)."""
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("SPEECH_PROVIDER", "mock")

    # 1. Create external meeting
    create_res = client.post("/api/meetings", json={
        "title": "External Audio Test",
        "meeting_type": "EXTERNAL",
    })
    assert create_res.status_code == 201
    meeting_id = create_res.json()["id"]

    # 2. Upload audio + process in single call
    fake_audio = io.BytesIO(b"external meeting audio recording")
    process_res = client.post(
        f"/api/meetings/{meeting_id}/process",
        files={"file": ("external.mp3", fake_audio, "audio/mpeg")},
    )
    assert process_res.status_code == 200
    data = process_res.json()
    assert data["summary"] != ""
    assert len(data["action_items"]) > 0

    # Verify transcript was created from STT
    transcript = db_session.query(Transcript).filter_by(meeting_id=meeting_id).first()
    assert transcript is not None
    assert transcript.content != ""

    # Verify meeting source type
    meeting = db_session.query(Meeting).filter_by(id=meeting_id).first()
    assert meeting.source_type == "UPLOADED_AUDIO"
