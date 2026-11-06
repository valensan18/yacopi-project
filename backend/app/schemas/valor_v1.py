"""Esquemas de la demostración académica del modelo RF v1 (VALOR_TERRENO_Ha)."""

from pydantic import BaseModel, Field

VALOR_V1_DISCLAIMER = (
    "Estimación orientativa de valor catastral unitario generada por un "
    "modelo experimental de demostración académica. No constituye un avalúo "
    "oficial, un precio de mercado ni un valor exclusivo de suelo verificado."
)

VALOR_V1_LIMITATIONS = [
    "Demostración académica: el modelo no superó a la referencia ZHG en MAE "
    "ni MdAPE en ninguna de las 5 particiones espaciales independientes.",
    "La variable objetivo es un cociente derivado del avalúo catastral "
    "TOTAL, sin fecha de vigencia verificable.",
    "Solo admite predios sin construcción registrada (escenario A).",
    "No existe todavía un modelo definitivo aprobado.",
]


class ValorV1Request(BaseModel):
    public_id: str = Field(min_length=1, max_length=40)


class ValorV1Response(BaseModel):
    public_id: str
    model_id: str
    model_version: str
    model_role: str
    target: str
    target_description: str
    unit: str
    predicted_cop_ha: float
    reference_zhg_cop_ha: float | None = None
    reference_zhg_note: str | None = None
    absolute_difference_vs_zhg_cop_ha: float | None = None
    relative_difference_vs_zhg_pct: float | None = None
    zone_code: str | None = None
    applicability_status: str
    applicability_conditions: list[str]
    evaluation_context: dict
    reference_date: None
    limitations: list[str]
    disclaimer: str


class ValorV1Info(BaseModel):
    habilitado: bool
    disponible: bool
    model_id: str | None = None
    model_version: str | None = None
