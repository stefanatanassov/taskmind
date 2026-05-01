from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from taskmind.config import get_settings
from taskmind.db import Base, engine, get_session
from taskmind.models import Run
from taskmind.schemas import RunRead, TaskCreate, TaskRead
from taskmind.services.tasks import create_task, get_task, list_tasks

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="taskmind", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
def readyz(session: Session = Depends(get_session)) -> dict:
    session.execute(text("SELECT 1"))
    redis_client = Redis.from_url(settings.redis_url)
    redis_ok = redis_client.ping()
    return {"status": "ready", "database": "ok", "redis": "ok" if redis_ok else "unavailable"}


@app.post("/tasks", response_model=TaskRead, status_code=201)
def create_task_endpoint(payload: TaskCreate, session: Session = Depends(get_session)) -> TaskRead:
    task = create_task(session, payload)
    return TaskRead.model_validate(task)


@app.get("/tasks", response_model=list[TaskRead])
def list_tasks_endpoint(session: Session = Depends(get_session)) -> list[TaskRead]:
    return [TaskRead.model_validate(task) for task in list_tasks(session)]


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task_endpoint(task_id: str, session: Session = Depends(get_session)) -> TaskRead:
    task = get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskRead.model_validate(task)


@app.get("/runs", response_model=list[RunRead])
def list_runs_endpoint(session: Session = Depends(get_session)) -> list[RunRead]:
    runs = session.query(Run).order_by(Run.started_at.desc()).all()
    return [RunRead.model_validate(run) for run in runs]
