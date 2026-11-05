"""Auditoria de la nueva variable objetivo predial (Fase 1, experimental).

VALOR_TERRENO_Ha = (VALOR_AVALUO * 10000) / AREA_TERRENO_M2  [COP/ha]
Escenario A: area_construida_m2 == 0
Escenario B: 0 < area_construida_m2 <= 32 (filtro del profesor Jesus)

Sin modificar datos ni SQLite; solo lectura de los CSV crudos.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "interseccion_terrenos_zhg_r1_yacopi.csv"
OUT = ROOT / "data" / "processed" / "09_auditoria_valor_terreno.json"

UMBRAL = 32.0


def pct(x: pd.Series, p: float) -> float:
    return float(np.nanpercentile(x, p))


def stats(s: pd.Series) -> dict:
    return {
        "n": int(s.notna().sum()),
        "nulos": int(s.isna().sum()),
        "ceros": int((s == 0).sum()),
        "negativos": int((s < 0).sum()),
        "min": float(s.min()),
        "p05": pct(s, 5),
        "p50": pct(s, 50),
        "p95": pct(s, 95),
        "max": float(s.max()),
    }


def main() -> None:
    df = pd.read_csv(RAW, dtype={"numero_predial": str}, low_memory=False)
    report: dict = {}

    report["filas_csv"] = len(df)
    report["predios_unicos"] = int(df["numero_predial"].nunique())
    dups = df["numero_predial"].duplicated().sum()
    report["filas_duplicadas_predio"] = int(dups)
    report["predios_con_mas_de_una_fila"] = int(
        (df.groupby("numero_predial").size() > 1).sum()
    )
    report["filas_con_mas_de_una_fila"] = int(
        df.groupby("numero_predial").size().gt(1).sum()
    )

    for col in ["valor_avaluo", "area_terreno_m2", "area_construida_m2",
                "area_en_zonageoeconomica_m2", "valor_hectarea_agropecuario"]:
        report[f"col_{col}"] = stats(df[col])

    # Umbral sobre CONSTRUCCION (no sobre terreno): aclaracion metodologica.
    df["valor_terreno_ha"] = np.where(
        df["area_terreno_m2"].gt(0),
        df["valor_avaluo"] * 10000 / df["area_terreno_m2"],
        np.nan,
    )
    esc_a = df[df["area_construida_m2"] == 0]
    esc_b = df[(df["area_construida_m2"] > 0) & (df["area_construida_m2"] <= UMBRAL)]
    constru_null = df["area_construida_m2"].isna()
    report["escenario_A_constr_0_predios"] = int(esc_a["numero_predial"].nunique())
    report["escenario_B_constr_0_32_predios"] = int(esc_b["numero_predial"].nunique())
    report["escenario_A_filas"] = len(esc_a)
    report["escenario_B_filas"] = len(esc_b)
    report["constr_nula_filas"] = int(constru_null.sum())
    report["constr_nula_NO_es_cero_confirmado"] = True
    report["constr_gt_32_filas"] = int((df["area_construida_m2"] > UMBRAL).sum())
    report["umbral_m2"] = UMBRAL
    report["umbral_aplica_a"] = "area_construida_m2"

    report["valor_terreno_ha_calculable"] = int(df["valor_terreno_ha"].notna().sum())
    report["area_terreno_invalida_filas"] = int((df["area_terreno_m2"] <= 0).sum())
    report["valor_avaluo_invalido_filas"] = int((df["valor_avaluo"] <= 0).sum())

    for nombre, sub in [("A_constr_0", esc_a), ("B_constr_0_32", esc_b)]:
        v = sub.loc[sub["area_terreno_m2"].gt(0) & sub["valor_avaluo"].gt(0),
                    "valor_terreno_ha"]
        report[f"esc_{nombre}_n_valido"] = int(v.notna().sum())
        report[f"esc_{nombre}_valor_ha_stats"] = stats(v)
        report[f"esc_{nombre}_unicos"] = int(v.nunique())
        report[f"esc_{nombre}_n_unico_por_predio"] = int(
            sub.groupby("numero_predial")["valor_terreno_ha"].nunique().max()
        )

    # Atipicos por area pequena
    peq = df[(df["area_terreno_m2"] > 0) & (df["area_terreno_m2"] <= 100)]
    report["area_terreno_leq_100m2_filas"] = int(len(peq))
    report["area_terreno_leq_100m2_valor_ha_max"] = float(
        np.nanmax(np.where(peq["area_terreno_m2"] > 0,
                           peq["valor_avaluo"] * 10000 / peq["area_terreno_m2"],
                           np.nan))
    )

    # Derivacion directa del valor zonal: VALOR_TERRENO_Ha vs valor_hectarea_agropecuario
    igual = df[df["area_terreno_m2"].gt(0)]
    igual["igual_zonal"] = np.isclose(
        igual["valor_terreno_ha"], igual["valor_hectarea_agropecuario"], rtol=1e-9
    )
    report["valor_terreno_ha_igual_a_zonal_pct"] = float(igual["igual_zonal"].mean())
    report["corr_valor_terreno_ha_vs_zonal"] = float(
        igual[["valor_terreno_ha", "valor_hectarea_agropecuario"]].corr().iloc[0, 1]
    )
    # Valores distintos del objetivo
    report["valor_terreno_ha_unicos_total"] = int(
        df["valor_terreno_ha"].nunique(dropna=True)
    )
    report["valor_hectarea_agropecuario_unicos"] = int(
        df["valor_hectarea_agropecuario"].nunique(dropna=True)
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
