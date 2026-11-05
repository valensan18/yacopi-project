"""Entrenamiento comparativo del experimento VALOR_TERRENO_Ha (experimental).

CORREGIDO (v2): dos protocolos independientes —
  PROTOCOLO PREDIO:   entrena con tr_predio, evalua con te_predio.
  PROTOCOLO ESPACIAL: entrena una instancia NUEVA con tr_esp, evalua con te_esp.
Antes (v1) los modelos entrenados con la particion aleatoria se evaluaban
sobre el test espacial (contaminacion: 81,3 % de te_esp en A y 79,7 % en B
estaban en tr_predio). Las metricas v1 quedaron archivadas como historicas en
historial_no_independiente_v1/.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from yacopi_ml.valor.dataset import CATEGORICAS, construir_dataset, seleccionar_features
from yacopi_ml.valor.modelos import entrenar_modelos, metricas, predecir
from yacopi_ml.valor.splits import dividir_espacial, dividir_predios, guardar_particiones

ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = ROOT / "ml" / "artifacts" / "exp-valor-terreno-001"


def validar_protocolo(
    ds: pd.DataFrame, tr: pd.DataFrame, te: pd.DataFrame, X: pd.DataFrame
) -> dict:
    """Entrena con `tr`, evalua con `te`; sin compartir IDs."""
    ids_tr = set(tr["numero_predial"])
    ids_te = set(te["numero_predial"])
    assert not ids_tr & ids_te, "train y test comparten IDs de predio"

    X_tr = tr[X.columns].copy()
    y_tr = tr["valor_terreno_ha"]
    X_te = te[X.columns]
    y_te = te["valor_terreno_ha"]

    modelos = entrenar_modelos(X_tr, y_tr)
    preds = predecir(modelos, X_te)

    resultados: dict[str, dict] = {
        nombre: metricas(y_te, pred) for nombre, pred in preds.items()
    }

    # Baselines sobre LOS MISMOS registros de test.
    mediana_global = float(y_tr.median())
    mediana_zonal = tr.groupby("codigo_zona_dominante")["valor_terreno_ha"].median()
    baseline_zonal = te["codigo_zona_dominante"].map(mediana_zonal).fillna(mediana_global)
    resultados["_baseline_mediana_zonal_objetivo_train"] = metricas(y_te, baseline_zonal)
    resultados["_baseline_mediana_global_train"] = metricas(
        y_te, np.full(len(y_te), mediana_global)
    )
    ref_zhg = te["referencia_zhg_por_ha"]
    valido = ref_zhg.notna()
    resultados["_referencia_zhg_del_dataset"] = metricas(y_te[valido], ref_zhg[valido])

    return resultados


def entrenar_y_evaluar(escenario: str) -> dict:
    ds = construir_dataset(escenario)
    X, y, _, _ = seleccionar_features(ds)
    ds = ds.assign(**{c: X[c] for c in X.columns})

    rutas = guardar_particiones(escenario, ds)
    tr_predio, te_predio = dividir_predios(ds)
    tr_esp, te_esp = dividir_espacial(ds)

    # Asserts de separacion de conjuntos.
    assert not set(tr_predio["numero_predial"]) & set(te_predio["numero_predial"])
    assert not set(tr_esp["numero_predial"]) & set(te_esp["numero_predial"])

    resultado_predio = validar_protocolo(ds, tr_predio, te_predio, X)
    resultado_esp = validar_protocolo(ds, tr_esp, te_esp, X)

    # Importancia CatBoost del protocolo predio (solo informativo).
    X_tr = tr_predio[X.columns]
    cat_idx = [X_tr.columns.get_loc(c) for c in CATEGORICAS if c in X_tr.columns]
    from catboost import CatBoostRegressor

    cat = CatBoostRegressor(
        iterations=1000, depth=6, learning_rate=0.05, loss_function="RMSE",
        random_seed=20261023, cat_features=cat_idx, verbose=False,
    )
    cat.fit(X_tr, tr_predio["valor_terreno_ha"].to_numpy())
    importancias = sorted(
        zip(X.columns, cat.feature_importances_.tolist(), strict=False),
        key=lambda t: -t[1],
    )[:15]
    resultado_predio["_importancia_catboost_top15"] = [
        {"feature": f, "importance": float(i)} for f, i in importancias
    ]

    resumen = {
        "escenario": escenario,
        "n_predios": int(len(ds)),
        "protocolos": {
            "predio": {
                "n_train": int(len(tr_predio)),
                "n_test": int(len(te_predio)),
                "train_test_disjuntos": True,
                "resultados": resultado_predio,
            },
            "espacial": {
                "n_train": int(len(tr_esp)),
                "n_test": int(len(te_esp)),
                "train_test_disjuntos": True,
                "resultados": resultado_esp,
            },
        },
        "rutas_splits": rutas,
        "version_protocolo": "v2_independiente",
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / f"resultados_esc_{escenario}.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return resumen


def main() -> None:
    todo = {}
    for esc in ["A", "B"]:
        r = entrenar_y_evaluar(esc)
        todo[esc] = r
    (ARTIFACTS / "resumen.json").write_text(
        json.dumps(todo, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(todo, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
