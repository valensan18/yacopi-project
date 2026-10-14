"""Pruebas del pipeline ML (Fase 2): anti-leakage, splits, métricas y smoke.

Las pruebas que requieren la base local se omiten en CI (sin datos).
"""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from yacopi_ml.evaluate import segmentation_errors
from yacopi_ml.labels import build_dataset
from yacopi_ml.metrics import compute_metrics
from yacopi_ml.schema import (
    FEATURE_COLUMNS,
    assert_no_blocked_columns,
    blocked_columns,
    load_label_contract,
)
from yacopi_ml.split import make_splits, spatial_groups
from yacopi_ml.train import check_contract, run

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "parcels.db"
HAS_DB = DB.exists()


class TestAntiLeakage:
    def test_production_rechazado_con_etiqueta_pendiente(self):
        with pytest.raises(SystemExit) as exc:
            check_contract("production")
        assert "RECHAZADO" in str(exc.value)

    def test_contrato_proxy_es_experimental(self):
        contract = load_label_contract("label_contract_proxy.yaml")
        assert contract["source_kind"] == "proxy"
        assert contract["production_eligible"] is False
        assert contract["unit"] == "COP/ha"

    def test_features_permitidas_no_contienen_bloqueadas(self):
        assert_no_blocked_columns(FEATURE_COLUMNS)

    def test_bloqueadas_detecta_intrusion(self):
        with pytest.raises(ValueError):
            assert_no_blocked_columns(FEATURE_COLUMNS + ["ZHG_VALOR_"])

    def test_columnas_bloqueadas_incluyen_valores_zonales(self):
        blocked = set(blocked_columns())
        assert {"ZHG_VALOR_", "ZHG_VALOR1", "valor_hectarea_agropecuario",
                "referencia_avaluo_total_por_ha_cop"} <= blocked


class TestMetrics:
    def test_perfecto_da_cero(self):
        y = np.array([100.0, 200.0, 300.0])
        m = compute_metrics(y, y.copy())
        assert m["mae_cop_ha"] == 0.0
        assert m["rmse_cop_ha"] == 0.0
        assert m["r2"] == 1.0
        assert m["mdape_pct"] == 0.0

    def test_porcentuales_excluyen_y_cero(self):
        y = np.array([0.0, 100.0])
        pred = np.array([50.0, 90.0])
        m = compute_metrics(y, pred)
        assert m["n_para_porcentuales"] == 1  # solo y=100

    def test_metricas_sinteticas_conocidas(self):
        y = np.array([100.0, 100.0])
        pred = np.array([110.0, 90.0])
        m = compute_metrics(y, pred)
        assert m["mae_cop_ha"] == 10.0
        assert m["mdape_pct"] == 10.0


class TestSplits:
    def test_integridad_y_reproducibilidad(self, tmp_path):
        rng = np.random.RandomState(0)
        ids = [f"parcela_{i:05d}" for i in range(300)]
        coords = pd.DataFrame({
            "tr_latitud": rng.uniform(5.3, 5.9, 300),
            "tr_longitud": rng.uniform(-74.6, -74.1, 300),
        })
        s1 = make_splits(ids, coords, splits_dir=tmp_path / "s1")
        s2 = make_splits(ids, coords, splits_dir=tmp_path / "s2")

        for name in ("train_random", "test_random", "train_spatial", "test_spatial"):
            assert s1[name] == s2[name], f"{name} no es reproducible"

        assert not set(s1["train_random"]) & set(s1["test_random"])
        assert not set(s1["train_spatial"]) & set(s1["test_spatial"])
        assert set(s1["train_spatial"]) | set(s1["test_spatial"]) == set(ids)

    def test_grupos_espaciales_no_cruzados(self, tmp_path):
        rng = np.random.RandomState(1)
        ids = [f"p{i}" for i in range(200)]
        coords = pd.DataFrame({
            "tr_latitud": rng.uniform(5.3, 5.9, 200),
            "tr_longitud": rng.uniform(-74.6, -74.1, 200),
        })
        groups = spatial_groups(coords)
        s = make_splits(ids, coords, splits_dir=tmp_path / "s")
        train_groups = {groups[ids.index(i)] for i in s["train_spatial"]}
        test_groups = {groups[ids.index(i)] for i in s["test_spatial"]}
        assert not train_groups & test_groups


class TestSegmentation:
    def test_segmentos_con_n(self):
        contexto = pd.DataFrame({
            "subzona": ["05", "05", "14"],
            "destino_economico": ["Agropecuario"] * 3,
            "area_terreno_catastral_m2": [40000.0, 60000.0, 300000.0],
            "area_construida_m2": [0.0, 10.0, 0.0],
            "n_alertas_calidad": [0, 1, 2],
        })
        y = pd.Series([1000.0, 2000.0, 3000.0])
        seg = segmentation_errors(contexto, y, y + 100.0)
        assert seg["por_subzona"]["05"]["n"] == 2
        assert seg["sin_construccion"]["n"] == 2
        assert seg["con_construccion"]["n"] == 1


@pytest.mark.skipif(not HAS_DB, reason="base local no presente")
class TestDatasetYSmoke:
    def test_dataset_valido(self):
        X, y, info = build_dataset(DB)
        assert X.shape[1] == len(FEATURE_COLUMNS)
        assert len(X) == len(y) == info["contexto"].shape[0]
        assert (y > 0).all()
        assert y.notna().all()
        assert info["excluidos"]["total_cohorte"] == 7694
        assert (X["area_terreno_catastral_m2"] > 0).all()

    def test_smoke_reproducible(self, tmp_path):
        def run_smoke(out_dir):
            args = SimpleNamespace(
                mode="research-proxy", output=str(out_dir), db=str(DB),
                smoke=True, n_iter=1, resplit=False,
            )
            return run(args)

        metrics_a = run_smoke(tmp_path / "a")
        metrics_b = run_smoke(tmp_path / "b")

        maes_a = {n: m["mae_cop_ha"]
                  for n, m in metrics_a["protocols"]["spatial"]["test"].items()}
        maes_b = {n: m["mae_cop_ha"]
                  for n, m in metrics_b["protocols"]["spatial"]["test"].items()}
        assert maes_a == maes_b
        assert set(maes_a) == {"dummy", "ridge", "tree", "forest", "catboost"}
        assert all(np.isfinite(v) for v in maes_a.values())

        assert metrics_a["label"]["source_kind"] == "proxy"
        assert metrics_a["label"]["production_eligible"] is False
        assert metrics_a["cohorte"]["n_cohorte_ml"] == 7694

        # artefactos del experimento seleccionado
        artifacts = tmp_path / "a"
        assert (artifacts / "metrics.json").exists()
        assert (artifacts / "MODEL_CARD.md").exists()
        assert (artifacts / "training_manifest.json").exists()
        assert (artifacts / "feature_schema.json").exists()
        card = (artifacts / "MODEL_CARD.md").read_text(encoding="utf-8")
        assert "EXPERIMENTAL" in card
        assert "proxy" in card.lower()

        # el modelo seleccionado quedó serializado
        modelo = metrics_a["seleccion"]["model"]
        serialized = artifacts / ("model.cbm" if modelo == "catboost" else "model.joblib")
        assert serialized.exists()

    def test_manifest_registra_versiones(self, tmp_path):
        args = SimpleNamespace(
            mode="research-proxy", output=str(tmp_path / "m"), db=str(DB),
            smoke=True, n_iter=1, resplit=False,
        )
        run(args)
        manifest = json.loads(
            (tmp_path / "m" / "training_manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["package_versions"]["scikit_learn"]
        assert manifest["feature_schema"]["unidades"]["area_terreno_catastral_m2"] == "m2"
        assert manifest["modo"] == "research-proxy"
