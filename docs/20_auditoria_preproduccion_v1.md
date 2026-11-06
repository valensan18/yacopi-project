# Doc 20 — Auditoría final preproducción del modelo RF v1 (demostración académica)

**Fecha:** 2026-11-06 · **Rama:** `feature/valor-modelo-v1` (commit `406b94e`)
**Resultado global:** GO condicionado — sin riesgos bloqueantes; la
activación pública queda pendiente de autorización (flag off por defecto).

## 1. Pertenencia al ajuste final (inferencia vs evaluación)

Verificación ejecutada (`scripts/verificar_artefacto_v1.py`): los **4.676
public_id** de `features.json` coinciden **exactamente** con la cohorte del
ajuste final del escenario A (`coincidencia_total: true`; 0 sobrantes, 0
faltantes). Por lo tanto **toda consulta del inventario es una inferencia
sobre un predio que participó en el ajuste final** y NO constituye una
evaluación independiente. Esto se declara en cada respuesta
(`evaluation_context.nota`) y en el manifiesto
(`nota_ajuste_final`). Las únicas métricas válidas son las de
`metrics_evaluacion.json` (test sellado v2 + 5 pliegues de estabilidad),
generadas ANTES del ajuste final.

## 2. Los artefactos no son descargables por rutas públicas

| Vía | Estado | Evidencia |
|---|---|---|
| FastAPI (StaticFiles/FileResponse/mount) | **0 usos** | grep en `backend/app/**` |
| Nginx interno | sin `alias` ni rutas a `/app/model` | `deploy/nginx-app.conf` solo tiene SPA fallback + proxy `/api` |
| Imagen backend | copia únicamente `backend/app` y lockfile | `backend/Dockerfile` (2 COPY) |
| Imagen frontend | solo `/app/dist`; sin `*.ipynb`, `parcels.db`, `*.joblib` en la imagen | inspección `docker run … find /` → `SIN_ARTEFACTOS_EN_IMAGEN` |
| Contexto de build | `deploy-model` y `ml/artifacts` excluidos | `.dockerignore` |

`features.json` vive SOLO en `deploy-model/` (montaje read-only en
`/app/model` del contenedor backend, sin puertos publicados).

## 3. Hashes, versiones, esquema y correspondencia

- Hashes SHA-256 registrados (verificar_artefacto_v1.py):
  `model.joblib` = `4bc3905b…8fd2b`, `features.json` = `c37812c3…3ec533`,
  `manifest.json` = `ddfe67d3…d0311`, `feature_schema.json` =
  `6eae3d00…9e303d`, `training_stats.json` = `3ec52f57…274e3`,
  `metrics_evaluacion.json` = `88598cf1…82f54`.
- Manifiesto ↔ backend: `model_id=atlas-vivo-rf-v1`,
  `model_version=1.0.0`, `rol=demostracion_academica`,
  `status=experimental_demo` (exactamente lo que valida
  `ValorV1Service.load()`), `n_fit=4676`, `seed=20261023`, hiperparámetros
  400/18/3.
- Esquema de entrada: `orden` (19 columnas), `numericas` (4) y
  `categoricas` (15) coinciden con las usadas por el servicio para armar el
  frame de inferencia.
- Dependencias en manifiesto: python 3.14, scikit-learn 1.9.1, pandas 3.0.6
  (iguales a `backend/requirements.lock.txt`).

## 4. Privacidad de features.json y de las respuestas

- Claves: todas `p_` + 16 hex (public_id opaco); **0** claves extra fuera
  del esquema; **0** campos sensibles (`numero_predial`,
  `valor_avaluo`, matrícula, ORIP) en todo el archivo (3,15 MB).
- Respuestas: sin identificadores privados ni avalúos (verificado por
  prueba automatizada `test_sin_fuga_en_respuesta_real` y por grep de la
  respuesta real).

## 5. API en ambos estados (evidencia capturada)

- **OFF** (`VALOR_V1_ENABLED=false`): `503 VALOR_V1_DISABLED`
  (evidencia en `entrega_presustentacion/evidencias/` y salida de la prueba
  de contenedor).
- **ON**: inferencia real `p_6049c425ce3cf79d` → 198.093,45 COP/ha,
  referencia ZHG 182.414,3 (dato separado), `applicability_status=admitted`,
  determinista (2 llamadas idénticas), predio inexistente → 404.
- Oficial sigue `503 MODEL_NOT_READY`; demo ZHG `503`; health `200`.

## 6. Pruebas de integración con el artefacto REAL

Nueva suite `backend/tests/test_valor_v1_real.py` (5 pruebas) que carga
`deploy-model/exp-valor-v1` real (skip automático si el artefacto no está
presente, p. ej. en CI): carga, inferencia del ejemplo documentado
(198.093,45), determinismo, separación de métricas y ausencia de fuga.
El resto de pruebas usa un artefacto fixture mínimo construido con
scikit-learn real (Pipeline + RandomForest), no mocks de `predict()`.

### Conteo de pruebas (aclaración del punto 11)

| Suite | Antes (dev) | Rama experimental | Rama integración (este trabajo) |
|---|---|---|---|
| ml/tests | 44 | 52 (+8 `test_valor_splits`, SOLO en experimental) | 44 |
| backend/tests | 52 | 52 | 74 (+17 `test_valor_v1` + 5 `test_valor_v1_real`) |
| **Total pytest** | **96** | **104** | **118** |
| Frontend vitest | 33 | 33 | 35 (+2 valor-v1) |

Los "104" corresponden a la rama experimental (incluye los 8 de
particiones); los "113" correspondían a la integración antes de la suite
real (96 + 17); ahora son **118** con las 5 pruebas del artefacto real.
Nada se reemplazó ni excluyó: los 8 de particiones viven en la rama
experimental y no aplican al servicio de integración.

## 7. Referencia ZHG siempre diferenciada

Campos dedicados: `reference_zhg_cop_ha` + `reference_zhg_note`
("Referencia geoeconómica ZHG consultada de los datos (dato territorial,
NO es una predicción del modelo)") + `absolute_difference_vs_zhg_cop_ha` /
`relative_difference_vs_zhg_pct`. La interfaz muestra "A. Referencia ZHG
(dato consultado)" y "B. Estimación Random Forest" por separado. Pruebas
frontend y backend lo verifican.

## 8. Métricas no atribuidas al ajuste final

`evaluation_context.nota`: "metricas de validacion INDEPENDIENTES del
ajuste final; el artefacto se entreno despues sobre los 4.676 predios".
El manifiesto repite la advertencia. La interfaz la muestra en
"Condiciones de aplicación y métricas de validación reales".

## 9. Revisión de la interfaz

Se revisaron los textos de `/prediccion`. **No se eliminó ningún aviso**: el
etiquetado actual ("funcionalidad experimental no habilitada oficialmente",
"Predicción oficial: no disponible", "Atlas Vivo no expide avalúos") sigue
siendo cierto con la demostración activa (el oficial continúa 503 y la demo
es experimental). Se añadió la sección nueva con su propio alcance,
métricas y limitaciones, sin suavizar la derrota frente a ZHG (visible:
"ganó en MAE 0/5 y en MdAPE 0/5").

## 10. Docker, Compose, montajes, entorno, health, límites y rollback

- `compose.yaml`: `VALOR_V1_ENABLED: "${VALOR_V1_ENABLED:-false}"`
  (desactivado por defecto; control por `.env`), `MODEL_DIR=/app/model` con
  `deploy-model:/app/model:ro`, backend sin puertos publicados.
- Healthchecks: definidos en ambos Dockerfiles; verificados `healthy` en la
  prueba aislada.
- Límites de API: se conservan los existentes (paginación, `max_map_points`);
  **recomendación no bloqueante**: añadir `limit_req` en el Nginx del host
  para el nuevo endpoint cuando se active.
- Rollback: `docs/19_despliegue_modelo_v1.md` (por imagen, por flag y por
  Git).

## 11. Prueba de despliegue aislado (configuración de producción)

Ejecutada con Docker Compose local (imágenes construidas desde la rama,
`.env` de producción, montajes reales `deploy-data`/`deploy-model`):

| Verificación | Resultado |
|---|---|
| `docker compose config -q` | válido |
| Ambos contenedores | healthy |
| Flag OFF → endpoint v1 | 503 VALOR_V1_DISABLED |
| Flag ON (vía `${VALOR_V1_ENABLED}`) | 200, pred 198.093,45 / ZHG 182.414,3 |
| Oficial / demo | 503 / 503 |
| Frontend compilado | contiene la sección "Estimación con Machine Learning" |
| Imágenes | sin notebooks, DB ni artefactos |

## 12. Matriz GO / NO-GO

| # | Criterio | Estado | Evidencia |
|---|---|---|---|
| 1 | Artefacto íntegro y correspondiente (hashes, manifiesto, esquema) | GO | verificar_artefacto_v1.py |
| 2 | Cohortes: 4.676 ids = ajuste final; inferencia ≠ evaluación | GO (declarado) | §1 |
| 3 | Sin fuga de privados en artefacto/respuestas | GO | §4 + pruebas |
| 4 | Artefactos no descargables por rutas públicas | GO | §2 |
| 5 | API OFF/ON correcta; oficial 503; demo off | GO | §5, §11 |
| 6 | Pruebas con artefacto real + suites completas (118 pytest, 35 vitest) | GO | §6 |
| 7 | ZHG diferenciada de la predicción | GO | §7 + pruebas |
| 8 | Métricas independientes no atribuidas al ajuste final | GO | §8 |
| 9 | Interfaz honesta, sin avisos falsos | GO | §9 |
| 10 | Despliegue aislado con configuración de producción | GO | §11 |
| 11 | Desempeño limitado comunicado (0/5 vs ZHG) | GO (transparencia) | metrics_evaluacion.json |
| 12 | Límites de tasa específicos del endpoint | NO BLOQUEANTE (recomendación) | §10 |
| 13 | Aprobación institucional para activar | **PENDIENTE (decisión humana)** | — |

**Veredicto: GO condicionado** — sin riesgos bloqueantes técnicos; la
activación pública requiere (a) revisar este informe y (b) ejecutar los
pasos de `docs/19` (transferir artefacto, verificar hashes, activar
`VALOR_V1_ENABLED=true` y aplicar la recomendación de rate limiting).

## Pasos exactos (resumen operativo)

Desplegar: `docs/19` §1 · Activar: `docs/19` §2 · Revertir: `docs/19` §3.
Hashtags de verificación del artefacto en §3 de este documento.
