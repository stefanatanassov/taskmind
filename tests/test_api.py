from __future__ import annotations


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_create_task(client):
    payload = {
        "title": "Test task",
        "description": "Create a first task.",
        "task_type": "feature",
        "risk_level": "medium",
        "acceptance_criteria": ["do one", "do two"],
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Test task"
    assert body["route"] == ["implementer", "critic"]
