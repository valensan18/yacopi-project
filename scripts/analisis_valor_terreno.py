"""Analisis de la nueva variable objetivo (Fase 1, parte 2, experimental).

- Verifica si VALOR_AVALUO se deriva mecanicamente del valor zonal (fuga).
- Compara VALOR_TERRENO_Ha contra la referencia ZHG por predio/zona.
- Compara areas: terreno catastral vs interseccion geoeconomica vs ZHF.
- Genera CSV de comparacion para ambos escenarios (sin sobrescribir datos).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "interseccion_terrenos_zhg_r1_yacopi.csv"
ZHF = ROOT / "data" / "raw" / "zhf_yacopi.csv"
OUT_JSON = ROOT / "data" / "processed" / "10_analisis_valor_terreno.json"
OUT_CSV = ROOT / "data" / "processed" / "10_comparacion_valor_terreno_zhg.csv"

UMBRAL = 32.0


def main() -> None:
    df = pd.read_csv(RAW, dtype={"numero_predial": str}, low_memory=False)
    df["valor_terreno_ha"] = df["valor_avaluo"] * 10000 / df["area_terreno_m2"]
    report: dict = {}

    # 1) Derivacion mecanica del valor zonal: avaluo == area * zonal_ha / 10000?
    df["avaluo_zonal_estimado"] = (
        df["area_terreno_m2"] * df["valor_hectarea_agropecuario"] / 10000
    )
    df["avaluo_igual_zonal_est"] = np.isclose(
        df["valor_avaluo"], df["avaluo_zonal_estimado"], rtol=1e-6
    )
    report["avaluo_igual_a_zonal_x_area_pct"] = float(df["avaluo_igual_zonal_est"].mean())
    report["corr_avaluo_vs_zonal_x_area"] = float(
        df[["valor_avaluo", "avaluo_zonal_estimado"]].corr().iloc[0, 1]
    )

    # Solo filas en una unica zona (predios sin particion)
    single = df.groupby("numero_predial").filter(lambda g: len(g) == 1)
    single["avaluo_zonal_est"] = (
        single["area_terreno_m2"] * single["valor_hectarea_agropecuario"] / 10000
    )
    report["unica_zona_avaluo_igual_zonal_pct"] = float(
        np.isclose(single["valor_avaluo"], single["avaluo_zonal_est"], rtol=1e-6).mean()
    )
    report["unica_zona_corr_avaluo_zonal_est"] = float(
        single[["valor_avaluo", "avaluo_zonal_est"]].corr().iloc[0, 1]
    )

    # 2) Comparacion VALOR_TERRENO_Ha vs referencia zonal por fila
    df["ratio_vs_zonal"] = df["valor_terreno_ha"] / df["valor_hectarea_agropecuario"]
    df["dif_vs_zonal_cop_ha"] = df["valor_terreno_ha"] - df["valor_hectarea_agropecuario"]
    esc_a = df[df["area_construida_m2"] == 0]
    esc_b = df[(df["area_construida_m2"] > 0) & (df["area_construida_m2"] <= UMBRAL)]
    for nombre, sub in [("A_constr_0", esc_a), ("B_constr_0_32", esc_b)]:
        r = sub["ratio_vs_zonal"]
        report[f"esc_{nombre}_ratio_vs_zonal_p50"] = float(np.nanmedian(r))
        report[f"esc_{nombre}_ratio_vs_zonal_p05"] = float(np.nanpercentile(r, 5))
        report[f"esc_{nombre}_ratio_vs_zonal_p95"] = float(np.nanpercentile(r, 95))
        report[f"esc_{nombre}_ratio_vs_zonal_pct_entre_0.5_2"] = float(
            ((r >= 0.5) & (r <= 2)).mean()
        )
        d = sub["dif_vs_zonal_cop_ha"]
        report[f"esc_{nombre}_dif_vs_zonal_p50_cop_ha"] = float(np.nanmedian(d))
        report[f"esc_{nombre}_dif_vs_zonal_mae_cop_ha"] = float(
            np.nanmean(np.abs(d))
        )
        report[f"esc_{nombre}_zona_igual_pct"] = float(
            (np.abs(sub["valor_terreno_ha"] - sub["valor_hectarea_agropecuario"]) < 1).mean()
        )

    # 3) Comparacion de areas: terreno vs interseccion geoeconomica vs ZHF
    df["pct_geoecon_vs_terreno"] = df["area_en_zonageoeconomica_m2"] / df["area_terreno_m2"]
    report["area_geoecon_p50_pct_del_terreno"] = float(np.nanmedian(df["pct_geoecon_vs_terreno"]))
    report["area_geoecon_sum_por_predio_p50_pct"] = float(
        df.groupby("numero_predial")["area_en_zonageoeconomica_m2"]
        .sum()
        .div(df.groupby("numero_predial")["area_terreno_m2"].first())
        .median()
    )
    report["filas_area_geoecon_gt_terreno"] = int(
        (df["area_en_zonageoeconomica_m2"] > df["area_terreno_m2"]).sum()
    )
    zhf = pd.read_csv(ZHF, low_memory=False, dtype={"CODPRED": str})
    zhf_cols = {c.lower(): c for c in zhf.columns}
    area_col = zhf_cols.get("area_terre")
    cod_col = zhf_cols.get("codpred")
    if area_col is not None and cod_col is not None:
        zhf_area = zhf.groupby(cod_col)[area_col].sum().rename("area_zhf_m2")
        df2 = df.merge(zhf_area, left_on="numero_predial", right_index=True, how="left")
        df2["pct_zhf_vs_terreno"] = df2["area_zhf_m2"] / df2["area_terreno_m2"]
        report["predios_con_dato_zhf"] = int(df2["area_zhf_m2"].notna().sum())
        report["area_zhf_p50_pct_del_terreno"] = float(np.nanmedian(df2["pct_zhf_vs_terreno"]))
        report["area_zhf_gt_terreno_pct"] = float(
            (df2["area_zhf_m2"] > df2["area_terreno_m2"]).mean()
        )
    else:
        report["area_zhf_comparacion"] = "columna no encontrada"

    # 4) CSV de comparacion (una fila por fila del CSV, escenarios marcados)
    out = df.assign(
        escenario=lambda d: np.where(
            d["area_construida_m2"] == 0,
            "A",
            np.where(d["area_construida_m2"] <= UMBRAL, "B", "excluido"),
        )
    )[
        [
            "numero_predial", "destino_economico", "codigo_zona_geoeconomica",
            "valor_avaluo", "area_terreno_m2", "area_construida_m2",
            "valor_terreno_ha", "valor_hectarea_agropecuario",
            "dif_vs_zonal_cop_ha", "ratio_vs_zonal", "escenario",
        ]
    ]
    out.to_csv(OUT_CSV, index=False)

    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
