"""Shared pytest fixtures.

Tests use an isolated in-memory SQLite database so they never touch the
developer's local database file.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    from app import models  # noqa: F401  (register all models on Base.metadata)

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    """API client backed by an isolated in-memory DB and temp upload dir.

    StaticPool keeps a single connection alive so the in-memory schema/data
    persists across the app's dependency-scoped sessions.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Redirect uploads to a temp directory for the duration of the test
    import app.services.document_service as doc_service

    monkeypatch.setattr(doc_service.settings, "upload_dir", str(tmp_path))

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    engine.dispose()


def make_files(invoice_bytes: bytes = b"%PDF-1.4 fake", contract_bytes: bytes = b"%PDF-1.4 fake"):
    """Build (files dict, optional form data) for multipart upload requests."""
    files = {
        "invoice": ("invoice.pdf", invoice_bytes, "application/pdf"),
        "contract": ("contract.pdf", contract_bytes, "application/pdf"),
    }
    return files
