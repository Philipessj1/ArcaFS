from fastapi import FastAPI

app = FastAPI(
    title="ArcaFS API",
    description="Cloud File Storage API built with FastAPI",
    version="0.1.0",
)

@app.get("/")
def root():
    return {"message": "Welcome to ArcaFS"}

@app.get("/health")
def health():
    return {"status": "ok"}