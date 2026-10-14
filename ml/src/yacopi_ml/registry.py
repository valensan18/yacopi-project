"""Registro local de experimentos (solo artefactos experimentales)."""

import json
from datetime import UTC, datetime

from .export import ARTIFACTS_ROOT, REGISTRY_PATH


def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"experiments": []}


def register_experiment(experiment_id: str, summary: dict) -> None:
    registry = load_registry()
    registry["experiments"].append({
        "experiment_id": experiment_id,
        "status": "experimental",
        "registered_at": datetime.now(UTC).isoformat(),
        **summary,
    })
    ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8"
    )
