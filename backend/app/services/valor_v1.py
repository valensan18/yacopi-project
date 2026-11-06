"""Servicio de la demostración académica del modelo RF v1 (escenario A).

- Carga UNA sola vez el artefacto exp-valor-v1 (pipeline completo) y
  verifica integridad (manifiesto + esquema + versión).
- Recibe únicamente public_id opaco; deriva las features desde el artefacto
  (construidas con el preprocesamiento exacto del entrenamiento).
- Controles de dominio: predio admitido (construcción = 0), áreas positivas,
  rangos numéricos y categorías del entrenamiento.
- Devuelve SIEMPRE la referencia ZHG (cuando existe) diferenciada de la
  predicción ML; sin intervalos de confianza.
- No expone avalúos originales ni identificadores catastrales privados.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ..core.errors import (
    OutOfDomainError,
    UnsupportedParcelError,
    ValorV1UnavailableError,
)
from ..schemas.valor_v1 import (
    VALOR_V1_DISCLAIMER,
    VALOR_V1_LIMITATIONS,
)

ARTIFACT_DIR = "exp-valor-v1"

CONDICIONES = [
    "Predio rural de Yacopí con construcción registrada igual a cero "
    "(escenario A del experimento).",
    "Área del terreno positiva y características dentro de los rangos "
    "observados en el entrenamiento.",
    "Resultado expresado como estimación orientativa de valor catastral "
    "unitario (COP/ha); no es precio comercial ni avalúo oficial.",
]


class ValorV1Service:
    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.artifact_dir = self.model_dir / ARTIFACT_DIR
        self.model = None
        self.features: dict[str, dict] = {}
        self.stats: dict = {}
        self.manifest: dict = {}
        self.schema: dict = {}
        self.evaluacion: dict = {}

    def available(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        required = [
            "model.joblib", "features.json", "manifest.json",
            "feature_schema.json", "training_stats.json",
            "metrics_evaluacion.json",
        ]
        for name in required:
            if not (self.artifact_dir / name).exists():
                raise ValorV1UnavailableError(details={
                    "experimento": ARTIFACT_DIR,
                    "faltante": name,
                })

        manifest = json.loads(
            (self.artifact_dir / "manifest.json").read_text(encoding="utf-8")
        )
        if manifest.get("rol") != "demostracion_academica":
            raise ValorV1UnavailableError(details={
                "razon": "el manifiesto no corresponde a la demostración académica",
            })
        if manifest.get("status") != "experimental_demo":
            raise ValorV1UnavailableError(details={
                "razon": "el artefacto no está marcado como experimental_demo",
            })

        try:
            model = joblib.load(self.artifact_dir / "model.joblib")
        except Exception as exc:
            raise ValorV1UnavailableError(details={
                "razon": f"error al deserializar: {type(exc).__name__}",
            }) from exc

        self.model = model
        self.manifest = manifest
        self.schema = json.loads(
            (self.artifact_dir / "feature_schema.json").read_text(encoding="utf-8")
        )
        self.stats = json.loads(
            (self.artifact_dir / "training_stats.json").read_text(encoding="utf-8")
        )
        self.features = json.loads(
            (self.artifact_dir / "features.json").read_text(encoding="utf-8")
        )
        self.evaluacion = json.loads(
            (self.artifact_dir / "metrics_evaluacion.json").read_text(encoding="utf-8")
        )

    def info(self) -> dict:
        return {
            "habilitado": False,
            "disponible": self.available(),
            "model_id": self.manifest.get("model_id") if self.available() else None,
            "model_version": (
                self.manifest.get("model_version") if self.available() else None
            ),
        }

    def predict(self, public_id: str) -> dict:
        if not self.available():
            raise ValorV1UnavailableError(details={
                "razon": "artefacto exp-valor-v1 no cargado",
            })

        entry = self.features.get(public_id)
        if entry is None:
            raise UnsupportedParcelError(details={
                "razon": (
                    "el predio no está admitido: no pertenece a la cohorte del "
                    "escenario A (construcción registrada igual a cero) o no "
                    "existe en el dataset"
                ),
            })

        row = entry["features"]
        numericas = set(self.schema["numericas"])
        categoricas = set(self.schema["categoricas"])

        if float(row.get("area_terreno_m2") or 0) <= 0:
            raise UnsupportedParcelError(details={
                "razon": "área de terreno no positiva",
            })
        if float(row.get("area_construida_m2") or 0) != 0:
            raise UnsupportedParcelError(details={
                "razon": "el predio registra construcción; la demostración "
                         "solo admite el escenario A (construcción = 0)",
            })

        fuera_de_dominio: list[str] = []
        for col in numericas:
            value = row.get(col)
            if value is None or not np.isfinite(float(value)):
                fuera_de_dominio.append(f"{col}: no disponible")
                continue
            stats_col = self.stats["numeric"].get(col)
            if stats_col and not (
                stats_col["min"] <= float(value) <= stats_col["max"]
            ):
                fuera_de_dominio.append(
                    f"{col}: {value} fuera de [{stats_col['min']}, {stats_col['max']}]"
                )
        for col in categoricas:
            value = str(row.get(col))
            levels = self.stats["categorical"].get(col, [])
            if value not in levels:
                fuera_de_dominio.append(f"{col}: categoría no vista en entrenamiento")

        if fuera_de_dominio:
            raise OutOfDomainError(details={
                "campos_fuera_de_dominio": fuera_de_dominio,
            })

        order = list(self.schema["orden"])
        frame = pd.DataFrame([{col: row.get(col) for col in order}])[order]
        for col in numericas:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")

        try:
            prediction = float(self.model.predict(frame)[0])
        except Exception as exc:
            raise ValorV1UnavailableError(details={
                "razon": f"error de inferencia: {type(exc).__name__}",
            }) from exc

        if not np.isfinite(prediction) or prediction <= 0:
            raise OutOfDomainError(details={
                "razon": "la predicción no es finita o no es físicamente "
                         "válida (≤ 0 COP/ha); no se emite ese valor",
            })

        reference = entry.get("reference_zhg_cop_ha")
        reference = float(reference) if reference else None
        if reference is not None and reference <= 0:
            reference = None

        absolute = round(prediction - reference, 2) if reference else None
        relative = (
            round(100.0 * (prediction - reference) / reference, 2)
            if reference
            else None
        )

        return {
            "public_id": public_id,
            "model_id": self.manifest.get("model_id", ARTIFACT_DIR),
            "model_version": self.manifest.get("model_version", "1.0.0"),
            "model_role": "demostracion_academica",
            "target": self.manifest.get("target", "VALOR_TERRENO_Ha"),
            "target_description": self.manifest.get("target_description", ""),
            "unit": "COP/ha",
            "predicted_cop_ha": round(prediction, 2),
            "reference_zhg_cop_ha": round(reference, 2) if reference else None,
            "reference_zhg_note": (
                "Referencia geoeconómica ZHG consultada de los datos "
                "(dato territorial, NO es una predicción del modelo)."
                if reference
                else None
            ),
            "absolute_difference_vs_zhg_cop_ha": absolute,
            "relative_difference_vs_zhg_pct": relative,
            "zone_code": entry.get("zone_code"),
            "applicability_status": "admitted",
            "applicability_conditions": CONDICIONES,
            "evaluation_context": self.evaluacion,
            "reference_date": None,
            "limitations": VALOR_V1_LIMITATIONS,
            "disclaimer": VALOR_V1_DISCLAIMER,
        }
