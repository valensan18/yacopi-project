"""Orquestador del experimento proxy (Ruta B) — Fase 2.

Uso:
  python -m yacopi_ml.train --mode research-proxy [--smoke] [--output DIR]

Modos:
  production      rechazado mientras label_contract.yaml siga en
                  pending_verification (anti-error por diseño).
  research-proxy  experimento con proxy_avaluo_total_cop_ha, artefactos
                  marcados como experimentales (nunca producción).

Flujo:
  1. Contrato de etiqueta verificado según modo.
  2. Cohorte y etiqueta desde SQLite (validación de área/unidades).
  3. Particiones congeladas aleatoria y espacial (ver split.py).
  4. Tuning con GroupKFold espacial (o params fijos en --smoke).
  5. Evaluación sellada: test espacial + test aleatorio + CV aleatorio.
  6. Selección por MAE en test espacial; segmentación e interpretabilidad.
  7. Exportación de artefactos + registro (estado experimental).
"""

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import (
    GroupKFold,
    KFold,
    RandomizedSearchCV,
    cross_validate,
)

from .evaluate import segmentation_errors
from .explain import (
    permutation,
    plot_permutation,
    plot_pred_vs_observed,
    plot_segmentation,
    plot_shap,
    shap_for_model,
)
from .export import build_model_card, git_commit, package_versions, save_artifacts
from .labels import build_dataset
from .metrics import compute_metrics
from .models import get_models, smoke_params
from .registry import register_experiment
from .schema import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    assert_no_blocked_columns,
    load_label_contract,
)
from .split import SPLITS_DIR, load_splits, make_splits

SEED = 42
DEFAULT_DB = Path(__file__).resolve().parents[3] / "data" / "parcels.db"
N_SPLITS = 5


def check_contract(mode: str) -> dict:
    if mode == "production":
        contract = load_label_contract("label_contract.yaml")
        if contract["source_status"] != "verified":
            raise SystemExit(
                "Entrenamiento production RECHAZADO: etiqueta en estado "
                f"{contract['source_status']}. Se requiere source_status=verified."
            )
        return contract
    if mode == "research-proxy":
        contract = load_label_contract("label_contract_proxy.yaml")
        if contract["source_kind"] != "proxy":
            raise SystemExit("Contrato proxy inválido: source_kind != proxy")
        return contract
    raise SystemExit(f"Modo desconocido: {mode}")


def run_tuning(
    name, estimator, distributions, X_train, y_train, groups_train, n_iter, smoke
):
    """Búsqueda aleatoria con GroupKFold espacial. Devuelve (mejor_modelo, params)."""
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
    cv = GroupKFold(n_splits=N_SPLITS)
    n_jobs = 1 if name == "catboost" else 6
    search = RandomizedSearchCV(
        estimator,
        param_distributions,
        n_iter=n_iter,
        scoring="neg_mean_absolute_error",
        cv=cv,
        random_state=SEED,
        n_jobs=n_jobs,
        refit=True,
        error_score="raise",
    )
    search.fit(X_train, y_train, groups=groups_train)
    return search.best_estimator_, search.best_params_


def predict(model, X):
    pred = model.predict(X)
    pred = np.asarray(pred, dtype=float)
    return np.where(np.isfinite(pred), pred, np.nan)


def random_cv_mae(name, model, X_train, y_train):
    """CV aleatorio KFold como referencia metodológica (no es la selección)."""
    if name == "dummy":
        return None
    scoring = "neg_mean_absolute_error"
    results = cross_validate(
        model, X_train, y_train,
        cv=KFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED),
        scoring=scoring, n_jobs=6,
    )
    return {
        "cv_mae_mean_cop_ha": float(-results["test_score"].mean()),
        "cv_mae_std_cop_ha": float(results["test_score"].std()),
    }


def run(args) -> dict:
    contract = check_contract(args.mode)
    assert_no_blocked_columns(FEATURE_COLUMNS)

    started = time.time()
    X, y, info = build_dataset(Path(args.db))
    contexto = info["contexto"]
    excluidos = info["excluidos"]

    ids = contexto["public_id"].tolist()
    coords = contexto[["tr_latitud", "tr_longitud"]].rename(
        columns={"tr_latitud": "tr_latitud", "tr_longitud": "tr_longitud"}
    )
    splits_paths = {f"{k}.json": (SPLITS_DIR / f"{k}.json").exists()
                    for k in ("train_random", "test_random",
                              "train_spatial", "test_spatial")}
    if args.resplit or not all(splits_paths.values()):
        splits = make_splits(ids, coords)
    else:
        splits = load_splits()

    df = pd.concat([X, contexto[["public_id"]].reset_index(drop=True)], axis=1)
    y_series = y.reset_index(drop=True)

    def subset(ids_list):
        idx = df[df["public_id"].isin(ids_list)].index
        return X.loc[idx].reset_index(drop=True), y_series.loc[idx].reset_index(drop=True), idx

    X_tr_spa, y_tr_spa, _ = subset(splits["train_spatial"])
    X_te_spa, y_te_spa, te_spa_idx = subset(splits["test_spatial"])
    X_tr_rnd, y_tr_rnd, _ = subset(splits["train_random"])
    X_te_rnd, y_te_rnd, _ = subset(splits["test_random"])

    ctx_te_spa = contexto.loc[te_spa_idx].reset_index(drop=True)

    # grupos espaciales (KMeans) para el CV agrupado del entrenamiento
    from .split import spatial_groups
    all_groups = spatial_groups(coords)
    groups_map = dict(zip(df["public_id"], all_groups, strict=False))
    groups_tr_spa = np.asarray(
        [groups_map[pid] for pid in splits["train_spatial"]]
    )

    models = get_models()
    if args.output:
        experiment_id = Path(args.output).name
    else:
        experiment_id = (
            f"exp-proxy-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
            if not args.smoke else "exp-proxy-smoke"
        )
    exp_dir = Path(args.output) if args.output else (
        Path(__file__).resolve().parents[2] / "artifacts" / experiment_id
    )
    exp_dir = Path(args.output) if args.output else (
        Path(__file__).resolve().parents[2] / "artifacts" / experiment_id
    )

    results: dict[str, dict] = {}
    best_params_all: dict[str, dict] = {}
    fitted: dict[str, object] = {}

    print(f"Experimento: {experiment_id} | modo: {args.mode} | "
          f"smoke: {args.smoke} | n_iter: {args.n_iter}")
    print(f"Train espacial: {len(X_tr_spa)} | test espacial: {len(X_te_spa)} | "
          f"train aleatorio: {len(X_tr_rnd)} | test aleatorio: {len(X_te_rnd)}")

    for name, (estimator, distributions, _) in models.items():
        t0 = time.time()
        model, params = run_tuning(
            name, estimator, distributions, X_tr_spa, y_tr_spa,
            groups_tr_spa, args.n_iter, args.smoke,
        )
        fitted[name] = model
        best_params_all[name] = params

        pred_spa = predict(model, X_te_spa)
        pred_rnd = predict(model, X_te_rnd)
        pred_cv = predict(model, X_tr_rnd)
        cv_metrics = compute_metrics(y_tr_rnd.to_numpy(), pred_cv)

        results[name] = {
            "params": {k: (str(v) if not isinstance(v, (int, float, str, bool, type(None))) else v)
                       for k, v in params.items()},
            "test_spatial": compute_metrics(y_te_spa.to_numpy(), pred_spa),
            "test_random": compute_metrics(y_te_rnd.to_numpy(), pred_rnd),
            "cv_random_train": cv_metrics,
            "random_cv_mae": random_cv_mae(name, model, X_tr_rnd, y_tr_rnd),
            "segundos": round(time.time() - t0, 1),
        }
        print(f"  {name}: MAE test espacial = "
              f"{results[name]['test_spatial']['mae_cop_ha']:,.2f} COP/ha "
              f"({results[name]['segundos']} s)")

    selected = min(
        results, key=lambda n: results[n]["test_spatial"]["mae_cop_ha"]
    )
    print(f"Seleccionado: {selected} (menor MAE en test espacial)")

    # --- Segmentación e interpretabilidad del modelo seleccionado ---
    seg = segmentation_errors(
        ctx_te_spa, y_te_spa, pd.Series(predict(fitted[selected], X_te_spa))
    )
    perm_df = permutation(fitted[selected], X_te_spa, y_te_spa)
    shap_result = shap_for_model(fitted[selected], X_te_spa) \
        if selected in ("catboost", "forest", "tree") else None
    shap_df = None
    if shap_result is not None:
        shap_df = shap_result[3]

    exp_dir.mkdir(parents=True, exist_ok=True)
    figs = {}
    figs["pred_vs_observado"] = plot_pred_vs_observed(
        y_te_spa, pd.Series(predict(fitted[selected], X_te_spa)),
        exp_dir / "fig_pred_vs_observado.png",
        f"Test espacial — {selected} (proxy, COP/ha)",
    )
    figs["importancia_permutacion"] = plot_permutation(
        perm_df, exp_dir / "fig_importancia_permutacion.png"
    )
    for key, title in [
        ("por_subzona", "MAE por subzona (test espacial)"),
        ("por_tamano", "MAE por tamaño de predio (test espacial)"),
        ("por_destino", "MAE por destino económico (test espacial)"),
    ]:
        path = plot_segmentation(seg, key, exp_dir / f"fig_{key}.png", title=title)
        if path:
            figs[key] = path
    if shap_result is not None:
        figs["shap_summary"] = plot_shap(
            shap_result[0], shap_result[1], shap_result[2],
            exp_dir / "fig_shap_summary.png",
            names=list(shap_df["feature"]),
        )

    metrics_payload = {
        "experiment_id": experiment_id,
        "mode": args.mode,
        "label": contract,
        "cohorte": {
            "n_total": excluidos["total_cohorte"],
            "n_cohorte_ml": len(X),
            "excluidos": excluidos,
            "n_con_construccion": int(
                (contexto["area_construida_m2"] > 0).sum()
            ),
        },
        "features": {
            "n": len(FEATURE_COLUMNS),
            "numericas": NUMERIC_FEATURES,
            "categoricas": CATEGORICAL_FEATURES,
        },
        "splits": {
            "n_train_spatial": len(X_tr_spa), "n_test_spatial": len(X_te_spa),
            "n_train_random": len(X_tr_rnd), "n_test_random": len(X_te_rnd),
            "manifest": splits.get("manifest"),
        },
        "protocols": {
            "spatial": {
                "test": {n: r["test_spatial"] for n, r in results.items()},
            },
            "random": {
                "test": {n: r["test_random"] for n, r in results.items()},
                "cv_aleatorio_train": {
                    n: r["random_cv_mae"] for n, r in results.items()
                },
                "train_reentrenado": {
                    n: r["cv_random_train"] for n, r in results.items()
                },
            },
        },
        "seleccion": {
            "model": selected,
            "criterio": "menor MAE en test espacial",
            "params": best_params_all[selected],
            "n_train": len(X_tr_spa),
            "n_test": len(X_te_spa),
        },
        "segmentacion_test_espacial": seg,
        "importancia_permutacion": {
            r["feature"]: round(r["importance_mean"], 2)
            for _, r in perm_df.head(15).iterrows()
        },
        "shap": None if shap_df is None else {
            r["feature"]: round(r["shap_mean_abs"], 4)
            for _, r in shap_df.head(15).iterrows()
        },
        "figuras": {k: str(Path(v).name) for k, v in figs.items()},
        "duracion_total_segundos": round(time.time() - started, 1),
    }

    manifest = {
        "experiment_id": experiment_id,
        "modo": args.mode,
        "git_commit": git_commit(),
        "seed": SEED,
        "n_splits": N_SPLITS,
        "n_iter_search": args.n_iter if not args.smoke else "smoke",
        "package_versions": package_versions(),
        "feature_schema": {
            "orden": FEATURE_COLUMNS,
            "numericas": NUMERIC_FEATURES,
            "categoricas": CATEGORICAL_FEATURES,
            "unidades": {
                "area_terreno_catastral_m2": "m2",
                "area_zhf_m2": "m2",
                "area_construida_m2": "m2",
                "tr_latitud": "grados",
                "tr_longitud": "grados",
            },
        },
        "hardware": "Intel i7-9700 (8 hilos), 24 GB RAM, CPU",
    }

    predictions_test = pd.DataFrame({
        "y_true_cop_ha": y_te_spa.to_numpy(),
        "y_pred_cop_ha": predict(fitted[selected], X_te_spa),
        "particion": "test_espacial",
    })

    model_card = build_model_card({
        "experiment_id": experiment_id,
        "metrics": metrics_payload,
        "excluidos": {
            "n_cohorte": len(X),
            "n_con_construccion": int((contexto["area_construida_m2"] > 0).sum()),
            "n_excluidos": excluidos["total_excluidos"],
        },
    })

    save_artifacts(exp_dir, selected, fitted[selected], {
        "metrics": metrics_payload,
        "feature_schema": manifest["feature_schema"],
        "manifest": manifest,
        "predictions_test": predictions_test,
        "model_card": model_card,
    })

    register_experiment(experiment_id, {
        "modelo": selected,
        "mae_test_espacial_cop_ha": round(
            results[selected]["test_spatial"]["mae_cop_ha"], 2
        ),
        "r2_test_espacial": round(
            results[selected]["test_spatial"]["r2"], 4
        ),
        "etiqueta": contract["label_name"],
        "production_eligible": False,
    })

    print(f"\nArtefactos en: {exp_dir}")
    print(json.dumps(metrics_payload, ensure_ascii=False, indent=2, default=str))
    return metrics_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True,
                        choices=["production", "research-proxy"])
    parser.add_argument("--output", default=None)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--n-iter", type=int, default=12)
    parser.add_argument("--resplit", action="store_true")
    args = parser.parse_args()
    run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
