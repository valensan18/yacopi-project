"""Mapas: GeoJSON de puntos reales (EPSG:4326), con bbox y límite."""

import sqlite3

from fastapi import APIRouter, Query, Request

from ..core.errors import InvalidQueryError
from ..db import repository
from ..db.connection import get_connection

router = APIRouter(tags=["maps"])


def _connect(request: Request) -> sqlite3.Connection:
    try:
        return get_connection(request.app.state.settings.database_path)
    except FileNotFoundError as exc:
        raise InvalidQueryError(details={"razon": str(exc)}) from exc


@router.get("/maps/points")
def map_points(
    request: Request,
    min_lat: float | None = Query(default=None, ge=-6, le=13),
    min_lon: float | None = Query(default=None, ge=-80, le=-66),
    max_lat: float | None = Query(default=None, ge=-6, le=13),
    max_lon: float | None = Query(default=None, ge=-80, le=-66),
    limit: int = Query(default=5000, ge=1),
) -> dict:
    settings = request.app.state.settings
    if limit > settings.max_map_points:
        limit = settings.max_map_points

    conn = _connect(request)
    try:
        points = repository.map_points(
            conn, min_lat, min_lon, max_lat, max_lon, limit
        )
    finally:
        conn.close()

    return {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [p["longitud"], p["latitud"]],
                },
                "properties": {
                    "public_id": p["public_id"],
                    "destino_economico": p["destino_economico"],
                    "subzona": p["subzona"],
                },
            }
            for p in points
            if p["latitud"] is not None and p["longitud"] is not None
        ],
        "aviso": (
            "Puntos referenciales del archivo ZHF (TR_LATITUD/TR_LONGITUD), "
            "no polígonos catastrales oficiales."
        ),
    }
