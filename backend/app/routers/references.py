"""Consulta de referencias ZHG (Fase 6B).

Dato económico territorial existente en las fuentes. NO es predicción de
aprendizaje automático ni avalúo oficial; los valores ponderados solo se
presentan como consolidación validada con cobertura consistente (≤1 %).
"""

import sqlite3

from fastapi import APIRouter, Request

from ..core.errors import InvalidQueryError, PropertyNotFoundError
from ..db import repository
from ..db.connection import get_connection
from ..schemas.references import (
    DEFAULT_LIMITATIONS,
    REFERENCE_TYPE,
    SOURCE_DESCRIPTION,
    UNIT,
    DominantZone,
    ParcelZoneItem,
    WeightedReference,
    ZhgReferenceResponse,
    ZhgZonesResponse,
    ZoneReferenceItem,
)

router = APIRouter(tags=["references"])


def _connect(request: Request) -> sqlite3.Connection:
    try:
        return get_connection(request.app.state.settings.database_path)
    except FileNotFoundError as exc:
        raise InvalidQueryError(
            details={"razon": "base de datos no disponible en este servidor"}
        ) from exc


def _weighted(zones: list[dict]) -> tuple[float | None, list[str]]:
    """Ponderación por área de intersección. Nunca usa el área total del
    predio como denominador; las zonas sin valor no se completan con cero."""
    numerador = 0.0
    denominador = 0.0
    warnings: list[str] = []
    for zone in zones:
        value = zone["value_cop_ha"]
        area = zone["area_intersection_m2"]
        if value is None or value <= 0:
            warnings.append(
                f"zona {zone['zone_code']} sin valor unitario: excluida de la ponderación"
            )
            continue
        if area is None or area <= 0:
            warnings.append(
                f"zona {zone['zone_code']} sin área de intersección: excluida de la ponderación"
            )
            continue
        numerador += value * area
        denominador += area
    if denominador <= 0:
        return None, warnings
    return numerador / denominador, warnings


def _dominant(zones: list[dict]) -> DominantZone | None:
    if not zones:
        return None
    best = max(
        zones,
        key=lambda z: (z["share_pct"] if z["share_pct"] is not None else -1.0),
    )
    return DominantZone(
        zone_code=best["zone_code"],
        value_cop_ha=best["value_cop_ha"],
        share_pct=best["share_pct"],
        note=(
            "zona con mayor participación del predio; no representa "
            "automáticamente el valor unitario de toda la propiedad cuando "
            "hay varias zonas"
        ),
    )


@router.get("/references/zhg/zones", response_model=ZhgZonesResponse)
def list_zhg_zones(request: Request) -> ZhgZonesResponse:
    conn = _connect(request)
    try:
        rows = repository.get_zhg_zones(conn)
    finally:
        conn.close()
    return ZhgZonesResponse(
        items=[ZoneReferenceItem(**row) for row in rows],
        unit=UNIT,
        reference_type=REFERENCE_TYPE,
        source_description=SOURCE_DESCRIPTION,
        reference_date=None,
        limitations=DEFAULT_LIMITATIONS,
    )


@router.get(
    "/properties/{public_id}/zhg-reference",
    response_model=ZhgReferenceResponse,
)
def parcel_zhg_reference(request: Request, public_id: str) -> ZhgReferenceResponse:
    conn = _connect(request)
    try:
        if not repository.parcel_exists(conn, public_id):
            raise PropertyNotFoundError(details={"public_id": public_id})
        rows = repository.get_parcel_zhg(conn, public_id)
    finally:
        conn.close()

    coverage = rows[0]["coverage_status"] if rows else None
    weighted_value, weighting_warnings = _weighted(rows)
    limitations = list(DEFAULT_LIMITATIONS) + weighting_warnings

    weighted_reference = None
    provisional_weighted_reference = None
    if weighted_value is not None:
        if coverage == "consistente":
            weighted_reference = WeightedReference(
                value_cop_ha=round(weighted_value, 2),
                coverage_status=coverage,
                status_label="consolidación validada (cobertura consistente ≤1 %)",
            )
        elif coverage == "dudosa":
            provisional_weighted_reference = WeightedReference(
                value_cop_ha=round(weighted_value, 2),
                coverage_status=coverage,
                status_label=(
                    "cálculo PROVISIONAL (cobertura dudosa 1–5 %): no es una "
                    "consolidación validada"
                ),
            )
        # no_apta: no se expone ningún ponderado

    if not rows:
        limitations.append(
            "Este predio no tiene referencias ZHG asociadas en la base."
        )

    return ZhgReferenceResponse(
        public_id=public_id,
        unit=UNIT,
        reference_type=REFERENCE_TYPE,
        zones=[ParcelZoneItem(**row) for row in rows],
        dominant_zone=_dominant(rows),
        weighted_reference=weighted_reference,
        provisional_weighted_reference=provisional_weighted_reference,
        coverage_status=coverage,
        source_description=SOURCE_DESCRIPTION,
        reference_date=None,
        limitations=limitations,
    )
