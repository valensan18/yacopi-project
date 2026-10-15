"""Pruebas de la demostración experimental ZHG (Fase 7B/7C)."""

import re
from pathlib import Path

import pytest
from app.core.config import Settings
from app.main import create_app
from conftest import build_mini_zhg_demo, public_id_for
from fastapi.testclient import TestClient


def valid_entry(n_zonas=1, reference=456041.7):
    return {
        "features": {
            "area_terreno_catastral_m2": 50000.0,
            "tr_latitud": 5.5,
            "destino_economico": "Agropecuario",
        },
        "zone_code": "07",
        "n_zonas": n_zonas,
        "reference_zhg_cop_ha": reference,
    }


def make_client(mini_db, tmp_path, entries, enabled: bool):
    model_dir = tmp_path / "models"
    model_dir.mkdir(parents=True)
    build_mini_zhg_demo(model_dir, entries)
    settings = Settings(
        database_path=mini_db,
        model_dir=model_dir,
        experimental_zhg_enabled=enabled,
        _env_file=None,
    )
    return TestClient(create_app(settings))


class TestDeshabilitadaPorDefecto:
    def test_503_cuando_flag_apagado(self, mini_db, tmp_path):
        entries = {public_id_for("A"): valid_entry()}
        with make_client(mini_db, tmp_path, entries, enabled=False) as client:
            response = client.post("/api/v1/predictions/experimental-zhg", json={
                "public_id": public_id_for("A"),
            })
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "EXPERIMENTAL_ZHG_DISABLED"

    def test_status_incluye_demo_deshabilitada(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path, {}, enabled=False) as client:
            body = client.get("/api/v1/system/status").json()
        assert body["experimental_zhg"]["habilitado"] is False


class TestDemoHabilitada:
    def test_monozona_exitoso(self, mini_db, tmp_path):
        pid = public_id_for("A")
        entries = {pid: valid_entry()}
        with make_client(mini_db, tmp_path, entries, enabled=True) as client:
            response = client.post("/api/v1/predictions/experimental-zhg", json={
                "public_id": pid,
            })
        assert response.status_code == 200
        body = response.json()
        assert body["model_status"] == "experimental"
        assert body["unit"] == "COP/ha"
        assert body["reference_zhg_cop_ha"] == 456041.7
        assert body["predicted_zhg_cop_ha"] == 500000.0
        assert abs(body["absolute_difference_cop_ha"] - (500000.0 - 456041.7)) < 1e-6
        assert body["relative_difference_pct"] is not None
        assert body["zone_code"] == "07"
        assert body["domain_status"] == "in_domain"
        assert body["evaluation_context"]["split_membership"]["predio"] == "train"
        assert body["evaluation_context"]["formo_parte_del_ajuste"] is True
        assert any(
            "forma parte de los datos utilizados para ajustar" in lim
            for lim in body["limitations"]
        )
        assert any("no constituye un avalúo" in lim for lim in body["limitations"])
        assert not re.search(r"\d{30}", str(body))

    def test_predio_inexistente_404(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path, {}, enabled=True) as client:
            response = client.post("/api/v1/predictions/experimental-zhg", json={
                "public_id": "p_noexiste",
            })
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PROPERTY_NOT_FOUND"

    def test_predio_sin_features_422(self, mini_db, tmp_path):
        pid = public_id_for("A")
        with make_client(mini_db, tmp_path, {}, enabled=True) as client:
            response = client.post("/api/v1/predictions/experimental-zhg", json={
                "public_id": pid,
            })
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "UNSUPPORTED_PARCEL"

    def test_multizona_rechazado(self, mini_db, tmp_path):
        pid = public_id_for("B")
        with make_client(mini_db, tmp_path, {pid: valid_entry(n_zonas=2)},
                         enabled=True) as client:
            response = client.post("/api/v1/predictions/experimental-zhg", json={
                "public_id": pid,
            })
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "UNSUPPORTED_MULTIZONE"

    def test_fuera_de_dominio(self, mini_db, tmp_path):
        pid = public_id_for("A")
        entry = valid_entry()
        entry["features"]["area_terreno_catastral_m2"] = 1e12
        with make_client(mini_db, tmp_path, {pid: entry}, enabled=True) as client:
            response = client.post("/api/v1/predictions/experimental-zhg", json={
                "public_id": pid,
            })
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "OUT_OF_DOMAIN"

    def test_categoria_no_vista(self, mini_db, tmp_path):
        pid = public_id_for("A")
        entry = valid_entry()
        entry["features"]["destino_economico"] = "CategoríaNueva"
        with make_client(mini_db, tmp_path, {pid: entry}, enabled=True) as client:
            response = client.post("/api/v1/predictions/experimental-zhg", json={
                "public_id": pid,
            })
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "OUT_OF_DOMAIN"

    def test_sin_referencia_positiva(self, mini_db, tmp_path):
        pid = public_id_for("A")
        with make_client(mini_db, tmp_path, {pid: valid_entry(reference=0.0)},
                         enabled=True) as client:
            response = client.post("/api/v1/predictions/experimental-zhg", json={
                "public_id": pid,
            })
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "UNSUPPORTED_PARCEL"

    def test_sin_artefacto_503(self, mini_db, tmp_path):
        settings = Settings(
            database_path=mini_db,
            model_dir=tmp_path / "vacio",
            experimental_zhg_enabled=True,
            _env_file=None,
        )
        with TestClient(create_app(settings)) as client:
            response = client.post("/api/v1/predictions/experimental-zhg", json={
                "public_id": public_id_for("A"),
            })
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "EXPERIMENTAL_ZHG_UNAVAILABLE"


class TestOficialIntacto:
    def test_predictions_sigue_503(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path, {}, enabled=False) as client:
            response = client.post("/api/v1/predictions", json={
                "features": {"area_terreno_catastral_m2": 50000},
            })
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "MODEL_NOT_READY"


REAL_DB = Path(__file__).resolve().parents[2] / "data" / "parcels.db"
REAL_ARTIFACT = (
    Path(__file__).resolve().parents[2] / "ml" / "artifacts" / "exp-zhg-001-demo"
)


@pytest.mark.skipif(
    not (REAL_DB.exists() and (REAL_ARTIFACT / "model.joblib").exists()),
    reason="base o artefacto real no presentes",
)
class TestE2EConArtefactoReal:
    """Prueba end-to-end aislada con la base y el artefacto REALES."""

    def _client(self):
        settings = Settings(
            database_path=REAL_DB,
            model_dir=REAL_ARTIFACT.parent,
            experimental_zhg_enabled=True,  # habilitación temporal en pruebas
            _env_file=None,
        )
        return TestClient(create_app(settings))

    def _ids(self):
        import sqlite3

        conn = sqlite3.connect(REAL_DB)
        conn.row_factory = sqlite3.Row
        mono = conn.execute(
            "SELECT p.public_id FROM parcels p "
            "JOIN parcel_zhg_references z ON z.public_id = p.public_id "
            "GROUP BY p.public_id HAVING COUNT(*) = 1 LIMIT 1"
        ).fetchone()["public_id"]
        multi = conn.execute(
            "SELECT p.public_id FROM parcels p "
            "JOIN parcel_zhg_references z ON z.public_id = p.public_id "
            "GROUP BY p.public_id HAVING COUNT(*) > 1 LIMIT 1"
        ).fetchone()["public_id"]
        conn.close()
        return mono, multi

    def test_flujo_completo(self):
        mono, multi = self._ids()
        with self._client() as client:
            # 1. predio monozona válido
            r = client.post("/api/v1/predictions/experimental-zhg",
                            json={"public_id": mono})
            assert r.status_code == 200
            body = r.json()
            assert body["predicted_zhg_cop_ha"] > 0
            assert body["reference_zhg_cop_ha"] > 0
            assert body["evaluation_context"]["formo_parte_del_ajuste"] is True
            assert any(
                "no constituye una evaluación independiente" in lim
                for lim in body["limitations"]
            )
            assert not re.search(r"\d{30}", str(body))

            # 2. predio multizona rechazado
            r = client.post("/api/v1/predictions/experimental-zhg",
                            json={"public_id": multi})
            assert r.status_code == 422
            assert r.json()["error"]["code"] == "UNSUPPORTED_MULTIZONE"

            # 3. identificador inexistente
            r = client.post("/api/v1/predictions/experimental-zhg",
                            json={"public_id": "p_noexiste"})
            assert r.status_code == 404

            # 4. oficial intacto
            r = client.post("/api/v1/predictions", json={"features": {}})
            assert r.status_code == 503

    def test_deshabilitada_por_defecto_con_artefacto_real(self):
        settings = Settings(
            database_path=REAL_DB,
            model_dir=REAL_ARTIFACT.parent,
            experimental_zhg_enabled=False,
            _env_file=None,
        )
        with TestClient(create_app(settings)) as client:
            r = client.post("/api/v1/predictions/experimental-zhg",
                            json={"public_id": "p_x"})
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "EXPERIMENTAL_ZHG_DISABLED"
