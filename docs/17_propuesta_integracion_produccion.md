# Doc 17 — Propuesta de integración selectiva a producción (revisión de seguridad)

**Fecha:** 2026-11-05 · **Rama:** `experimental/valor-terreno-ha`
(commits `b3b0b38`, `b37cd4c`) vs `dev` (`9429da3`).
**Alcance:** análisis y propuesta. NO se hizo push, merge ni despliegue.

## 1. Conclusión principal

**No existe ninguna actualización necesaria para el sitio público.**
La rama experimental **no modifica** código de frontend, backend, base de
datos, modelos desplegados, Dockerfiles, compose ni configuración del Nginx.
Los 78 archivos que difieren de `dev` son: experimentación ML
(`ml/src/yacopi_ml/valor/`, `scripts/`), particiones experimentales
(`data/splits/valor/`), documentación para el profesor (`entrega_docente/`,
`docs/16`) y un script local de generación de PDF
(`frontend/scripts/generar-pdf.mjs`, no importado por la app).

La plataforma pública ya muestra correctamente que **no existe un modelo
predictivo definitivo aprobado** (estado de `dev`, sin cambios en esta rama).

## 2. Clasificación de los cambios (rama vs dev)

| Área | Archivos | ¿Afecta producción? |
|---|---|---|
| Frontend de la app (`src/`, `index.html`, `vite.config`) | 0 cambios | No |
| Backend de la app (`backend/app/**`) | 0 cambios | No |
| Base de datos / SQLite | 0 cambios | No |
| Modelos desplegados / artefactos | 0 cambios (artefactos nuevos solo en `ml/artifacts/`, ignorados por Git) | No |
| Docker y despliegue (`Dockerfile*`, `compose.yaml`, `deploy/`, `.dockerignore`) | 0 cambios | No |
| CI (`.github/workflows/ci.yml`) | 0 cambios | No |
| Tooling local | `frontend/scripts/generar-pdf.mjs` (genera el PDF académico; no lo importa la app ni se incluye en el bundle) | No |
| Configuración de lint | `pyproject.toml` (excluye de ruff los generadores y cuadernos de la entrega docente) | No |
| Experimentación ML | `ml/src/yacopi_ml/valor/**`, `scripts/audit_*.py`, `scripts/evidencia_solapamiento.py`, `scripts/ver_*.py`, `scripts/comparar_*.py`, `scripts/generar_*.py`, `scripts/ejecutar_notebooks.py` | No (código offline) |
| Pruebas de experimentación | `ml/tests/test_valor_splits.py` | No |
| Particiones experimentales | `data/splits/valor/valor_terreno_ha_{A,B}_n*/**` (contienen `numero_predial`) | No |
| Documentación metodológica | `docs/16_nueva_variable_valor_terreno.md`, `entrega_docente/*.md`, PDF, 17 figuras, 13 notebooks | No (solo repositorio) |

## 3. Verificaciones realizadas hoy

1. `git diff dev...HEAD -- frontend backend compose.yaml deploy .dockerignore .github`:
   **un solo archivo** (generar-pdf.mjs).
2. Estado del sitio (sin cambios en la rama): `/modelos` identifica el
   experimento proxy como histórico (exp-proxy-001) con sus particiones y
   cifras verificadas por reentrenamiento; distingue experimentos ZHG
   rechazados, la demo desactivada y la predicción oficial 503; los R²
   negativos se muestran fielmente.
3. Flags de producción: `EXPERIMENTAL_INFERENCE_ENABLED=false` y
   `EXPERIMENTAL_ZHG_ENABLED=false` en `backend/Dockerfile` (sin cambios);
   endpoint oficial sigue 503 `MODEL_NOT_READY` (pruebas backend).
4. Imágenes Docker inspeccionadas (build real del frontend desde esta rama +
   imagen backend existente): **sin** `*.ipynb`, `parcels.db`, `*.joblib`,
   `*.cbm`, `entrega_docente/` ni `numero_predial` en los assets. El
   `backend/Dockerfile` solo copia `backend/app` y
   `backend/requirements.lock.txt`; el frontend solo sirve `/app/dist`.
5. Privacidad: 0 identificadores prediales (números ≥ 20 dígitos) en
   `entrega_docente/*.md`, `*.json` y notebooks.
6. Pruebas: pytest **104/104** · vitest **33/33** · oxlint limpio · build
   frontend OK · `docker compose config` válido · ruff limpio.

## 4. Propuesta de integración selectiva

### Opción A (recomendada): no integrar nada a `dev` todavía
Entregar al profesor el paquete `entrega_docente/` directamente desde la
rama experimental (exportar la carpeta o clonar la rama). Cero riesgo para
el sitio y para `dev`. La documentación queda disponible como referencia
mientras la investigación continúa.

### Opción B (si se desea documentación en `dev`): cherry-pick solo de docs
Archivos candidatos (sin efectos en runtime):

- `docs/16_nueva_variable_valor_terreno.md`
- `entrega_docente/*.md` (12 documentos metodológicos)
- opcional: `entrega_docente/figuras/`, PDF y notebooks (aumentan el tamaño
  del repo; pueden omitirse).

NO integrar (investigación/privacidad):

- `ml/src/yacopi_ml/valor/**`, `ml/tests/test_valor_splits.py`, `scripts/`
  experimentales (a menos que se decida oficializar el experimento).
- `data/splits/valor/**` (contienen `numero_predial` privados y no aportan
  a producción).
- `pyproject.toml` (solo relevante junto con los generadores excluidos).

**Riesgos de la opción B:** ninguno en runtime (solo archivos .md/.png/.pdf
versionados). **Pruebas:** `ruff check .`, `pytest`, `vitest` (no deberían
variar; no tocan código). **Reversión:** `git revert <commit-del-cherry-pick>`
o `git push --force-with-lease` no aplica: basta revert; el sitio no cambia.

### Opción C: mantener todo en la rama experimental
Continuar el trabajo metodológico hasta la decisión docente; luego decidir
qué se promociona a `dev` con revisión.

## 5. Qué permanece en investigación

- Experimentos VALOR_TERRENO_Ha (protocolo v2), sus particiones, baselines y
  análisis de sensibilidad.
- La decisión de modelo definitivo (pendiente de confirmaciones docentes:
  vigencia del avalúo, contenido, áreas mínimas, alcance interpretativo).

## 6. Recomendación final

- **Sitio público:** no requiere ninguna actualización desde esta rama.
- **Repositorio:** si el profesor debe acceder a la documentación desde
  `dev`, aplicar la opción B (solo docs) tras revisión; en caso contrario,
  mantener la opción A/C.
- **Seguridad:** añadir `entrega_docente/` al `.dockerignore` como defensa en
  profundidad (reduce el contexto de build; hoy no se copia en ninguna
  imagen). Cambio opcional, sin efecto en el runtime.
