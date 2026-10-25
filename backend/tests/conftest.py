from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    database_path = (tmp_path / "test.db").as_posix()
    return Settings(
        _env_file=None,
        environment="test",
        database_url=f"sqlite:///{database_path}",
        auto_create_tables=True,
        seed_demo_data=True,
        max_draft_chars=5_000,
        max_purpose_chars=200,
        max_request_bytes=250_000,
        cors_origins="http://localhost:3000",
        log_level="WARNING",
    )


@pytest.fixture
def client(settings: Settings):
    app = create_app(settings)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def demo_payload() -> dict:
    return {
        "brand_id": "brand_001",
        "draft_text": (
            "Our cheapest plan is guaranteed to be revolutionary!!! "
            "Users love it. TrueLine ships free over $50."
        ),
        "purpose": "marketing",
    }
