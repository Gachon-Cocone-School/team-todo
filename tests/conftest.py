import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # 동일 in-memory DB 연결 재사용
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session: Session = session_factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def override_get_db() -> Session:
        yield db_session  # type: ignore[misc]

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client  # type: ignore[misc]
    app.dependency_overrides.clear()
