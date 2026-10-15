"""Estadísticas descriptivas calculadas sobre datos reales."""

import sqlite3

from fastapi import APIRouter, Query, Request

from ..core.errors import InvalidQueryError
from ..db import repository
from ..db.connection import get_connection

router = APIRouter(tags=["statistics"])


def _connect(request: Request) -> sqlite3.Connection:
    try:
        return get_connection(request.app.state.settings.database_path)
    except FileNotFoundError as exc:
        raise InvalidQueryError(
            details={"razon": "base de datos no disponible en este servidor"}
        ) from exc


@router.get("/statistics/overview")
def overview(request: Request) -> dict:
    conn = _connect(request)
    try:
        stats = repository.overview_stats(conn)
    finally:
        conn.close()
    return {
        "dataset_version": request.app.state.dataset_version,
        **stats,
    }


@router.get("/statistics/distributions")
def distributions(
    request: Request,
    field: str = Query(
        default="destino_economico",
        pattern="^(destino_economico|subzona|area_terreno_catastral_m2)$",
    ),
) -> dict:
    conn = _connect(request)
    try:
        result = repository.distribution(conn, field)
    finally:
        conn.close()
    return {
        "dataset_version": request.app.state.dataset_version,
        **result,
    }
