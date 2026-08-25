# API Reference

The backend uses FastAPI, meaning complete, interactive Swagger API documentation is automatically generated.

## Accessing the Interactive Docs
1. Start the backend server (`uvicorn app.main:app --reload`).
2. Navigate to `http://localhost:8000/docs` in your browser.
3. You can authenticate directly in the Swagger UI using the "Authorize" button to test protected endpoints.

## Core API Routes

### Authentication (`/api/auth`)
- `POST /api/auth/token`: Obtain JWT token using username/password.
- `GET /api/auth/me`: Get current logged-in user profile.

### Users (`/api/users`)
- `GET /api/users`: List users (Admin only).
- `POST /api/users`: Create a new user.

### Meetings (`/api/meetings`)
- `GET /api/meetings`: List meetings, supports deep search (`search`, `date`, `person_id`).
- `POST /api/meetings`: Create a meeting.
- `GET /api/meetings/{id}`: Get meeting details including transcripts and analysis.

### Tasks (`/api/tasks`)
- `GET /api/tasks`: List tasks. Supports search (`search`, `date`). Employees only see their approved/actionable tasks.
- `PUT /api/tasks/{id}`: Update task status.
- `PUT /api/tasks/{id}/review`: Manager review for `PENDING_REVIEW` tasks.

### Dashboards (`/api/dashboards`)
- `GET /api/dashboards/employee`: Metrics for employee tasks.
- `GET /api/dashboards/manager`: Metrics across manager's scope.
- `GET /api/dashboards/admin`: System-wide analytics.

### Processing & Transcripts
- `POST /api/processing/upload`: Upload audio or documents for processing.
- `POST /api/processing/process`: Trigger the AI extraction pipeline on a transcript.
