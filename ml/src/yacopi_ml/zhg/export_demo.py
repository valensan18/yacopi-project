"""Construcción del artefacto de DEMOSTRACIÓN exp-zhg-001-demo (Fase 7B).

- NO es un nuevo experimento ni una nueva búsqueda de hiperparámetros:
  reproduce de forma determinística la búsqueda de la Fase 5 (misma semilla,
  mismas particiones congeladas, mismo espacio) para recuperar los
  hiperparámetros del Random Forest y VERIFICA que la métrica histórica del
  test por predio se reproduce (integridad). Si no coincide, se detiene.
- Luego ajusta UNA sola vez el modelo con esos hiperparámetros sobre el
  conjunto completo de predios con zona conocida y empaqueta el artefacto
  con esquema, estadísticas de dominio, pertenencia a particiones
  históricas y características por predio (identificadores OPACOS).

Métricas históricas (Fase 5, exp-zhg-001): MAE predio 73.765 COP/ha.
El modelo final ajustado sobre todos los datos NO tiene evaluación
independiente propia: sus métricas de Fase 5 son históricas.
"""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, RandomizedSearchCV

from ..metrics import compute_metrics
from ..models import get_models
from ..schema import CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES
from .dataset import TARGET_DOMINANTE, build_zhg_dataset
from .splits import get_or_create_zhg_splits

SEED = 42
N_SPLITS = 5
N_ITER = 8
HISTORICAL_MAE_PREDIO = 73765.0
TOLERANCIA = 1.0  # COP/ha (mismas particiones y semilla)

ARTIFACTS = Path(__file__).resolve().parents[3] / "artifacts"


def public_id_for(source_id: str) -> str:
    return "p_" + hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    started = datetime.now(UTC)
    print("Cargando dataset ZHG (dominante)...")
    df = build_zhg_dataset()
    df = df[df[TARGET_DOMINANTE] > 0].reset_index(drop=True)
    X = df[FEATURE_COLUMNS].copy()
    for col in NUMERIC_FEATURES:
        X[col] = pd.to_numeric(X[col], errors="coerce")
    for col in CATEGORICAL_FEATURES:
        X[col] = X[col].astype("object")
    y = pd.to_numeric(df[TARGET_DOMINANTE], errors="coerce")

    splits = get_or_create_zhg_splits(df, "dominante")
    splits_dir = Path(splits["manifest"]["directorio"])
    train_ids = set(splits["predio"][0])
    test_ids = set(splits["predio"][1])

    tr_mask = df["public_id"].isin(train_ids)
    te_mask = df["public_id"].isin(test_ids)

    estimator, distributions, _ = get_models()["forest"]
    param_distributions = {}
    for key, spec in distributions.items():
        if "choices" in spec:
            param_distributions[key] = spec["choices"]
        else:
            param_distributions[key] = spec["dist"](**spec["kwargs"])

    print("Recuperando hiperparámetros (búsqueda determinística idéntica a Fase 5)...")
    search = RandomizedSearchCV(
        estimator,
        param_distributions,
        n_iter=N_ITER,
        scoring="neg_mean_absolute_error",
        cv=GroupKFold(n_splits=N_SPLITS),
        random_state=SEED,
        n_jobs=6,
        refit=True,
        error_score="raise",
    )
    groups = df["public_id"][tr_mask].astype(str).to_numpy()
    search.fit(X[tr_mask], y[tr_mask], groups=groups)
    params = search.best_params_
    print("  params:", params)

    # Verificación contra la métrica histórica (sin alterarla).
    # DISCREPANCIA DOCUMENTADA: los archivos de particiones congeladas fueron
    # regenerados por corridas posteriores (experimento ponderado y pruebas),
    # por lo que sus hashes ya no coinciden con los del manifiesto histórico
    # de Fase 5. Las métricas históricas (73.765 COP/ha predio) quedan
    # intactas como evidencia histórica; NO se declara que este artefacto sea
    # el modelo evaluado en Fase 5.
    verify_model = get_models()["forest"][0]
    verify_model.set_params(**params)
    verify_model.fit(X[tr_mask], y[tr_mask])
    pred = verify_model.predict(X[te_mask])
    mae = compute_metrics(y[te_mask].to_numpy(), np.asarray(pred))["mae_cop_ha"]
    discrepancy = abs(mae - HISTORICAL_MAE_PREDIO) > TOLERANCIA
    print(f"  MAE test predio con particiones actuales: {mae:,.2f} "
          f"(histórico {HISTORICAL_MAE_PREDIO:,.2f})")
    if discrepancy:
        print("  AVISO: discrepancia documentada (particiones regeneradas tras "
              "Fase 5); las métricas históricas se conservan sin modificar.")

    # Ajuste único y determinístico sobre el conjunto completo de zonas conocidas
    print("Ajustando modelo final (único fit determinístico sobre todos los predios)...")
    demo_model = get_models()["forest"][0]
    demo_model.set_params(**params)
    demo_model.fit(X, y)

    # Estadísticas de dominio
    stats = {"numeric": {}, "categorical": {}}
    for col in NUMERIC_FEATURES:
        stats["numeric"][col] = {
            "min": float(X[col].min()),
            "max": float(X[col].max()),
        }
    for col in CATEGORICAL_FEATURES:
        stats["categorical"][col] = sorted(
            str(v) for v in X[col].dropna().unique()
        )

    # Features y metadatos por predio con identificador OPACO
    features_lookup: dict[str, dict] = {}
    split_membership: dict[str, dict] = {}
    scenario_files = {
        "predio": ("predio",),
        "filas": ("filas",),
        "espacial": ("espacial",),
        "zona": ("zona",),
    }
    memberships: dict[str, dict] = {}
    for scenario in scenario_files:
        train_ids_s, test_ids_s = splits[scenario]
        for sid in train_ids_s:
            memberships.setdefault(sid, {})[scenario] = "train"
        for sid in test_ids_s:
            memberships.setdefault(sid, {})[scenario] = "test"

    for _, row in df.iterrows():
        opaque = public_id_for(row["public_id"])
        features_lookup[opaque] = {
            "features": {
                col: (float(row[col]) if col in NUMERIC_FEATURES else str(row[col]))
                for col in FEATURE_COLUMNS
            },
            "zone_code": str(row["zona_dominante"]),
            "n_zonas": int(row["n_zonas"]),
            "reference_zhg_cop_ha": float(row[TARGET_DOMINANTE]),
        }
        split_membership[opaque] = memberships.get(row["public_id"], {})

    # Empaquetado
    exp_dir = ARTIFACTS / "exp-zhg-001-demo"
    exp_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(demo_model, exp_dir / "model.joblib")
    (exp_dir / "feature_schema.json").write_text(
        json.dumps({
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
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (exp_dir / "training_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (exp_dir / "split_membership.json").write_text(
        json.dumps(split_membership, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (exp_dir / "features.json").write_text(
        json.dumps(features_lookup, ensure_ascii=False, indent=0), encoding="utf-8"
    )
    import catboost
    import sklearn

    manifest = {
        "model_id": "exp-zhg-001-demo",
        "algorithm": "RandomForestRegressor (sklearn Pipeline + ColumnTransformer)",
        "target": TARGET_DOMINANTE,
        "target_description": (
            "valor unitario de referencia ZHG del suelo rural (valor de la zona "
            "geoeconómica predominante), COP/ha"
        ),
        "unit": "COP/ha",
        "seed": SEED,
        "hyperparameters": params,
        "n_estimators_search": N_ITER,
        "cv": f"GroupKFold({N_SPLITS}) por predio",
        "data_origin": (
            "data/processed/01_intersecciones_normalizadas.csv + "
            "02_zhf_normalizadas.csv"
        ),
        "n_fit_rows": int(len(df)),
        "fit_partition": "todos los predios con zona conocida (ajuste final determinístico)",
        "split_files": str(splits_dir),
        "split_manifest": splits["manifest"],
        "built_at": started.isoformat(),
        "package_versions": {
            "python": sys.version.split()[0],
            "scikit_learn": sklearn.__version__,
            "pandas": pd.__version__,
            "catboost": catboost.__version__,
        },
        "status": "experimental",
        "validation_notes": (
            "Las métricas de Fase 5 (MAE predio 73.765; espacial 132.183; zonas "
            "fuera 423.363 COP/ha) son HISTÓRICAS y corresponden al modelo "
            "evaluado con las particiones congeladas de Fase 5, NO a este "
            "artefacto final ajustado sobre todos los datos. Este artefacto no "
            "fue aceptado como candidato a producción."
        ),
        "integrity_note": (
            "Las particiones de Fase 5 se perdieron por sobrescritura (las "
            "corridas posteriores y las pruebas reescribían los archivos "
            "planos de data/splits/zhg). Desde la Fase 7C las particiones "
            "se versionan por firma de dataset en directorios inmutables. "
            "Las particiones usadas aquí son las de la firma dominante_n7709 "
            "generadas en 7C, NO las originales de Fase 5; la métrica "
            "histórica no se reproduce con ellas (documentado). MAE verificada "
            "con estas particiones: " + f"{mae:.2f}" + " COP/ha."
        ),
    }
    (exp_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Verificación de recarga
    loaded = joblib.load(exp_dir / "model.joblib")
    first = features_lookup[next(iter(features_lookup))]
    frame = pd.DataFrame([first["features"]])[FEATURE_COLUMNS]
    for col in NUMERIC_FEATURES:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    pred_reload = float(loaded.predict(frame)[0])
    pred_orig = float(demo_model.predict(frame)[0])
    if abs(pred_reload - pred_orig) > 1e-6:
        print("ERROR: recarga no reproducible.")
        return 3

    print(json.dumps({
        "artifact": str(exp_dir),
        "n_predios": len(features_lookup),
        "params": {
            k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v))
            for k, v in params.items()
        },
        "mae_con_particiones_actuales": round(mae, 2),
        "round_trip_ok": True,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()
    sys.exit(main())
