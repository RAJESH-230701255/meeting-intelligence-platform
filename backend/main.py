from fastapi import FastAPI
from database import engine

app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "Meeting Intelligence API is running"
    }


@app.get("/health")
def health():
    try:
        with engine.connect():
            return {
                "status": "healthy",
                "database": "connected"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }