"""Construcción del dataset del experimento ZHG (Fase 5).

Unidad de análisis: PREDIO (una fila). El objetivo es una referencia zonal
(11 valores posibles) consolidada de dos formas:
  - valor_zona_dominante_cop_ha: valor de la zona con mayor participación.
  - valor_ponderado_cop_ha: promedio ponderado por área de intersección,
    SOLO para predios con cobertura consistente (diferencia ≤5 % entre suma
    de intersecciones y área catastral). Fuera de esa regla queda NaN.

Reglas de cobertura (docs/06):
  cobertura_consistente: dif ≤ 1 %  |  cobertura_dudosa: 1–5 %  |  no_apta: >5 %
"""

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from ..schema import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)

PROCESSED = Path(__file__).resolve().parents[4] / "data" / "processed"

TARGET_DOMINANTE = "valor_zona_dominante_cop_ha"
TARGET_PONDERADO = "valor_ponderado_cop_ha"


def fnum(value):
    try:
        ans = float(value)
    except (TypeError, ValueError):
        return None
    return ans if np.isfinite(ans) else None


def _read_intersections() -> list[dict]:
    path = PROCESSED / "01_intersecciones_normalizadas.csv"
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _read_zhf() -> list[dict]:
    path = PROCESSED / "02_zhf_normalizadas.csv"
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def build_zhg_dataset(processed: Path = PROCESSED) -> pd.DataFrame:
    inter_rows = _read_intersections()
    zhf_rows = _read_zhf()

    zhf_by_predio: dict[str, dict] = {}
    for row in zhf_rows:
        zhf_by_predio.setdefault(row["CODPRED"], row)

    groups: dict[str, list[dict]] = defaultdict(list)
    for row in inter_rows:
        groups[row["numero_predial"]].append(row)

    records: list[dict] = []
    for predio, rows in groups.items():
        area = fnum(rows[0]["area_terreno_m2"]) or 0.0
        shares: dict[str, float] = defaultdict(float)
        values_by_zone: dict[str, float] = {}
        area_by_zone: dict[str, float] = defaultdict(float)
        for row in rows:
            zone = str(row["codigo_zona_geoeconomica"]).zfill(2)
            share = fnum(row["porcentaje_en_zonageo_respecto_suma"]) or 0.0
            value = fnum(row["valor_hectarea_agropecuario"]) or 0.0
            area_zone = fnum(row["area_en_zonageoeconomica_m2"]) or 0.0
            shares[zone] += share
            values_by_zone[zone] = value
            area_by_zone[zone] += area_zone

        if not shares:
            continue

        zona_dominante = max(shares, key=shares.get)
        valor_dominante = values_by_zone[zona_dominante]

        suma_areas = sum(area_by_zone.values())
        valor_ponderado = None
        if area > 0 and suma_areas > 0:
            rel = abs(suma_areas - area) / area
            cobertura = (
                "consistente" if rel <= 0.01 else
                "dudosa" if rel <= 0.05 else "no_apta"
            )
            if cobertura != "no_apta":
                valor_ponderado = (
                    sum(area_by_zone[z] * values_by_zone[z] for z in area_by_zone)
                    / suma_areas
                )
        else:
            cobertura = "no_apta"

        zf = zhf_by_predio.get(predio)
        record = {
            "public_id": predio,
            "destino_economico": rows[0].get("destino_economico", ""),
            "area_terreno_catastral_m2": area or None,
            "area_construida_m2": fnum(rows[0].get("area_construida_m2")),
            "area_zhf_m2": fnum(zf["AREA_TERRE"]) if zf else None,
            "tr_latitud": fnum(zf["TR_LATITUD"]) if zf else None,
            "tr_longitud": fnum(zf["TR_LONGITU"]) if zf else None,
            "n_intersecciones": len(rows),
            "n_zonas": len(shares),
            "zona_dominante": zona_dominante,
            "participacion_dominante": shares[zona_dominante],
            "cobertura": cobertura,
            TARGET_DOMINANTE: valor_dominante,
            TARGET_PONDERADO: valor_ponderado,
        }
        if zf:
            for col in (
                "zhf_codigo", "zhf_dispon", "zhf_influe", "zhf_uso_ac",
                "aht_vpoten", "vus_vocaci", "ups",
            ):
                record[col] = zf.get(col.upper(), "")
            for i in range(1, 7):
                record[f"clc_nivel{i}"] = zf.get(f"CLC_NIVEL{i}", "")
        records.append(record)

    df = pd.DataFrame(records)
    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in CATEGORICAL_FEATURES:
        if col not in df.columns:
            df[col] = "SIN_DATO"
        df[col] = df[col].astype("object")
        df[col] = df[col].mask(df[col].isna(), "SIN_DATO")
    return df
