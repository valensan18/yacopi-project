"""Prueba de integracion con el ARTEFACTO REAL exp-valor-v1 (auditoria preproduccion).

Se ejecuta solo cuando el artefacto real esta presente en
deploy-model/exp-valor-v1 (transferencia local autorizada); en entornos sin
artefacto (CI) se omite con skip. No usa mocks: carga el pipeline real y
verifica la prediccion conocida del ejemplo documentado.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.services.valor_v1 import ValorV1Service

ROOT = Path(__file__).resolve().parents[2]
ARTEFACTO = ROOT / "deploy-model" / "exp-valor-v1"

pytestmark = pytest.mark.skipif(
    not (ARTEFACTO / "model.joblib").exists(),
    reason="artefacto real exp-valor-v1 no disponible en este entorno",
)


@pytest.fixture(scope="module")
def servicio_real():
    service = ValorV1Service(ARTEFACTO.parent)
    service.load()
    return service


class TestArtefactoReal:
    def test_carga_real(self, servicio_real):
        assert servicio_real.available()
        info = servicio_real.info()
        assert info["model_id"] == "atlas-vivo-rf-v1"
        assert info["model_version"] == "1.0.0"

    def test_inferencia_real_ejemplo_documentado(self, servicio_real):
        respuesta = servicio_real.predict("p_6049c425ce3cf79d")
        assert respuesta["predicted_cop_ha"] == pytest.approx(198093.45, abs=0.01)
        assert respuesta["reference_zhg_cop_ha"] == pytest.approx(182414.3, abs=0.01)
        assert respuesta["applicability_status"] == "admitted"

    def test_determinismo_real(self, servicio_real):
        a = servicio_real.predict("p_6049c425ce3cf79d")["predicted_cop_ha"]
        b = servicio_real.predict("p_6049c425ce3cf79d")["predicted_cop_ha"]
        assert a == b

    def test_manifiesto_y_metricas_separadas(self, servicio_real):
        respuesta = servicio_real.predict("p_6049c425ce3cf79d")
        contexto = respuesta["evaluation_context"]
        assert "estabilidad_5_pliegues_espaciales" in contexto
        assert contexto["estabilidad_5_pliegues_espaciales"]["rf_gana_mae_en"] == 0
        assert respuesta["reference_zhg_note"] is not None

    def test_sin_fuga_en_respuesta_real(self, servicio_real):
        respuesta = servicio_real.predict("p_6049c425ce3cf79d")
        texto = json.dumps(respuesta, ensure_ascii=False)
        for prohibido in ["numero_predial", "valor_avaluo", "parcel_source_id"]:
            assert prohibido not in texto
