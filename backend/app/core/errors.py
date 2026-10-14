"""Errores normalizados de la API.

Formato único de error (guía §8.3):
  {"error": {"code", "message", "details", "request_id"}}
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    code = "INTERNAL_ERROR"
    status = 500
    message = "Error interno del servidor"
    details: dict | None = None

    def __init__(self, details: dict | None = None, message: str | None = None):
        self.details = details or {}
        if message:
            self.message = message
        super().__init__(self.message)


class PropertyNotFoundError(ApiError):
    code = "PROPERTY_NOT_FOUND"
    status = 404
    message = "Predio no encontrado"


class ModelNotReadyError(ApiError):
    code = "MODEL_NOT_READY"
    status = 503
    message = "No existe un modelo validado disponible para predicciones de suelo"


class ExperimentalInferenceDisabledError(ApiError):
    code = "EXPERIMENTAL_INFERENCE_DISABLED"
    status = 503
    message = "La inferencia experimental está desactivada en este entorno"


class ExperimentalModelUnavailableError(ApiError):
    code = "EXPERIMENTAL_MODEL_UNAVAILABLE"
    status = 503
    message = (
        "El artefacto experimental no está disponible o no superó la "
        "verificación de integridad"
    )


class InvalidQueryError(ApiError):
    code = "INVALID_INPUT"
    status = 422
    message = "Parámetros de consulta inválidos"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", None),
            }},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": {
                "code": "INVALID_INPUT",
                "message": "Entrada inválida: revise tipos, rangos y campos requeridos",
                "details": exc.errors(),
                "request_id": getattr(request.state, "request_id", None),
            }},
        )
