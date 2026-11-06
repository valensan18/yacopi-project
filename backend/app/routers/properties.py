"""Consulta de predios (solo public_id opaco)."""

import sqlite3

from fastapi import APIRouter, Query, Request

from ..core.errors import (
    InvalidQueryError,
    PropertyNotFoundError,
    ValorV1DisabledError,
    ValorV1UnavailableError,
)
from ..db import repository
from ..db.connection import get_connection
from ..schemas.properties import (
    ParcelDetail,
    ParcelDetailResponse,
    ParcelPage,
    ParcelSummary,
)

router = APIRouter(tags=["properties"])

PUBLIC_NOTICE = (
    "Identificadores prediales reales no se exponen: cada predio usa un "
    "public_id opaco."
)


def _connect(request: Request) -> sqlite3.Connection:
    try:
        return get_connection(request.app.state.settings.database_path)
    except FileNotFoundError as exc:
        raise InvalidQueryError(
            details={"razon": "base de datos no disponible en este servidor"}
        ) from exc


@router.get("/properties", response_model=ParcelPage)
def list_properties(
    request: Request,
    destino: str | None = Query(default=None, max_length=100),
    subzona: str | None = Query(default=None, max_length=20),
    min_area_m2: float | None = Query(default=None, ge=0, le=1e12),
    max_area_m2: float | None = Query(default=None, ge=0, le=1e12),
    min_lat: float | None = Query(default=None, ge=-90, le=90),
    min_lon: float | None = Query(default=None, ge=-180, le=180),
    max_lat: float | None = Query(default=None, ge=-90, le=90),
    max_lon: float | None = Query(default=None, ge=-180, le=180),
    sort: str = Query(
        default="public_id",
        pattern="^(public_id|destino_economico|area|subzona|latitud|longitud)$",
    ),
    sort_desc: bool = False,
    limit: int = Query(default=20, ge=1),
    offset: int = Query(default=0, ge=0),
    public_id_prefix: str | None = Query(
        default=None, min_length=2, max_length=18,
        pattern="^p_[0-9a-f]{0,16}$",
        description="Prefijo de identificador público (búsqueda para el selector)",
    ),
    solo_estimables: bool = Query(
        default=False,
        description=(
            "Mostrar únicamente predios elegibles para la estimación del "
            "modelo académico RF v1 (escenario A, validaciones de dominio)"
        ),
    ),
) -> ParcelPage:
    settings = request.app.state.settings
    if limit > settings.max_page_limit:
        limit = settings.max_page_limit

    only_ids: set[str] | None = None
    if solo_estimables:
        if not settings.valor_v1_enabled:
            raise ValorV1DisabledError(details={
                "config": "VALOR_V1_ENABLED=false",
            })
        service = request.app.state.valor_v1
        if not service.available():
            raise ValorV1UnavailableError(details={
                "razon": "artefacto exp-valor-v1 no cargado",
            })
        only_ids = service.admitidos()

    conn = _connect(request)
    try:
        rows, total = repository.list_parcels(
            conn,
            destino=destino, subzona=subzona,
            min_area=min_area_m2, max_area=max_area_m2,
            min_lat=min_lat, min_lon=min_lon,
            max_lat=max_lat, max_lon=max_lon,
            public_id_prefix=public_id_prefix,
            only_ids=only_ids,
            sort=sort, sort_desc=sort_desc,
            limit=limit, offset=offset,
        )
    finally:
        conn.close()

    return ParcelPage(
        items=[ParcelSummary(**r) for r in rows],
        pagination={"limit": limit, "offset": offset, "total": total},
        dataset_version=request.app.state.dataset_version,
        public_notice=PUBLIC_NOTICE,
    )


@router.get("/properties/{public_id}", response_model=ParcelDetailResponse)
def get_property(request: Request, public_id: str) -> ParcelDetailResponse:
    conn = _connect(request)
    try:
        parcel = repository.get_parcel(conn, public_id)
    finally:
        conn.close()
    if parcel is None:
        raise PropertyNotFoundError(details={"public_id": public_id})
    return ParcelDetailResponse(
        item=ParcelDetail(**parcel),
        dataset_version=request.app.state.dataset_version,
        public_notice=PUBLIC_NOTICE,
    )
