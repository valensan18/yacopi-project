"""Pruebas del servicio y endpoint de la demostración académica RF v1."""

import json

import joblib
import pandas as pd
import pytest
from app.core.config import Settings
from app.core.errors import (
    OutOfDomainError,
    UnsupportedParcelError,
    ValorV1UnavailableError,
)
from app.main import create_app
from app.services.valor_v1 import ValorV1Service
from fastapi.testclient import TestClient
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from scripts.build_db import public_id_for  # type: ignore


def build_mini_valor_v1(model_dir) -> None:
    """Artefacto exp-valor-v1 mínimo con un RandomForest real y determinista."""
    art = model_dir / "exp-valor-v1"
    art.mkdir(parents=True, exist_ok=True)

    schema = {
        "orden": ["area_terreno_m2", "tr_latitud", "destino_economico"],
        "numericas": ["area_terreno_m2", "tr_latitud"],
        "categoricas": ["destino_economico"],
    }
    (art / "feature_schema.json").write_text(json.dumps(schema), encoding="utf-8")

    stats = {
        "numeric": {
            "area_terreno_m2": {"min": 1000.0, "max": 900_000.0},
            "tr_latitud": {"min": 5.3, "max": 5.9},
        },
        "categorical": {"destino_economico": ["Agropecuario", "SIN_DATO"]},
    }
    (art / "training_stats.json").write_text(json.dumps(stats), encoding="utf-8")

    (art / "metrics_evaluacion.json").write_text(
        json.dumps({
            "nota": "metricas de validacion independientes (fixture de prueba)",
            "test_sellado_v2_espacial": {
                "n": 3,
                "rf": {"mae_cop_ha": 1.0, "mdape": 0.01, "rmse_cop_ha": 1.0, "r2": 0.5},
                "referencia_zhg": {"mae_cop_ha": 2.0, "mdape": 0.02},
            },
            "estabilidad_5_pliegues_espaciales": {
                "rf_gana_mae_en": 0, "rf_gana_mdape_en": 0,
                "rf_mae_mediana": 259000.0, "zhg_mae_mediana": 197000.0,
                "rf_mdape_mediana": 0.2, "zhg_mdape_mediana": 0.054,
            },
        }),
        encoding="utf-8",
    )

    (art / "manifest.json").write_text(
        json.dumps({
            "model_id": "atlas-vivo-rf-v1",
            "model_version": "1.0.0",
            "rol": "demostracion_academica",
            "status": "experimental_demo",
            "target": "VALOR_TERRENO_Ha",
            "target_description": "valor catastral unitario derivado del avaluo total",
            "n_fit": 40,
            "seed": 20261023,
        }),
        encoding="utf-8",
    )

    # Ajuste sintetico determinista: y crece con el area y latitud.
    rng = pd.DataFrame({
        "area_terreno_m2": [1_000, 5_000, 50_000, 100_000, 300_000, 600_000] * 7,
        "tr_latitud": [5.31, 5.40, 5.55, 5.66, 5.75, 5.89] * 7,
        "destino_economico": ["Agropecuario", "SIN_DATO"] * 21,
    })
    y = rng["area_terreno_m2"] / 100 + rng["tr_latitud"] * 1_000
    pre = ColumnTransformer(
        [
            ("num", Pipeline([
                ("imp", SimpleImputer(strategy="median")),
                ("sca", StandardScaler()),
            ]), ["area_terreno_m2", "tr_latitud"]),
            ("cat", Pipeline([
                ("imp", SimpleImputer(strategy="constant", fill_value="SIN_DATO")),
                ("ohe", OneHotEncoder(handle_unknown="ignore", min_frequency=1)),
            ]), ["destino_economico"]),
        ],
        remainder="drop",
    )
    model = Pipeline([
        ("enc", pre),
        ("reg", RandomForestRegressor(n_estimators=10, random_state=42)),
    ])
    model.fit(rng, y)
    joblib.dump(model, art / "model.joblib")

    features = {}
    for i, (_, fila) in enumerate(rng.iterrows()):
        pid = f"p_fixture_{i}"
        features[pid] = {
            "features": {
                "area_terreno_m2": float(fila["area_terreno_m2"]),
                "tr_latitud": float(fila["tr_latitud"]),
                "destino_economico": str(fila["destino_economico"]),
            },
            "zone_code": "05",
            "reference_zhg_cop_ha": 500_000.0,
        }
    # Entradas especiales para pruebas de dominio
    features["p_valido"] = {
        "features": {
            "area_terreno_m2": 50_000.0,
            "tr_latitud": 5.55,
            "destino_economico": "Agropecuario",
        },
        "zone_code": "05",
        "reference_zhg_cop_ha": 500_000.0,
    }
    features["p_con_construccion"] = {
        "features": {
            "area_terreno_m2": 50_000.0,
            "area_construida_m2": 120.0,
            "tr_latitud": 5.55,
            "destino_economico": "Agropecuario",
        },
        "zone_code": "05",
        "reference_zhg_cop_ha": 500_000.0,
    }
    features["p_area_cero"] = {
        "features": {
            "area_terreno_m2": 0.0,
            "tr_latitud": 5.55,
            "destino_economico": "Agropecuario",
        },
        "zone_code": "05",
        "reference_zhg_cop_ha": 500_000.0,
    }
    features["p_faltante"] = {
        "features": {
            "area_terreno_m2": 50_000.0,
            "tr_latitud": None,
            "destino_economico": "Agropecuario",
        },
        "zone_code": "05",
        "reference_zhg_cop_ha": 500_000.0,
    }
    features["p_fuera_rango"] = {
        "features": {
            "area_terreno_m2": 5_000_000.0,
            "tr_latitud": 5.55,
            "destino_economico": "Agropecuario",
        },
        "zone_code": "05",
        "reference_zhg_cop_ha": 500_000.0,
    }
    features["p_categoria_nueva"] = {
        "features": {
            "area_terreno_m2": 50_000.0,
            "tr_latitud": 5.55,
            "destino_economico": "Comercial",
        },
        "zone_code": "05",
        "reference_zhg_cop_ha": None,
    }
    features["p_sin_referencia"] = {
        "features": {
            "area_terreno_m2": 50_000.0,
            "tr_latitud": 5.55,
            "destino_economico": "Agropecuario",
        },
        "zone_code": "05",
        "reference_zhg_cop_ha": None,
    }
    (art / "features.json").write_text(json.dumps(features), encoding="utf-8")


@pytest.fixture
def valor_artifact(tmp_path):
    build_mini_valor_v1(tmp_path)
    return tmp_path


@pytest.fixture
def valor_service(valor_artifact):
    service = ValorV1Service(valor_artifact)
    service.load()
    return service


class TestServicio:
    def test_carga_valida(self, valor_service):
        assert valor_service.available()
        info = valor_service.info()
        assert info["disponible"] is True
        assert info["model_id"] == "atlas-vivo-rf-v1"

    def test_manifiesto_incorrecto_rechazado(self, valor_artifact):
        art = valor_artifact / "exp-valor-v1"
        manifest = json.loads((art / "manifest.json").read_text(encoding="utf-8"))
        manifest["status"] = "production"
        (art / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with pytest.raises(ValorV1UnavailableError):
            ValorV1Service(valor_artifact).load()

    def test_archivo_faltante_rechazado(self, valor_artifact):
        (valor_artifact / "exp-valor-v1" / "model.joblib").unlink()
        with pytest.raises(ValorV1UnavailableError):
            ValorV1Service(valor_artifact).load()

    def test_prediccion_determinista(self, valor_service):
        a = valor_service.predict("p_valido")
        b = valor_service.predict("p_valido")
        assert a["predicted_cop_ha"] == b["predicted_cop_ha"]
        assert a["predicted_cop_ha"] > 0
        assert a["model_id"] == "atlas-vivo-rf-v1"
        assert a["model_version"] == "1.0.0"
        assert a["unit"] == "COP/ha"

    def test_predio_inexistente(self, valor_service):
        with pytest.raises(UnsupportedParcelError):
            valor_service.predict("p_no_existe")

    def test_con_construccion(self, valor_service):
        with pytest.raises(UnsupportedParcelError):
            valor_service.predict("p_con_construccion")

    def test_area_cero(self, valor_service):
        with pytest.raises(UnsupportedParcelError):
            valor_service.predict("p_area_cero")

    def test_faltante_critico(self, valor_service):
        with pytest.raises(OutOfDomainError):
            valor_service.predict("p_faltante")

    def test_fuera_de_rango(self, valor_service):
        with pytest.raises(OutOfDomainError):
            valor_service.predict("p_fuera_rango")

    def test_categoria_no_vista(self, valor_service):
        with pytest.raises(OutOfDomainError):
            valor_service.predict("p_categoria_nueva")

    def test_sin_fuga_de_identificadores(self, valor_service):
        respuesta = valor_service.predict("p_valido")
        claves = json.dumps(respuesta, ensure_ascii=False)
        assert "numero_predial" not in claves
        assert "valor_avaluo" not in claves
        assert "parcel_source_id" not in claves
        assert respuesta["public_id"] == "p_valido"

    def test_referencia_zhg_diferenciada(self, valor_service):
        con_ref = valor_service.predict("p_valido")
        assert con_ref["reference_zhg_cop_ha"] == 500_000.0
        assert con_ref["reference_zhg_note"] is not None
        assert con_ref["absolute_difference_vs_zhg_cop_ha"] is not None
        sin_ref = valor_service.predict("p_sin_referencia")
        assert sin_ref["reference_zhg_cop_ha"] is None


class TestApi:
    def _client(self, mini_db, valor_artifact, habilitado: bool):
        settings = Settings(
            database_path=mini_db,
            model_dir=valor_artifact,
            valor_v1_enabled=habilitado,
        )
        return TestClient(create_app(settings))

    def test_503_cuando_flag_apagado(self, mini_db, valor_artifact):
        with self._client(mini_db, valor_artifact, habilitado=False) as client:
            res = client.post(
                "/api/v1/predictions/valor-terreno-v1",
                json={"public_id": "p_valido"},
            )
            assert res.status_code == 503
            assert res.json()["error"]["code"] == "VALOR_V1_DISABLED"

    def test_200_para_predio_admitido(self, mini_db, valor_artifact):
        # Se agrega el public_id del predio "A" del mini_db al artefacto con
        # features validas para probar el flujo completo (DB -> features ->
        # model.predict()).
        art = valor_artifact / "exp-valor-v1"
        features = json.loads((art / "features.json").read_text(encoding="utf-8"))
        pid_a = public_id_for("A")
        features[pid_a] = features["p_valido"].copy()
        (art / "features.json").write_text(json.dumps(features), encoding="utf-8")

        with self._client(mini_db, valor_artifact, habilitado=True) as client:
            res = client.post(
                "/api/v1/predictions/valor-terreno-v1",
                json={"public_id": pid_a},
            )
            assert res.status_code == 200
            body = res.json()
            assert body["model_id"] == "atlas-vivo-rf-v1"
            assert body["predicted_cop_ha"] > 0
            assert "numero_predial" not in json.dumps(body)

    def test_404_para_predio_inexistente_en_db(self, mini_db, valor_artifact):
        with self._client(mini_db, valor_artifact, habilitado=True) as client:
            res = client.post(
                "/api/v1/predictions/valor-terreno-v1",
                json={"public_id": "p_zzzzzzzzzzzzzzzz"},
            )
            assert res.status_code == 404

    def test_status_incluye_valor_v1(self, mini_db, valor_artifact):
        with self._client(mini_db, valor_artifact, habilitado=False) as client:
            res = client.get("/api/v1/system/status")
            assert res.status_code == 200
            valor_v1 = res.json()["valor_v1"]
            assert valor_v1["habilitado"] is False
            assert valor_v1["disponible"] is False

    def test_oficial_sigue_bloqueado(self, mini_db, valor_artifact):
        with self._client(mini_db, valor_artifact, habilitado=True) as client:
            res = client.post("/api/v1/predictions", json={"features": {}})
            assert res.status_code == 503
            assert res.json()["error"]["code"] == "MODEL_NOT_READY"
