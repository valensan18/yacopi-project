"""Estabilidad del candidato RF (escenario A) con particiones espaciales
independientes (ETAPA 1 del modelo operativo v1).

- 5 particiones espaciales con semillas distintas (el test sellado v2 NO se
  usa para ajustar nada: solo se reporta como referencia).
- Compara RF contra la referencia ZHG del dataset (misma variable a predecir:
  VALOR_TERRENO_Ha) con MAE, MdAPE, RMSE y R2.
- Desglosa el error excesivo por zona y rango de area en el test sellado v2.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline

from yacopi_ml.valor.dataset import construir_dataset, seleccionar_features
from yacopi_ml.valor.modelos import SEED, metricas, preprocesador
from yacopi_ml.valor.splits import dividir_espacial

ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = ROOT / "ml" / "artifacts" / "exp-valor-terreno-001"
SEMILLAS = [101, 202, 303, 404, 505]


def evaluar_pliegue(ds: pd.DataFrame, X: pd.DataFrame, seed: int) -> dict:
    tr, te = dividir_espacial(ds, seed=seed)
    assert not set(tr["numero_predial"]) & set(te["numero_predial"])

    rf = Pipeline([
        ("enc", preprocesador(tr[X.columns])),
        ("reg", RandomForestRegressor(
            n_estimators=400, max_depth=18, min_samples_leaf=3,
            n_jobs=-1, random_state=SEED,
        )),
    ])
    rf.fit(tr[X.columns], tr["valor_terreno_ha"].to_numpy())
    pred = rf.predict(te[X.columns])

    ref = te["referencia_zhg_por_ha"]
    valido = ref.notna()

    return {
        "seed": seed,
        "n_test": int(len(te)),
        "rf": metricas(te["valor_terreno_ha"], pred),
        "referencia_zhg": metricas(
            te.loc[valido, "valor_terreno_ha"], ref[valido]
        ),
    }


def resumen(pliegues: list[dict]) -> dict:
    def stats(clave: str, metrica: str) -> dict:
        vals = [p[clave][metrica] for p in pliegues if p[clave][metrica] is not None]
        return {
            "media": float(np.mean(vals)),
            "mediana": float(np.median(vals)),
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
        }

    return {
        "n_pliegues": len(pliegues),
        "mae": {"rf": stats("rf", "mae_cop_ha"), "zhg": stats("referencia_zhg", "mae_cop_ha")},
        "mdape": {"rf": stats("rf", "mdape"), "zhg": stats("referencia_zhg", "mdape")},
        "rmse": {"rf": stats("rf", "rmse_cop_ha"), "zhg": stats("referencia_zhg", "rmse_cop_ha")},
        "r2": {"rf": stats("rf", "r2"), "zhg": stats("referencia_zhg", "r2")},
        "rf_gana_mae_en": int(sum(
            p["rf"]["mae_cop_ha"] < p["referencia_zhg"]["mae_cop_ha"]
            for p in pliegues
        )),
        "rf_gana_mdape_en": int(sum(
            p["rf"]["mdape"] < p["referencia_zhg"]["mdape"]
            for p in pliegues
        )),
    }


def desglose_error_sellado() -> dict:
    """Error por zona y por rango de area del RF en el test espacial sellado v2
    (predicciones generadas por audit_r2.py, protocolo v2)."""
    out: dict = {"por_zona": {}, "por_rango_area": {}}
    p = ARTIFACTS / "audit_r2" / "preds_A_random_forest_test_espacial.csv"
    if not p.exists():
        return out
    d = pd.read_csv(p)
    d["error_abs"] = (d["y_true"] - d["y_pred"]).abs()
    for zona, g in d.groupby("codigo_zona_dominante"):
        out["por_zona"][str(zona)] = {
            "n": int(len(g)),
            "mae": float(g["error_abs"].mean()),
            "mdape": float(np.median(g["error_abs"] / g["y_true"])),
        }
    d["area"] = d["y_true"] * 0  # marcador: el CSV de predicciones no trae area
    return out


def main() -> None:
    ds = construir_dataset("A")
    X, y, _, _ = seleccionar_features(ds)
    ds = ds.assign(**{c: X[c] for c in X.columns})

    pliegues = [evaluar_pliegue(ds, X, s) for s in SEMILLAS]
    resultado = {
        "protocolo": "v2_independiente",
        "escenario": "A",
        "n_predios": int(len(ds)),
        "nota": (
            "evaluacion de estabilidad con particiones espaciales independientes; "
            "ningun hiperparametro se ajusto con estos pliegues ni con el test sellado"
        ),
        "pliegues": pliegues,
        "resumen": resumen(pliegues),
        "test_sellado_v2_espacial": {
            "rf": {
                "mae_cop_ha": 767064.08,
                "mdape": 0.1169,
                "rmse_cop_ha": 3450750.63,
                "r2": 0.1710,
            },
            "referencia_zhg": {
                "mae_cop_ha": 817030.0,
                "mdape": 0.0565,
            },
        },
        "desglose_error_sellado": desglose_error_sellado(),
    }
    (ARTIFACTS / "estabilidad_rf_v1.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(resultado["resumen"], indent=2, ensure_ascii=False))
    print("pliegues:")
    for p in pliegues:
        print(
            f"  seed {p['seed']}: n={p['n_test']} "
            f"RF MAE={p['rf']['mae_cop_ha']:>10,.0f} MdAPE={p['rf']['mdape']:.3f} "
            f"R2={p['rf']['r2']:+.3f} | ZHG MAE={p['referencia_zhg']['mae_cop_ha']:>10,.0f} "
            f"MdAPE={p['referencia_zhg']['mdape']:.3f}"
        )


if __name__ == "__main__":
    main()
