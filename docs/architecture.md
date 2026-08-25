# System Architecture

## Overview
The application follows a standard client-server architecture with a RESTful API backend and a Single Page Application (SPA) frontend.

## Components

### 1. Frontend (React)
- **Framework**: React with Vite
- **Styling**: TailwindCSS
- **State Management**: React Context (AuthContext)
- **Routing**: React Router DOM
- **Responsibilities**:
  - Capturing in-browser audio via MediaRecorder.
  - Presenting real-time role-based dashboards (Admin, Manager, Employee).
  - Managing meetings, task execution, and deep search across intelligence artifacts.

### 2. Backend (FastAPI)
- **Framework**: FastAPI (Python)
- **Responsibilities**:
  - Exposing REST API endpoints.
  - Handling JWT Authentication and Role-Based Access Control (RBAC).
  - Orchestrating the AI Pipeline (audio processing, transcript analysis).
  - Executing deep search queries using SQLAlchemy exists subqueries.

### 3. Database (PostgreSQL)
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Responsibilities**:
  - Relational storage of Users, Meetings, Transcripts, Summaries, Decisions, and Tasks.
  - Providing transactional integrity for AI extraction output.

### 4. Third-Party Integrations
- **Speech-to-Text**: OpenAI Whisper SDK (transcription of uploaded or captured audio).
- **Intelligence (LLM)**: OpenAI SDK (extracting decisions, tasks, and summary from transcripts).

## Security & RBAC
- **Authentication**: JWT tokens generated upon login.
- **Authorization**: Endpoint-level dependency injection (`get_current_user`) verifying roles (`ADMIN`, `MANAGER`, `EMPLOYEE`).
- **Data Isolation**:
  - Employees only see their approved, actionable tasks.
  - Employees only see meetings they are participants of.
  - Managers can see their own tasks and tasks they assign/review (`PENDING_REVIEW`).
