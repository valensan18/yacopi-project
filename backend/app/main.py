"""Yacopí Predictor API — backend FastAPI.

Modos:
- Consulta/estadísticas/mapas: SIEMPRE disponibles con datos reales.
- Predicción oficial: 503 MODEL_NOT_READY (etiqueta pendiente).
- Predicción experimental (proxy): solo si
  EXPERIMENTAL_INFERENCE_ENABLED=true (desactivada por defecto).
"""

import logging
import sqlite3
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .core.config import Settings, get_settings
from .core.errors import register_error_handlers
from .db.connection import get_connection
from .routers import (
    health,
    maps,
    models,
    predictions,
    properties,
    references,
    statistics,
    system,
)
from .services.demo import ExperimentalZhgService
from .services.prediction import (
    ExperimentalPredictionService,
    OfficialPredictionService,
)
from .services.valor_v1 import ValorV1Service

logger = logging.getLogger("yacopi.api")

API_PREFIX = "/api/v1"


def resolve_dataset_version(settings: Settings) -> str | None:
    try:
        conn = get_connection(settings.database_path)
        try:
            row = conn.execute(
                "SELECT value FROM dataset_meta WHERE key='dataset_version'"
            ).fetchone()
            return row["value"] if row else None
        finally:
            conn.close()
    except (FileNotFoundError, sqlite3.Error):
        return None


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    experimental_predictor = ExperimentalPredictionService(settings.model_dir)
    experimental_zhg = ExperimentalZhgService(settings.model_dir)
    valor_v1 = ValorV1Service(settings.model_dir)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.dataset_version = resolve_dataset_version(settings)
        app.state.official_predictor = OfficialPredictionService()
        app.state.experimental_predictor = experimental_predictor
        app.state.experimental_zhg = experimental_zhg
        app.state.valor_v1 = valor_v1

        if settings.experimental_inference_enabled:
            try:
                experimental_predictor.load()
                logger.info("Artefacto experimental cargado: %s",
                            experimental_predictor.artifact_dir)
            except Exception as exc:  # noqa: BLE001 — se registra y sigue sin ML
                logger.warning("Artefacto experimental NO cargado: %s", exc)
        else:
            logger.info("Inferencia experimental desactivada por configuración")

        if settings.experimental_zhg_enabled:
            try:
                experimental_zhg.load()
                logger.info("Demostración ZHG cargada: %s",
                            experimental_zhg.artifact_dir)
            except Exception as exc:  # noqa: BLE001 — se registra y sigue sin demo
                logger.warning("Demostración ZHG NO cargada: %s", exc)
        else:
            logger.info("Demostración ZHG desactivada por configuración")

        if settings.valor_v1_enabled:
            try:
                valor_v1.load()
                logger.info("Modelo RF v1 cargado: %s", valor_v1.artifact_dir)
            except Exception as exc:  # noqa: BLE001 — se registra y sigue sin v1
                logger.warning("Modelo RF v1 NO cargado: %s", exc)
        else:
            logger.info("Modelo RF v1 desactivado por configuración")

        app.state.dataset_version = resolve_dataset_version(settings)
        yield

    app = FastAPI(
        title="Yacopi Predictor API",
        version="0.2.0",
        description=(
            "API académica de consulta territorial para Yacopí, Cundinamarca. "
            "Estimaciones de apoyo; no constituyen avalúo oficial."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex[:12]
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    register_error_handlers(app)

    for router in (
        health.router, system.router, properties.router,
        statistics.router, maps.router, models.router, predictions.router,
        references.router,
    ):
        app.include_router(router, prefix=API_PREFIX)

    return app


app = create_app()
