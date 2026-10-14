"""Análisis de errores por segmentos: subzona, tamaño, uso y calidad."""

import numpy as np
import pandas as pd

SIZE_BINS = [(0, 5), (5, 20), (20, 100), (100, np.inf)]
SIZE_LABELS = ["<=5 ha", "5-20 ha", "20-100 ha", ">100 ha"]


def segmentation_errors(
    contexto: pd.DataFrame,
    y_true: pd.Series,
    y_pred: pd.Series,
) -> dict:
    """Calcula MAE y MdAPE por segmento sobre un conjunto evaluado."""
    df = pd.DataFrame({
        "y_true": y_true.to_numpy(),
        "y_pred": y_pred.to_numpy(),
    })
    area_ha = contexto["area_terreno_catastral_m2"].to_numpy() / 10_000.0

    def group_stats(mask) -> dict:
        if not mask.any():
            return None
        err = df.loc[mask, "y_pred"] - df.loc[mask, "y_true"]
        abs_pct = 100.0 * np.abs(err.to_numpy()) / np.maximum(
            np.abs(df.loc[mask, "y_true"].to_numpy()), 1e-3
        )
        return {
            "n": int(mask.sum()),
            "mae_cop_ha": float(np.mean(np.abs(err))),
            "mdape_pct": float(np.median(abs_pct)),
        }

    out = {"por_subzona": {}, "por_tamano": {}, "por_destino": {}, "por_calidad": {}}

    for subzona in sorted(contexto["subzona"].dropna().unique()):
        mask = (contexto["subzona"] == subzona).to_numpy()
        stats = group_stats(mask)
        if stats:
            out["por_subzona"][str(subzona)] = stats

    for (low, high), label in zip(SIZE_BINS, SIZE_LABELS, strict=True):
        mask = (area_ha > low) & (area_ha <= high)
        stats = group_stats(mask)
        if stats:
            out["por_tamano"][label] = stats

    for destino in sorted(contexto["destino_economico"].dropna().unique()):
        mask = (contexto["destino_economico"] == destino).to_numpy()
        stats = group_stats(mask)
        if stats:
            out["por_destino"][str(destino)] = stats

    sin_construccion = (contexto["area_construida_m2"] <= 0).to_numpy()
    con_construccion = ~sin_construccion
    out["con_construccion"] = group_stats(con_construccion)
    out["sin_construccion"] = group_stats(sin_construccion)

    sin_alertas = (contexto["n_alertas_calidad"] == 0).to_numpy()
    con_alertas = ~sin_alertas
    out["sin_alertas_calidad"] = group_stats(sin_alertas)
    out["con_alertas_calidad"] = group_stats(con_alertas)

    return out
