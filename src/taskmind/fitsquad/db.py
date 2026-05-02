from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from taskmind.fitsquad.models import Base
from taskmind.fitsquad.seed import seed_packages


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite+pysqlite:///{(DATA_DIR / 'fitsquad_phase1.db').as_posix()}"


def make_session_factory(database_url: str = DATABASE_URL) -> sessionmaker[Session]:
    engine = create_engine(database_url, future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    return factory


SessionLocal = make_session_factory()


def init_db() -> None:
    with SessionLocal() as session:
        seed_packages(session)
