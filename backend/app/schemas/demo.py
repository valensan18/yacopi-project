"""Esquemas de la demostración experimental ZHG (Fase 7B)."""

from pydantic import BaseModel, Field

DEMO_DISCLAIMER = (
    "Demostración experimental de aprendizaje automático. Su resultado no "
    "constituye un avalúo individual certificado ni reemplaza la referencia "
    "ZHG."
)

DEMO_LIMITATIONS = [
    DEMO_DISCLAIMER,
    "Válida únicamente para predios de zonas conocidas del municipio "
    "(interpolación); no se declara generalización a zonas no observadas.",
    "El valor de referencia ZHG ya era consultable; la estimación ML no lo "
    "reemplaza.",
    "Las métricas de la Fase 5 son históricas y no constituyen una "
    "evaluación independiente de este artefacto.",
    "Fecha de vigencia de la referencia: no disponible.",
]


class ZhgDemoRequest(BaseModel):
    public_id: str = Field(min_length=1, max_length=40)


class ZhgDemoResponse(BaseModel):
    public_id: str
    model_id: str
    model_status: str
    unit: str
    target_description: str
    reference_zhg_cop_ha: float
    predicted_zhg_cop_ha: float
    absolute_difference_cop_ha: float
    relative_difference_pct: float | None
    zone_code: str
    domain_status: str
    source_description: str
    reference_date: None
    limitations: list[str]
    evaluation_context: dict
    disclaimer: str


class ExperimentalZhgInfo(BaseModel):
    habilitado: bool
    disponible: bool
    model_id: str | None = None
