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

## FASES 1–8 — No iniciadas

| Fase | Estado | Bloqueo |
|---|---|---|
| 1. Validación final de datos | No iniciada | Requiere autorización tras Fase 0 |
| 2. Modelos (Ruta B) | No iniciada | Etiqueta pendiente (solo proxy experimental) |
| 3. Backend FastAPI | No iniciada | — |
| 4. Frontend React | No iniciada | — |
| 5. Integración | No iniciada | — |
| 6. Pruebas y rendimiento | No iniciada | — |
| 7. Despliegue VPS | No iniciada | Sin VPS (diferido) |
| 8. Documentación académica | No iniciada | Requiere resultados reales de ML |
