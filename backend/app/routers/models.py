"""Registro de modelos: solo artefactos experimentales reales."""

import json
from pathlib import Path

from fastapi import APIRouter, Request

router = APIRouter(tags=["models"])

DISCLAIMER = (
    "Modelos experimentales (proxy de avalúo catastral total por hectárea). "
    "No existe un modelo validado del valor exclusivo del suelo."
)


def _registry(request: Request) -> dict:
    path = Path(request.app.state.settings.model_dir) / "registry.json"
    if not path.exists():
        return {"experiments": []}
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/models")
def list_models(request: Request) -> dict:
    registry = _registry(request)
    return {
        "models": [
            {
                **entry,
                "status": "experimental",
                "production_eligible": False,
            }
            for entry in registry["experiments"]
        ],
        "official_model": None,
        "label_status": "pending_verification",
        "disclaimer": DISCLAIMER,
    }


@router.get("/models/active")
def active_model(request: Request) -> dict:
    registry = _registry(request)
    experiments = registry["experiments"]
    if not experiments:
        return {
            "active": None,
            "label_status": "pending_verification",
            "disclaimer": DISCLAIMER,
        }
    latest = experiments[-1]
    return {
        "active": {
            "experiment_id": latest["experiment_id"],
            "modelo": latest.get("modelo"),
            "mae_test_espacial_cop_ha": latest.get("mae_test_espacial_cop_ha"),
            "r2_test_espacial": latest.get("r2_test_espacial"),
            "target": "proxy_avaluo_total_cop_ha",
            "unit": "COP/ha",
            "status": "experimental",
            "production_eligible": False,
        },
        "label_status": "pending_verification",
        "disclaimer": DISCLAIMER,
    }
