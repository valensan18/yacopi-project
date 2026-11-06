"""Sensibilidad del protocolo a incluir area_terreno_m2 como predictor.

area_terreno_m2 aparece en el denominador de VALOR_TERRENO_Ha y como feature:
se repite el protocolo v2 (predio y espacial) CON y SIN esa variable para
RandomForest y CatBoost en el escenario A, conservando todo lo demas.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from catboost import CatBoostRegressor
from sklearn.ensemble import RandomForestRegressor

from yacopi_ml.valor.dataset import CATEGORICAS, construir_dataset, seleccionar_features
from yacopi_ml.valor.modelos import SEED, metricas, preprocesador
from yacopi_ml.valor.splits import dividir_espacial, dividir_predios

ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = ROOT / "ml" / "artifacts" / "exp-valor-terreno-001" / "sensibilidad"


def entrenar_variante(X_tr: pd.DataFrame, y_tr, modelo: str, sin_area: bool):
    X_tr = X_tr.copy()
    if sin_area:
        X_tr = X_tr.drop(columns=["area_terreno_m2"], errors="ignore")
    if modelo == "random_forest":
        m = RandomForestRegressor(
            n_estimators=400, max_depth=18, min_samples_leaf=3,
            n_jobs=-1, random_state=SEED,
        )
        pre = preprocesador(X_tr)
        from sklearn.pipeline import Pipeline

        pipe = Pipeline([("enc", pre), ("reg", m)])
        pipe.fit(X_tr, y_tr.to_numpy())
        return pipe
    cat = CatBoostRegressor(
        iterations=1000, depth=6, learning_rate=0.05, loss_function="RMSE",
        random_seed=SEED,
        cat_features=[X_tr.columns.get_loc(c) for c in CATEGORICAS if c in X_tr.columns],
        verbose=False,
    )
    cat.fit(X_tr, y_tr.to_numpy())
    return cat


def evaluar_variante(ds: pd.DataFrame, tr: pd.DataFrame, te: pd.DataFrame,
                     X: pd.DataFrame, modelo: str, sin_area: bool) -> dict:
    assert not set(tr["numero_predial"]) & set(te["numero_predial"])
    m = entrenar_variante(tr[X.columns], tr["valor_terreno_ha"], modelo, sin_area)
    X_te = te[X.columns]
    if sin_area:
        X_te = X_te.drop(columns=["area_terreno_m2"], errors="ignore")
    return metricas(te["valor_terreno_ha"], m.predict(X_te))


def main() -> None:
    ds = construir_dataset("A")
    X, y, _, _ = seleccionar_features(ds)
    ds = ds.assign(**{c: X[c] for c in X.columns})
    tr, te = dividir_predios(ds)
    tr_esp, te_esp = dividir_espacial(ds)

    salida: dict = {"escenario": "A", "protocolo": "v2_independiente"}
    for sin_area in [False, True]:
        clave = "sin_area_terreno_m2" if sin_area else "con_area_terreno_m2"
        salida[clave] = {}
        for modelo in ["random_forest", "catboost"]:
            salida[clave][modelo] = {
                "predio": evaluar_variante(ds, tr, te, X, modelo, sin_area),
                "espacial": evaluar_variante(ds, tr_esp, te_esp, X, modelo, sin_area),
            }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "sensibilidad_area_terreno.json").write_text(
        json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(salida, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
