from fastapi import FastAPI

app = FastAPI(
    title="Smart Dataset Understanding Agent",
    description="AI-powered dataset analysis and understanding system",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "Welcome to the Smart Dataset Understanding Agent!"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }