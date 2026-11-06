"""Dataset de la variable objetivo predial VALOR_TERRENO_Ha (experimental).

VALOR_TERRENO_Ha = (VALOR_AVALUO * 10000) / AREA_TERRENO_M2  [COP/ha]
Escenario A: area_construida_m2 == 0
Escenario B: 0 < area_construida_m2 <= 32
Una fila por predio (numero_predial).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
RAW_INT = ROOT / "data" / "raw" / "interseccion_terrenos_zhg_r1_yacopi.csv"
RAW_ZHF = ROOT / "data" / "raw" / "zhf_yacopi.csv"

UMBRAL_M2 = 32.0

FEATURES_EXCLUIDAS = {
    "valor_avaluo",
    "valor_hectarea_agropecuario",
    "codigo_zona_geoeconomica",
    "area_en_zonageoeconomica_m2",
    "porcentaje_en_zonageo_respecto_suma",
    "zhg_codigo",
    "zhg_valor_",
    "zhg_valor1",
    "zhg_subzon",
}

CATEGORICAS = [
    "destino_economico",
    "zhf_codigo",
    "zhf_dispon",
    "zhf_influe",
    "zhf_uso_ac",
    "sinap_nomb",
    "sinap_cate",
    "aht_vpoten",
    "fa_element",
    "vus_vocaci",
    "ups",
    "clc_nivel1",
    "clc_nivel2",
    "clc_nivel3",
    "clc_nivel4",
    "clc_nivel5",
    "clc_nivel6",
]

NUMERICAS = [
    "area_terreno_m2",
    "area_construida_m2",
    "area_zhf_m2",
    "tr_latitud",
    "tr_longitud",
]


def cargar_intersecciones() -> pd.DataFrame:
    return pd.read_csv(RAW_INT, dtype={"numero_predial": str}, low_memory=False)


def cargar_zhf() -> pd.DataFrame:
    zhf = pd.read_csv(RAW_ZHF, dtype={"CODPRED": str}, low_memory=False)
    zhf.columns = [c.lower() for c in zhf.columns]
    return zhf


def zhf_dominante_por_predio(zhf: pd.DataFrame) -> pd.DataFrame:
    """Atributos ZHF del poligono con mayor area por predio (sin valores zonales)."""
    cols_utf = {
        "codpred": "numero_predial",
        "area_terre": "area_zhf_m2",
        "tr_latitud": "tr_latitud",
        "tr_longitu": "tr_longitud",
        "zhf_codigo": "zhf_codigo",
        "zhf_dispon": "zhf_dispon",
        "zhf_influe": "zhf_influe",
        "zhf_uso_ac": "zhf_uso_ac",
        "sinap_nomb": "sinap_nomb",
        "sinap_cate": "sinap_cate",
        "aht_vpoten": "aht_vpoten",
        "fa_element": "fa_element",
        "vus_vocaci": "vus_vocaci",
        "ups": "ups",
        "clc_nivel1": "clc_nivel1",
        "clc_nivel2": "clc_nivel2",
        "clc_nivel3": "clc_nivel3",
        "clc_nivel4": "clc_nivel4",
        "clc_nivel5": "clc_nivel5",
        "clc_nivel6": "clc_nivel6",
    }
    z = zhf[list(cols_utf)].rename(columns=cols_utf).copy()
    z["_area"] = z["area_zhf_m2"].fillna(0)
    # skipna=False: conservar los valores de la MISMA fila del poligono de
    # mayor area (first() por defecto rellenaba NaN con otras filas,
    # mezclando atributos de poligonos distintos).
    return (
        z.sort_values("_area", ascending=False)
        .groupby("numero_predial")
        .first(skipna=False)
    )


def construir_dataset(escenario: str) -> pd.DataFrame:
    df = cargar_intersecciones()
    df["valor_terreno_ha"] = df["valor_avaluo"] * 10000 / df["area_terreno_m2"]
    if escenario == "A":
        df = df[df["area_construida_m2"] == 0]
    elif escenario == "B":
        df = df[(df["area_construida_m2"] > 0) & (df["area_construida_m2"] <= UMBRAL_M2)]
    else:
        raise ValueError(f"escenario desconocido: {escenario}")

    # Zona dominante por AREA de interseccion (no la primera registrada).
    zona_dom = df.loc[
        df.groupby("numero_predial")["area_en_zonageoeconomica_m2"].idxmax(),
        ["numero_predial", "codigo_zona_geoeconomica", "valor_hectarea_agropecuario"],
    ].rename(
        columns={
            "codigo_zona_geoeconomica": "codigo_zona_dominante",
            "valor_hectarea_agropecuario": "referencia_zhg_por_ha",
        }
    )

    zhf = zhf_dominante_por_predio(cargar_zhf())
    base = df.groupby("numero_predial").agg(
        valor_avaluo=("valor_avaluo", "first"),
        area_terreno_m2=("area_terreno_m2", "first"),
        area_construida_m2=("area_construida_m2", "first"),
        valor_terreno_ha=("valor_terreno_ha", "first"),
        destino_economico=("destino_economico", "first"),
    ).reset_index()

    ds = base.merge(zona_dom, on="numero_predial", how="left")
    ds = ds.merge(zhf, on="numero_predial", how="left")
    ds["tiene_zhf"] = ds["area_zhf_m2"].notna().astype(int)
    return ds


def seleccionar_features(ds: pd.DataFrame) -> pd.DataFrame:
    """Devuelve X (solo features permitidas) e y."""
    drop = [c for c in FEATURES_EXCLUIDAS if c in ds.columns]
    keep = [c for c in NUMERICAS + CATEGORICAS if c in ds.columns]
    X = ds[keep].copy()
    for c in [c for c in CATEGORICAS if c in X.columns]:
        X[c] = X[c].astype(str).fillna("SIN_DATO").replace(
            {"None": "SIN_DATO", "none": "SIN_DATO"}
        )
    constantes = [c for c in X.columns if X[c].nunique() <= 1]
    X = X.drop(columns=constantes)
    y = ds["valor_terreno_ha"].astype(float)
    meta = ds[
        [
            "numero_predial",
            "codigo_zona_dominante",
            "valor_avaluo",
            "referencia_zhg_por_ha",
        ]
    ].copy()
    return X, y, meta, drop
