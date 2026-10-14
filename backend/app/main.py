"""Yacopí Predictor — backend FastAPI.

Fase 0: esqueleto mínimo con health check. Endpoints de consulta, estadísticas,
mapas y predicción (503 hasta modelo validado) se implementan en Fase 3.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Yacopi Predictor API",
    version="0.1.0",
    description=(
        "Estimación académica de apoyo del valor del suelo rural en Yacopí. "
        "No constituye avalúo oficial."
    ),
)


@app.get("/api/v1/health/live", tags=["health"])
def health_live() -> dict:
    return {"status": "ok"}
