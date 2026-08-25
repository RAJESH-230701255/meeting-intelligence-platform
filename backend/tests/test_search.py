import pytest
from datetime import date
from app.models.meeting import Meeting
from app.models.task import Task
from app.models.transcript import Transcript
from app.models.summary import MeetingSummary
from app.models.decision import Decision
from app.models.participant import MeetingParticipant
from app.models.user import User

def test_meeting_search(client, db_session, admin_user, employee_user):
    # Setup data
    m1 = Meeting(title="Project Alpha", description="Kickoff", meeting_type="INTERNAL", host_id=admin_user.id, meeting_date=date(2023, 10, 10))
    m2 = Meeting(title="Beta Sync", description="Weekly sync", meeting_type="INTERNAL", host_id=admin_user.id, meeting_date=date(2023, 10, 11))
    m3 = Meeting(title="Gamma Review", description="Quarterly review", meeting_type="INTERNAL", host_id=admin_user.id, meeting_date=date(2023, 10, 12))
    db_session.add_all([m1, m2, m3])
    db_session.commit()
    
    # 1. Title search
    res = client.get("/api/meetings?search=Alpha")
    assert res.status_code == 200
    assert len(res.json()["meetings"]) == 1
    
    # 2. Description search
    res = client.get("/api/meetings?search=Kickoff")
    assert len(res.json()["meetings"]) == 1
    
    # 3. Transcript search
    t = Transcript(meeting_id=m1.id, content="We need to discuss the budget.", source="MANUAL")
    db_session.add(t)
    db_session.commit()
    res = client.get("/api/meetings?search=budget")
    assert len(res.json()["meetings"]) == 1
    assert res.json()["meetings"][0]["id"] == m1.id
    
    # 4. Summary & 5. Key Point search
    s = MeetingSummary(meeting_id=m2.id, summary="Important decisions were made.", key_points=["Deployment tomorrow"])
    db_session.add(s)
    db_session.commit()
    res = client.get("/api/meetings?search=decisions")
    assert len(res.json()["meetings"]) == 1
    res = client.get("/api/meetings?search=tomorrow")
    assert len(res.json()["meetings"]) == 1
    
    # 6. Decision text & 7. context search
    d = Decision(meeting_id=m3.id, decision_text="Approve the new design.", decision_context="Based on user feedback.")
    db_session.add(d)
    db_session.commit()
    res = client.get("/api/meetings?search=Approve")
    assert len(res.json()["meetings"]) == 1
    res = client.get("/api/meetings?search=feedback")
    assert len(res.json()["meetings"]) == 1
    
    # 10. Person filter
    db_session.add(MeetingParticipant(meeting_id=m2.id, user_id=employee_user.id))
    db_session.commit()
    res = client.get(f"/api/meetings?person_id={employee_user.id}")
    assert len(res.json()["meetings"]) == 1
    assert res.json()["meetings"][0]["id"] == m2.id
    
    # 11. Date filter
    res = client.get("/api/meetings?date=2023-10-10")
    assert len(res.json()["meetings"]) == 1
    
    # 18. Duplicate meeting test
    m1.description = "budget planning"
    db_session.commit()
    res = client.get("/api/meetings?search=budget")
    assert len(res.json()["meetings"]) == 1

def test_task_search(client_as, db_session, admin_user, employee_user):
    admin_client = client_as(admin_user)
    
    # 8. & 9. Title & Description
    t1 = Task(title="Fix backend bug", description="Error in search route", created_by=admin_user.id, assigned_to=employee_user.id, status="PENDING")
    t2 = Task(title="Update frontend", description="Add date picker", created_by=admin_user.id, assigned_to=employee_user.id, status="PENDING_REVIEW")
    t3 = Task(title="Test PENDING", description="Testing", created_by=admin_user.id, assigned_to=employee_user.id, status="REJECTED")
    db_session.add_all([t1, t2, t3])
    db_session.commit()
    
    res = admin_client.get("/api/tasks?search=bug")
    assert len(res.json()["tasks"]) == 1
    res = admin_client.get("/api/tasks?search=route")
    assert len(res.json()["tasks"]) == 1
    
    # 12 & 13. Status and Priority
    admin_client = client_as(admin_user) # Re-instantiate to fix override collision
    res = admin_client.get("/api/tasks?status_filter=PENDING_REVIEW")
    assert len(res.json()["tasks"]) == 1
    
    emp_client = client_as(employee_user)
    res = emp_client.get("/api/tasks")
    tasks = res.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["id"] == t1.id

def test_rbac_meeting_search(client_as, db_session, admin_user, manager_user, employee_user):
    # 14. Employee cannot search and discover unauthorized meetings
    emp_client = client_as(employee_user)
    
    # Create a meeting employee is NOT in
    m_hidden = Meeting(title="Secret Meeting", description="Top secret", meeting_type="INTERNAL", host_id=admin_user.id)
    # Create a meeting employee IS in
    m_visible = Meeting(title="Public Sync", description="Everyone welcome", meeting_type="INTERNAL", host_id=admin_user.id)
    db_session.add_all([m_hidden, m_visible])
    db_session.commit()
    
    db_session.add(MeetingParticipant(meeting_id=m_visible.id, user_id=employee_user.id))
    db_session.commit()
    
    # Search for "Secret"
    res = emp_client.get("/api/meetings?search=Secret")
    assert len(res.json()["meetings"]) == 0
    
    # Search for "Sync"
    res = emp_client.get("/api/meetings?search=Sync")
    assert len(res.json()["meetings"]) == 1
    assert res.json()["meetings"][0]["id"] == m_visible.id
