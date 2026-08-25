# AI-Powered Meeting Intelligence and Task Tracking Platform

## Project Purpose
This platform is a final-year project designed to automate the extraction of actionable intelligence from meetings. It supports internal recording via browser MediaRecorder as well as external audio/document uploads. Using advanced Speech-to-Text (e.g., OpenAI Whisper) and Large Language Models, it converts meeting audio/transcripts into a structured analysis comprising a summary, key points, decisions, and action items.

## Core Workflow
1. **Meeting Capture**: Record audio directly in the browser or upload an existing recording.
2. **Transcription**: Audio is processed into text via Whisper API.
3. **AI Analysis**: The transcript is fed to an LLM (e.g., GPT-4) to extract actionable items and decisions.
4. **Human Review**: Managers or Admins review `PENDING_REVIEW` tasks, editing or confirming them.
5. **Execution**: Approved tasks are dispatched to Employees.
6. **Analytics**: Real-time dashboards provide deep insights into meeting productivity and task completion trends.

## Technology Stack
- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0, Alembic, PostgreSQL, PyJWT, passlib
- **Frontend**: React (Vite), TailwindCSS, Context API
- **AI/Speech**: OpenAI Whisper SDK, OpenAI Chat Completions SDK

## Documentation Directory
- [Setup & Installation](docs/setup.md)
- [System Architecture](docs/architecture.md)
- [AI Pipeline & Workflow](docs/ai-pipeline.md)
- [Database Schema & Migrations](docs/database.md)
- [API Reference](docs/api.md)

## Evaluation & Research
See the `evaluation/` directory for scripts used to calculate Word Error Rate (WER) and extraction metrics (Precision, Recall, F1).
