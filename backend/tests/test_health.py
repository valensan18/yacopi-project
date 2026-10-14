"""Pruebas de humo del backend (Fase 0)."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_live_returns_200():
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
