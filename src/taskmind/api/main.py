from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from taskmind.config import get_settings
from taskmind.db import Base, engine, get_session
from taskmind.models import Run
from taskmind.schemas import (
    AdaptationProposalRead,
    AgentUsefulnessRead,
    FeedbackEventRead,
    ReviewCheckpointDecision,
    ReviewCheckpointRead,
    RunRead,
    TaskCreate,
    TaskRead,
)
from taskmind.services.adaptation import (
    list_adaptation_proposals,
    list_review_checkpoints,
    refresh_adaptation_proposals,
    update_review_checkpoint,
)
from taskmind.services.analytics import (
    build_failed_run_analytics,
    build_route_analytics,
    build_summary,
    list_agent_usefulness,
    list_recent_feedback,
)
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
      :root { color-scheme: dark; --bg:#0b1020; --panel:#141c2f; --line:#2b3654; --text:#e7edf8; --muted:#9fb0d1; --good:#50c878; --warn:#f4b942; --bad:#ff6b6b; }
      body { margin:0; font-family: ui-sans-serif, system-ui, sans-serif; background: radial-gradient(circle at top, #182441 0, #0b1020 55%); color:var(--text); }
      .wrap { max-width: 1180px; margin: 0 auto; padding: 32px 20px 60px; }
      h1 { margin: 0 0 8px; font-size: 34px; }
      h2 { margin: 0 0 12px; }
      p { color: var(--muted); }
      .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin: 26px 0; }
      .card { background: rgba(20,28,47,.92); border:1px solid var(--line); border-radius: 16px; padding: 18px; box-shadow: 0 12px 34px rgba(0,0,0,.22); }
      .metric { font-size: 28px; font-weight: 700; margin-top: 8px; }
      .label { color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }
      .section { margin-top: 26px; }
      .toolbar { display:flex; gap:12px; flex-wrap:wrap; margin-top: 18px; }
      .control { display:flex; flex-direction:column; gap:6px; min-width:200px; }
      label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }
      select, button { background:#0e1629; color:var(--text); border:1px solid var(--line); border-radius:10px; padding:10px 12px; }
      button { cursor:pointer; }
      table { width:100%; border-collapse: collapse; }
      th, td { padding: 12px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
      th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }
      .pill { display:inline-block; padding:4px 10px; border-radius:999px; background:#1f2a46; color:var(--text); font-size:12px; }
      .ok { color: var(--good); }
      .warn { color: var(--warn); }
      .bad { color: var(--bad); }
      .muted { color: var(--muted); }
      .stack { display:grid; gap:10px; }
      a { color:#cfe0ff; }
      .mono { font-family: ui-monospace, SFMono-Regular, monospace; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <h1>taskmind</h1>
      <p>Task-driven execution, feedback history, and agent usefulness in one place.</p>
      <div id="summary" class="grid"></div>
      <div class="section card">
        <h2>Filters</h2>
        <div class="toolbar">
          <div class="control">
            <label for="run-status">Run status</label>
            <select id="run-status">
              <option value="">All runs</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          <div class="control">
            <label for="route-filter">Route</label>
            <select id="route-filter">
              <option value="">All routes</option>
            </select>
          </div>
          <div class="control">
            <label for="feedback-agent">Feedback agent</label>
            <select id="feedback-agent">
              <option value="">All agents</option>
            </select>
          </div>
        </div>
      </div>
      <div class="section card">
        <h2>Recent runs</h2>
        <table><thead><tr><th>Run</th><th>Status</th><th>Route</th><th>Coverage</th><th>Failure reason</th><th>Details</th></tr></thead><tbody id="runs"></tbody></table>
      </div>
      <div class="section card">
        <h2>Agent usefulness</h2>
        <table><thead><tr><th>Agent</th><th>Runs</th><th>Accepted</th><th>Avg usefulness</th><th>Last usefulness</th></tr></thead><tbody id="agents"></tbody></table>
      </div>
      <div class="section card">
        <h2>Route analytics</h2>
        <table><thead><tr><th>Route</th><th>Runs</th><th>Completed</th><th>Failed</th><th>Success rate</th><th>Coverage</th><th>Baseline</th><th>Delta vs baseline</th></tr></thead><tbody id="routes"></tbody></table>
      </div>
      <div class="section card">
        <h2>Adaptation proposals</h2>
        <div class="toolbar">
          <button id="refresh-proposals" type="button">Refresh proposals</button>
        </div>
        <table><thead><tr><th>Type</th><th>Target</th><th>Priority</th><th>Status</th><th>Recommendation</th><th>Why</th></tr></thead><tbody id="proposals"></tbody></table>
      </div>
      <div class="section card">
        <h2>Failed runs</h2>
        <table><thead><tr><th>Task</th><th>Route</th><th>Reason</th><th>Missing criteria</th><th>Error summary</th></tr></thead><tbody id="failures"></tbody></table>
      </div>
      <div class="section card">
        <h2>Review checkpoints</h2>
        <table><thead><tr><th>Type</th><th>Status</th><th>Task</th><th>Run</th><th>Rationale</th></tr></thead><tbody id="checkpoints"></tbody></table>
      </div>
      <div class="section card">
        <h2>Recent feedback</h2>
        <table><thead><tr><th>Agent</th><th>Task status</th><th>Accepted</th><th>Usefulness</th><th>Coverage</th><th>Notes</th></tr></thead><tbody id="feedback"></tbody></table>
      </div>
    </div>
    <script>
      const fmtPct = (n) => `${(Number(n) * 100).toFixed(0)}%`;
      const fmtNum = (n) => Number(n).toFixed(2);
      let allRuns = [];
      let allFeedback = [];
      let allRoutes = [];
      let allFailures = [];
      let allProposals = [];
      let allCheckpoints = [];

      function routeLabel(route) {
        return Array.isArray(route) ? route.join(' -> ') : route;
      }

      function populateSelect(id, values, allLabel) {
        const select = document.getElementById(id);
        const current = select.value;
        select.innerHTML = [`<option value="">${allLabel}</option>`]
          .concat(values.map(value => `<option value="${value}">${value}</option>`))
          .join('');
        select.value = values.includes(current) ? current : '';
      }

      function renderRuns() {
        const statusFilter = document.getElementById('run-status').value;
        const routeFilter = document.getElementById('route-filter').value;
        const filteredRuns = allRuns.filter(run => (!statusFilter || run.status === statusFilter) && (!routeFilter || routeLabel(run.route) === routeFilter));
        document.getElementById('runs').innerHTML = filteredRuns.map(run => `
          <tr>
            <td><span class="pill mono">${run.id.slice(0, 8)}</span></td>
            <td class="${run.status === 'completed' ? 'ok' : 'bad'}">${run.status}</td>
            <td>${routeLabel(run.route)}</td>
            <td>${fmtPct(run.evaluation.requirements_covered ?? 0)}</td>
            <td>${run.evaluation.failure_reason ?? ''}</td>
            <td><a href="/runs/${run.id}" target="_blank" rel="noreferrer">JSON</a></td>
          </tr>`).join('');
      }

      function renderRoutes() {
        const routeFilter = document.getElementById('route-filter').value;
        const filteredRoutes = allRoutes.filter(route => !routeFilter || route.route === routeFilter);
        document.getElementById('routes').innerHTML = filteredRoutes.map(route => {
          const delta = route.marginal_success_vs_simpler_route == null
            ? '<span class="muted">n/a</span>'
            : `${fmtPct(route.marginal_success_vs_simpler_route)} / ${fmtPct(route.marginal_coverage_vs_simpler_route)}`;
          return `
          <tr>
            <td><div class="stack"><span>${route.route}</span><span class="muted">${route.dominant_cohort ?? ''}</span></div></td>
            <td>${route.runs}</td>
            <td>${route.completed}</td>
            <td>${route.failed}</td>
            <td>${fmtPct(route.success_rate)}</td>
            <td>${fmtPct(route.average_requirements_covered)}</td>
            <td>${route.comparison_baseline_route ?? '<span class="muted">none yet</span>'}</td>
            <td>${delta}</td>
          </tr>`;
        }).join('');
      }

      function renderFailures() {
        const routeFilter = document.getElementById('route-filter').value;
        const filteredFailures = allFailures.filter(run => !routeFilter || run.route === routeFilter);
        document.getElementById('failures').innerHTML = filteredFailures.map(run => `
          <tr>
            <td><div class="stack"><span>${run.task_title ?? run.task_id}</span><span class="muted">${run.task_type ?? ''}${run.risk_level ? ` · ${run.risk_level}` : ''}</span></div></td>
            <td>${run.route}</td>
            <td class="bad">${run.failure_reason}</td>
            <td>${run.missing_criteria_count}</td>
            <td>${run.error_summary ?? ''}</td>
          </tr>`).join('');
      }

      function renderFeedback() {
        const agentFilter = document.getElementById('feedback-agent').value;
        const filteredFeedback = allFeedback.filter(event => !agentFilter || event.agent_role === agentFilter);
        document.getElementById('feedback').innerHTML = filteredFeedback.map(event => `
          <tr>
            <td>${event.agent_role}</td>
            <td>${event.task_status}</td>
            <td>${event.accepted ? 'yes' : 'no'}</td>
            <td class="${event.usefulness_score >= 0 ? 'ok' : 'warn'}">${fmtNum(event.usefulness_score)}</td>
            <td>${fmtPct(event.requirements_covered)}</td>
            <td>${event.notes ?? ''}</td>
          </tr>`).join('');
      }

      function renderProposals() {
        document.getElementById('proposals').innerHTML = allProposals.map(proposal => `
          <tr>
            <td>${proposal.proposal_type}</td>
            <td><div class="stack"><span>${proposal.target_kind}</span><span class="muted">${proposal.target_id}</span></div></td>
            <td>${proposal.priority}</td>
            <td>${proposal.status}</td>
            <td>${proposal.recommendation.action ?? ''}</td>
            <td>${proposal.rationale}</td>
          </tr>`).join('');
      }

      function renderCheckpoints() {
        document.getElementById('checkpoints').innerHTML = allCheckpoints.map(checkpoint => `
          <tr>
            <td>${checkpoint.checkpoint_type}</td>
            <td>${checkpoint.status}</td>
            <td>${checkpoint.payload.task_title ?? checkpoint.task_id ?? ''}</td>
            <td>${checkpoint.run_id ? checkpoint.run_id.slice(0, 8) : ''}</td>
            <td>${checkpoint.rationale}</td>
          </tr>`).join('');
      }

      async function refreshProposals() {
        const response = await fetch('/adaptation/proposals/refresh', { method: 'POST' });
        allProposals = await response.json();
        renderProposals();
      }

      async function load() {
        const [summary, agents, routes, feedback, runs, failures, proposals, checkpoints] = await Promise.all([
          fetch('/analytics/summary').then(r => r.json()),
          fetch('/analytics/agents').then(r => r.json()),
          fetch('/analytics/routes').then(r => r.json()),
          fetch('/feedback').then(r => r.json()),
          fetch('/runs').then(r => r.json()),
          fetch('/analytics/failures').then(r => r.json()),
          fetch('/adaptation/proposals').then(r => r.json()),
          fetch('/review-checkpoints').then(r => r.json()),
        ]);
        allRuns = runs;
        allFeedback = feedback;
        allRoutes = routes;
        allFailures = failures;
        allProposals = proposals;
        allCheckpoints = checkpoints;

        document.getElementById('summary').innerHTML = [
          ['Tasks', summary.total_tasks],
          ['Runs', summary.total_runs],
          ['Success rate', fmtPct(summary.run_success_rate)],
          ['Avg coverage', fmtPct(summary.average_requirements_covered)],
          ['Failed runs', summary.failed_runs],
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

        populateSelect('route-filter', [...new Set(routes.map(route => route.route))], 'All routes');
        populateSelect('feedback-agent', [...new Set(feedback.map(event => event.agent_role))], 'All agents');
        renderRuns();
        renderRoutes();
        renderFailures();
        renderProposals();
        renderCheckpoints();
        renderFeedback();
      }

      document.getElementById('run-status').addEventListener('change', renderRuns);
      document.getElementById('route-filter').addEventListener('change', () => {
        renderRuns();
        renderRoutes();
        renderFailures();
      });
      document.getElementById('feedback-agent').addEventListener('change', renderFeedback);
      document.getElementById('refresh-proposals').addEventListener('click', refreshProposals);
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
def list_runs_endpoint(
    status: str | None = Query(default=None),
    route: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[RunRead]:
    query = session.query(Run).order_by(Run.started_at.desc())
    if status:
        query = query.filter(Run.status == status)
    runs = query.all()
    if route:
        runs = [run for run in runs if " -> ".join(run.route or []) == route]
    return [RunRead.model_validate(run) for run in runs]


@app.get("/runs/{run_id}", response_model=RunRead)
def get_run_endpoint(run_id: str, session: Session = Depends(get_session)) -> RunRead:
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunRead.model_validate(run)


@app.get("/feedback", response_model=list[FeedbackEventRead])
def list_feedback_endpoint(
    agent_role: str | None = Query(default=None),
    task_status: str | None = Query(default=None),
    accepted: bool | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[FeedbackEventRead]:
    feedback = list_recent_feedback(session, agent_role=agent_role, task_status=task_status, accepted=accepted)
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


@app.get("/analytics/failures")
def analytics_failures_endpoint(
    route: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[dict]:
    return build_failed_run_analytics(session, route=route, limit=limit)


@app.get("/adaptation/proposals", response_model=list[AdaptationProposalRead])
def adaptation_proposals_endpoint(
    status: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[AdaptationProposalRead]:
    proposals = list_adaptation_proposals(session, status=status)
    return [AdaptationProposalRead.model_validate(item) for item in proposals]


@app.post("/adaptation/proposals/refresh", response_model=list[AdaptationProposalRead])
def refresh_adaptation_proposals_endpoint(session: Session = Depends(get_session)) -> list[AdaptationProposalRead]:
    proposals = refresh_adaptation_proposals(session)
    return [AdaptationProposalRead.model_validate(item) for item in proposals]


@app.get("/review-checkpoints", response_model=list[ReviewCheckpointRead])
def review_checkpoints_endpoint(
    status: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[ReviewCheckpointRead]:
    checkpoints = list_review_checkpoints(session, status=status)
    return [ReviewCheckpointRead.model_validate(item) for item in checkpoints]


@app.post("/review-checkpoints/{checkpoint_id}", response_model=ReviewCheckpointRead)
def update_review_checkpoint_endpoint(
    checkpoint_id: str,
    payload: ReviewCheckpointDecision,
    session: Session = Depends(get_session),
) -> ReviewCheckpointRead:
    if payload.status not in {"approved", "rejected", "pending"}:
        raise HTTPException(status_code=400, detail="Unsupported checkpoint status")
    checkpoint = update_review_checkpoint(session, checkpoint_id, payload.status)
    if checkpoint is None:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return ReviewCheckpointRead.model_validate(checkpoint)
