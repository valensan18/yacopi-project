"""Carga de la cohorte y de la variable proxy desde la base SQLite.

La variable proxy es `referencia_avaluo_total_por_ha_cop` (avalúo catastral
TOTAL / área catastral x 10.000, COP/ha). NO es un valor exclusivo de
terreno: se usa únicamente en el experimento Ruta B y se documenta en
`ml/config/label_contract_proxy.yaml`.
"""

import sqlite3
from pathlib import Path

import pandas as pd

from .schema import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
)

PROXY_REFERENCE_TYPE = "avaluo_total_ha"
MIN_AREA_M2 = 1.0  # área catastral mínima para que el cociente tenga sentido
MIN_TARGET_COP_HA = 1.0


def load_cohort(db_path: Path) -> pd.DataFrame:
    """Une parcels + parcel_features y devuelve la cohorte ML.

    La cohorte es el conjunto de predios con coincidencia ZHF (atributos
    físicos y coordenadas disponibles): 7.694 predios. Los 15 predios solo
    de la primera fuente se excluyen por cobertura (documentado, no es
    limpieza de anomalías).
    """
    conn = sqlite3.connect(db_path)
    parcels = pd.read_sql_query(
        """SELECT public_id, parcel_source_id, destino_economico,
                  area_terreno_catastral_m2, area_zhf_m2, area_construida_m2,
                  latitud AS tr_latitud, longitud AS tr_longitud,
                  subzona, coincide_zhf, tiene_alertas_calidad,
                  n_alertas_calidad
           FROM parcels""",
        conn,
    )
    features = pd.read_sql_query(
        "SELECT * FROM parcel_features", conn
    ).set_index("public_id")
    conn.close()

    cohort = parcels.join(features, on="public_id")
    cohort = cohort[cohort["coincide_zhf"] == 1].copy()
    cohort = cohort.drop_duplicates(subset="parcel_source_id")
    return cohort.reset_index(drop=True)


def build_dataset(db_path: Path) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Construye (X, y, contexto) validando la etiqueta proxy.

    Reglas de validación de la etiqueta:
      - área catastral finita y > MIN_AREA_M2
      - valor del avalúo por ha finito y >= MIN_TARGET_COP_HA
      - unidades COP/ha (el cociente ya viene en esa unidad en la fuente)
    Los casos descartados se reportan en `contexto["excluidos"]` sin
    eliminarse de la base.
    """
    cohort = load_cohort(db_path)
    avaluo_ha = load_proxy_references(db_path)

    data = cohort.join(avaluo_ha.set_index("public_id"), on="public_id")

    area = pd.to_numeric(data["area_terreno_catastral_m2"], errors="coerce")
    target = pd.to_numeric(data["proxy_cop_ha"], errors="coerce")

    valid_area = area.notna() & (area >= MIN_AREA_M2)
    valid_target = target.notna() & (target >= MIN_TARGET_COP_HA)
    mask = valid_area & valid_target

    excluidos = {
        "sin_referencia_proxy": int((~data["proxy_cop_ha"].notna()).sum()),
        "area_invalida": int((~valid_area).sum()),
        "objetivo_invalido": int((~valid_target).sum()),
        "total_excluidos": int((~mask).sum()),
        "total_cohorte": len(data),
    }

    kept = data[mask].reset_index(drop=True)
    X = kept[FEATURE_COLUMNS].copy()
    for col in NUMERIC_FEATURES:
        X[col] = pd.to_numeric(X[col], errors="coerce")
    for col in CATEGORICAL_FEATURES:
        # "SIN_DATO" = valor faltante en la fuente (marcador documentado,
        # compatible con sklearn y CatBoost; nunca un valor inventado).
        X[col] = X[col].astype("object")
        X[col] = X[col].mask(X[col].isna(), "SIN_DATO")

    y = pd.to_numeric(kept["proxy_cop_ha"], errors="coerce")

    contexto = pd.DataFrame({
        "public_id": kept["public_id"],
        "destino_economico": kept["destino_economico"],
        "subzona": kept["subzona"],
        "tiene_alertas_calidad": kept["tiene_alertas_calidad"],
        "n_alertas_calidad": kept["n_alertas_calidad"],
        "area_construida_m2": pd.to_numeric(
            kept["area_construida_m2"], errors="coerce"
        ).fillna(0.0),
        "area_terreno_catastral_m2": area[mask].reset_index(drop=True),
        "tr_latitud": kept["tr_latitud"],
        "tr_longitud": kept["tr_longitud"],
    })

    return X, y, {"excluidos": excluidos, "contexto": contexto}


def load_proxy_references(db_path: Path) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    refs = pd.read_sql_query(
        """SELECT public_id, value_cop AS proxy_cop_ha
           FROM parcel_value_references
           WHERE reference_type = ? AND unit = 'COP/ha'""",
        conn,
        params=(PROXY_REFERENCE_TYPE,),
    )
    conn.close()
    return refs
