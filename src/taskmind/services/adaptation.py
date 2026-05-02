from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmind.models import AdaptationProposal, AgentUsefulness, ReviewCheckpoint, Run, Task
from taskmind.services.analytics import build_failed_run_analytics, build_route_analytics


def list_adaptation_proposals(session: Session, status: str | None = None) -> list[AdaptationProposal]:
    stmt = select(AdaptationProposal).order_by(AdaptationProposal.created_at.desc())
    if status:
        stmt = stmt.where(AdaptationProposal.status == status)
    return list(session.scalars(stmt))


def refresh_adaptation_proposals(session: Session) -> list[AdaptationProposal]:
    proposals: list[AdaptationProposal] = []

    for aggregate in session.scalars(select(AgentUsefulness)):
        if aggregate.total_runs < 2 or aggregate.average_usefulness >= 0.35:
            continue
        dedupe_key = f"deactivate-agent:{aggregate.agent_id}"
        proposal = _upsert_proposal(
            session,
            dedupe_key=dedupe_key,
            proposal_type="agent_deactivation",
            target_kind="agent",
            target_id=aggregate.agent_id,
            priority="high" if aggregate.average_usefulness < 0 else "medium",
            title=f"Review low-value agent {aggregate.agent_role}",
            rationale=(
                f"Agent '{aggregate.agent_role}' is averaging usefulness {aggregate.average_usefulness:.2f} "
                f"across {aggregate.total_runs} runs."
            ),
            evidence={
                "agent_role": aggregate.agent_role,
                "total_runs": aggregate.total_runs,
                "accepted_runs": aggregate.accepted_runs,
                "average_usefulness": aggregate.average_usefulness,
            },
            recommendation={
                "action": "review_for_disable",
                "reason": "consistently_low_usefulness",
            },
        )
        proposals.append(proposal)

    for route in build_route_analytics(session):
        if (
            route.get("comparison_baseline_route") is None
            or route.get("marginal_success_vs_simpler_route") is None
            or route["runs"] < 2
        ):
            continue
        if route["marginal_success_vs_simpler_route"] >= 0 and route["marginal_coverage_vs_simpler_route"] >= 0:
            continue
        dedupe_key = f"route-change:{route['route']}:{route['comparison_baseline_route']}"
        proposal = _upsert_proposal(
            session,
            dedupe_key=dedupe_key,
            proposal_type="route_change",
            target_kind="route",
            target_id=route["route"],
            priority="high" if route["marginal_success_vs_simpler_route"] < 0 else "medium",
            title=f"Compare route '{route['route']}' against simpler baseline",
            rationale=(
                f"Route '{route['route']}' is underperforming simpler baseline "
                f"'{route['comparison_baseline_route']}' for cohort {route.get('dominant_cohort') or 'unknown'}."
            ),
            evidence={
                "route": route["route"],
                "baseline_route": route["comparison_baseline_route"],
                "runs": route["runs"],
                "success_rate": route["success_rate"],
                "coverage": route["average_requirements_covered"],
                "marginal_success_vs_simpler_route": route["marginal_success_vs_simpler_route"],
                "marginal_coverage_vs_simpler_route": route["marginal_coverage_vs_simpler_route"],
                "cohort": route.get("dominant_cohort"),
            },
            recommendation={
                "action": "review_route_policy",
                "prefer_route": route["comparison_baseline_route"],
            },
        )
        proposals.append(proposal)

    failures = build_failed_run_analytics(session, limit=50)
    acceptance_failures = [failure for failure in failures if failure["failure_reason"] == "acceptance_criteria_missing"]
    if acceptance_failures:
        dedupe_key = "materials-review:implementer"
        proposal = _upsert_proposal(
            session,
            dedupe_key=dedupe_key,
            proposal_type="material_improvement",
            target_kind="agent",
            target_id="implementer_v1",
            priority="medium",
            title="Review implementer materials for repeated criteria misses",
            rationale="Recent failed runs show acceptance criteria misses that may need stronger implementation grounding.",
            evidence={
                "failure_count": len(acceptance_failures),
                "examples": acceptance_failures[:5],
            },
            recommendation={
                "action": "review_materials",
                "material_target": "implementation heuristics",
            },
        )
        proposals.append(proposal)

    session.commit()
    return list_adaptation_proposals(session)


def list_review_checkpoints(session: Session, status: str | None = None) -> list[ReviewCheckpoint]:
    stmt = select(ReviewCheckpoint).order_by(ReviewCheckpoint.created_at.desc())
    if status:
        stmt = stmt.where(ReviewCheckpoint.status == status)
    return list(session.scalars(stmt))


def ensure_review_checkpoint(session: Session, task: Task, run: Run) -> ReviewCheckpoint | None:
    evaluation = run.evaluation or {}
    should_create = task.risk_level == "high" or bool(evaluation.get("review_recommended"))
    if not should_create:
        return None

    checkpoint_type = "high_risk_validation" if task.risk_level == "high" else "failed_run_review"
    existing = session.scalars(
        select(ReviewCheckpoint).where(ReviewCheckpoint.run_id == run.id, ReviewCheckpoint.checkpoint_type == checkpoint_type)
    ).first()
    if existing:
        return existing

    checkpoint = ReviewCheckpoint(
        task_id=task.id,
        run_id=run.id,
        checkpoint_type=checkpoint_type,
        status="pending",
        rationale=(
            "High-risk task requires human validation before downstream action."
            if task.risk_level == "high"
            else "Run failed or triggered review recommendation and should be inspected by a human."
        ),
        payload={
            "task_title": task.title,
            "task_status": task.status,
            "run_status": run.status,
            "route": run.route,
            "failure_reason": evaluation.get("failure_reason"),
            "requirements_covered": evaluation.get("requirements_covered"),
        },
    )
    session.add(checkpoint)
    return checkpoint


def update_review_checkpoint(session: Session, checkpoint_id: str, status: str) -> ReviewCheckpoint | None:
    checkpoint = session.get(ReviewCheckpoint, checkpoint_id)
    if checkpoint is None:
        return None
    checkpoint.status = status
    session.add(checkpoint)
    session.commit()
    session.refresh(checkpoint)
    return checkpoint


def _upsert_proposal(
    session: Session,
    *,
    dedupe_key: str,
    proposal_type: str,
    target_kind: str,
    target_id: str,
    priority: str,
    title: str,
    rationale: str,
    evidence: dict,
    recommendation: dict,
) -> AdaptationProposal:
    proposal = session.scalars(select(AdaptationProposal).where(AdaptationProposal.dedupe_key == dedupe_key)).first()
    if proposal is None:
        proposal = AdaptationProposal(
            dedupe_key=dedupe_key,
            proposal_type=proposal_type,
            target_kind=target_kind,
            target_id=target_id,
            status="open",
            priority=priority,
            title=title,
            rationale=rationale,
            evidence=evidence,
            recommendation=recommendation,
        )
        session.add(proposal)
        return proposal

    proposal.priority = priority
    proposal.title = title
    proposal.rationale = rationale
    proposal.evidence = evidence
    proposal.recommendation = recommendation
    session.add(proposal)
    return proposal
