"""Exportacion del artefacto RF v1 (demostracion academica, escenario A).

- Entrenamiento FINAL: RandomForest (400/18/3, seed 20261023) sobre la
  cohorte completa del escenario A (4.676 predios), con el preprocesador
  real del protocolo v2.
- Exporta: pipeline joblib, features por public_id, schema, estadisticas de
  dominio, manifiesto, model card y las metricas de validacion como
  evidencia HISTORICA SEPARADA del ajuste final.
- Salida: ml/artifacts/exp-valor-v1/ (investigacion) y
  deploy-model/exp-valor-v1/ (montaje de despliegue). No se versiona en Git.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline

from yacopi_ml.valor.dataset import construir_dataset, seleccionar_features
from yacopi_ml.valor.modelos import SEED, preprocesador

ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = ROOT / "ml" / "artifacts" / "exp-valor-v1"
DEPLOY = ROOT / "deploy-model" / "exp-valor-v1"

MODEL_ID = "atlas-vivo-rf-v1"
MODEL_VERSION = "1.0.0"

TARGET_DESCRIPTION = (
    "VALOR_TERRENO_Ha = VALOR_AVALUO x 10000 / AREA_TERRENO_M2 (COP/ha): "
    "valor catastral unitario derivado del avaluo total, para predios sin "
    "construccion registrada. NO es precio comercial ni avaluo oficial."
)

LIMITATIONS = [
    "Demostracion academica: el modelo NO supero a la referencia ZHG en MAE "
    "ni MdAPE en ninguna de las 5 particiones espaciales independientes "
    "(docs/18_diagnostico_modelo_operativo_v1.md).",
    "La variable objetivo es un cociente derivado del avaluo catastral "
    "TOTAL; no es un valor exclusivo de suelo verificado.",
    "Sin fecha de vigencia verificable del avaluo.",
    "Solo aplica a predios del escenario A (construccion registrada igual a "
    "cero) dentro del dominio observado en el entrenamiento.",
    "No existe todavia un modelo definitivo aprobado.",
]


def public_id_for(parcel_source_id: str) -> str:
    return "p_" + hashlib.sha256(parcel_source_id.encode("utf-8")).hexdigest()[:16]


def metricas_evaluacion() -> dict:
    est = json.loads(
        (ROOT / "ml" / "artifacts" / "exp-valor-terreno-001" / "estabilidad_rf_v1.json")
        .read_text(encoding="utf-8")
    )
    return {
        "nota": (
            "metricas de validacion INDEPENDIENTES del ajuste final; el artefacto "
            "se entreno despues sobre los 4.676 predios del escenario A"
        ),
        "test_sellado_v2_espacial": {
            "n": 689,
            "rf": {
                "mae_cop_ha": 767064.08,
                "mdape": 0.1169,
                "rmse_cop_ha": 3450750.63,
                "r2": 0.1710,
            },
            "referencia_zhg": {"mae_cop_ha": 817030.0, "mdape": 0.0565},
        },
        "estabilidad_5_pliegues_espaciales": {
            "rf_gana_mae_en": est["resumen"]["rf_gana_mae_en"],
            "rf_gana_mdape_en": est["resumen"]["rf_gana_mdape_en"],
            "rf_mae_mediana": est["resumen"]["mae"]["rf"]["mediana"],
            "zhg_mae_mediana": est["resumen"]["mae"]["zhg"]["mediana"],
            "rf_mdape_mediana": est["resumen"]["mdape"]["rf"]["mediana"],
            "zhg_mdape_mediana": est["resumen"]["mdape"]["zhg"]["mediana"],
        },
    }


def exportar() -> None:
    ds = construir_dataset("A")
    X, y, _, _ = seleccionar_features(ds)
    ds = ds.assign(**{c: X[c] for c in X.columns})

    pipeline = Pipeline([
        ("enc", preprocesador(X)),
        ("reg", RandomForestRegressor(
            n_estimators=400, max_depth=18, min_samples_leaf=3,
            n_jobs=-1, random_state=SEED,
        )),
    ])
    pipeline.fit(X, y.to_numpy())

    numericas = list(X.select_dtypes(include="number").columns)
    categoricas = [c for c in X.columns if c not in numericas]
    orden = list(X.columns)

    stats_numeric = {
        c: {"min": float(X[c].min()), "max": float(X[c].max())}
        for c in numericas
    }
    stats_categorical = {
        c: sorted(X[c].astype(str).unique().tolist()) for c in categoricas
    }

    features: dict[str, dict] = {}
    for _, fila in ds.iterrows():
        public_id = public_id_for(fila["numero_predial"])
        features[public_id] = {
            "features": {c: _json_valor(fila[c]) for c in orden},
            "zone_code": str(fila["codigo_zona_dominante"]),
            "reference_zhg_cop_ha": _json_valor(fila["referencia_zhg_por_ha"]),
        }

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT
    ).stdout.strip()
    manifest = {
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION,
        "algorithm": "RandomForestRegressor (Pipeline sklearn + ColumnTransformer)",
        "rol": "demostracion_academica",
        "target": "VALOR_TERRENO_Ha",
        "target_description": TARGET_DESCRIPTION,
        "unit": "COP/ha",
        "escenario": "A (construccion registrada = 0)",
        "n_fit": int(len(ds)),
        "seed": SEED,
        "hiperparametros": {
            "n_estimators": 400, "max_depth": 18, "min_samples_leaf": 3,
        },
        "preprocesamiento": (
            "imputacion mediana + estandarizacion (numericas); imputacion "
            "SIN_DATO + one-hot min_frequency=10 (categoricas); ajustado con "
            "el entrenamiento"
        ),
        "trained_at": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "package_versions": {
            "python": "3.14", "scikit_learn": "1.9.1", "pandas": "3.0.6",
        },
        "data_hashes": {
            "interseccion_terrenos_zhg_r1_yacopi.csv":
                "8402f527a5468f94a80753b547f54c64ee96e4a938bc2afe4d119b488a3d6875",
            "zhf_yacopi.csv":
                "9bd88923146530ade9ba9eb964d8e97aee32e28ce56e4b95b08e380b684e15ad",
        },
        "status": "experimental_demo",
        "nota_ajuste_final": (
            "el artefacto se ajusto sobre TODOS los predios del escenario A; "
            "las metricas de validacion (metrics_evaluacion.json) provienen de "
            "evaluaciones anteriores y NO describen este ajuste final"
        ),
        "limitations": LIMITATIONS,
    }

    for destino in (ARTIFACTS, DEPLOY):
        destino.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, destino / "model.joblib")
        (destino / "features.json").write_text(
            json.dumps(features, ensure_ascii=False), encoding="utf-8"
        )
        (destino / "feature_schema.json").write_text(
            json.dumps(
                {"orden": orden, "numericas": numericas, "categoricas": categoricas},
                indent=2, ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (destino / "training_stats.json").write_text(
            json.dumps(
                {"numeric": stats_numeric, "categorical": stats_categorical},
                indent=2, ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (destino / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (destino / "metrics_evaluacion.json").write_text(
            json.dumps(metricas_evaluacion(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (destino / "MODEL_CARD.md").write_text(model_card(manifest), encoding="utf-8")

    print("artefacto exportado a:", ARTIFACTS, "y", DEPLOY)
    print("n_fit:", len(ds), "| features:", len(features))


def _json_valor(v) -> float | str | None:
    if isinstance(v, (int, float)):
        return None if pd.isna(v) else float(v)
    return str(v)


def model_card(manifest: dict) -> str:
    return f"""# Model Card — {MODEL_ID} (v{MODEL_VERSION})

- **Rol:** demostración académica (NO predictor recomendado, NO avalúo).
- **Variable:** {TARGET_DESCRIPTION}
- **Algoritmo:** Random Forest; hiperparámetros {manifest['hiperparametros']};
  semilla {SEED}; pipeline de preprocesamiento del protocolo v2.
- **Ajuste final:** {manifest['n_fit']} predios del escenario A (construcción
  registrada = 0). Las métricas de validación están en
  `metrics_evaluacion.json` y corresponden a evaluaciones independientes
  anteriores, NO a este ajuste.
- **Desempeño limitado:** no superó a la referencia ZHG en MAE ni MdAPE en
  ninguna de las 5 particiones espaciales independientes (ver docs/18).
- **Condiciones de aplicación:** predios con construcción = 0, áreas
  positivas y características dentro del dominio observado.
- **Uso seguro:** cargar solo desde la fuente local confiable
  (deploy-model/exp-valor-v1) y verificar `manifest.json` antes de servir.
"""


if __name__ == "__main__":
    exportar()
