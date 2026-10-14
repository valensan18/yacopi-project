"""Carga de esquema de variables: allowlist y columnas bloqueadas."""

from pathlib import Path

import yaml

ML_ROOT = Path(__file__).resolve().parents[2]  # ml/
CONFIG_DIR = ML_ROOT / "config"

# Columnas numéricas y categóricas efectivas del experimento proxy (Fase 2).
# Tras auditar disponibilidad/cobertura en Fase 1, fa_element se excluye del
# experimento por cobertura baja (471 vacíos de 7.709) y se documenta.
NUMERIC_FEATURES = [
    "area_terreno_catastral_m2",
    "area_zhf_m2",
    "area_construida_m2",
    "tr_latitud",
    "tr_longitud",
]

CATEGORICAL_FEATURES = [
    "destino_economico",
    "zhf_codigo",
    "zhf_dispon",
    "zhf_influe",
    "zhf_uso_ac",
    "aht_vpoten",
    "vus_vocaci",
    "ups",
    "clc_nivel1",
    "clc_nivel2",
    "clc_nivel3",
    "clc_nivel4",
    "clc_nivel5",
    "clc_nivel6",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Columnas que solo existen en la base de datos (nombres SQLite)
SEGMENTATION_COLUMNS = [
    "destino_economico", "subzona", "tiene_alertas_calidad",
    "n_alertas_calidad", "area_construida_m2",
]


def load_features_config() -> dict:
    return yaml.safe_load(
        (CONFIG_DIR / "features.yaml").read_text(encoding="utf-8")
    )


def load_label_contract(name: str = "label_contract.yaml") -> dict:
    return yaml.safe_load((CONFIG_DIR / name).read_text(encoding="utf-8"))


def allowed_features() -> list[str]:
    return [
        item["name"] for item in load_features_config()["features"]["allowed"]
    ]


def blocked_columns() -> list[str]:
    return load_features_config()["blocked"]


def assert_no_blocked_columns(feature_columns: list[str]) -> None:
    """Falla si una columna bloqueada entra como predictora (anti-leakage)."""
    blocked = set(blocked_columns())
    used = set(feature_columns)
    overlap = used & blocked
    if overlap:
        raise ValueError(f"Columnas bloqueadas presentes en X: {sorted(overlap)}")
