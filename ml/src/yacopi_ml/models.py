"""Definición de los modelos candidatos y sus distribuciones de tuning."""

from catboost import CatBoostRegressor
from scipy.stats import randint, uniform
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeRegressor

from .preprocess import preprocess_sklearn
from .schema import CATEGORICAL_FEATURES

SEED = 42


class CatBoostWrapper(BaseEstimator, RegressorMixin):
    """Envoltorio sklearn-compatible de CatBoost (cat_features clonable)."""

    def __init__(self, cat_features, iterations=500, depth=6,
                 learning_rate=0.07, l2_leaf_reg=3.0, random_seed=SEED):
        self.cat_features = cat_features
        self.iterations = iterations
        self.depth = depth
        self.learning_rate = learning_rate
        self.l2_leaf_reg = l2_leaf_reg
        self.random_seed = random_seed

    def fit(self, X, y):
        self.model_ = CatBoostRegressor(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=self.learning_rate,
            l2_leaf_reg=self.l2_leaf_reg,
            random_seed=self.random_seed,
            verbose=0,
            allow_writing_files=False,
            cat_features=self.cat_features,
        )
        self.model_.fit(X, y)
        return self

    def predict(self, X):
        return self.model_.predict(X)


def get_models() -> dict:
    """Devuelve {nombre: (estimador, distribuciones, usa_categorias_catboost)}."""
    return {
        "dummy": (
            DummyRegressor(strategy="median"),
            {},
            False,
        ),
        "ridge": (
            Pipeline([
                ("preprocess", preprocess_sklearn(with_scaler=True)),
                ("model", Ridge(random_state=SEED)),
            ]),
            {"model__alpha": {"dist": uniform, "kwargs": {"loc": 0.1, "scale": 200}}},
            False,
        ),
        "tree": (
            Pipeline([
                ("preprocess", preprocess_sklearn(with_scaler=False)),
                ("model", DecisionTreeRegressor(random_state=SEED)),
            ]),
            {
                "model__max_depth": {"dist": randint, "kwargs": {"low": 4, "high": 20}},
                "model__min_samples_leaf": {"dist": randint, "kwargs": {"low": 5, "high": 100}},
            },
            False,
        ),
        "forest": (
            Pipeline([
                ("preprocess", preprocess_sklearn(with_scaler=False)),
                ("model", RandomForestRegressor(random_state=SEED, n_jobs=6)),
            ]),
            {
                "model__n_estimators": {"dist": randint, "kwargs": {"low": 200, "high": 601}},
                "model__max_depth": {"choices": [None, 10, 20, 30]},
                "model__min_samples_leaf": {"dist": randint, "kwargs": {"low": 1, "high": 20}},
            },
            False,
        ),
        "catboost": (
            CatBoostWrapper(cat_features=CATEGORICAL_FEATURES),
            {
                "iterations": {"dist": randint, "kwargs": {"low": 200, "high": 801}},
                "depth": {"dist": randint, "kwargs": {"low": 4, "high": 11}},
                "learning_rate": {"dist": uniform, "kwargs": {"loc": 0.02, "scale": 0.13}},
                "l2_leaf_reg": {"dist": uniform, "kwargs": {"loc": 1.0, "scale": 20.0}},
            },
            True,
        ),
    }


def smoke_params(model_name: str) -> dict:
    """Parámetros fijos reducidos para corrida de humo (rápida)."""
    if model_name == "catboost":
        return {
            "iterations": 30, "depth": 5, "learning_rate": 0.1, "l2_leaf_reg": 3.0,
        }
    if model_name == "forest":
        return {
            "model__n_estimators": 50, "model__max_depth": 10,
            "model__min_samples_leaf": 5,
        }
    if model_name == "tree":
        return {"model__max_depth": 8, "model__min_samples_leaf": 20}
    if model_name == "ridge":
        return {"model__alpha": 10.0}
    return {}
