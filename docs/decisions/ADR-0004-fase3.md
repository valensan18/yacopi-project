# ADR-0004 — Arquitectura del backend y política de inferencia (Fase 3)

- **Fecha:** 2026-10-14
- **Estado:** Aceptado

## Contexto

La API debía servir consultas/estadísticas/mapas reales y mantener bloqueada
la predicción oficial mientras no exista etiqueta validada, ofreciendo además
un canal experimental controlado para el proxy de Fase 2.

## Decisiones

1. **Doble canal de predicción, separados por contrato:**
   - `POST /api/v1/predictions` (oficial): responde **503 MODEL_NOT_READY**
     siempre que `label_contract.yaml` siga en `pending_verification`
     (verificado por prueba).
   - `POST /api/v1/predictions/experimental`: inferencia del artefacto
     `exp-proxy-001`, **desactivada por defecto** con
     `EXPERIMENTAL_INFERENCE_ENABLED=false`; solo en desarrollo local.
     Cada respuesta declara `is_experimental: true`,
     `predicts_land_value: false` y un disclaimer de proxy (no suelo, no
     avalúo). Resuelve el pendiente #13 con la opción conservadora: 503
     global en producción y canal local opt-in.
2. **Carga única del artefacto en lifespan** (nunca por petición ni
   reentrenamiento). Verificación de procedencia: `model.joblib` +
   `feature_schema.json` + `training_manifest.json` (modo `research-proxy`)
   + `metrics.json`; sin verificación → `EXPERIMENTAL_MODEL_UNAVAILABLE`.
3. **`public_id` opaco** en toda la API; `parcel_source_id` nunca sale de la
   base. Las referencias económicas (`parcel_value_references`) tampoco se
   exponen en `/properties` (consulta pública mínima).
4. **Validación en la firma Pydantic** (422 normalizado `INVALID_INPUT`),
   errores únicos con `{error:{code,message,details,request_id}}`,
   paginación con límite máximo (100), orden con lista blanca, filtros y
   bbox acotados, SQL parametrizada, CORS restrictivo.
5. **SQLite abierto en modo read-only** por la API; la escritura ocurre
   offline (`scripts/build_db.py`).
6. **Backend desacoplado de `yacopi_ml`:** el predictor experimental lee
   `feature_schema.json` del artefacto como fuente de verdad (orden, tipos,
   unidades); no importa el paquete ML.

## Alternativas rechazadas

- Exponer inferencia experimental siempre activa: riesgo de uso indebido
  fuera del entorno académico local.
- Copiar identificadores prediales en respuestas: rechazado por privacidad.
- Calcular estadísticas en el cliente o en CSV por petición: rechazado
  (SQLite indexada, lecturas <10 ms medidas).

## Riesgos

- Si el artefacto cambia de esquema, el backend lo declara no disponible y
  reporta causa (no reconstruye features).
- El canal experimental depende de que el director apruebe su uso (pendiente
  #12) y nunca se habilitará en despliegue público sin decisión explícita.

## Pruebas asociadas

- `backend/tests/test_api.py` (27 pruebas) y benchmark
  `scripts/benchmark_api.py` (mediciones reales p50/p95/p99).
