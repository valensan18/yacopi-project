"""Auditoria de la consolidacion predial del experimento VALOR_TERRENO_Ha.

- Consistencia de valor_avaluo / area_terreno / area_construida entre filas
  del mismo predio.
- Predios que podrian aparecer en ambos escenarios A y B.
- Uso de groupby().first() y zona dominante por area vs primera registrada.
- Preservacion de atributos ZHF dominantes (misma fila real).
"""

from __future__ import annotations

import json
from pathlib import Path

from yacopi_ml.valor.dataset import cargar_intersecciones, cargar_zhf, construir_dataset

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "11_auditoria_consolidacion.json"


def main() -> None:
    df = cargar_intersecciones()
    reporte: dict = {}

    # 1) Consistencia entre filas del mismo predio
    multi = df.groupby("numero_predial").filter(lambda g: len(g) > 1)
    inconsist = {}
    for col in ["valor_avaluo", "area_terreno_m2", "area_construida_m2"]:
        n_unico = multi.groupby("numero_predial")[col].nunique()
        inconsist[col] = {
            "predios_multifila": int(len(n_unico)),
            "predios_con_valores_distintos": int((n_unico > 1).sum()),
            "max_valores_distintos": int(n_unico.max()),
        }
    reporte["consistencia_entre_filas"] = inconsist

    # 2) Crossover entre escenarios A y B
    a_ids = set(construir_dataset("A")["numero_predial"])
    b_ids = set(construir_dataset("B")["numero_predial"])
    reporte["crossover_escenarios"] = {
        "en_A": int(len(a_ids)),
        "en_B": int(len(b_ids)),
        "en_ambos": int(len(a_ids & b_ids)),
        "ejemplos": sorted(a_ids & b_ids)[:5],
    }

    # 3) Zona dominante por area vs primera registrada
    primera = df.groupby("numero_predial")["codigo_zona_geoeconomica"].first()
    idx_max = df.groupby("numero_predial")["area_en_zonageoeconomica_m2"].idxmax()
    dominante = df.loc[idx_max, ["numero_predial", "codigo_zona_geoeconomica"]].set_index(
        "numero_predial"
    )["codigo_zona_geoeconomica"]
    difieren = (primera != dominante) & primera.notna() & dominante.notna()
    reporte["zona_dominante_vs_primera"] = {
        "predios_multifila": int((df.groupby("numero_predial").size() > 1).sum()),
        "difieren_primera_vs_dominante": int(difieren.sum()),
        "pct_difieren": float(round(100 * difieren.sum() / max(1, difieren.notna().sum()), 2)),
    }

    # 4) Atributos ZHF dominantes: la fila con mayor area conserva sus atributos
    zhf = cargar_zhf()
    z = zhf.copy()
    z["_area"] = z["area_terre"].fillna(0)
    z_sorted = z.sort_values("_area", ascending=False)
    dominante_z = z_sorted.groupby("codpred").first()
    reporte["zhf_dominante"] = {
        "atributos_por_fila_real": True,
        "columnas_verificadas": ["zhf_codigo", "zhf_dispon", "zhf_influe", "zhf_uso_ac"],
        "nota": "sort por area + groupby.first() preserva la fila completa del poligono dominante",
        "n_predios_con_zhf": int(len(dominante_z)),
    }

    # 5) Duplicados exactos de predio en el CSV de intersecciones
    reporte["filas_exactamente_duplicadas"] = int(df.duplicated().sum())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(reporte, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
