"""Pruebas de humo del backend (health, sin datos)."""

from pathlib import Path

from app.core.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


def test_health_live_returns_200(mini_db, tmp_path):
    settings = Settings(
        database_path=mini_db, model_dir=tmp_path / "models", _env_file=None
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "model_ready": False}


def test_docs_disponibles(mini_db, tmp_path):
    settings = Settings(
        database_path=mini_db, model_dir=tmp_path / "models", _env_file=None
    )
    with TestClient(create_app(settings)) as client:
        assert client.get("/docs").status_code == 200
