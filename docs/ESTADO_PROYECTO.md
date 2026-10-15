# ESTADO_PROYECTO — Yacopí Predictor

Registro cronológico de avance, decisiones, errores y pendientes.
Formato: una sección por fase. No se declara completada una fase sin ejecutar
su criterio de aceptación.

Última actualización: 2026-10-14

---

## FASE 0 — Inicialización del repositorio y entorno (COMPLETADA 2026-10-14)

### Decisiones tomadas

- Repositorio local en `C:\Users\DIEGHOST\Documents\yacopi-project`; remoto
  privado `git@github-valensan18:valensan18/yacopi-project.git` (cuenta
  `valensan18`). Ver ADR-0001.
- Rama de trabajo: `dev`; el remoto traía un commit inicial en `main`
  (README autogenerado) y `dev` se basó sobre él (`reset --hard origin/main`
  local, sin force push al remoto).
- Identidad de autor SOLO local: `valensan18` /
  `342352447+valensan18@users.noreply.github.com` (derivada del ID público de
  la API de GitHub, formato oficial noreply). La configuración global de Git
  (`DIEGHOST64`) permanece intacta. Verificada en commit local.
- Clave SSH dedicada `~/.ssh/id_ed25519_valensan18` + alias
  `github-valensan18` en `~/.ssh/config` (nuevo; no existía config previo).
  La clave personal `id_ed25519` no se modificó. `ssh -T` OK.
- **Python 3.14.4 aprobado**: se instaló en `.venv` y se verificó
  importación y ejecución real de pandas 3.0.6, numpy 2.5.4, geopandas 1.2.0,
  shapely 2.2.0, pyproj 3.8.0, scikit-learn 1.9.1, catboost 1.2.10, fastapi
  0.143.0, pydantic 2.14.1. CatBoost entrena en CPU (smoke sintético) y
  Shapely lee el EWKB real del CSV (área consistente con el dato tabular).
  **No fue necesario el fallback Python 3.13** (descartado, sin instalar).
- Estrategia ML: **Ruta B** — todo el producto funciona en modo
  `ANALISIS_SIN_MODELO`; experimentos proxy con avalúo total/ha en rama
  experimental separada, jamás promovidos a modelo oficial de suelo sin
  etiqueta validada.
- VPS diferido: se entregará Docker Compose + Nginx + runbooks listos.
- Frontend: Vite 8 + React 19 + TS, react-router-dom 7, TanStack Query 5,
  leaflet 1.9 + react-leaflet 5, plotly.js 4 + react-plotly.js, vitest 5,
  oxlint (lint). ESLint/Prettier eliminados para no duplicar oxlint.

### Tareas completadas

- [x] Estructura de directorios según guía maestra §5.4.
- [x] `README.md`, `.gitignore`, `.editorconfig`, `.env.example`, `Makefile`,
      CI (`ci.yml`: ruff + pytest + build frontend).
- [x] `docs/ESTADO_PROYECTO.md`, `docs/pendientes.md`, `docs/decisions/` +
      ADR-0001; copia de la guía maestra a `docs/00_contexto_maestro.md`.
- [x] SSH dedicada + alias verificados (`ssh -T` → "Hi valensan18!").
- [x] `git init -b dev`, identidad local, `remote add origin` (URL exacta),
      base sobre `origin/main`.
- [x] CSV originales copiados a `data/raw/` con SHA-256 + `data_manifest.json`
      (originales del Desktop intactos).
- [x] Entorno Python 3.14 + verificación real de GeoPandas/CatBoost.
- [x] Frontend Vite React+TS + dependencias + lockfile + proxy `/api`.
- [x] Comprobaciones: `ruff check .` limpio; `pytest` 4 passed (backend +
      contrato de etiqueta); `oxlint` limpio; `vitest` 1 passed;
      `npm run build` OK.
- [x] Commit local en `dev` con autor verificado (`valensan18` + noreply).
      **Sin push** (pendiente autorización expresa).

### Errores / problemas encontrados

- `catboost_info/` (logs del smoke de CatBoost) se coló al staging inicial:
  corregido añadiéndolo a `.gitignore` y eliminándolo del índice/disco antes
  del commit.
- `gh auth login` indicado como completado por el usuario no persistió:
  `%APPDATA%\GitHub CLI\hosts.yml` no existe y `gh auth status` reporta sin
  sesión. **Pendiente** retomar el login para verificar privacidad y
  colaboradores por API. Mitigación parcial: la API pública devuelve 404 para
  el repo (comportamiento de repos privados) y `ssh -T` confirma acceso.
- El PDF de Jesús (`PROYECTO REALIZADO POR JESUS.pdf`) no tiene capa de
  texto; su contenido se usa vía resumen de la guía maestra §2. OCR solo si
  se requiere.
- Advertencia (no bloqueante): `starlette.testclient` sugiere migrar a
  `httpx2`; los tests actuales pasan con httpx 0.28.1. Revisar en Fase 3.

---

## FASE 1 — Validación final de datos y base SQLite (COMPLETADA 2026-10-14)

### Decisiones tomadas

- **Reutilización del pipeline heredado**: `scripts/preparar_datos.py` se copió
  sin modificaciones funcionales y se conserva byte-idéntico como referencia
  de reproducibilidad (excluido de ruff vía `pyproject.toml`, justificado en
  el propio archivo). Ver ADR-0002.
- **Reproducibilidad confirmada**: al ejecutarlo sobre `data/raw/` produce
  exactamente el diagnóstico de referencia (24 claves comparadas, 0
  diferencias): 7.709 predios consolidados, 7.694 coincidentes, 227
  solo-ZHF, 15 solo-intersecciones.
- **CRS verificado**: `geometria`/`geometria_interseccion` → SRID 9377;
  `geom` ZHF → SRID 3116 (100 % de las filas auditadas). Mapas exportados a
  EPSG:4326: 7.694 puntos referenciales y 7.968 polígonos simplificados
  (15 m), 0 inválidos.
- **SQLite** (`data/parcels.db`, no versionado): 7 tablas (parcels 7.709,
  parcel_features 7.709, parcel_value_references 46.224, quality_flags
  15.489, model_targets 0, zhf_only_parcels 227, dataset_meta 9).
  `public_id` opaco determinista (`p_` + SHA-256[:16] del numero_predial);
  los identificadores oficiales permanecen solo en la base local.
- **Allowlist/excluidas** actualizadas con cardinalidades y nulos reales en
  `ml/config/features.yaml`; diccionario completo en
  `docs/02_diccionario_datos.md`. La variable objetivo sigue
  `pending_verification`; estrategia Ruta B intacta.

### Tareas completadas

- [x] Pipeline heredado reproducido; conteos idénticos a la referencia.
- [x] `scripts/verify_inputs.py`: hashes SHA-256, tamaños, encabezados y
      conteos de los CSV originales (OK).
- [x] `scripts/audit_data.py`: reejecuta el pipeline, compara contra la
      referencia y calcula nulos, unicidad, rangos de coordenadas y banderas;
      escribe `08_validacion_fase1.json`.
- [x] `scripts/build_maps.py`: auditoría de SRID + GeoJSON Leaflet (puntos y
      polígonos WGS84).
- [x] `scripts/build_db.py`: construcción reproducible de SQLite.
- [x] `docs/02_diccionario_datos.md`: 49 columnas documentadas con origen,
      tipo, unidades, nulos, cardinalidad y rol.
- [x] 17 pruebas automatizadas (integridad, unicidad, coordenadas, SRID,
      DB, mapas, reproducibilidad doble corrida, verificación de entradas,
      contrato de etiqueta); `ruff` limpio.

### Hallazgos de validación (reales, sin eliminaciones)

- 15 predios sin coincidencia ZHF → sin coordenadas ni atributos ZHF/CLC.
- `fa_element` con 471 vacíos y `aht_vpoten` con 40 (fuera de los 15).
- `N/A` en CLC niveles 4–6 es categoría original (6.100–7.510 predios).
- 4.924 predios con diferencia >5 % entre área ZHF y área catastral;
  843 con zona ZHG discordante; ninguna fila eliminada (solo banderas).
- Coordenadas: 7.694 válidas, 0 fuera de rango Colombia.
- Deprecación `shapely.ops.transform` → migrado a `shapely.transform(...
  interleaved=False)` compatible con pyproj.

### Errores / problemas encontrados (ya resueltos)

- `shapely.transform` en modo intercalado es incompatible con la firma
  `transform(xx, yy)` de pyproj → corregido con `interleaved=False`.
- YAML de `features.yaml` corrompido por doble codificación al editarlo vía
  PowerShell → reescrito limpio; barrido global sin mojibake.

### Pendientes que permanecen

- Ver `docs/pendientes.md` (etiqueta, diccionario oficial, fechas, permisos).

---

## FASE 2 — Modelos: experimento proxy (Ruta B) (COMPLETADA 2026-10-14)

### Decisiones tomadas

- **Ruta B ejecutada como experimento separado**: etiqueta
  `proxy_avaluo_total_cop_ha` (COP/ha, avalúo total/área), contrato
  `label_contract_proxy.yaml` (`production_eligible: false`). El contrato
  principal sigue `pending_verification`; `--mode production` **rechaza** el
  entrenamiento (probado). Ver ADR-0003 y `docs/04_metodologia_ml.md`.
- Cohorte ML: 7.694 predios coincidentes; 19 variables (5 numéricas + 14
  categóricas con marcador `SIN_DATO`); `fa_element` excluido por cobertura.
- Particiones congeladas (seed 42): aleatoria por predio y espacial
  KMeans(25)+GroupShuffleSplit; tuning solo con GroupKFold(5) en train
  espacial; test sellado usado una vez.
- Modelos: Dummy(mediana), Ridge, Árbol, RandomForest, CatBoost.
  Seleccionado **RandomForest** por menor MAE en test espacial.

### Resultados reales (resumen; detalle en `docs/04_metodologia_ml.md`)

| Modelo | MAE espacial | R² espacial | MAE aleatorio | R² aleatorio |
|---|---:|---:|---:|---:|
| Dummy | 6.592.762 | −0,03 | 7.889.929 | −0,02 |
| Ridge | 15.196.282 | −0,11 | 13.581.815 | 0,40 |
| Árbol | 4.215.432 | 0,53 | 4.176.143 | 0,66 |
| **Forest** | **3.226.230** | **0,74** | **2.674.886** | **0,82** |
| CatBoost | 3.730.373 | 0,76 | 3.336.590 | 0,81 |

(COP/ha; test espacial n=1.353, aleatorio n=1.155)

- Hallazgos: validación espacial claramente más exigente que la aleatoria;
  Ridge colapsa (extrapolación lineal); el error se concentra en predios
  ≤5 ha y en destinos no agropecuarios; con construcción el MAE se
  multiplica ~7× → evidencia de que el proxy no es valor exclusivo de
  terreno. Importancia (permutación y SHAP) dominada por áreas — relación
  parcialmente mecánica con el denominador del proxy, declarada.
- Artefactos en `ml/artifacts/exp-proxy-001/` (LOCALES, no versionados):
  `model.joblib` (54 MB), `metrics.json`, `feature_schema.json`,
  `training_manifest.json`, `predictions_test.csv`, `MODEL_CARD.md`
  (EXPERIMENTAL) y 6 figuras reales.
- Reproducibilidad: 1 comando (`python -m yacopi_ml.train --mode
  research-proxy --output ml/artifacts/exp-proxy-001`); doble corrida smoke
  idéntica (prueba).

### Errores encontrados y resueltos

- `pd.NA` en categóricas rompía SimpleImputer y CatBoost → marcador
  `SIN_DATO` documentado.
- CatBoost no clonable en sklearn (cat_features) → `CatBoostWrapper`.
- SHAP fallaba sobre Pipeline → desenvuelve paso `model` y preprocesa la
  muestra (OHE) antes del explainer.
- Prueba de smoke mal indexada (claves ya resueltas del payload) → corregida.

### Pendientes que permanecen

- **Modelo de suelo oficial**: sigue bloqueado por etiqueta (pendientes #1–3).
- Decisión del director sobre el valor académico del experimento proxy y
  si autoriza experimentos adicionales (log(y), sin coordenadas, subset sin
  construcción) — pendiente #12.

---

## FASE 3 — Backend FastAPI (COMPLETADA 2026-10-14)

### Decisiones tomadas

- Arquitectura modular: `core` (config/errores), `db` (conexión read-only +
  repositorio), `schemas`, `routers` (7 módulos), `services` (predicción).
  Ver ADR-0004.
- Doble canal de predicción: oficial `POST /predictions` → **503
  MODEL_NOT_READY** (etiqueta pendiente); experimental
  `POST /predictions/experimental` → proxy RandomForest, desactivado por
  defecto (`EXPERIMENTAL_INFERENCE_ENABLED=false`), solo desarrollo local,
  con disclaimer explícito (no es suelo, no es avalúo). Pendiente #13
  resuelto con la opción conservadora.
- Artefacto cargado UNA vez en `lifespan` tras verificar procedencia
  (joblib + feature_schema + training_manifest research-proxy + metrics);
  nunca se reentrena por petición.
- `public_id` opaco en todas las respuestas; `parcel_source_id` y las
  referencias económicas no se exponen.
- Validación Pydantic en firma (422 `INVALID_INPUT` normalizado), errores
  `{error:{code,message,details,request_id}}`, paginación tope 100, sort con
  lista blanca, bbox acotado, SQL parametrizada, CORS restrictivo.

### Endpoints verificados con datos reales

`/health/live|ready`, `/system/status` (label_pending),
`/properties` (total 7.709; filtro Agropecuario 6.746),
`/properties/{public_id}` (+features y flags), `/statistics/overview`
(3.033 con construcción, 7.694 con coordenadas), `/statistics/distributions`,
`/maps/points` (GeoJSON EPSG:4326), `/models` (solo exp-proxy-001,
experimental), `/models/active`, `/predictions` (503), 
`/predictions/experimental` (200 con flag; predicción reproducible).

### Rendimiento medido (i7-9700 local, n=100, servidor con 1 worker)

| Endpoint | p50 | p95 | p99 |
|---|---:|---:|---:|
| health/live | 1,4 ms | 1,9 ms | 2,1 ms |
| system/status | 2,0 ms | 2,7 ms | 3,8 ms |
| properties (20) | 3,0 ms | 3,5 ms | 3,9 ms |
| properties filtradas | 5,2 ms | 5,8 ms | 5,9 ms |
| statistics/overview | 8,2 ms | 9,0 ms | 9,5 ms |
| maps/points (1.000) | 5,6 ms | 7,0 ms | 27,1 ms |
| predicción experimental (RF 349 árboles) | 59,2 ms | 68,7 ms | 70,9 ms |

0 errores en todas las series. Script reproducible: `scripts/benchmark_api.py`.

### Pruebas

58 pruebas totales pasan (27 nuevas de API con base sintética: paginación,
filtros, 422/404/503, GeoJSON, bloqueo oficial, experimental on/off,
reproducibilidad, categorías desconocidas, artefacto real); `ruff` limpio.

### Errores encontrados y resueltos

- Validación Pydantic dentro del handler no disparaba el manejador 422 →
  movida a la firma (`ExperimentalRequest.features: PredictionFeatures`).
- Las corridas smoke de las pruebas contaminaban `registry.json` real →
  los smoke ya no registran experimentos; registro depurado a
  `exp-proxy-001`.
- Health/ready simplificado (sin estados confusos).

---

## FASE 4 — Frontend ATLAS VIVO (COMPLETADA funcionalmente 2026-10-14)

### Decisiones tomadas

- Dirección visual aprobada por el usuario: **A — ATLAS VIVO (cartografía
  cinematográfica)** con acentos de B (densidad tabular GEO LAB en Predios)
  y C (ritmo editorial TERRITORIO en Metodología).
- Sistema de diseño formalizado en `docs/DESIGN_SYSTEM.md`: paleta mineral
  (verde profundo/cobre/marfil), Fraunces + Public Sans + JetBrains Mono,
  tokens de 3 capas (primitiva→semántica→componente), 8 px de espaciado.
- Skills de diseño del proyecto (`.opencode/skills/`) aplicadas: búsquedas
  de `ui-ux-pro-max` (design-system + dominios gsap/threejs/ux/landing)
  validaron la implementación (Points+BufferGeometry, fog, parallax solo
  decorativo, contraste AA, patrones de aterrizaje). Se descartó la paleta
  "Cyberpunk" sugerida genéricamente por no ajustarse a la dirección
  aprobada (la skill exige verificar pertinencia).
- Motores de animación: Lenis (solo Inicio) + GSAP/ScrollTrigger (scroll) +
  Motion (microinteracciones). 3D solo en Inicio (React Three Fiber,
  lazy). Leaflet y Plotly lazy por página. `prefers-reduced-motion` y
  fallback sin WebGL implementados.
- Banner de estado: compacto en escritorio; en móvil muestra resumen
  "Modelo predictivo pendiente de validación" + botón "Ver detalles"
  (aria-expanded, operable por teclado).

### Pantallas implementadas (rutas reales)

| Ruta | Contenido |
|---|---|
| `/` | Portada 3D + narrativa (aprobada, sin cambios de fondo) |
| `/predios` | Catálogo 7.709 predios: paginación real, filtros (destino, subzona, rangos de área), orden, búsqueda exacta por public_id, URL sincronizada, tabla GEO LAB |
| `/predios/:public_id` | Ficha: identificador, superficies, coordenadas, mini-mapa (si hay coords), atributos ZHF/CLC, banderas con etiquetas, nulos = "No disponible", sin avalúos |
| `/mapa` | Leaflet con capa canvas, bbox sincronizado con la API, leyenda por destino con mostrar/ocultar, popup → ficha, atribución CARTO/OSM, aviso "puntos, no polígonos" |
| `/exploracion` | Plotly: destino, subzona, histograma de áreas, donut de construcción, cobertura/calidad; títulos, unidades, origen y resumen accesible |
| `/modelos` | Estado oficial (label_pending), experimento proxy (métricas reales vía API), tabla documentada espacial vs aleatoria, avalúo total/ha vs suelo, advertencias |
| `/prediccion` | Bloqueo oficial con comprobación real (503), experimental desactivada por defecto con explicación; formulario tipado solo si el backend la habilita |
| `/metodologia` | Editorial CRISP-DM con línea de tiempo, fuentes, calidad, variables, evaluación espacial, limitaciones del proxy, validación pendiente |
| `/acerca-de` | Propósito, contexto académico (sin nombres), alcance, arquitectura, tecnologías, limitaciones |

### Verificación

- 10 pruebas frontend (vitest) pasan: portada, banner, fallback 2D,
  catálogo, detalle con nulos, modelos, predicción, metodología.
- `oxlint` limpio; `tsc -b && vite build` OK (3D lazy ≈242 kB gzip;
  Leaflet/Plotly en chunks separados).
- 8 rutas responden 200 con los servidores reales; proxy API verificado;
  POST oficial devuelve 503 real.
- Capturas en `docs/capturas/` (home desktop/móvil + 6 pantallas).
- Cartografía: CARTO Basemaps Dark Matter como mapa base con clave vía
  `VITE_CARTO_BASEMAPS_KEY` (frontend/.env.local, excluido de Git; la
  variable VITE_ es pública en el navegador y se recomiendan restricciones
  de dominio en el panel de CARTO). Sin clave → respaldo OpenStreetMap
  estándar sin marcas de agua. Verificado: tesela real de Yacopí responde
  200 image/png con el endpoint rastertiles oficial.
- Limitación documentada: la búsqueda de predios es por public_id exacto
  (el endpoint actual no filtra por prefijo; ampliación futura requiere
  cambio mínimo compatible del contrato, pendiente de autorización).

### Fase 4.1 — Pulido profesional del mapa (completada)

- Panel "Visualización": opacidad (15–100 %, inicial 70 %), tamaño
  (1,5–7 px, inicial 3,2 px) con ajuste adaptativo opcional según zoom,
  "Restablecer visualización" y "Ver todo el territorio" (fitBounds sobre
  los registros cargados). Valores en mono; sin refetch ni reconstrucción
  de marcadores al mover sliders (setStyle + rAF).
- Leyenda mejorada: categorías colapsables con conteos de la vista actual,
  mostrar/ocultar individual, "Mostrar todas"/"Ocultar todas".
- Contadores honestos: total del sistema vs registros con coordenadas vs
  cargados en la vista vs visibles tras filtro (definiciones visibles).
- Conservado: renderer canvas, consulta por bbox con micro-retardo,
  popups, CARTO Dark Matter + respaldo OSM, atribuciones.
- Verificación funcional con Playwright (script `frontend/scripts/verify-map.mjs`)
  contra los servidores reales: sliders aplican y resetean, zoom nativo
  funciona, leyenda colapsa y filtra, 62 teselas CARTO 200 (0 fallidas) en
  escritorio y 16 en móvil, 0 errores de consola. Pruebas unitarias 16/16.

---

## FASE 5 — Modelo del valor catastral del suelo: experimento ZHG (COMPLETADA 2026-10-14)

### Decisiones tomadas

- Alcance comunicado por los responsables: el software se orienta al **valor
  catastral del suelo rural** (no precio comercial). No se atribuye al
  director una aprobación formal; la opción ZHG quedó como experimento
  técnico documentado (Ruta C).
- Inspección del software anterior de Valentina (solo lectura): objetivo
  `valor_hectarea_agropecuario` = `ZHG_VALOR_` (equivalencia verificada en
  las 11 zonas); su dataset "integrado" tenía fuga por estadísticos zonales
  (R²=1.0, RMSE≈0); su experimento honesto no superaba el baseline.
- Nuevo pipeline experimental `yacopi_ml/zhg/` (modo research): dataset a
  nivel predio (objetivos dominante y ponderado con reglas de cobertura),
  4 escenarios de validación (filas/predio/espacial/zonas) +
  leave-one-zone-out, baselines mediana y moda zonal, criterio de
  aceptación predefinido, allowlist 19 / bloqueadas 57.

### Resultados reales (resumen; detalle en `docs/06_fase5_modelo_valor_suelo_zhg.md`)

- Escenarios con zonas compartidas: Forest MAE 73.765 COP/ha, R² 0,82
  (reproduce la zona, no valora independientemente).
- **Zonas fuera**: todos los modelos con R² negativo; la "moda zonal"
  trivial gana (168.954 vs 423.363 Forest). Leave-one-zone-out colapsa.
- Criterio predefinido: `aceptado = false` → **no se elige modelo
  ganador**. Opciones A/B/C documentadas para decisión del director.
- Predicción oficial: sigue **503 MODEL_NOT_READY** (verificado por la
  suite de backend intacta). Artefactos `exp-zhg-001` y
  `exp-zhg-001-ponderado` locales (no versionados, no registrados como
  candidatos).

### Pruebas

66/66 (8 nuevas de ZHG: equivalencia, fuga, cobertura, splits, smoke LOO);
`ruff` limpio.

---

## FASE 6B — Implementación de referencias ZHG (COMPLETADA 2026-10-14)

### Decisiones tomadas

- Funcionalidad A aprobada e implementada: consulta de referencias ZHG
  (dato, no predicción). ML experimental NO habilitado.
- Precisión sobre la propuesta 6A: la ponderación consolidada se expone
  solo con cobertura consistente (≤1 %); entre 1–5 % se muestra como
  cálculo PROVISIONAL inequívoco; >5 % sin ponderado (documentado en
  `docs/08_implementacion_referencias_zhg.md`).
- SQLite ampliado con `zhg_zones` (11) y `parcel_zhg_references` (9.434),
  idempotente vía `scripts/build_db.py`.

### Resultados

- Endpoints: `GET /references/zhg/zones` y
  `GET /properties/{public_id}/zhg-reference` (404 para inexistente;
  `zones: []` sin datos; `reference_date: null`).
- Frontend: `ZhgReferenceCard` en ficha y sección de consulta en
  `/prediccion` con tres conceptos diferenciados (referencia ZHG /
  predicción ML no habilitada / avalúo no emitido).
- Verificación real: 11 zonas correctas; monozona y multizona según reglas;
  `POST /predictions` sigue **503 MODEL_NOT_READY**.
- Pruebas: 77 pytest + 17 vitest; ruff/oxlint limpios; build OK.

### Ajustes de presentación (revisión visual de la ficha)

- Tarjeta ZHG: "participación" aclarada como participación dentro de las
  intersecciones zonales registradas (no cobertura catastral); línea
  "Vigencia de la referencia: no disponible" (sustituye el técnico
  "reference_date = null").
- Alertas de calidad: solo descripciones legibles; el código interno queda
  accesible en `title` al pasar el cursor, sin ensuciar la vista.
- Atributos territoriales: etiquetas según diccionario + nota de que la
  decodificación semántica oficial de los códigos está pendiente (sin
  inventar significados).
- Contraste y tamaño de textos secundarios mejorados (advertencias y
  alertas). Mensajes de valoración coherentes: existe referencia zonal del
  suelo, no avalúo individual certificado.
- Verificación Playwright escritorio/móvil (`scripts/verify-detail.mjs`):
  6/6 comprobaciones, 0 errores de consola, capturas en `docs/capturas/`.

---

## FASE 7B — Demostración experimental de ML (COMPLETADA, desactivada por defecto)

- Artefacto `exp-zhg-001-demo` (Random Forest, 19 características, 7.709
  predios) construido de forma determinística y trazable
  (`yacopi_ml.zhg.export_demo.py`). Hallazgo de integridad documentado: los
  hashes de las particiones congeladas actuales difieren de los históricos
  (regeneradas tras Fase 5); las métricas de Fase 5 quedan intactas como
  históricas y este artefacto no se presenta como el modelo evaluado.
- Endpoint `POST /predictions/experimental-zhg` (por `public_id` opaco,
  features derivadas del artefacto) con guards de dominio: monozona,
  referencia positiva, rangos numéricos y categorías vistas, predicción
  física finita; desactivado por defecto (`EXPERIMENTAL_ZHG_ENABLED=false`).
- `/prediccion`: sección "Demostración experimental (zonas conocidas)"
  (flag off → explicación sin controles falsos; flag on → estimación +
  referencia + diferencia + limitaciones).
- Oficial intacto: **503 MODEL_NOT_READY**. Pruebas: 88 pytest + 19 vitest;
  Playwright escritorio/móvil 7/7 sin errores de consola. Ver `docs/10`.

### Fase 7C — Auditoría de integridad (correcciones)

- **Particiones versionadas e inmutables** por firma de dataset
  (`data/splits/zhg/<objetivo>_n<n>/`); las pruebas usan directorios
  temporales y ya no sobrescriben particiones reales; archivos planos
  heredados movidos a `_legacy_sobrescritos/`. Pérdida de las particiones
  originales de Fase 5 documentada (sin reconstrucción artificial).
- **Alcance real del artefacto:** ajustado sobre los 7.709 predios; cada
  respuesta incluye `formo_parte_del_ajuste: true` y la advertencia
  obligatoria de que la diferencia mostrada no es una evaluación
  independiente.
- **Opacidad verificada con evidencia** (7.709 claves `p_[0-9a-f]{16}`,
  coincidencia exacta con `parcels.public_id`, servicio sin IDs privados) +
  prueba automatizada.
- **Consistencia del pipeline probada** (esquema de 19 características
  idéntico al entrenamiento, sin fuga, referencia = valor de zona) + E2E
  aislado con base y artefacto reales.
- Suite final: **94 pytest + 19 vitest**; flag experimental false por
  defecto; oficial 503 intacto.

---

## FASE 7E — Accesibilidad y comprensión (COMPLETADA)

- Glosario central con 56 términos (3 categorías) con búsqueda, en la
  navegación; HelpTip accesible (teclado/Escape/aria-expanded) en ficha,
  catálogo, mapa, análisis, modelos y predicción.
- «¿Qué significa esto para este predio?» con datos reales: ficha general,
  referencia ZHG (mono/multizona/cobertura), alertas y resultado ML.
- Correcciones en Predicción: diferencia en COP/ha, `in_domain` traducido,
  advertencias priorizadas (ajuste → no evaluación independiente → no
  avalúo) + resto en desplegable.
- Modelos: sección que distingue Fase 5 histórica / artefacto actual /
  referencia ZHG / oficial 503; ayuda de MAE/RMSE/R².
- Pruebas: 28 vitest + 94 pytest; Playwright escritorio/móvil 4/4 sin
  errores de consola. Detalle en `docs/11_accesibilidad_y_comprension.md`.

---

## FASE 8 — Auditoría integral (COMPLETADA)

- Auditoría ejecutada contra servidores reales: 10 rutas en escritorio y
  móvil sin errores de aplicación; interacciones verificadas (filtros,
  fichas, mapa CARTO, gráficas, glosario, ayudas, 503 oficial, consulta
  ZHG); integridad API↔DB 12/12.
- Sin defectos críticos ni importantes. 404/503 intencionales documentados
  como comportamiento esperado.
- **Dictamen: LISTO PARA ENTREGA CON LIMITACIONES EXPLÍCITAS** (ver
  `docs/12_auditoria_integral.md`): ¿Funciona? SÍ · ¿Se entiende? SÍ según
  revisión heurística · ¿Cumple el anteproyecto? SÍ como prototipo con
  limitaciones científicas declaradas.
- Backend local restaurado a estado por defecto (flags apagados); oficial
  503; sin push.

---

## FASES 1–8 — Estado

| Fase | Estado | Bloqueo |
|---|---|---|
| 1. Validación final de datos | **Completada** | — |
| 2. Modelos (Ruta B) | **Completada (experimental)** | Modelo oficial sigue pendiente de etiqueta |
| 3. Backend FastAPI | **Completada** | — |
| 4. Frontend React | **Completada funcionalmente** | Pendiente revisión visual del usuario |
| 5. Modelo valor catastral (ZHG) | **Completada (experimental, sin ganador)** | Decisión del director: opciones A/B/C |
| 5. Integración | No iniciada | — |
| 6. Pruebas y rendimiento | No iniciada | — |
| 7. Despliegue VPS | No iniciada | Sin VPS (diferido) |
| 8. Documentación académica | No iniciada | Requiere resultados reales de ML |
