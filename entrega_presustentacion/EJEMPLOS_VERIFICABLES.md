# Ejemplos verificables (respuestas reales del sistema)

Todos los ejemplos se generaron con el backend local cargando el artefacto
`deploy-model/exp-valor-v1` (`VALOR_V1_ENABLED=true`, base de datos real
`data/parcels.db`). No son simulaciones: provienen de `model.predict()`.

## Ejemplo 1 — Predio admitido (escenario A)

Consulta: `POST /api/v1/predictions/valor-terreno-v1`
```json
{"public_id": "p_6049c425ce3cf79d"}
```

Respuesta (resumen; el JSON completo está en
`evidencias/respuesta_api_ejemplo.json`):

| Campo | Valor |
|---|---|
| model_id | atlas-vivo-rf-v1 |
| model_version | 1.0.0 |
| predicted_cop_ha | **198.093,45** |
| reference_zhg_cop_ha | **182.414,3** (dato, zona 10) |
| absolute_difference_vs_zhg_cop_ha | 15.679,15 |
| relative_difference_vs_zhg_pct | 8,6 % |
| applicability_status | admitted |

## Ejemplo 2 — Funcionalidad desactivada (estado por defecto)

```json
{"error": {"code": "VALOR_V1_DISABLED", "status": 503,
 "message": "La demostración académica del modelo RF v1 está desactivada en este entorno",
 "details": {"config": "VALOR_V1_ENABLED=false"}}}
```

## Ejemplo 3 — Predio no admitido (con construcción registrada)

```json
{"error": {"code": "UNSUPPORTED_PARCEL", "status": 422,
 "details": {"razon": "el predio registra construcción; la demostración solo admite el escenario A (construcción = 0)"}}}
```

## Ejemplo 4 — Predio inexistente

```json
{"error": {"code": "PROPERTY_NOT_FOUND", "status": 404}}
```

## Cómo verificar en vivo

```bash
# 1) Backend local con el artefacto (desde la raíz del repo)
$env:VALOR_V1_ENABLED="true"; $env:MODEL_DIR="deploy-model"
$env:DATABASE_PATH="data/parcels.db"
cd backend; ..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000

# 2) Consumir el endpoint
curl -s -X POST http://127.0.0.1:8000/api/v1/predictions/valor-terreno-v1 ^
     -H "Content-Type: application/json" ^
     -d '{"public_id":"p_6049c425ce3cf79d"}'
```

Determinismo: repetir la consulta devuelve el mismo valor (verificado en las
pruebas automatizadas `backend/tests/test_valor_v1.py`).
