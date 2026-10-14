"""Pruebas de integración de la API (base mínima sintética, sin datos reales).

Las pruebas del artefacto experimental real se omiten si no existe
ml/artifacts/exp-proxy-001 (p. ej. en CI).
"""

from pathlib import Path

import pytest
from app.core.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "ml" / "artifacts" / "exp-proxy-001"
HAS_ARTIFACT = (ARTIFACT / "model.joblib").exists() and (
    ARTIFACT / "feature_schema.json"
).exists()


def make_client(mini_db, tmp_path, experimental_enabled: bool):
    settings = Settings(
        database_path=mini_db,
        model_dir=tmp_path / "models",
        experimental_inference_enabled=experimental_enabled,
        _env_file=None,
    )
    return TestClient(create_app(settings))


@pytest.fixture
def client(mini_db, tmp_path):
    with make_client(mini_db, tmp_path, experimental_enabled=False) as c:
        yield c


class TestHealthYEstado:
    def test_live(self, client):
        assert client.get("/api/v1/health/live").json() == {
            "status": "ok", "model_ready": False,
        }

    def test_ready(self, client):
        assert client.get("/api/v1/health/ready").status_code == 200

    def test_system_status_sin_modelo_oficial(self, client):
        response = client.get("/api/v1/system/status")
        assert response.status_code == 200
        body = response.json()
        assert body["model_status"] == "label_pending"
        assert body["model_ready"] is False
        assert body["target_unit"] == "COP/ha"
        assert body["dataset_version"] == "test-v1"
        assert body["experimental_model"]["habilitado"] is False

    def test_openapi_documenta_endpoints(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        paths = response.json()["paths"]
        for expected in (
            "/api/v1/health/live", "/api/v1/health/ready",
            "/api/v1/system/status", "/api/v1/properties",
            "/api/v1/properties/{public_id}", "/api/v1/statistics/overview",
            "/api/v1/statistics/distributions", "/api/v1/maps/points",
            "/api/v1/models", "/api/v1/models/active",
            "/api/v1/predictions", "/api/v1/predictions/experimental",
        ):
            assert expected in paths, f"falta {expected} en OpenAPI"


class TestProperties:
    def test_paginacion_y_total(self, client):
        body = client.get(
            "/api/v1/properties?limit=2&offset=0"
        ).json()
        assert body["pagination"]["total"] == 5
        assert len(body["items"]) == 2
        assert body["dataset_version"] == "test-v1"
        assert "parcel_source_id" not in str(body)

    def test_filtro_destino(self, client):
        body = client.get(
            "/api/v1/properties", params={"destino": "Agropecuario"}
        ).json()
        assert body["pagination"]["total"] == 3

    def test_filtro_rango_area(self, client):
        body = client.get(
            "/api/v1/properties",
            params={"min_area_m2": 50000, "max_area_m2": 100000},
        ).json()
        assert body["pagination"]["total"] == 2

    def test_orden_no_permitido_rechazado(self, client):
        response = client.get(
            "/api/v1/properties", params={"sort": "valor_avaluo"}
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_INPUT"

    def test_detalle_con_features_y_flags(self, client):
        listing = client.get("/api/v1/properties?limit=1").json()
        public_id = listing["items"][0]["public_id"]
        body = client.get(f"/api/v1/properties/{public_id}").json()
        assert body["item"]["public_id"] == public_id
        assert "zhf_codigo" in body["item"]["features"]
        assert isinstance(body["item"]["quality_flags"], list)

    def test_detalle_inexistente_404(self, client):
        response = client.get("/api/v1/properties/p_noexiste")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PROPERTY_NOT_FOUND"

    def test_limite_maximo_aplicado(self, client):
        body = client.get("/api/v1/properties?limit=5000").json()
        assert body["pagination"]["limit"] <= 100


class TestStatistics:
    def test_overview_real(self, client):
        body = client.get("/api/v1/statistics/overview").json()
        assert body["total_predios"] == 5
        assert body["con_construccion"] == 2
        assert body["predios_con_coordenadas"] == 5
        assert body["area"]["total_m2"] > 0

    def test_distribuciones(self, client):
        body = client.get(
            "/api/v1/statistics/distributions",
            params={"field": "destino_economico"},
        ).json()
        assert body["field"] == "destino_economico"
        assert body["bins"][0]["n"] == 3

    def test_distribucion_area(self, client):
        body = client.get(
            "/api/v1/statistics/distributions",
            params={"field": "area_terreno_catastral_m2"},
        ).json()
        total = sum(b["n"] for b in body["bins"])
        assert total == 5

    def test_campo_distribucion_invalido_422(self, client):
        response = client.get(
            "/api/v1/statistics/distributions", params={"field": "precio"}
        )
        assert response.status_code == 422


class TestMaps:
    def test_geojson_puntos(self, client):
        body = client.get("/api/v1/maps/points").json()
        assert body["type"] == "FeatureCollection"
        assert body["crs"]["properties"]["name"] == "EPSG:4326"
        assert len(body["features"]) == 5
        first = body["features"][0]
        assert first["geometry"]["type"] == "Point"

    def test_bbox_y_limite(self, client):
        body = client.get(
            "/api/v1/maps/points",
            params={"min_lat": 5.54, "min_lon": -74.5, "max_lat": 5.58,
                    "max_lon": -74.34, "limit": 1},
        ).json()
        assert len(body["features"]) == 1


class TestModels:
    def test_lista_vacia_sin_registro(self, client):
        body = client.get("/api/v1/models").json()
        assert body["official_model"] is None
        assert body["label_status"] == "pending_verification"

    def test_active_vacio(self, client):
        body = client.get("/api/v1/models/active").json()
        assert body["active"] is None


class TestPredictions:
    def test_oficial_bloqueada_503(self, client):
        response = client.post("/api/v1/predictions", json={
            "features": {"area_terreno_catastral_m2": 50000},
        })
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "MODEL_NOT_READY"

    def test_experimental_desactivada_por_defecto(self, client):
        response = client.post("/api/v1/predictions/experimental", json={
            "features": {"area_terreno_catastral_m2": 50000},
        })
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "EXPERIMENTAL_INFERENCE_DISABLED"

    def test_experimental_sin_artefacto_503(self, mini_db, tmp_path):
        with make_client(mini_db, tmp_path, experimental_enabled=True) as c:
            response = c.post("/api/v1/predictions/experimental", json={
                "features": {"area_terreno_catastral_m2": 50000},
            })
            assert response.status_code == 503
            assert response.json()["error"]["code"] == "EXPERIMENTAL_MODEL_UNAVAILABLE"

    def test_input_invalido_422(self, client):
        response = client.post("/api/v1/predictions/experimental", json={
            "features": {"area_terreno_catastral_m2": -5},
        })
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_INPUT"


@pytest.mark.skipif(not HAS_ARTIFACT, reason="artefacto experimental no presente")
class TestPrediccionExperimentalReal:
    @pytest.fixture
    def exp_client(self, mini_db, tmp_path):
        model_dir = tmp_path / "models"
        model_dir.mkdir()
        import shutil

        shutil.copytree(ARTIFACT, model_dir / "exp-proxy-001")
        with make_client(mini_db, tmp_path, experimental_enabled=True) as c:
            yield c

    def test_prediccion_proxy_valida(self, exp_client):
        response = exp_client.post("/api/v1/predictions/experimental", json={
            "features": {
                "area_terreno_catastral_m2": 50000,
                "area_construida_m2": 0,
                "tr_latitud": 5.55,
                "tr_longitud": -74.35,
                "destino_economico": "Agropecuario",
                "zhf_codigo": "05",
                "zhf_dispon": "4",
                "zhf_influe": "3",
                "zhf_uso_ac": "16",
                "aht_vpoten": "23",
                "vus_vocaci": "ASPp",
                "ups": "Zonas de desarrollo agropecuario sin restricciones",
                "clc_nivel1": "2. Territorios Agrícolas",
            },
        })
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "experimental_proxy_prediction"
        assert body["unit"] == "COP/ha"
        assert body["prediction_cop_ha"] > 0
        assert body["is_experimental"] is True
        assert body["predicts_land_value"] is False
        assert "proxy" in body["disclaimer"]
        assert "NO es el valor exclusivo del suelo" in body["disclaimer"]

    def test_prediccion_reproducible(self, exp_client):
        payload = {"features": {
            "area_terreno_catastral_m2": 30000,
            "destino_economico": "Agropecuario",
        }}
        first = exp_client.post("/api/v1/predictions/experimental", json=payload)
        second = exp_client.post("/api/v1/predictions/experimental", json=payload)
        assert first.json()["prediction_cop_ha"] == second.json()["prediction_cop_ha"]

    def test_categoria_desconocida_manejada(self, exp_client):
        response = exp_client.post("/api/v1/predictions/experimental", json={
            "features": {
                "area_terreno_catastral_m2": 20000,
                "destino_economico": "CategoríaDesconocida123",
            },
        })
        assert response.status_code == 200
        assert response.json()["prediction_cop_ha"] > 0
