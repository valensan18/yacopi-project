# ESTADO_PROYECTO — Yacopí Predictor

Registro cronológico de avance, decisiones, errores y pendientes.
Formato: una sección por fase. No se declara completada una fase sin ejecutar
su criterio de aceptación.

Última actualización: 2026-10-14

---

## FASE 0 — Inicialización del repositorio y entorno (EN CURSO)

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
  (`DIEGHOST64`) permanece intacta.
- Clave SSH dedicada `~/.ssh/id_ed25519_valensan18` + alias
  `github-valensan18` en `~/.ssh/config` (nuevo; no existía config previo).
  La clave personal `id_ed25519` no se modificó.
- Estrategia ML: **Ruta B** — todo el producto funciona en modo
  `ANALISIS_SIN_MODELO`; experimentos proxy con avalúo total/ha en rama
  experimental separada, jamás promovidos a modelo oficial de suelo sin
  etiqueta validada.
- VPS diferido: se entregará Docker Compose + Nginx + runbooks listos.

### Tareas completadas

- [x] Estructura de directorios según guía maestra §5.4.
- [x] `README.md`, `.gitignore`, `.editorconfig`, `.env.example`, `Makefile`,
      CI (`ci.yml`: ruff + pytest + build frontend).
- [x] `docs/ESTADO_PROYECTO.md`, `docs/pendientes.md`, `docs/decisions/`.
- [x] SSH dedicada + alias verificados (`ssh -T` → "Hi valensan18!").
- [x] `git init -b dev`, identidad local, `remote add origin` (URL exacta).
- [x] `git fetch` + base sobre `origin/main`.

### Tareas pendientes de la fase

- [ ] Copiar CSV originales a `data/raw/` con SHA-256 + `data_manifest.json`.
- [ ] Entorno Python (venv) + verificación real de GeoPandas/CatBoost.
- [ ] Frontend Vite React+TS + dependencias + lockfile.
- [ ] Comprobaciones: ruff, pytest (smoke), build frontend, `git check-ignore`.
- [ ] Commits locales (sin push hasta autorización).

### Errores / problemas encontrados

- `gh auth login` indicado como completado por el usuario no persistió:
  `%APPDATA%\GitHub CLI\hosts.yml` no existe y `gh auth status` reporta sin
  sesión. **Pendiente** retomar el login para verificar privacidad y
  colaboradores por API. Mitigación parcial: la API pública devuelve 404 para
  el repo (comportamiento de repos privados) y `ssh -T` confirma acceso.
- El PDF de Jesús (`PROYECTO REALIZADO POR JESUS.pdf`) no tiene capa de
  texto; su contenido se usa vía resumen de la guía maestra §2. OCR solo si
  se requiere.

### Decisiones pendientes de usuario/director

- Ver `docs/pendientes.md` (etiqueta de suelo, diccionario, fechas, permisos).

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
