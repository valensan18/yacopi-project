"""Interpretabilidad: importancia por permutación y SHAP (si es viable)."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shap  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402

from .schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES  # noqa: E402

FIG_WIDTH = 9


def permutation(model, X: pd.DataFrame, y: pd.Series, rng_seed: int = 42) -> pd.DataFrame:
    result = permutation_importance(
        model, X, y, n_repeats=8, random_state=rng_seed, scoring="neg_mean_absolute_error"
    )
    df = pd.DataFrame({
        "feature": X.columns,
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std,
    }).sort_values("importance_mean", ascending=False)
    return df


def plot_permutation(df: pd.DataFrame, path, top_n: int = 15) -> str:
    top = df.head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 0.35 * len(top) + 1))
    ax.barh(top["feature"], top["importance_mean"], xerr=top["importance_std"])
    ax.set_xlabel("Aumento de MAE por permutación (COP/ha)")
    ax.set_title("Importancia por permutación (test espacial)")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return str(path)


def _unwrap(model):
    """Modelo interno de CatBoostWrapper o del paso 'model' de un Pipeline."""
    inner = getattr(model, "model_", None)
    if inner is not None:
        return inner
    if hasattr(model, "named_steps"):
        return model.named_steps["model"]
    return model


def _encode_sample(model, sample: pd.DataFrame):
    """Preprocesa la muestra para modelos sklearn (OHE) y devuelve (X, nombres)."""
    if hasattr(model, "named_steps"):
        preprocess = model.named_steps["preprocess"]
        encoded = preprocess.transform(sample)
        names = preprocess.get_feature_names_out()
        return encoded, names
    return sample, list(sample.columns)


def shap_for_model(model, X: pd.DataFrame, sample_size: int = 300, seed: int = 42):
    """SHAP TreeExplainer sobre una muestra del test. Devuelve None si falla."""
    try:
        inner = _unwrap(model)
        sample = X.sample(n=min(sample_size, len(X)), random_state=seed)
        encoded, names = _encode_sample(model, sample)
        explainer = shap.TreeExplainer(inner, feature_perturbation="tree_path_dependent")
        values = np.asarray(explainer.shap_values(encoded))
        importance = pd.DataFrame({
            "feature": names,
            "shap_mean_abs": np.abs(values).mean(axis=0),
        }).sort_values("shap_mean_abs", ascending=False)
        return explainer, encoded, values, importance
    except Exception:
        return None


def plot_shap(explainer, sample_encoded, values: np.ndarray, path, names=None) -> str:
    fig = plt.figure(figsize=(FIG_WIDTH, 5))
    shap.summary_plot(values, sample_encoded, feature_names=names,
                      show=False, max_display=15)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def shap_mean_importance(values: np.ndarray, names: list[str]) -> pd.DataFrame:
    df = pd.DataFrame({
        "feature": names,
        "shap_mean_abs": np.abs(values).mean(axis=0),
    }).sort_values("shap_mean_abs", ascending=False)
    return df


def plot_pred_vs_observed(
    y_true: pd.Series, y_pred: pd.Series, path, title: str
) -> str:
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.scatter(y_true, y_pred, s=4, alpha=0.35)
    lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
    ax.plot(lims, lims, "r--", linewidth=1)
    ax.set_xlabel("Observado (COP/ha)")
    ax.set_ylabel("Predicho (COP/ha)")
    ax.set_title(title)
    ax.ticklabel_format(style="plain", axis="both")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return str(path)


def plot_segmentation(seg: dict, key: str, path, metric: str = "mae_cop_ha", title=None):
    groups = seg[key]
    if not groups:
        return None
    labels = list(groups.keys())
    values = [g[metric] for g in groups.values()]
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 0.32 * len(labels) + 1.2))
    ax.barh(labels[::-1], values[::-1])
    ax.set_xlabel(f"{metric} (COP/ha)" if metric != "mdape_pct" else "MdAPE (%)")
    ax.set_title(title or key)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return str(path)


_FEATURE_UNITS = {
    "area_terreno_catastral_m2": "m2",
    "area_zhf_m2": "m2",
    "area_construida_m2": "m2",
    "tr_latitud": "grados",
    "tr_longitud": "grados",
}


def categoricals() -> list[str]:
    return CATEGORICAL_FEATURES


def numerics() -> list[str]:
    return NUMERIC_FEATURES


def feature_units() -> dict:
    return _FEATURE_UNITS
