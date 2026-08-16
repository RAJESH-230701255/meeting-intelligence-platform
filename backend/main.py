from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "Meeting Intelligence API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }