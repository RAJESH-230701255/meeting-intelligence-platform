import io
from app.models.meeting import Meeting
from app.models.task import Task
from app.models.summary import MeetingSummary
from app.models.transcript import Transcript


def test_full_pipeline_integration(client, db_session, admin_user, monkeypatch):
    """
    Integration test matching Phase 2 criteria:
    Upload Audio -> Speech-to-text -> AI analysis -> Summary/Decisions/Tasks
    """
    # 1. Enforce mock providers
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("SPEECH_PROVIDER", "mock")

    # 2. Create meeting
    create_res = client.post(
        "/api/meetings",
        json={
            "title": "Integration Test Meeting",
            "description": "Testing the pipeline",
            "meeting_type": "INTERNAL",
            "participant_ids": []
        }
    )
    assert create_res.status_code == 201
    meeting_id = create_res.json()["id"]

    # 3. Simulate ending meeting (Optional, but matches real flow)
    client.post(f"/api/meetings/{meeting_id}/start")
    client.post(f"/api/meetings/{meeting_id}/end")

    # 4. Upload Audio (triggers mock STT)
    # Create a dummy audio file
    fake_audio = io.BytesIO(b"fake audio content")
    fake_audio.name = "test.wav"
    upload_res = client.post(
        f"/api/meetings/{meeting_id}/audio",
        files={"file": ("test.wav", fake_audio, "audio/wav")}
    )
    assert upload_res.status_code == 200
    assert "transcript_preview" in upload_res.json()

    # Verify transcript is stored
    transcript = db_session.query(Transcript).filter_by(meeting_id=meeting_id).first()
    assert transcript is not None
    assert transcript.content != ""

    # 5. Process Audio (trigger AI analysis)
    process_res = client.post(f"/api/meetings/{meeting_id}/analyze")
    assert process_res.status_code == 200
    assert "summary" in process_res.json()
    assert len(process_res.json()["action_items"]) > 0

    # 6. Verify persistence
    analysis_res = client.get(f"/api/meetings/{meeting_id}/analysis")
    assert analysis_res.status_code == 200
    data = analysis_res.json()
    assert data["summary"] != ""
    assert len(data["action_items"]) > 0

    # 7. Check if task made it to task list pending review
    task_res = client.get(f"/api/meetings/{meeting_id}/action-items")
    assert task_res.status_code == 200
    assert len(task_res.json()) > 0
    assert task_res.json()[0]["status"] == "PENDING_REVIEW"
