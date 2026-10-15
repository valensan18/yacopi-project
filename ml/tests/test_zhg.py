"""Pruebas del experimento ZHG (Fase 5): equivalencia, fuga, integridad."""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from yacopi_ml.metrics import compute_metrics
from yacopi_ml.schema import FEATURE_COLUMNS
from yacopi_ml.zhg.dataset import (
    TARGET_DOMINANTE,
    TARGET_PONDERADO,
    build_zhg_dataset,
)
from yacopi_ml.zhg.splits import make_zhg_splits
from yacopi_ml.zhg.train import assert_no_leak, load_zhg_blocked, run

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
HAS_DATA = (PROCESSED / "01_intersecciones_normalizadas.csv").exists()


class TestFuga:
    def test_features_no_contienen_bloqueadas_zhg(self):
        assert_no_leak(FEATURE_COLUMNS)

    def test_bloqueadas_detecta_intrusion(self):
        with pytest.raises(ValueError):
            assert_no_leak(FEATURE_COLUMNS + ["ZHG_VALOR_"])

    def test_bloqueadas_incluyen_estadisticos_zonales_del_software_anterior(self):
        blocked = load_zhg_blocked()
        assert {
            "latitud_promedio", "longitud_promedio", "n_registros_zhf",
            "ups_moda", "valor_hectarea_agropecuario", "ZHG_VALOR_",
            "zona_code", "zhg_subzona",
        } <= blocked


@pytest.mark.skipif(not HAS_DATA, reason="datos procesados no presentes")
class TestDatasetZhg:
    def test_equivalencia_zona_valor(self):
        import csv

        with (PROCESSED / "01_intersecciones_normalizadas.csv").open(
            encoding="utf-8", newline=""
        ) as fh:
            inter = list(csv.DictReader(fh))
        with (PROCESSED / "02_zhf_normalizadas.csv").open(
            encoding="utf-8", newline=""
        ) as fh:
            zhf = list(csv.DictReader(fh))

        map_i: dict[str, float] = {}
        for r in inter:
            val = float(r["valor_hectarea_agropecuario"])
            if val > 0:
                zone = str(r["codigo_zona_geoeconomica"]).zfill(2)
                if zone not in map_i:
                    map_i[zone] = val
                assert map_i[zone] == val, f"zona {zone} con valores distintos"
        map_z: dict[str, float] = {}
        for r in zhf:
            val = float(r["ZHG_VALOR_"])
            if val > 0:
                zone = str(r["ZHG_CODIGO"]).zfill(2)
                map_z.setdefault(zone, val)
        assert set(map_i) == set(map_z)
        assert len(map_i) == 11
        for zone in map_i:
            assert abs(map_i[zone] - map_z[zone]) < 1e-6, zone

    def test_dataset_predio_unico_y_objetivo_valido(self):
        df = build_zhg_dataset()
        assert df["public_id"].nunique() == len(df) == 7709
        assert (df[TARGET_DOMINANTE] > 0).all()
        assert df["zona_dominante"].nunique() == 11
        # ponderado solo para cobertura consistente/dudosa
        no_apta = df[df["cobertura"] == "no_apta"]
        assert no_apta[TARGET_PONDERADO].isna().all()
        consistent = df[df["cobertura"].isin(["consistente", "dudosa"])]
        assert consistent[TARGET_PONDERADO].notna().all()

    def test_splits_sin_solapes_y_reproducibles(self, tmp_path):
        df = build_zhg_dataset()
        s1 = make_zhg_splits(df, splits_dir=tmp_path / "s1")
        s2 = make_zhg_splits(df, splits_dir=tmp_path / "s2")
        for scenario in ("filas", "predio", "espacial", "zona"):
            assert s1[scenario][0] == s2[scenario][0]
            assert not set(s1[scenario][0]) & set(s1[scenario][1])

    def test_smoke_run_payload(self, tmp_path):
        args = SimpleNamespace(smoke=True, output=str(tmp_path / "exp"), target="dominante")
        payload = run(args)
        assert payload["n_zonas"] == 11
        assert payload["valores_objetivo_unicos"] == 11
        for name in ("dummy", "ridge", "tree", "forest", "catboost"):
            assert name in payload["scenarios"]
            for scenario in ("filas", "predio", "espacial", "zona"):
                assert np.isfinite(payload["scenarios"][name][scenario]["mae_cop_ha"])
        assert "predio_mediana" in payload["baselines"]
        assert len(payload["leave_one_zone_out"]) == 11
        assert payload["criterio_aceptacion"]["definicion"]
        assert (tmp_path / "exp" / "metrics.json").exists()


class TestMetricasSinteticas:
    def test_compute_metrics_zhg(self):
        y = np.array([300000.0, 500000.0, 700000.0])
        m = compute_metrics(y, y)
        assert m["mae_cop_ha"] == 0.0
        assert m["r2"] == 1.0

    def test_r2_no_interpretable_con_objetivo_constante(self):
        y = np.full(50, 547247.2)
        pred = np.full(50, 600000.0)
        m = compute_metrics(y, pred)
        assert np.isnan(m["r2"])
        assert np.isfinite(m["mae_cop_ha"])

    def test_r2_no_interpretable_con_ruido_de_punto_flotante(self):
        # reproduce el artefacto del leave-one-zone-out (ss_tot ~ 1e-17)
        y = np.array([547247.2, 547247.20000000001, 547247.19999999999])
        pred = np.array([600000.0, 500000.0, 550000.0])
        m = compute_metrics(y, pred)
        assert np.isnan(m["r2"])
