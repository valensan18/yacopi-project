"""Predicciones: oficial bloqueada (503) + experimental proxy controlada."""

from fastapi import APIRouter, Request

from ..core.errors import (
    ExperimentalInferenceDisabledError,
    ExperimentalModelUnavailableError,
)
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
