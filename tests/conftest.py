from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ["TASKMIND_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["TASKMIND_PROVIDER"] = "mock"

from taskmind.api.main import app
from taskmind.db import Base, engine


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
