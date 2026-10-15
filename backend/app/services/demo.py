"""Servicio de la demostración experimental ZHG (Fase 7B).

- Carga UNA sola vez el artefacto exp-zhg-001-demo (generado por
  yacopi_ml.zhg.export_demo) y verifica su integridad (manifest + esquema).
- Recibe únicamente public_id opaco; deriva las 19 características desde el
  artefacto (construidas con el preprocesamiento exacto del entrenamiento).
- Aplica controles de dominio: predio existente, monozona, rangos numéricos
  y categorías del entrenamiento, referencia ZHG disponible.
- La estimación se devuelve SIEMPRE junto a la referencia ZHG y su
  diferencia; sin intervalos de confianza.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ..core.errors import (
    ExperimentalZhgUnavailableError,
    OutOfDomainError,
    UnsupportedMultizoneError,
    UnsupportedParcelError,
)
from ..schemas.demo import DEMO_DISCLAIMER, DEMO_LIMITATIONS

ARTIFACT_DIR = "exp-zhg-001-demo"

SOURCE_DESCRIPTION = (
    "valor_hectarea_agropecuario (equivalente a ZHG_VALOR_ por zona, "
    "verificado en Fase 5A)."
)


class ExperimentalZhgService:
    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.artifact_dir = self.model_dir / ARTIFACT_DIR
        self.model = None
        self.features: dict[str, dict] = {}
        self.stats: dict = {}
        self.manifest: dict = {}
        self.schema: dict = {}
        self.membership: dict[str, dict] = {}

    def available(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        required = ["model.joblib", "features.json", "training_stats.json",
                    "manifest.json", "feature_schema.json",
                    "split_membership.json"]
        for name in required:
            if not (self.artifact_dir / name).exists():
                raise ExperimentalZhgUnavailableError(details={
                    "artifact_dir": str(self.artifact_dir),
                    "faltante": name,
                })

        manifest = json.loads(
            (self.artifact_dir / "manifest.json").read_text(encoding="utf-8")
        )
        if manifest.get("status") != "experimental":
            raise ExperimentalZhgUnavailableError(details={
                "razon": "el manifiesto no corresponde a un artefacto experimental",
            })

        try:
            model = joblib.load(self.artifact_dir / "model.joblib")
        except Exception as exc:
            raise ExperimentalZhgUnavailableError(details={
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
        self.membership = json.loads(
            (self.artifact_dir / "split_membership.json").read_text(
                encoding="utf-8"
            )
        )

    def info(self) -> dict:
        return {
            "habilitado": self.available(),
            "disponible": self.available(),
            "model_id": self.manifest.get("model_id") if self.available() else None,
        }

    def predict(self, public_id: str) -> dict:
        if not self.available():
            raise ExperimentalZhgUnavailableError()

        entry = self.features.get(public_id)
        if entry is None:
            raise UnsupportedParcelError(details={
                "public_id": public_id,
                "razon": (
                    "el predio no está en el conjunto de características del "
                    "artefacto de demostración"
                ),
            })

        if entry["n_zonas"] > 1:
            raise UnsupportedMultizoneError(details={
                "n_zonas": entry["n_zonas"],
            })

        reference = float(entry["reference_zhg_cop_ha"])
        if reference <= 0:
            raise UnsupportedParcelError(details={
                "razon": "sin referencia ZHG positiva para comparar",
            })

        numericas = set(self.schema["numericas"])
        categoricas = set(self.schema["categoricas"])
        row = entry["features"]
        fuera_de_dominio: list[str] = []
        for col in numericas:
            value = row.get(col)
            if value is None or not np.isfinite(value):
                fuera_de_dominio.append(f"{col}: no disponible")
                continue
            stats_col = self.stats["numeric"].get(col)
            if stats_col and not (
                stats_col["min"] <= float(value) <= stats_col["max"]
            ):
                fuera_de_dominio.append(
                    f"{col}: {value} fuera de [{stats_col['min']}, "
                    f"{stats_col['max']}]"
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
            raise ExperimentalZhgUnavailableError(details={
                "razon": f"error de inferencia: {type(exc).__name__}",
            }) from exc

        if not np.isfinite(prediction) or prediction <= 0:
            raise OutOfDomainError(details={
                "razon": (
                    "la predicción no es finita o no es físicamente válida "
                    "(≤ 0 COP/ha); la demostración no emite ese valor"
                ),
            })

        absolute = prediction - reference
        relative = round(100.0 * absolute / reference, 2) if reference > 0 else None
        membership = self.membership.get(public_id, {})

        return {
            "public_id": public_id,
            "model_id": self.manifest.get("model_id", ARTIFACT_DIR),
            "model_status": "experimental",
            "unit": "COP/ha",
            "target_description": self.manifest.get("target_description", ""),
            "reference_zhg_cop_ha": round(reference, 2),
            "predicted_zhg_cop_ha": round(prediction, 2),
            "absolute_difference_cop_ha": round(absolute, 2),
            "relative_difference_pct": relative,
            "zone_code": str(entry["zone_code"]),
            "domain_status": "in_domain",
            "source_description": SOURCE_DESCRIPTION,
            "reference_date": None,
            "limitations": DEMO_LIMITATIONS,
            "evaluation_context": {
                "split_membership": membership,
                "nota": (
                    "la pertenencia a una partición histórica se informa sin "
                    "identificadores privados; una predicción sobre un predio "
                    "del entrenamiento no demuestra generalización"
                ),
            },
            "disclaimer": DEMO_DISCLAIMER,
        }
