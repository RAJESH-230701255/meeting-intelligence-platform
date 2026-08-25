# Database Schema & Migrations

## ORM and Migrations
- We use **SQLAlchemy 2.0** for object-relational mapping.
- We use **Alembic** for managing database migrations.

## Core Entities
1. **User** (`users` table): Stores credentials (hashed password), email, full name, and role (`ADMIN`, `MANAGER`, `EMPLOYEE`).
2. **Meeting** (`meetings` table): Stores meeting metadata (title, status, scheduled time, host_id).
3. **MeetingParticipant** (`meeting_participants` table): Association table linking Users to Meetings.
4. **Transcript** (`transcripts` table): Stores the full text transcript linked to a meeting.
5. **MeetingSummary** (`meeting_summaries` table): Stores the AI-generated summary and key points.
6. **Decision** (`decisions` table): Stores structured decisions extracted from a meeting.
7. **Task** (`tasks` table): Stores action items, tracking their status (`PENDING_REVIEW`, `PENDING`, `IN_PROGRESS`, `COMPLETED`, `REJECTED`), priority, assignee, and source (`AI` vs `MANUAL`).
8. **Notification** (`notifications` table): Tracks system alerts for users (e.g., new task assignments).

## Alembic Migration Commands
Whenever you make changes to `backend/app/models/`, you must generate a new migration:

```bash
# Generate a new migration script automatically
alembic revision --autogenerate -m "Add new column"

# Apply migrations to the database
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```
