# Guía del repositorio — Atlas Vivo (yacopi-project)

Documento de referencia para entender qué contiene este repositorio, qué hace
cada parte y cómo se relacionan. Pensado para quien llega al proyecto por
primera vez o necesita localizar un componente.

---

## 1. Qué es Atlas Vivo

Prototipo académico (Ingeniería de Sistemas y Computación) que integra datos
catastrales reales del municipio de Yacopí (Cundinamarca, Colombia) con
análisis estadístico y aprendizaje supervisado, presentados en una experiencia
cartográfica web.

- **Objetivo de software:** consulta territorial, estadísticas y predicción de
  **valor catastral del suelo rural** (COP/ha).
- **Estado de la predicción:** el endpoint oficial permanece **bloqueado
  (503 MODEL_NOT_READY)** porque la etiqueta de valor exclusivo de suelo aún
  no está validada. Solo existe una **demostración experimental** (Random
  Forest ZHG) desactivada por defecto.
- **Aviso institucional:** las estimaciones son apoyo académico; no constituyen
  avalúo oficial ni reemplazan la referencia ZHG.

### Estado actual (resumen)

| Área | Estado |
|---|---|
| Datos | 7.709 predios, 7.694 con coordenadas, 11 zonas ZHG, 9.434 referencias ZHG |
| Backend FastAPI | En producción (consulta, estadísticas, mapas) |
| Frontend React | En producción (10 rutas públicas) |
| Predicción oficial | Bloqueada por diseño (503) |
| Demo ML experimental | Implementada, desactivada por defecto |
| Despliegue | Producción en https://atlasvivo.xyz (VPS Contabo, Docker Compose) |
| Última corrección | Referrer-Policy para teselas del mapa (commit `9429da3`, docs/15) |

---

## 2. Arquitectura general

```
Navegador
   │ HTTPS
   ▼
Nginx del host (TLS Let's Encrypt, 80/443)
   │ proxy a 127.0.0.1:8080
   ▼
Contenedor FRONTEND (nginx interno: SPA compilada + proxy /api)
   │ red interna de Docker (atlas)
   ▼
Contenedor BACKEND (FastAPI + Uvicorn, SIN puertos publicados)
   │ lectura
   ├─ /app/data/parcels.db   ← montado ro desde deploy-data/parcels.db
   └─ /app/model/            ← montado ro desde deploy-model/
```

- El backend no publica puertos al host; solo es accesible a través del
  frontend.
- La base SQLite y el artefacto ML viven **fuera de Git y de las imágenes**
  (se transfieren por scp a la VPS).
- El pipeline de ML es **offline** (se entrena/exporta aparte); la API solo
  consume el artefacto exportado.

---

## 3. Estructura del repositorio (raíz)

| Ruta | Qué es / qué hace |
|---|---|
| `README.md` | Presentación, arranque local, pruebas, privacidad |
| `GUIA_REPOSITORIO.md` | Este documento |
| `compose.yaml` | Orquestación Docker de producción (backend + frontend) |
| `.dockerignore` | Excluye del contexto de build: datos, artefactos, secretos (`**/.env*`, `*.db`, etc.) |
| `.gitignore` | Excluye de Git: `.env`, `frontend/.env.local`, `data/`, `deploy-data/`, `deploy-model/`, `ml/artifacts/`, venvs, `node_modules`, `dist` |
| `.env.example` | Plantilla de variables de entorno (flags y CORS); el `.env` real es local y secreto |
| `Makefile` | Accesos rápidos multiplataforma: `setup`, `lint`, `test`, `build-web`, `data-audit`, `clean` |
| `pyproject.toml` | Configuración de pytest (paths de ml y backend) y de ruff (lint Python) |
| `.editorconfig` | Estilo de archivos (indentación, charset, fin de línea) |
| `.github/workflows/ci.yml` | CI de GitHub Actions: lint + tests de Python y frontend en cada push/PR a dev/main |

---

## 4. `backend/` — API FastAPI

Servidor Python (FastAPI + Uvicorn + Pydantic) en modo consulta.

| Ruta | Qué contiene |
|---|---|
| `app/main.py` | Aplicación FastAPI: routers, middlewares, CORS, manejo de errores |
| `app/core/config.py` | Configuración desde variables de entorno (flags, rutas, CORS) |
| `app/core/errors.py` | Errores tipados de la API (códigos estables como `MODEL_NOT_READY`) |
| `app/db/connection.py` | Apertura de la SQLite en modo solo lectura |
| `app/db/repository.py` | Consultas SQL (predios, estadísticas, zonas ZHG, referencias) |
| `app/routers/` | Endpoints por dominio (ver §4.1) |
| `app/schemas/` | Modelos Pydantic de entrada/salida |
| `app/services/demo.py` | Carga y consulta del artefacto demo ZHG (si el flag lo permite) |
| `app/services/prediction.py` | Lógica de predicción oficial (bloqueada) y experimental proxy (apagada) |
| `tests/` | Suites pytest (API, health, referencias ZHG, demo) |
| `requirements.txt` | Dependencias directas del backend |
| `requirements.lock.txt` | Versiones exactas verificadas para la imagen Docker |
| `Dockerfile` | Imagen `python:3.14-slim` multietapa con healthcheck |

### 4.1 Endpoints (`/api/v1`)

| Método y ruta | Función |
|---|---|
| `GET /health/live`, `GET /health/ready` | Liveness/readiness para Docker y monitoreo |
| `GET /system/status` | Estado del sistema y flags activos |
| `GET /properties` | Catálogo paginado de predios (filtro `public_id_prefix`, filtros territoriales) |
| `GET /properties/{public_id}` | Ficha de un predio (ZHF, zona, coordenada referencial) |
| `GET /statistics/overview` | Resumen estadístico municipal |
| `GET /statistics/distributions` | Distribuciones para gráficas de exploración |
| `GET /maps/points` | Puntos geográficos para el mapa (límite de registros) |
| `GET /models`, `GET /models/active` | Registro de modelos/experimentos |
| `GET /references/zhg/zones` | Zonas ZHG (11 zonas) |
| `GET /properties/{public_id}/zhg-reference` | Referencia ZHG del predio (consultable, no es avalúo) |
| `POST /predictions` | **Oficial: 503 `MODEL_NOT_READY`** (bloqueada por diseño) |
| `POST /predictions/experimental` | Proxy histórico: apagada (`EXPERIMENTAL_INFERENCE_ENABLED=false`) |
| `POST /predictions/experimental-zhg` | Demo Random Forest: apagada (`EXPERIMENTAL_ZHG_ENABLED=false`); solo monozona y zonas conocidas |

---

## 5. `frontend/` — SPA React + TypeScript

| Ruta | Qué contiene |
|---|---|
| `src/pages/` | Páginas públicas (ver §5.1) |
| `src/components/` | Componentes compartidos: `AppShell` (nav/pie), `ParcelSelector`, `ZhgReferenceCard`, `MiniMap`, `InterpretationCard`, `DataQualityBadge`, `HelpTip`, `Disclaimer`, `Scene3D`, `SystemStatusBanner`, `map/` (capa de puntos, leyenda, panel de visualización) |
| `src/api/client.ts` | Cliente HTTP hacia `/api/v1` (timeouts, manejo de errores) |
| `src/api/types.ts` | Tipos TypeScript de las respuestas de la API |
| `src/lib/appContent.ts` | **Fuente única de texto institucional** (footer, banners, avisos) |
| `src/lib/basemap.ts` | Mapa base: CARTO Dark Matter si existe `VITE_CARTO_BASEMAPS_KEY`; si no, OSM estándar |
| `src/lib/glossary.ts` | Glosario de términos (57 términos) |
| `src/lib/interpretation.ts` | Interpretación de resultados (diferencias, advertencias priorizadas, `in_domain`) |
| `src/lib/format.ts` | Formato de moneda/áreas colombianas |
| `src/lib/map-colors.ts`, `src/lib/map-utils.ts` | Colores y utilidades cartográficas |
| `src/lib/motion-setup.ts` | Animaciones (GSAP/Lenis) |
| `src/test/` | Pruebas Vitest (contenido, interpretación, mapa base, páginas, ayudas) |
| `scripts/verify-*.mjs`, `audit-integrity.mjs` | Scripts de verificación/auditoría de contenido, mapa, demo y coherencia |
| `index.html`, `vite.config.ts`, `tsconfig*.json`, `.oxlintrc.json`, `.nvmrc` | Configuración de build, TypeScript y lint |
| `public/` | favicon e iconos SVG |
| `Dockerfile` | Multietapa: build con Node 24 → servido por nginx:1.27-alpine |

### 5.1 Páginas (rutas)

`/` (Inicio 3D) · `/predios` (catálogo) · `/predios/:id` (ficha) · `/mapa`
(mapa con puntos, filtros y controles) · `/exploracion` (gráficas Plotly) ·
`/modelos` (experimentos) · `/prediccion` (consulta demo experimental) ·
`/metodologia` · `/acerca` · `/glosario`.

---

## 6. `ml/` — Pipeline de datos y Machine Learning (offline)

| Ruta | Qué contiene |
|---|---|
| `config/features.yaml` | Features base (proxy) |
| `config/features_zhg.yaml` | Features del experimento ZHG |
| `config/label_contract*.yaml` | Contratos de la variable objetivo (proxy, ZHG) |
| `config/training.yaml` | Parámetros de entrenamiento |
| `src/yacopi_ml/preprocess.py` | Limpieza e ingeniería de features |
| `src/yacopi_ml/labels.py` | Construcción de etiquetas (incluye la de suelo exclusivo, pendiente de validación) |
| `src/yacopi_ml/split.py` | Particiones espaciales/aleatorias **versionadas** (`data/splits/zhg/`) |
| `src/yacopi_ml/train.py`, `models.py`, `metrics.py`, `evaluate.py` | Entrenamiento, modelos, métricas (R²→NaN ante objetivo constante) y evaluación |
| `src/yacopi_ml/explain.py` | Explicabilidad de modelos |
| `src/yacopi_ml/export.py`, `registry.py`, `schema.py` | Exportación de artefactos, registro de experimentos, validación de esquemas |
| `src/yacopi_ml/zhg/` | Flujo específico ZHG: `dataset.py` (construcción), `splits.py`, `train.py`, `export_demo.py` (artefacto demo) |
| `tests/` | Integridad de datos, pipeline, smoke, ZHG |
| `requirements.txt` | Dependencias ML (scikit-learn, catboost, pandas…) |
| `ml/artifacts/` | Artefactos exportados (LOCAL, no versionado) |

Artefacto en producción: `exp-zhg-001-demo` (RandomForest, sin validación
independiente; solo demostración). Los experimentos históricos (proxy,
ZHG Fase 5) se conservan documentados, no como modelo actual.

---

## 7. `data/`, `deploy-data/`, `deploy-model/` — Datos y artefactos (privados)

| Ruta | Contenido | En Git |
|---|---|---|
| `data/` | CSV originales y SQLite de desarrollo (`parcels.db`) | No |
| `deploy-data/parcels.db` | SQLite de producción (7.709 predios) | No |
| `deploy-model/exp-zhg-001-demo/` | Artefacto ML de producción | No |
| `data/splits/zhg/` | Particiones versionadas del experimento ZHG | Sí |

Los `public_id` (`p_` + hash) son los únicos identificadores expuestos; los
`numero_predial` reales quedan en la base privada.

---

## 8. `deploy/` — Despliegue

| Archivo | Qué hace |
|---|---|
| `nginx-app.conf` | Nginx **interno** del contenedor frontend: SPA fallback, proxy `/api` a `backend:8000`, gzip, cabeceras de seguridad (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy: strict-origin-when-cross-origin`) |
| `README.md` | Runbook completo de despliegue en la VPS (build, healthchecks, Nginx del host + TLS, verificación, rollback) |

---

## 9. `docs/` — Documentación y decisiones

| Archivo | Contenido |
|---|---|
| `00_leer_primero.md`, `00_contexto_maestro.md` | Punto de entrada y contexto maestro del proyecto |
| `02_diccionario_datos.md` | Diccionario de variables |
| `04_metodologia_ml.md` | Metodología ML |
| `05_alineacion_anteproyecto.md` | Alineación con el anteproyecto |
| `06_fase5_modelo_valor_suelo_zhg.md` | Experimento ZHG (Fase 5) |
| `07_propuesta_sistema_valoracion.md` | Propuesta del sistema de valoración |
| `08_implementacion_referencias_zhg.md` | Implementación de referencias ZHG |
| `09_propuesta_predictiva_final.md` | Propuesta predictiva final |
| `10_demostracion_ml_experimental.md` | Demo ML experimental |
| `11_accesibilidad_y_comprension.md` | Accesibilidad y comprensión |
| `12_auditoria_integral.md` | Auditoría integral del sistema |
| `13_preparacion_vps.md` | Preparación de la VPS |
| `14_coherencia_textos.md` | Coherencia de textos institucionales |
| `15_correccion_mapa_403.md` | **Corrección del 403 del mapa** (Referrer-Policy) |
| `ESTADO_PROYECTO.md` | Registro cronológico de avance |
| `pendientes.md` | Pendientes científicos y técnicos |
| `DESIGN_SYSTEM.md` | Sistema de diseño del frontend |
| `decisions/ADR-*.md` | Decisiones de arquitectura registradas (fases 0–3) |

---

## 10. `scripts/`, `notebooks/`, `tests/`

| Ruta | Qué hace |
|---|---|
| `scripts/audit_data.py` | Auditoría de calidad de datos |
| `scripts/build_db.py` | Construcción de la SQLite desde los CSV |
| `scripts/build_maps.py` | Generación de datos para mapas |
| `scripts/preparar_datos.py` | Script histórico de preparación (conservado byte-idéntico) |
| `scripts/verify_inputs.py` | Verificación de entradas esperadas |
| `scripts/benchmark_api.py` | Benchmark de la API |
| `notebooks/` | Exploración Jupyter (no es código de producción) |
| `tests/e2e/README.md` | Definición de flujos end-to-end (Playwright) |
| `tests/fixtures/` | Fixtures de diagnóstico |

---

## 11. Seguridad y privacidad

- **Git:** no se versionan CSV, SQLite, artefactos ML, `.env`, ni claves CARTO.
- **Docker:** `.dockerignore` excluye `**/.env*` (incluido `frontend/.env.local`),
  `*.db`, `*.joblib/*.cbm/*.pkl`, `data/`, `deploy-*`, `ml/artifacts`.
- **API pública:** solo `public_id` opacos; sin rutas internas en errores.
- **Predicción:** oficial bloqueada; demo desactivada por defecto mediante
  flags de entorno.
- **Teselas:** `Referrer-Policy: strict-origin-when-cross-origin` (política de
  OSM); atribución visible; la clave CARTO es de navegador (no es secreto) y
  debe protegerse con allowlist de dominio en el panel de CARTO.

---

## 12. Comandos útiles

```powershell
# Backend + ML (venv)
py -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install -r ml/requirements.txt -r backend/requirements.txt
uvicorn app.main:app --reload --port 8000        # desde backend/

# Pruebas y calidad
ruff check .                                      # lint Python
pytest                                            # ml + backend
cd frontend; npm run lint; npm run test; npm run build

# Docker (producción)
docker compose build
docker compose up -d
docker compose ps                                  # healthchecks
# Frontend local: http://127.0.0.1:8080  · OpenAPI local: http://127.0.0.1:8000/docs
```

---

## 13. Decisiones clave

- La **referencia ZHG es dato consultable**, no un avalúo.
- El endpoint oficial solo se habilitará con una etiqueta de suelo exclusivo
  verificada; mientras tanto responde 503 `MODEL_NOT_READY`.
- La demo ML solo opera en monozona y zonas conocidas; muestra diferencias
  absolutas y relativas con advertencias y limitaciones explícitas.
- `public_id` opaco evita exponer correspondencias internas.
- Docker: backend sin puertos públicos; frontend solo en loopback `127.0.0.1:8080`;
  Nginx del host termina TLS.
- Métricas históricas de Fase 5 no evalúan el artefacto demo.

## 14. Pendientes principales

- Diccionario oficial de códigos y fecha de vigencia de la referencia ZHG.
- Etiqueta verificada de valor exclusivo de suelo (bloqueante de la predicción).
- Validación independiente del modelo con datos nuevos.
- Decisión sobre activar la demo públicamente (y limitación de tasa en Nginx).
- Evaluar proveedor comercial de teselas si el tráfico crece.
