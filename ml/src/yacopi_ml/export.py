"""Empaquetado de artefactos experimentales y registro de versiones."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import joblib
import pandas as pd

ML_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_ROOT = ML_ROOT / "artifacts"
REGISTRY_PATH = ARTIFACTS_ROOT / "registry.json"


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def package_versions() -> dict:
    import catboost
    import numpy
    import pandas as pd_mod
    import scipy
    import shap
    import sklearn

    return {
        "python": sys.version.split()[0],
        "numpy": numpy.__version__,
        "pandas": pd_mod.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "catboost": catboost.__version__,
        "shap": shap.__version__,
    }


def save_artifacts(exp_dir: Path, selected_name: str, model, payload: dict):
    """Serializa el modelo seleccionado y escribe los metadatos del experimento."""
    exp_dir.mkdir(parents=True, exist_ok=True)

    model_path = exp_dir / ("model.cbm" if selected_name == "catboost" else "model.joblib")
    inner_model = getattr(model, "model_", model)
    if selected_name == "catboost":
        inner_model.save_model(str(model_path))
    else:
        joblib.dump(model, model_path)

    (exp_dir / "metrics.json").write_text(
        json.dumps(payload["metrics"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (exp_dir / "feature_schema.json").write_text(
        json.dumps(payload["feature_schema"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (exp_dir / "training_manifest.json").write_text(
        json.dumps(payload["manifest"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    shutil.copyfile(
        ML_ROOT / "config" / "label_contract_proxy.yaml",
        exp_dir / "label_contract_proxy.yaml",
    )

    preds = payload["predictions_test"]
    pd.DataFrame(preds).to_csv(exp_dir / "predictions_test.csv", index=False)

    (exp_dir / "MODEL_CARD.md").write_text(
        payload["model_card"], encoding="utf-8"
    )


def build_model_card(experiment: dict) -> str:
    m = experiment["metrics"]
    sel = m["seleccion"]
    test = m["protocols"]["spatial"]["test"][sel["model"]]
    excl = experiment["excluidos"]
    return f"""# MODEL CARD — {experiment['experiment_id']} (EXPERIMENTAL, Ruta B)

**Estado:** experimental — NO es un modelo de producción. No predice el valor
exclusivo del suelo; predice un proxy (avalúo catastral total por hectárea).
No usar para avalúos ni decisiones oficiales.

## Etiqueta (proxy)

- `proxy_avaluo_total_cop_ha` (COP/ha) = valor_avaluo_total_cop /
  area_terreno_catastral_m2 x 10.000.
- **Incluye potencialmente construcciones** ({excl["n_cohorte"]} predios de
  cohorte; {excl["n_con_construccion"]} con área construida > 0).
- NO acredita valor exclusivo de terreno. Fecha de valoración: desconocida.

## Población

- Cohorte: {excl["n_cohorte"]} predios coincidentes entre fuentes (los 15 sin
  ZHF se excluyen por cobertura). Excluidos por validación de proxy:
  {excl["n_excluidos"]}. Entrenamiento espacial: {sel["n_train"]},
  test espacial: {sel["n_test"]}.

## Modelo seleccionado

- {sel["model"]} — criterio: menor MAE en test espacial.
- Hiperparámetros: ver training_manifest.json.

## Rendimiento en test espacial (real, no inventado)

- MAE: {test['mae_cop_ha']:.2f} COP/ha
- RMSE: {test['rmse_cop_ha']:.2f} COP/ha
- R²: {test['r2']:.4f}
- MdAPE: {test['mdape_pct']:.2f} %
- % err<30: {test['pct_error_lt_30']*100:.2f} %

## Limitaciones y riesgos

- Proxy, no suelo exclusivo: sensible a construcciones y al denominador
  (área) que también es predictor (relación mecánica parcial).
- Validación espacial más exigente: reportar siempre junto a la aleatoria.
- Sin fecha de valoración ni diccionario oficial de códigos.
- Interpretabilidad = asociación del modelo, no causalidad.

## Usos permitidos

Análisis académico comparativo de algoritmos. PROHIBIDO como avalúo.
"""
