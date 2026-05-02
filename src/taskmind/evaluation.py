from __future__ import annotations

import re

from taskmind.models import Task

PROMPT_MARKERS = (
    "role:",
    "purpose:",
    "expected outputs:",
    "reference materials:",
    "acceptance criteria:",
    "context:",
)
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "into",
    "your",
    "will",
    "have",
    "been",
    "about",
    "only",
    "they",
    "them",
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _criterion_keywords(criterion: str) -> set[str]:
    return {token for token in _tokenize(criterion) if len(token) >= 4 and token not in STOPWORDS}


def _criterion_matched(criterion: str, implemented: str) -> bool:
    lower_output = implemented.lower()
    if criterion.lower() in lower_output:
        return True
    keywords = _criterion_keywords(criterion)
    if not keywords:
        return False
    present = sum(1 for keyword in keywords if keyword in lower_output)
    threshold = max(1, min(len(keywords), (len(keywords) + 1) // 2))
    return present >= threshold


def _prompt_echo_marker_count(text: str) -> int:
    lower = text.lower()
    return sum(1 for marker in PROMPT_MARKERS if marker in lower)


def _looks_low_signal(text: str, criteria_count: int) -> tuple[bool, str | None]:
    tokens = _tokenize(text)
    marker_hits = _prompt_echo_marker_count(text)
    if marker_hits >= 3:
        return True, "prompt_echo"
    minimum_tokens = 30 if criteria_count <= 2 else 60
    if len(tokens) < minimum_tokens:
        return True, "low_signal_output"
    return False, None


def evaluate_run(task: Task, artifacts: dict) -> dict:
    implemented = artifacts.get("implementer", "")
    criteria = task.acceptance_criteria or []
    matched_criteria = [criterion for criterion in criteria if _criterion_matched(criterion, implemented)]
    missing_criteria = [criterion for criterion in criteria if criterion not in matched_criteria]
    criteria_hits = len(matched_criteria)
    missing_criteria_count = len(missing_criteria)
    coverage = criteria_hits / len(criteria) if criteria else 1.0

    low_signal, low_signal_reason = _looks_low_signal(implemented, len(criteria))
    accepted = coverage >= 0.75 and not low_signal
    failure_reason = None
    if not accepted:
        failure_reason = low_signal_reason or "acceptance_criteria_missing"

    return {
        "accepted": accepted,
        "requirements_covered": coverage,
        "criteria_total": len(criteria),
        "criteria_hits": criteria_hits,
        "matched_criteria": matched_criteria,
        "missing_criteria": missing_criteria,
        "missing_criteria_count": missing_criteria_count,
        "artifact_roles_present": sorted(artifacts.keys()),
        "route_length": len(task.route or []),
        "review_recommended": (task.risk_level == "high") or not accepted,
        "agent_was_necessary": len(task.route or []) > 1,
        "failure_reason": failure_reason,
        "notes": artifacts.get("critic", ""),
    }
