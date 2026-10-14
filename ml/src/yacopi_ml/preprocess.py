"""Preprocesamiento por familia de modelos (todo se ajusta solo en train)."""

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def numeric_transformer(with_scaler: bool):
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if with_scaler:
        steps.append(("scaler", StandardScaler()))
    return Pipeline(steps)


def categorical_transformer():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])


def column_transformer(with_scaler: bool) -> ColumnTransformer:
    return ColumnTransformer([
        ("num", numeric_transformer(with_scaler), NUMERIC_FEATURES),
        ("cat", categorical_transformer(), CATEGORICAL_FEATURES),
    ])


def preprocess_sklearn(with_scaler: bool) -> Pipeline:
    """Pipeline completo para estimadores scikit-learn (Ridge/Árbol/RF)."""
    return Pipeline([
        ("preprocess", column_transformer(with_scaler)),
    ])
