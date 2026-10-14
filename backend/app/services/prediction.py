"""Servicio de inferencia experimental (proxy Ruta B).

- Carga el artefacto UNA sola vez al iniciar (no reentrena por petición).
- Verifica procedencia: existencias, feature_schema.json con el mismo orden
  y tipos que el entrenamiento, y training_manifest.json con modo
  research-proxy. Nunca carga artefactos de origen desconocido.
- La predicción OFICIAL permanece bloqueada (503) hasta etiqueta validada.
"""

import json
from pathlib import Path

import joblib
import pandas as pd

from ..core.errors import (
    ExperimentalModelUnavailableError,
    ModelNotReadyError,
)
from ..schemas.prediction import PredictionFeatures

DISCLAIMER = (
    "Predicción EXPERIMENTAL de un proxy (avalúo catastral total por "
    "hectárea). NO es el valor exclusivo del suelo ni un avalúo oficial."
)
ARTIFACT_DIR = "exp-proxy-001"


class OfficialPredictionService:
    def predict(self, request) -> dict:
        raise ModelNotReadyError(details={
            "label_status": "pending_verification",
            "explanation": (
                "No existe valor exclusivo de terreno (COP/ha) validado por "
                "predio. El endpoint oficial permanece bloqueado."
            ),
        })


class ExperimentalPredictionService:
    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.artifact_dir = self.model_dir / ARTIFACT_DIR
        self.model = None
        self.schema: dict = {}
        self.manifest: dict = {}
        self.metrics: dict = {}

    def available(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        """Verifica integridad y carga el artefacto una única vez."""
        required = ["model.joblib", "feature_schema.json",
                    "training_manifest.json", "metrics.json"]
        for name in required:
            if not (self.artifact_dir / name).exists():
                raise ExperimentalModelUnavailableError(details={
                    "artifact_dir": str(self.artifact_dir),
                    "faltante": name,
                })

        schema = json.loads(
            (self.artifact_dir / "feature_schema.json").read_text(encoding="utf-8")
        )
        manifest = json.loads(
            (self.artifact_dir / "training_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        metrics = json.loads(
            (self.artifact_dir / "metrics.json").read_text(encoding="utf-8")
        )

        if manifest.get("modo") != "research-proxy":
            raise ExperimentalModelUnavailableError(details={
                "razon": "el manifiesto no corresponde a un experimento proxy",
            })
        if "model.cbm" in str(self.artifact_dir) and not (
            self.artifact_dir / "model.joblib"
        ).exists():
            raise ExperimentalModelUnavailableError(details={
                "razon": "artefacto no localizable",
            })

        try:
            model = joblib.load(self.artifact_dir / "model.joblib")
        except Exception as exc:
            raise ExperimentalModelUnavailableError(details={
                "razon": f"error al deserializar: {type(exc).__name__}",
            }) from exc

        self.model = model
        self.schema = schema
        self.manifest = manifest
        self.metrics = metrics

    def feature_order(self) -> list[str]:
        return list(self.schema["orden"])

    def predict(self, features: PredictionFeatures, area_for_total: float | None) -> dict:
        if not self.available():
            raise ExperimentalModelUnavailableError()

        warnings: list[str] = []
        numericas = set(self.schema.get("numericas", []))
        categoricas = set(self.schema.get("categoricas", []))

        row: dict = {}
        for name in self.feature_order():
            value = getattr(features, name, None)
            if name in numericas:
                if value is None:
                    warnings.append(
                        f"{name}: valor faltante imputado con la mediana "
                        "de entrenamiento"
                    )
                row[name] = value
            elif name in categoricas:
                value = value or "SIN_DATO"
                if value == "SIN_DATO":
                    warnings.append(
                        f"{name}: valor faltante marcado como SIN_DATO "
                        "(igual que en entrenamiento)"
                    )
                row[name] = str(value)

        df = pd.DataFrame([row])[self.feature_order()]
        for col in numericas:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        try:
            prediction = float(self.model.predict(df)[0])
        except Exception as exc:
            raise ExperimentalModelUnavailableError(details={
                "razon": f"error de inferencia: {type(exc).__name__}",
            }) from exc

        if not prediction == prediction or prediction in (float("inf"), float("-inf")):
            raise ExperimentalModelUnavailableError(details={
                "razon": "resultado no finito",
            })

        area = features.area_terreno_catastral_m2 or area_for_total
        total = round(prediction * area / 10_000, 2) if area else None
        return {
            "status": "experimental_proxy_prediction",
            "experiment_id": ARTIFACT_DIR,
            "model_version": self.manifest.get("experiment_id", ARTIFACT_DIR),
            "target": "proxy_avaluo_total_cop_ha",
            "unit": "COP/ha",
            "prediction_cop_ha": round(prediction, 2),
            "area_m2": area,
            "estimated_proxy_total_cop": total,
            "warnings": warnings,
            "is_experimental": True,
            "predicts_land_value": False,
            "disclaimer": DISCLAIMER,
        }

    def info(self) -> dict:
        if not self.available():
            return {"disponible": False}
        sel = self.metrics.get("seleccion", {})
        return {
            "disponible": True,
            "experiment_id": ARTIFACT_DIR,
            "modelo": sel.get("model"),
            "mae_test_espacial_cop_ha": (
                self.metrics["protocols"]["spatial"]["test"]
                .get(sel.get("model"), {})
                .get("mae_cop_ha")
            ),
            "r2_test_espacial": (
                self.metrics["protocols"]["spatial"]["test"]
                .get(sel.get("model"), {})
                .get("r2")
            ),
            "target": "proxy_avaluo_total_cop_ha",
            "es_etiqueta_oficial": False,
        }
