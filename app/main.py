from fastapi import FastAPI
from sqlalchemy import text

from app.database.base import Base
from app.database.database import engine
from app.models.user import User

Base.metadata.create_all(bind=engine)

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

@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"db_test": result.scalar()}
