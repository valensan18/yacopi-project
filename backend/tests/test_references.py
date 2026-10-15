"""Pruebas de referencias ZHG (Fase 6B)."""

import re

from app.core.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient


def make_client(mini_db, tmp_path):
    settings = Settings(
        database_path=mini_db,
        model_dir=tmp_path / "models",
        _env_file=None,
    )
    return TestClient(create_app(settings))


class TestZonas:
    def test_zonas_correctas(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path) as client:
            body = client.get("/api/v1/references/zhg/zones").json()
        assert body["unit"] == "COP/ha"
        assert body["reference_type"] == "zhg_zonal_reference"
        assert body["reference_date"] is None
        assert len(body["items"]) == 2
        assert {z["zone_code"] for z in body["items"]} == {"03", "06"}
        valores = {z["zone_code"]: z["value_cop_ha"] for z in body["items"]}
        assert valores["03"] == 1368119.6
        assert valores["06"] == 547247.2
        assert any(
            "no es" in lim.lower() and "predicción" in lim.lower()
            for lim in body["limitations"]
        )

    def test_sin_identificadores_privados(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path) as client:
            body = client.get("/api/v1/references/zhg/zones").json()
        assert "parcel_source_id" not in str(body)


class TestReferenciaPredio:
    def _public_ids(self):
        from conftest import public_id_for

        return {source: public_id_for(source) for source in "ABCDE"}

    def test_monozona_consistente(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path) as client:
            pid = self._public_ids()["A"]
            body = client.get(f"/api/v1/properties/{pid}/zhg-reference").json()
        assert body["public_id"] == pid
        assert len(body["zones"]) == 1
        assert body["zones"][0]["zone_code"] == "03"
        assert body["zones"][0]["value_cop_ha"] == 1368119.6
        assert body["dominant_zone"]["zone_code"] == "03"
        assert body["weighted_reference"] is not None
        assert body["weighted_reference"]["coverage_status"] == "consistente"
        assert body["provisional_weighted_reference"] is None
        assert body["coverage_status"] == "consistente"

    def test_multizona_dudosa_con_provisional(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path) as client:
            pid = self._public_ids()["B"]
            body = client.get(f"/api/v1/properties/{pid}/zhg-reference").json()
        assert len(body["zones"]) == 2
        assert body["coverage_status"] == "dudosa"
        assert body["weighted_reference"] is None
        provisional = body["provisional_weighted_reference"]
        assert provisional is not None
        assert "PROVISIONAL" in provisional["status_label"]
        expected = (1368119.6 * 1200 + 547247.2 * 1200) / 2400
        assert abs(provisional["value_cop_ha"] - round(expected, 2)) < 1e-6
        assert "no representa" in body["dominant_zone"]["note"]

    def test_multizona_no_apta_sin_ponderado(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path) as client:
            pid = self._public_ids()["C"]
            body = client.get(f"/api/v1/properties/{pid}/zhg-reference").json()
        assert body["coverage_status"] == "no_apta"
        assert body["weighted_reference"] is None
        assert body["provisional_weighted_reference"] is None
        assert len(body["zones"]) == 2

    def test_predio_sin_referencias(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path) as client:
            pid = self._public_ids()["D"]
            body = client.get(f"/api/v1/properties/{pid}/zhg-reference").json()
        assert body["zones"] == []
        assert body["dominant_zone"] is None
        assert body["coverage_status"] is None
        assert any("no tiene referencias ZHG" in lim for lim in body["limitations"])

    def test_predio_inexistente_404(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path) as client:
            response = client.get("/api/v1/properties/p_noexiste/zhg-reference")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PROPERTY_NOT_FOUND"

    def test_respuesta_sin_numero_predial_real(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path) as client:
            pid = self._public_ids()["A"]
            body = client.get(f"/api/v1/properties/{pid}/zhg-reference").json()
        assert not re.search(r"\d{30}", str(body))


class TestInferenciaOficialIntacta:
    def test_predictions_sigue_503(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path) as client:
            response = client.post("/api/v1/predictions", json={
                "features": {"area_terreno_catastral_m2": 50000},
            })
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "MODEL_NOT_READY"
