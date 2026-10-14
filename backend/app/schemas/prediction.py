"""Esquemas de predicción (oficial bloqueada + experimental proxy)."""


from pydantic import BaseModel, Field

# Colombia continental (grados WGS84)
LAT_MIN, LAT_MAX = -6.0, 13.0
LON_MIN, LON_MAX = -80.0, -66.0
MAX_AREA_M2 = 1e9


class PredictionFeatures(BaseModel):
    area_terreno_catastral_m2: float | None = Field(
        default=None, gt=0, le=MAX_AREA_M2,
        description="Superficie catastral del terreno (m2)",
    )
    area_zhf_m2: float | None = Field(
        default=None, gt=0, le=MAX_AREA_M2, description="Área ZHF (m2)"
    )
    area_construida_m2: float | None = Field(
        default=None, ge=0, le=MAX_AREA_M2, description="Superficie construida (m2)"
    )
    tr_latitud: float | None = Field(default=None, ge=LAT_MIN, le=LAT_MAX)
    tr_longitud: float | None = Field(default=None, ge=LON_MIN, le=LON_MAX)
    destino_economico: str | None = Field(default=None, max_length=100)
    zhf_codigo: str | None = Field(default=None, max_length=20)
    zhf_dispon: str | None = Field(default=None, max_length=20)
    zhf_influe: str | None = Field(default=None, max_length=20)
    zhf_uso_ac: str | None = Field(default=None, max_length=20)
    aht_vpoten: str | None = Field(default=None, max_length=20)
    vus_vocaci: str | None = Field(default=None, max_length=20)
    ups: str | None = Field(default=None, max_length=200)
    clc_nivel1: str | None = Field(default=None, max_length=200)
    clc_nivel2: str | None = Field(default=None, max_length=200)
    clc_nivel3: str | None = Field(default=None, max_length=200)
    clc_nivel4: str | None = Field(default=None, max_length=200)
    clc_nivel5: str | None = Field(default=None, max_length=200)
    clc_nivel6: str | None = Field(default=None, max_length=200)


class PredictionRequest(BaseModel):
    features: PredictionFeatures
    area_m2_for_total: float | None = Field(
        default=None, gt=0, le=MAX_AREA_M2,
        description="Área para calcular el total estimado (m2)",
    )


class PredictionResponse(BaseModel):
    status: str
    model_version: str | None
    dataset_version: str | None
    target: str
    unit: str
    prediction_cop_ha: float | None
    area_m2: float | None
    estimated_proxy_total_cop: float | None
    warnings: list[str]
    is_experimental: bool
    predicts_land_value: bool
    disclaimer: str


class ExperimentalRequest(BaseModel):
    features: PredictionFeatures
    area_m2_for_total: float | None = Field(
        default=None, gt=0, le=MAX_AREA_M2,
        description="Área opcional para estimar el total del proxy (m2)",
    )


class ExperimentalResponse(BaseModel):
    status: str
    experiment_id: str
    model_version: str
    target: str
    unit: str
    prediction_cop_ha: float
    area_m2: float | None
    estimated_proxy_total_cop: float | None
    warnings: list[str]
    is_experimental: bool
    predicts_land_value: bool
    disclaimer: str
