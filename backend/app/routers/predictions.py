"""Predicciones: oficial bloqueada (503) + experimental proxy + demo ZHG."""

from fastapi import APIRouter, Request

from ..core.errors import (
    ExperimentalInferenceDisabledError,
    ExperimentalModelUnavailableError,
    ExperimentalZhgDisabledError,
    ExperimentalZhgUnavailableError,
    PropertyNotFoundError,
)
from ..schemas.demo import ZhgDemoRequest, ZhgDemoResponse
from ..schemas.prediction import (
    ExperimentalRequest,
    ExperimentalResponse,
    PredictionRequest,
    PredictionResponse,
)

router = APIRouter(tags=["predictions"])


@router.post("/predictions", response_model=PredictionResponse)
def official_prediction(request: Request, payload: PredictionRequest):
    """Predicción OFICIAL: bloqueada hasta etiqueta validada (guía §8.2)."""
    request.app.state.official_predictor.predict(payload)


@router.post("/predictions/experimental", response_model=ExperimentalResponse)
def experimental_prediction(request: Request, payload: ExperimentalRequest):
    """Inferencia EXPERIMENTAL del proxy (solo desarrollo, desactivada por defecto)."""
    settings = request.app.state.settings
    if not settings.experimental_inference_enabled:
        raise ExperimentalInferenceDisabledError(details={
            "config": "EXPERIMENTAL_INFERENCE_ENABLED=false",
        })

    predictor = request.app.state.experimental_predictor
    if not predictor.available():
        raise ExperimentalModelUnavailableError(details={
            "config": "EXPERIMENTAL_INFERENCE_ENABLED=true pero el artefacto "
                      "no se cargó (verifique ml/artifacts/exp-proxy-001/)",
        })

    return ExperimentalResponse(
        **predictor.predict(payload.features, payload.area_m2_for_total)
    )


@router.post("/predictions/experimental-zhg", response_model=ZhgDemoResponse)
def experimental_zhg(request: Request, payload: ZhgDemoRequest):
    """Demostración experimental ZHG (Fase 7B): solo zonas conocidas y
    predios monozona; desactivada por defecto. Devuelve SIEMPRE la
    referencia ZHG junto a la estimación."""
    settings = request.app.state.settings
    if not settings.experimental_zhg_enabled:
        raise ExperimentalZhgDisabledError(details={
            "config": "EXPERIMENTAL_ZHG_ENABLED=false",
        })

    service = request.app.state.experimental_zhg
    if not service.available():
        raise ExperimentalZhgUnavailableError(details={
            "razon": "artefacto exp-zhg-001-demo no cargado",
        })

    from ..db import repository
    from ..db.connection import get_connection

    try:
        conn = get_connection(settings.database_path)
    except FileNotFoundError:
        conn = None
    if conn is not None:
        try:
            exists = repository.parcel_exists(conn, payload.public_id)
        finally:
            conn.close()
        if not exists:
            raise PropertyNotFoundError(details={"public_id": payload.public_id})

    return ZhgDemoResponse(**service.predict(payload.public_id))
