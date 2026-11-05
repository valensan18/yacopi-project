"""Modelos compartidos del experimento VALOR_TERRENO_Ha (experimental).

Centraliza construccion de modelos, preprocesador y metricas para que
train.py y audit_r2.py usen exactamente el mismo protocolo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor

from yacopi_ml.valor.dataset import CATEGORICAS, NUMERICAS

SEED = 20261023


def metricas(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ape = np.abs((y_true - y_pred) / np.where(y_true == 0, np.nan, y_true))
    return {
        "n": int(len(y_true)),
        "mae_cop_ha": float(mean_absolute_error(y_true, y_pred)),
        "rmse_cop_ha": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
        "mdape": float(np.nanmedian(ape)) if np.isfinite(ape).any() else None,
    }


def preprocesador(X_train: pd.DataFrame) -> ColumnTransformer:
    cat = [c for c in CATEGORICAS if c in X_train.columns]
    num = [c for c in NUMERICAS if c in X_train.columns]
    return ColumnTransformer(
        [
            ("num", Pipeline([
                ("imp", SimpleImputer(strategy="median")),
                ("sca", StandardScaler()),
            ]), num),
            ("cat", Pipeline([
                ("imp", SimpleImputer(strategy="constant", fill_value="SIN_DATO")),
                ("ohe", OneHotEncoder(handle_unknown="ignore", min_frequency=10)),
            ]), cat),
        ],
        remainder="drop",
    )


def entrenar_modelos(X_tr: pd.DataFrame, y_tr: pd.Series) -> dict:
    """Ajusta los 5 algoritmos con los datos de entrenamiento dados."""
    modelos: dict[str, object] = {
        "dummy_media": DummyRegressor(strategy="mean"),
        "arbol": Pipeline([
            ("enc", preprocesador(X_tr)),
            ("reg", DecisionTreeRegressor(max_depth=6, random_state=SEED)),
        ]),
        "random_forest": Pipeline([
            ("enc", preprocesador(X_tr)),
            ("reg", RandomForestRegressor(
                n_estimators=400, max_depth=18, min_samples_leaf=3,
                n_jobs=-1, random_state=SEED,
            )),
        ]),
    }
    for m in modelos.values():
        m.fit(X_tr, y_tr.to_numpy())
    ridge = Pipeline([("enc", preprocesador(X_tr)), ("reg", Ridge(alpha=1.0))])
    ridge.fit(X_tr, np.log1p(y_tr.to_numpy()))
    modelos["ridge_log"] = ridge
    cat = CatBoostRegressor(
        iterations=1000, depth=6, learning_rate=0.05, loss_function="RMSE",
        random_seed=SEED,
        cat_features=[X_tr.columns.get_loc(c) for c in CATEGORICAS if c in X_tr.columns],
        verbose=False,
    )
    cat.fit(X_tr, y_tr.to_numpy())
    modelos["catboost"] = cat
    return modelos


def predecir(modelos: dict, X: pd.DataFrame) -> dict:
    preds = {}
    for nombre, m in modelos.items():
        if nombre == "ridge_log":
            preds[nombre] = np.expm1(m.predict(X))
        else:
            preds[nombre] = m.predict(X)
    return preds
