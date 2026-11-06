"""Pruebas del filtro de predios elegibles para la estimación RF v1.

- Elegibilidad calculada en el backend desde el inventario del artefacto
  aplicando las validaciones de dominio (construcción = 0, área positiva,
  rangos numéricos y categorías del entrenamiento).
- El filtro se aplica ANTES de paginación, búsqueda y conteo.
- Con el flag desactivado, la consulta responde 503 (sin listados falsos).
"""

import json

import pytest
from app.core.config import Settings
from app.main import create_app
from app.services.valor_v1 import ValorV1Service
from fastapi.testclient import TestClient

from backend.tests.test_valor_v1 import build_mini_valor_v1
from scripts.build_db import public_id_for  # type: ignore

ID_A = public_id_for("A")
ID_E = public_id_for("E")


@pytest.fixture
def valor_artifact(tmp_path):
    build_mini_valor_v1(tmp_path)
    # Agregar al inventario los predios A y E del mini_db con features validas.
    art = tmp_path / "exp-valor-v1"
    features = json.loads((art / "features.json").read_text(encoding="utf-8"))
    for pid in (ID_A, ID_E):
        features[pid] = features["p_valido"].copy()
    (art / "features.json").write_text(json.dumps(features), encoding="utf-8")
    return tmp_path


@pytest.fixture
def service(valor_artifact):
    s = ValorV1Service(valor_artifact)
    s.load()
    return s


def _client(mini_db, valor_artifact, habilitado: bool):
    settings = Settings(
        database_path=mini_db,
        model_dir=valor_artifact,
        valor_v1_enabled=habilitado,
    )
    return TestClient(create_app(settings))


class TestElegibilidad:
    def test_conteo_real_de_admitidos(self, service):
        admitidos = service.admitidos()
        # 42 p_fixture_* + p_valido + p_sin_referencia + A + E = 46
        assert len(admitidos) == 46
        for excluido in (
            "p_con_construccion", "p_area_cero", "p_faltante",
            "p_fuera_rango", "p_categoria_nueva",
        ):
            assert excluido not in admitidos
        assert "p_valido" in admitidos
        assert "p_sin_referencia" in admitidos
        assert ID_A in admitidos and ID_E in admitidos

    def test_info_incluye_conteo(self, service):
        assert service.info()["predios_admitidos"] == 46


class TestFiltroApi:
    def test_503_cuando_flag_apagado(self, mini_db, valor_artifact):
        with _client(mini_db, valor_artifact, habilitado=False) as client:
            res = client.get("/api/v1/properties?solo_estimables=true")
            assert res.status_code == 503
            assert res.json()["error"]["code"] == "VALOR_V1_DISABLED"

    def test_listado_solo_elegibles_con_total_correcto(self, mini_db, valor_artifact):
        with _client(mini_db, valor_artifact, habilitado=True) as client:
            res = client.get("/api/v1/properties?solo_estimables=true")
            assert res.status_code == 200
            body = res.json()
            ids = {item["public_id"] for item in body["items"]}
            assert ids == {ID_A, ID_E}
            assert body["pagination"]["total"] == 2

    def test_busqueda_dentro_de_elegibles(self, mini_db, valor_artifact):
        with _client(mini_db, valor_artifact, habilitado=True) as client:
            res = client.get(
                "/api/v1/properties?solo_estimables=true"
                f"&public_id_prefix={ID_A[:10]}"
            )
            assert res.status_code == 200
            body = res.json()
            assert [i["public_id"] for i in body["items"]] == [ID_A]
            assert body["pagination"]["total"] == 1

    def test_paginacion_sobre_elegibles(self, mini_db, valor_artifact):
        with _client(mini_db, valor_artifact, habilitado=True) as client:
            res = client.get(
                "/api/v1/properties?solo_estimables=true&limit=1&offset=0"
            )
            assert res.status_code == 200
            body = res.json()
            assert body["pagination"]["total"] == 2
            assert len(body["items"]) == 1

    def test_sin_filtro_sigue_devolviendo_todos(self, mini_db, valor_artifact):
        with _client(mini_db, valor_artifact, habilitado=True) as client:
            res = client.get("/api/v1/properties")
            assert res.status_code == 200
            assert res.json()["pagination"]["total"] == 5

    def test_no_expone_features_del_artefacto(self, mini_db, valor_artifact):
        with _client(mini_db, valor_artifact, habilitado=True) as client:
            res = client.get("/api/v1/properties?solo_estimables=true")
            texto = json.dumps(res.json(), ensure_ascii=False)
            assert "valor_avaluo" not in texto
            assert "clc_nivel" not in texto
            assert "fa_element" not in texto
            assert "reference_zhg" not in texto
