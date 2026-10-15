"""Entrenamiento y evaluaciÃ³n del EXPERIMENTO ZHG (Fase 5E/5F).

Uso:
  python -m yacopi_ml.zhg.train [--smoke] [--output ml/artifacts/exp-zhg-001]

Reglas:
  - Solo modo experimental (research_zhg); jamÃ¡s production.
  - Objetivo: valor_suelo_referencia_zhg_cop_ha (11 valores zonales).
  - Criterio de aceptaciÃ³n PREDEFINIDO (antes de ver resultados):
      1) MAE menor que el baseline mediana en test predio Y test espacial.
      2) MAE menor que el baseline "valor de zona mÃ¡s frecuente" en test
         con zonas fuera.
  - Si no se cumple, NO se elige ganador; se documenta (opciones A/B/C).
"""

import json
import sys
import time
from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import GroupKFold, RandomizedSearchCV

from ..metrics import compute_metrics
from ..models import get_models, smoke_params
from ..schema import CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES
from .dataset import TARGET_DOMINANTE, TARGET_PONDERADO, build_zhg_dataset
from .splits import make_zhg_splits

ML_ROOT = Path(__file__).resolve().parents[3]
CONFIG = ML_ROOT / "config"
ARTIFACTS = ML_ROOT / "artifacts"
SEED = 42
N_SPLITS = 5


def load_zhg_blocked() -> set:
    config = yaml.safe_load((CONFIG / "features_zhg.yaml").read_text(encoding="utf-8"))
    return set(config["blocked"])


def assert_no_leak(features: list[str]) -> None:
    overlap = set(features) & load_zhg_blocked()
    if overlap:
        raise ValueError(f"Fuga detectada en X: {sorted(overlap)}")


def tune(
    name, estimator, distributions, X_train, y_train, groups_train,
    n_iter, smoke,
):
    if name == "dummy":
        estimator.fit(X_train, y_train)
        return estimator, {}
    if smoke:
        fixed = smoke_params(name)
        param_names = sorted(distributions)
        grid = {k: fixed[k] for k in param_names if k in fixed}
        estimator.set_params(**grid)
        estimator.fit(X_train, y_train)
        return estimator, grid
    param_distributions = {}
    for key, spec in distributions.items():
        if "choices" in spec:
            param_distributions[key] = spec["choices"]
        else:
            param_distributions[key] = spec["dist"](**spec["kwargs"])
    search = RandomizedSearchCV(
        estimator,
        param_distributions,
        n_iter=n_iter,
        scoring="neg_mean_absolute_error",
        cv=GroupKFold(n_splits=N_SPLITS),
        random_state=SEED,
        n_jobs=1 if name == "catboost" else 6,
        refit=True,
        error_score="raise",
    )
    search.fit(X_train, y_train, groups=groups_train)
    return search.best_estimator_, search.best_params_


def run(args) -> dict:
    started = time.time()
    assert_no_leak(FEATURE_COLUMNS)

    df = build_zhg_dataset()
    target_col = TARGET_PONDERADO if args.target == "ponderado" else TARGET_DOMINANTE
    if args.target == "ponderado":
        df = df[df[TARGET_PONDERADO].notna()].reset_index(drop=True)
    df = df[df[target_col] > 0].reset_index(drop=True)

    splits = make_zhg_splits(df)
    X_all = df[FEATURE_COLUMNS].copy()
    for col in NUMERIC_FEATURES:
        X_all[col] = pd.to_numeric(X_all[col], errors="coerce")
    for col in CATEGORICAL_FEATURES:
        X_all[col] = X_all[col].astype("object")

    y_all = pd.to_numeric(df[target_col], errors="coerce")
    zona_all = df["zona_dominante"].astype(str)

    def subset(ids_list):
        mask = df["public_id"].isin(ids_list)
        return (
            X_all[mask].reset_index(drop=True),
            y_all[mask].reset_index(drop=True),
            df["public_id"][mask].tolist(),
            zona_all[mask].tolist(),
        )

    models = get_models()

    # Tuning SOLO dentro del train del escenario predio (agrupado por predio)
    train_ids, _ = splits["predio"]
    X_t, y_t, _, groups_t = subset(train_ids)
    groups_arr = np.asarray(groups_t, dtype=object)

    n_iter = 1 if args.smoke else 8
    tuned: dict[str, object] = {}
    tuned_params: dict[str, dict] = {}
    for name, (estimator, distributions, _) in models.items():
        model, params = tune(
            name, estimator, distributions, X_t, y_t, groups_arr, n_iter, args.smoke
        )
        tuned[name] = model
        tuned_params[name] = params
        print(f"  tuning {name}: listo")

    def predict(model, X):
        pred = np.asarray(model.predict(X), dtype=float)
        return np.where(np.isfinite(pred), pred, np.nan)

    results: dict[str, dict] = {}
    scenario_results: dict[str, dict] = {}
    for scenario, split_value in splits.items():
        if scenario == "manifest":
            continue
        tr_ids, te_ids = split_value
        X_tr, y_tr, _, _ = subset(tr_ids)
        X_te, y_te, _, _ = subset(te_ids)
        for name, model in tuned.items():
            fitted = model
            # re-fit sobre el train de este escenario con los params ya elegidos
            if name != "dummy":
                fitted = type_aware_refit(name, model, X_tr, y_tr, tuned_params[name])
            else:
                fitted.fit(X_tr, y_tr)
            metrics = compute_metrics(y_te.to_numpy(), predict(fitted, X_te))
            results.setdefault(name, {})[scenario] = metrics
            if scenario == "predio":
                scenario_results.setdefault(name, {})["params"] = {
                    k: (str(v) if not isinstance(v, (int, float, str, bool, type(None))) else v)
                    for k, v in tuned_params[name].items()
                }

    # Baselines
    baseline_rows = {}
    for scenario, split_value in splits.items():
        if scenario == "manifest":
            continue
        tr_ids, te_ids = split_value
        _, y_tr, _, _ = subset(tr_ids)
        _, y_te, _, _ = subset(te_ids)
        median_pred = np.full(len(y_te), y_tr.median())
        baseline_rows[f"{scenario}_mediana"] = compute_metrics(y_te.to_numpy(), median_pred)
        mode_value = y_tr.mode().iloc[0]
        baseline_rows[f"{scenario}_moda_zonal"] = compute_metrics(
            y_te.to_numpy(), np.full(len(y_te), mode_value)
        )

    # Leave-one-zone-out (modelo seleccionado provisional por MAE predio)
    candidates = sorted(results, key=lambda n: results[n]["predio"]["mae_cop_ha"])
    selected = candidates[0]
    loo_rows = []
    X_loo = X_all.copy()
    y_loo = y_all.copy()
    for zone in sorted(set(zona_all)):
        train_mask = zona_all != zone
        X_tr = X_loo[train_mask].reset_index(drop=True)
        y_tr = y_loo[train_mask].reset_index(drop=True)
        X_te = X_loo[~train_mask].reset_index(drop=True)
        y_te = y_loo[~train_mask].reset_index(drop=True)
        model = tuned[selected]
        if selected == "dummy":
            model.fit(X_tr, y_tr)
        else:
            model = type_aware_refit(selected, model, X_tr, y_tr, tuned_params[selected])
        m = compute_metrics(y_te.to_numpy(), predict(model, X_te))
        loo_rows.append({"zona": zone, "n": m["n"], **{k: m[k] for k in (
            "mae_cop_ha", "rmse_cop_ha", "r2", "mdape_pct")}})

    # Criterio de aceptaciÃ³n predefinido
    predio_mae = results[selected]["predio"]["mae_cop_ha"]
    espacial_mae = results[selected]["espacial"]["mae_cop_ha"]
    zona_mae = results[selected]["zona"]["mae_cop_ha"]
    beats_median = (
        predio_mae < baseline_rows["predio_mediana"]["mae_cop_ha"]
        and espacial_mae < baseline_rows["espacial_mediana"]["mae_cop_ha"]
    )
    beats_mode = zona_mae < baseline_rows["zona_moda_zonal"]["mae_cop_ha"]
    aceptado = bool(beats_median and beats_mode)

    payload = {
        "experiment_id": "exp-zhg-001",
        "target": target_col,
        "target_unit": "COP/ha",
        "n_predios": int(len(df)),
        "n_zonas": int(zona_all.nunique()),
        "valores_objetivo_unicos": int(y_all.nunique()),
        "cobertura": df["cobertura"].value_counts().to_dict(),
        "n_ponderado_disponible": int(df[TARGET_PONDERADO].notna().sum()),
        "features": FEATURE_COLUMNS,
        "splits_manifest": splits["manifest"],
        "scenarios": {n: {s: r[s] for s in ("filas", "predio", "espacial", "zona")}
                      for n, r in results.items()},
        "baselines": baseline_rows,
        "leave_one_zone_out": loo_rows,
        "seleccion_provisional": selected,
        "criterio_aceptacion": {
            "definicion": (
                "MAE < mediana en test predio y espacial, y MAE < moda zonal "
                "en test con zonas fuera (criterio predefinido antes de ver resultados)"
            ),
            "beats_median": beats_median,
            "beats_mode": beats_mode,
            "aceptado": aceptado,
        },
        "duracion_segundos": round(time.time() - started, 1),
    }

    exp_dir = Path(args.output) if args.output else ARTIFACTS / "exp-zhg-001"
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "metrics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return payload


def type_aware_refit(name, model, X, y, params):
    """Reajusta el mismo estimador con los hiperparÃ¡metros ya elegidos."""
    if name == "catboost":
        model.set_params(**params)
        model.fit(X, y)
        return model
    from sklearn.base import clone

    cloned = clone(model)
    cloned.set_params(**params)
    cloned.fit(X, y)
    return cloned


def main() -> int:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument(
        "--target", default="dominante",
        choices=["dominante", "ponderado"],
        help="dominante = valor de la zona con mayor participacion; "
             "ponderado = promedio ponderado por area (solo cobertura de hasta 5 por ciento)",
    )
    args = parser.parse_args()
    run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

