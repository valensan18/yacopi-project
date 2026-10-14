"""Métricas de evaluación con reglas explícitas (COP/ha).

- `mdape` / `mape` / `pct_lt_*` solo se calculan sobre observaciones con
  |y| > EPS (regla explícita para denominadores ≈ 0).
- `n_para_porcentuales` registra el denominador usado.
"""

import numpy as np

EPS = 1e-3


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) == 0:
        raise ValueError("y_true vacío")

    error = y_pred - y_true
    abs_error = np.abs(error)

    mask_pct = np.abs(y_true) > EPS
    n_pct = int(mask_pct.sum())
    abs_pct = np.full_like(abs_error, np.nan)
    if n_pct > 0:
        abs_pct[mask_pct] = 100.0 * abs_error[mask_pct] / np.abs(y_true[mask_pct])

    ss_res = float(np.sum(error**2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    return {
        "n": int(len(y_true)),
        "mae_cop_ha": float(np.mean(abs_error)),
        "rmse_cop_ha": float(np.sqrt(np.mean(error**2))),
        "r2": r2,
        "mdae_cop_ha": float(np.median(abs_error)),
        "mdape_pct": float(np.nanmedian(abs_pct)),
        "mape_pct": float(np.nanmean(abs_pct)),
        "pct_error_lt_20": float(np.nanmean(abs_pct < 20.0)) if n_pct else float("nan"),
        "pct_error_lt_30": float(np.nanmean(abs_pct < 30.0)) if n_pct else float("nan"),
        "n_para_porcentuales": n_pct,
    }


def format_metrics(metrics: dict) -> dict:
    return {
        "n": metrics["n"],
        "MAE (COP/ha)": round(metrics["mae_cop_ha"], 2),
        "RMSE (COP/ha)": round(metrics["rmse_cop_ha"], 2),
        "R2": round(metrics["r2"], 4),
        "MdAE (COP/ha)": round(metrics["mdae_cop_ha"], 2),
        "MdAPE (%)": round(metrics["mdape_pct"], 2),
        "MAPE (%)": round(metrics["mape_pct"], 2),
        "% err<20": round(metrics["pct_error_lt_20"], 4),
        "% err<30": round(metrics["pct_error_lt_30"], 4),
    }
