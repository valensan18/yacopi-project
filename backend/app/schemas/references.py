"""Esquemas de referencias ZHG (dato territorial, no predicción)."""

from pydantic import BaseModel

REFERENCE_TYPE = "zhg_zonal_reference"
UNIT = "COP/ha"

DEFAULT_LIMITATIONS = [
    "Referencia zonal catastral; no es un avalúo individual certificado "
    "del predio.",
    "La vigencia oficial del valor zonal no está acreditada en los datos "
    "recibidos (reference_date = null).",
    "No es una predicción de aprendizaje automático.",
]

SOURCE_DESCRIPTION = (
    "valor_hectarea_agropecuario (CSV de intersecciones), equivalente a "
    "ZHG_VALOR_ por zona geoeconómica (equivalencia verificada en Fase 5A)."
)


class ZoneReferenceItem(BaseModel):
    zone_code: str
    value_cop_ha: float
    source_column: str


class ZhgZonesResponse(BaseModel):
    items: list[ZoneReferenceItem]
    unit: str
    reference_type: str
    source_description: str
    reference_date: None
    limitations: list[str]


class ParcelZoneItem(BaseModel):
    zone_code: str
    value_cop_ha: float | None
    area_intersection_m2: float | None
    share_pct: float | None


class DominantZone(BaseModel):
    zone_code: str
    value_cop_ha: float | None
    share_pct: float | None
    note: str


class WeightedReference(BaseModel):
    value_cop_ha: float
    coverage_status: str
    status_label: str


class ZhgReferenceResponse(BaseModel):
    public_id: str
    unit: str
    reference_type: str
    zones: list[ParcelZoneItem]
    dominant_zone: DominantZone | None
    weighted_reference: WeightedReference | None
    provisional_weighted_reference: WeightedReference | None
    coverage_status: str | None
    source_description: str
    reference_date: None
    limitations: list[str]
