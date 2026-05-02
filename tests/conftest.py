from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["TASKMIND_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["TASKMIND_PROVIDER"] = "mock"

from taskmind.api.main import app
from taskmind.db import Base, engine
from taskmind.fitsquad import db as fitsquad_db
from taskmind.fitsquad import router as fitsquad_router
from taskmind.fitsquad.models import Base as FitSquadBase
from taskmind.fitsquad.seed import seed_packages


@pytest.fixture(autouse=True)
def reset_db(tmp_path, monkeypatch):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    fitsquad_engine = create_engine(
        f"sqlite+pysqlite:///{(tmp_path / 'fitsquad_test.db').as_posix()}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    FitSquadBase.metadata.drop_all(bind=fitsquad_engine)
    FitSquadBase.metadata.create_all(bind=fitsquad_engine)
    fitsquad_session_factory = sessionmaker(bind=fitsquad_engine, autocommit=False, autoflush=False)
    monkeypatch.setattr(fitsquad_db, "SessionLocal", fitsquad_session_factory)
    monkeypatch.setattr(fitsquad_router, "SessionLocal", fitsquad_session_factory)
    with fitsquad_session_factory() as session:
        seed_packages(session)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
