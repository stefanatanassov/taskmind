from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from taskmind.config import get_settings
from taskmind.db import Base, engine, get_session
from taskmind.models import Run
from taskmind.schemas import AgentUsefulnessRead, FeedbackEventRead, RunRead, TaskCreate, TaskRead
from taskmind.services.analytics import build_route_analytics, build_summary, list_agent_usefulness, list_recent_feedback
from taskmind.services.tasks import create_task, get_task, list_tasks

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="taskmind", version="0.1.0", lifespan=lifespan)


def dashboard_html() -> str:
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>taskmind dashboard</title>
    <style>
      :root { color-scheme: dark; --bg:#0b1020; --panel:#141c2f; --line:#2b3654; --text:#e7edf8; --muted:#9fb0d1; --good:#50c878; --warn:#f4b942; }
      body { margin:0; font-family: ui-sans-serif, system-ui, sans-serif; background: radial-gradient(circle at top, #182441 0, #0b1020 55%); color:var(--text); }
      .wrap { max-width: 1180px; margin: 0 auto; padding: 32px 20px 60px; }
      h1 { margin: 0 0 8px; font-size: 34px; }
      p { color: var(--muted); }
      .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin: 26px 0; }
      .card { background: rgba(20,28,47,.92); border:1px solid var(--line); border-radius: 16px; padding: 18px; box-shadow: 0 12px 34px rgba(0,0,0,.22); }
      .metric { font-size: 28px; font-weight: 700; margin-top: 8px; }
      .label { color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }
      .section { margin-top: 26px; }
      table { width:100%; border-collapse: collapse; }
      th, td { padding: 12px 10px; border-bottom:1px solid var(--line); text-align:left; }
      th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }
      .pill { display:inline-block; padding:4px 10px; border-radius:999px; background:#1f2a46; color:var(--text); font-size:12px; }
      .ok { color: var(--good); }
      .warn { color: var(--warn); }
      .muted { color: var(--muted); }
    </style>
  </head>
  <body>
    <div class="wrap">
      <h1>taskmind</h1>
      <p>Task-driven execution, feedback history, and agent usefulness in one place.</p>
      <div id="summary" class="grid"></div>
      <div class="section card">
        <h2>Agent usefulness</h2>
        <table><thead><tr><th>Agent</th><th>Runs</th><th>Accepted</th><th>Avg usefulness</th><th>Last usefulness</th></tr></thead><tbody id="agents"></tbody></table>
      </div>
      <div class="section card">
        <h2>Route analytics</h2>
        <table><thead><tr><th>Route</th><th>Runs</th><th>Completed</th><th>Success rate</th><th>Coverage</th></tr></thead><tbody id="routes"></tbody></table>
      </div>
      <div class="section card">
        <h2>Recent feedback</h2>
        <table><thead><tr><th>Agent</th><th>Task status</th><th>Accepted</th><th>Usefulness</th><th>Coverage</th><th>Notes</th></tr></thead><tbody id="feedback"></tbody></table>
      </div>
    </div>
    <script>
      const fmtPct = (n) => `${(n * 100).toFixed(0)}%`;
      const fmtNum = (n) => Number(n).toFixed(2);
      async function load() {
        const [summary, agents, routes, feedback] = await Promise.all([
          fetch('/analytics/summary').then(r => r.json()),
          fetch('/analytics/agents').then(r => r.json()),
          fetch('/analytics/routes').then(r => r.json()),
          fetch('/feedback').then(r => r.json()),
        ]);

        document.getElementById('summary').innerHTML = [
          ['Tasks', summary.total_tasks],
          ['Runs', summary.total_runs],
          ['Success rate', fmtPct(summary.run_success_rate)],
          ['Avg coverage', fmtPct(summary.average_requirements_covered)],
          ['Feedback events', summary.feedback_events],
        ].map(([label, value]) => `<div class="card"><div class="label">${label}</div><div class="metric">${value}</div></div>`).join('');

        document.getElementById('agents').innerHTML = agents.map(agent => `
          <tr>
            <td><span class="pill">${agent.agent_role}</span> <span class="muted">${agent.agent_id}</span></td>
            <td>${agent.total_runs}</td>
            <td>${agent.accepted_runs}</td>
            <td class="${agent.average_usefulness >= 0 ? 'ok' : 'warn'}">${fmtNum(agent.average_usefulness)}</td>
            <td>${fmtNum(agent.last_usefulness)}</td>
          </tr>`).join('');

        document.getElementById('routes').innerHTML = routes.map(route => `
          <tr>
            <td>${route.route}</td>
            <td>${route.runs}</td>
            <td>${route.completed}</td>
            <td>${fmtPct(route.success_rate)}</td>
            <td>${fmtPct(route.average_requirements_covered)}</td>
          </tr>`).join('');

        document.getElementById('feedback').innerHTML = feedback.map(event => `
          <tr>
            <td>${event.agent_role}</td>
            <td>${event.task_status}</td>
            <td>${event.accepted ? 'yes' : 'no'}</td>
            <td class="${event.usefulness_score >= 0 ? 'ok' : 'warn'}">${fmtNum(event.usefulness_score)}</td>
            <td>${fmtPct(event.requirements_covered)}</td>
            <td>${event.notes ?? ''}</td>
          </tr>`).join('');
      }
      load();
    </script>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return dashboard_html()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
def readyz(session: Session = Depends(get_session)) -> dict:
    session.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}


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


@app.get("/feedback", response_model=list[FeedbackEventRead])
def list_feedback_endpoint(session: Session = Depends(get_session)) -> list[FeedbackEventRead]:
    feedback = list_recent_feedback(session)
    return [FeedbackEventRead.model_validate(event) for event in feedback]


@app.get("/analytics/summary")
def analytics_summary_endpoint(session: Session = Depends(get_session)) -> dict:
    return build_summary(session)


@app.get("/analytics/agents", response_model=list[AgentUsefulnessRead])
def analytics_agents_endpoint(session: Session = Depends(get_session)) -> list[AgentUsefulnessRead]:
    aggregates = list_agent_usefulness(session)
    return [AgentUsefulnessRead.model_validate(item) for item in aggregates]


@app.get("/analytics/routes")
def analytics_routes_endpoint(session: Session = Depends(get_session)) -> list[dict]:
    return build_route_analytics(session)
