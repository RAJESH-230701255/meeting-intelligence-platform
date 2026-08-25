# Setup & Installation

## Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+ (or 20+)
- **Database**: PostgreSQL 13+
- **Tools**: Git, Docker (optional for containerized deployment)

## Environment Variables

### Backend (`backend/.env`)
Create a `.env` file in the `backend/` directory with the following contents:
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/meeting_db

# Security
SECRET_KEY=your-super-secret-jwt-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI & Speech Configuration
SPEECH_PROVIDER=whisper
WHISPER_API_KEY=YOUR_OPENAI_API_KEY
AI_PROVIDER=openai
AI_MODEL=gpt-4
OPENAI_API_KEY=YOUR_OPENAI_API_KEY

# Frontend
FRONTEND_URL=http://localhost:5173
```

### Frontend (`frontend/.env`)
Create a `.env` file in the `frontend/` directory (if different from default Vite port):
```env
VITE_API_BASE_URL=http://localhost:8000
```

## Local Development Setup

### 1. Database Setup
Ensure PostgreSQL is running and create a database named `meeting_db` (or whatever you configure in `DATABASE_URL`).

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Activate venv: .\venv\Scripts\activate (Windows) or source venv/bin/activate (macOS/Linux)
pip install -r requirements.txt

# Run migrations to setup schema
alembic upgrade head

# Run backend server
uvicorn app.main:app --reload
```
The backend API documentation will be available at `http://localhost:8000/docs`.

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The application will be available at `http://localhost:5173`.
