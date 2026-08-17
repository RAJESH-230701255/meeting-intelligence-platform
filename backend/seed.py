"""Seed script — creates development data.

Usage:
    cd backend
    python seed.py

WARNING: This is for DEVELOPMENT ONLY. Do not use in production.
"""

import sys
from datetime import date, timedelta

from app.core.security import hash_password
from app.database.database import SessionLocal, engine
from app.database.base import Base
from app.models import *  # noqa: F401, F403


def seed():
    """Create seed data for development."""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_user = db.query(User).filter(User.email == "admin@meeting-intel.dev").first()
        if existing_user:
            print("Seed data already exists. Skipping.")
            return

        print("Creating seed data...")

        # ============================================================
        # USERS — Development credentials only
        # ============================================================
        admin = User(
            name="Admin User",
            email="admin@meeting-intel.dev",
            password_hash=hash_password("admin123"),
            role="ADMIN",
        )
        manager = User(
            name="Manager User",
            email="manager@meeting-intel.dev",
            password_hash=hash_password("manager123"),
            role="MANAGER",
        )
        rajesh = User(
            name="Rajesh Kumar",
            email="rajesh@meeting-intel.dev",
            password_hash=hash_password("employee123"),
            role="EMPLOYEE",
        )
        priya = User(
            name="Priya Sharma",
            email="priya@meeting-intel.dev",
            password_hash=hash_password("employee123"),
            role="EMPLOYEE",
        )
        amit = User(
            name="Amit Patel",
            email="amit@meeting-intel.dev",
            password_hash=hash_password("employee123"),
            role="EMPLOYEE",
        )

        db.add_all([admin, manager, rajesh, priya, amit])
        db.flush()

        print(f"  Created users: Admin({admin.id}), Manager({manager.id}), "
              f"Rajesh({rajesh.id}), Priya({priya.id}), Amit({amit.id})")

        # ============================================================
        # MEETING
        # ============================================================
        meeting = Meeting(
            title="Sprint Planning — Week 34",
            description="Sprint planning meeting to discuss project deliverables and assign tasks.",
            meeting_type="INTERNAL",
            host_id=manager.id,
            room_id="sprint-34-room",
            meeting_date=date.today(),
            status="COMPLETED",
            source_type="INTERNAL_AUDIO",
        )
        db.add(meeting)
        db.flush()

        # Add participants
        for user, role in [(manager, "HOST"), (rajesh, "PARTICIPANT"), (priya, "PARTICIPANT"), (amit, "PARTICIPANT")]:
            p = MeetingParticipant(
                meeting_id=meeting.id,
                user_id=user.id,
                role_in_meeting=role,
            )
            db.add(p)

        print(f"  Created meeting: {meeting.title} (ID: {meeting.id})")

        # ============================================================
        # TRANSCRIPT
        # ============================================================
        transcript = Transcript(
            meeting_id=meeting.id,
            source="AUTO_RECORDED",
            content=(
                "Rajesh will prepare the project report by Friday. "
                "Priya will review the report on Monday. "
                "The team decided to complete testing before the next meeting. "
                "Amit should update the deployment documentation by Wednesday."
            ),
            language="en",
        )
        db.add(transcript)
        print(f"  Created transcript for meeting {meeting.id}")

        # ============================================================
        # SUMMARY
        # ============================================================
        summary = MeetingSummary(
            meeting_id=meeting.id,
            summary="The team discussed project reporting, review responsibilities, testing completion, and deployment documentation updates.",
            key_points=[
                "Rajesh will prepare the project report",
                "Priya will review the project report",
                "Testing must be completed before the next meeting",
                "Amit to update deployment documentation",
            ],
        )
        db.add(summary)
        print(f"  Created summary for meeting {meeting.id}")

        # ============================================================
        # DECISIONS
        # ============================================================
        decision = Decision(
            meeting_id=meeting.id,
            decision_text="Testing must be completed before the next meeting.",
            decision_context="The team agreed on a testing deadline to ensure quality before the next sprint.",
        )
        db.add(decision)

        # ============================================================
        # TASKS
        # ============================================================
        today = date.today()
        friday = today + timedelta(days=(4 - today.weekday()) % 7 or 7)
        monday = today + timedelta(days=(0 - today.weekday()) % 7 or 7)
        wednesday = today + timedelta(days=(2 - today.weekday()) % 7 or 7)

        task1 = Task(
            meeting_id=meeting.id,
            assigned_to=rajesh.id,
            created_by=manager.id,
            title="Prepare project report",
            description="Prepare and submit the project report",
            deadline=friday,
            priority="MEDIUM",
            status="PENDING",
            source_text="Rajesh will prepare the project report by Friday.",
            ai_confidence=0.91,
            source="AI_EXTRACTED",
        )
        task2 = Task(
            meeting_id=meeting.id,
            assigned_to=priya.id,
            created_by=manager.id,
            title="Review project report",
            description="Review the project report prepared by Rajesh",
            deadline=monday,
            priority="MEDIUM",
            status="PENDING",
            source_text="Priya will review the report on Monday.",
            ai_confidence=0.89,
            source="AI_EXTRACTED",
        )
        task3 = Task(
            meeting_id=meeting.id,
            assigned_to=amit.id,
            created_by=manager.id,
            title="Update deployment documentation",
            description="Update the deployment documentation for the current sprint",
            deadline=wednesday,
            priority="MEDIUM",
            status="IN_PROGRESS",
            source_text="Amit should update the deployment documentation by Wednesday.",
            ai_confidence=0.85,
            source="AI_EXTRACTED",
        )

        db.add_all([task1, task2, task3])
        db.flush()

        print(f"  Created tasks: {task1.id}, {task2.id}, {task3.id}")

        # ============================================================
        # NOTIFICATIONS
        # ============================================================
        for user, task in [(rajesh, task1), (priya, task2), (amit, task3)]:
            n = Notification(
                user_id=user.id,
                task_id=task.id,
                type="TASK_ASSIGNED",
                message=f'You have been assigned a new task: "{task.title}"',
            )
            db.add(n)

        db.commit()

        print("\n✅ Seed data created successfully!")
        print("\n--- Development Credentials ---")
        print("Admin:    admin@meeting-intel.dev    / admin123")
        print("Manager:  manager@meeting-intel.dev  / manager123")
        print("Rajesh:   rajesh@meeting-intel.dev   / employee123")
        print("Priya:    priya@meeting-intel.dev    / employee123")
        print("Amit:     amit@meeting-intel.dev     / employee123")
        print("-------------------------------")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating seed data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
