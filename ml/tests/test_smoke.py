"""Pruebas de humo del paquete yacopi_ml (Fase 0)."""

from pathlib import Path

import yaml
from yacopi_ml import __version__

ML_DIR = Path(__file__).resolve().parents[1]


def test_package_importable():
    assert __version__ == "0.1.0"


def test_label_contract_starts_pending():
    contract = yaml.safe_load(
        (ML_DIR / "config" / "label_contract.yaml").read_text(encoding="utf-8")
    )
    assert contract["label_name"] == "valor_terreno_cop_ha"
    assert contract["source_status"] == "pending_verification"
    assert contract["production_eligible"] is False


def test_blocked_columns_include_geoeconomic_references():
    features = yaml.safe_load((ML_DIR / "config" / "features.yaml").read_text(encoding="utf-8"))
    blocked = set(features["blocked"])
    assert {"ZHG_VALOR_", "ZHG_VALOR1", "valor_hectarea_agropecuario"} <= blocked
