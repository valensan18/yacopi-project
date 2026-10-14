"""Esquemas de predios y paginación."""

from pydantic import BaseModel


class ParcelSummary(BaseModel):
    public_id: str
    destino_economico: str | None
    area_terreno_catastral_m2: float | None
    area_zhf_m2: float | None
    area_construida_m2: float | None
    latitud: float | None
    longitud: float | None
    subzona: str | None
    coincide_zhf: int
    cantidad_intersecciones: int | None
    cantidad_zonas_zhg: int | None
    tiene_alertas_calidad: bool
    n_alertas_calidad: int


class ParcelDetail(ParcelSummary):
    features: dict[str, str | None]
    quality_flags: list[str]


class ParcelPage(BaseModel):
    items: list[ParcelSummary]
    pagination: dict
    dataset_version: str
    public_notice: str


class ParcelDetailResponse(BaseModel):
    item: ParcelDetail
    dataset_version: str
    public_notice: str
