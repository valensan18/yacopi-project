# Fase 7B — Demostración experimental de ML (implementación)

Fecha: 2026-10-14 · Rama dev · **Desactivada por defecto** ·
`POST /api/v1/predictions` sigue en **503 MODEL_NOT_READY**.

## 1. Arquitectura de la demostración

```
yacopi_ml.zhg.export_demo.py  →  artefacto exp-zhg-001-demo (offline)
backend.services.demo          →  carga verificada UNA vez + guards + inferencia
POST /api/v1/predictions/experimental-zhg  →  desactivado por defecto
React /prediccion              →  sección "Demostración experimental" (flag off/on)
```

## 2. Modelo utilizado y procedencia del artefacto

- **Random Forest** (sklearn Pipeline + ColumnTransformer), objetivo
  `valor_zona_dominante_cop_ha` (COP/ha).
- **Procedencia:** no existía artefacto serializado de Fase 5 (solo
  `metrics.json`). Los hiperparámetros no se persistieron, así que se
  recuperaron re-ejecutando **la misma búsqueda determinística** de Fase 5
  (seed 42, GroupKFold(5) por predio, 8 iteraciones, mismas distribuciones)
  sobre las particiones congeladas actuales: `max_depth=30,
  min_samples_leaf=1, n_estimators=513`.
- **Hallazgo de integridad documentado (sin alterar Fase 5):** los archivos
  de particiones congeladas fueron regenerados por corridas posteriores
  (experimento ponderado y pruebas); sus hashes difieren de los del
  manifiesto histórico de Fase 5. La métrica histórica (MAE predio 73.765
  COP/ha) no se reproduce con las particiones actuales (56.131 COP/ha).
  **Las métricas de Fase 5 quedan intactas como evidencia histórica; este
  artefacto NO es el modelo evaluado en Fase 5** y no tiene evaluación
  independiente propia.
- Ajuste final: un único fit determinístico sobre los 7.709 predios con
  zona conocida; verificado con round-trip de serialización.

## 3. Dataset de origen

`01_intersecciones_normalizadas.csv` + `02_zhf_normalizadas.csv` (data
procesada de Fase 1, sin cambios). 7.709 predios, objetivo con 11 valores
zonales.

## 4. Construcción del artefacto

`python -m yacopi_ml.zhg.export_demo` genera, en `ml/artifacts/exp-zhg-001-demo/`:
`model.joblib`, `feature_schema.json`, `training_stats.json`,
`split_membership.json` (ids opacos), `features.json` (ids opacos) y
`manifest.json` (algoritmo, hiperparámetros, semilla, versiones, notas de
validación e integridad). Reproductible y trazable.

## 5. Características predictoras

Las **19 de la Fase 5** (5 numéricas: 3 áreas + coordenadas reales del
predio; 14 categóricas ZHF/UPS/CLC). La inferencia NO recibe features del
cliente: el backend las deriva del artefacto (construidas con el
preprocesamiento exacto del entrenamiento). Sin valores ZHG como
predictoras, sin identificadores de zona, sin estadísticos zonales.

## 6. Contrato de inferencia

`POST /api/v1/predictions/experimental-zhg` con `{"public_id": "p_…"}`.

Respuesta 200 (fragmento):
```json
{
  "public_id": "p_…",
  "model_id": "exp-zhg-001-demo",
  "model_status": "experimental",
  "unit": "COP/ha",
  "reference_zhg_cop_ha": 456041.7,
  "predicted_zhg_cop_ha": 452000.0,
  "absolute_difference_cop_ha": -4041.7,
  "relative_difference_pct": -0.89,
  "zone_code": "07",
  "domain_status": "in_domain",
  "reference_date": null,
  "limitations": ["…"],
  "evaluation_context": {"split_membership": {"predio": "train"}, "nota": "…"},
  "disclaimer": "Demostración experimental…"
}
```

## 7. Controles del dominio

- Predio existente (404 `PROPERTY_NOT_FOUND`).
- Características compatibles (422 `UNSUPPORTED_PARCEL`).
- **Monozona** obligatorio en esta versión (422 `UNSUPPORTED_MULTIZONE`).
- Referencia ZHG positiva para comparar (422 `UNSUPPORTED_PARCEL`).
- Numéricas dentro de [min, max] del entrenamiento y categorías vistas
  (422 `OUT_OF_DOMAIN`, con campos detallados).
- Predicción finita y > 0; si no, `OUT_OF_DOMAIN` (regla técnica explícita:
  no se emite un valor no físico).
- Flag `EXPERIMENTAL_ZHG_ENABLED=false` → 503 `EXPERIMENTAL_ZHG_DISABLED`.
- Sin artefacto → 503 `EXPERIMENTAL_ZHG_UNAVAILABLE`.
- Nunca se revelan identificadores privados: todo opera con `public_id`
  opaco (la correspondencia interna vive en el artefacto local).

## 8. Endpoints

| Endpoint | Estado |
|---|---|
| `POST /predictions` (oficial) | **503 MODEL_NOT_READY** (intacto) |
| `POST /predictions/experimental-zhg` | implementado, desactivado por defecto |
| `GET /system/status` | añade `experimental_zhg: {habilitado, disponible, model_id}` (aditivo) |

## 9. Comportamiento del frontend

`/prediccion` conserva los tres bloques (referencia ZHG / predicción ML /
avalúo no emitido). Dentro del bloque ML: sección **"Demostración
experimental (zonas conocidas)"**:
- flag apagado → explicación clara, sin controles que prometan predicción;
- flag activo → entrada de `public_id`, resultado con referencia ZHG,
  estimación, diferencia absoluta y relativa, zona, dominio, versión del
  modelo, limitaciones y el disclaimer obligatorio.

## 10. Evidencia de pruebas

- Backend: **48 pruebas** (11 nuevas de la demostración: deshabilitada por
  defecto, monozona exitoso con diferencias correctas, 404, sin features,
  multizona rechazado, fuera de dominio numérico/categórico, sin referencia
  positiva, sin artefacto, 503 oficial intacto, sin IDs privados).
- Frontend: **19 pruebas vitest** (demo desactivada sin botón falso; demo
  activa con resultado completo). `ruff`/`oxlint` limpios; build TS+Vite OK.
- Playwright (escritorio 1440×900 y móvil 390×844, estado por defecto):
  7/7 comprobaciones, 0 errores de consola. Capturas en `docs/capturas/`.
- Suite total: **88 pytest + 19 vitest**.

## 11. Métricas históricas y sus limitaciones

MAE predio 73.765 · espacial 132.183 · zonas fuera 423.363 COP/ha
(Fase 5): **históricas**; pertenecen al modelo evaluado con las particiones
congeladas de Fase 5 y NO evalúan este artefacto. Ninguna de ellas se
presenta como precisión esperada ni como intervalo de confianza individual.

## 12. Diferencia entre referencia conocida y predicción ML

La referencia ZHG es un **dato consultable** (Fase 6B); la estimación ML es
una **demostración experimental** que se muestra siempre junto a la
referencia y su diferencia, y no la reemplaza. Una predicción sobre un
predio del entrenamiento no demuestra generalización (se informa la
pertenencia a particiones históricas sin identificadores privados).

## 13. Restricciones para promover el modelo a producción

Requiere: autorización expresa, etiqueta verificada (`label_contract.yaml`),
evaluación independiente con datos nuevos (no reparticiones de los mismos
datos) y revisión de criterios. Nada de esto ocurre en esta fase.
