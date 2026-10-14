# Yacopí Predictor — Estimación académica del valor del suelo rural

Sistema predictivo para estimar el valor del suelo rural en el municipio de
Yacopí, Cundinamarca (Colombia), como proyecto académico de Ingeniería de
Sistemas y Computación (modalidad artículo).

> **Aviso:** las estimaciones son **apoyo académico**, no constituyen avalúo
> oficial ni sustituyen la valoración catastral o comercial profesional.

## Estado del proyecto

| Componente | Estado |
|---|---|
| Auditoría de datos | Completada (ver `docs/` y guía maestra) |
| Variable objetivo (valor exclusivo de suelo COP/ha) | **Pendiente de validación** (bloqueante) |
| Modelos predictivos | No entrenados; solo experimentos proxy segregados (Ruta B) |
| Backend FastAPI | En desarrollo (modo consulta sin inferencia) |
| Frontend React | En desarrollo |
| Despliegue | Pendiente (VPS diferido) |

Ver `docs/ESTADO_PROYECTO.md` para el registro detallado de avance.

## Estructura

```
data/raw/          CSV originales (NO versionados; solo locales)
docs/              Guía maestra, estado, decisiones (ADR) y pendientes
ml/                Pipeline de datos + ML offline (src/yacopi_ml, config, tests)
backend/           API FastAPI (consulta, estadísticas, mapas, predicción condicionada)
frontend/          SPA React + TypeScript + Vite
scripts/           Ingestión, auditoría y construcción de bases/mapas
notebooks/         Exploración (no es código de producción)
deploy/            Docker Compose, Nginx, runbooks de VPS
tests/e2e/         Pruebas de integración end-to-end
```

## Requisitos

- Python 3.13+ (probado con 3.14; ver `docs/decisions/` por compatibilidad)
- Node.js 24 LTS y npm
- Git, Docker (para despliegue)

## Arranque en Windows PowerShell

```powershell
# Backend y ML (una sola vez)
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r ml/requirements.txt
python -m pip install -r backend/requirements.txt

# Frontend (otra terminal)
cd frontend
npm ci
npm run dev

# API (terminal con venv activo)
cd backend
uvicorn app.main:app --reload --port 8000
```

Probar: `http://127.0.0.1:8000/docs` (OpenAPI) y la URL que asigne Vite.

## Pruebas y calidad

```powershell
ruff check .            # lint (desde la raíz con venv activo)
pytest                  # ml + backend (desde la raíz)
cd frontend && npm run lint && npm run test && npm run build
```

## Privacidad

- Los CSV originales, la base de datos y los artefactos ML **no se versionan**.
- La API pública usa identificadores opacos (`public_id`); los
  `numero_predial` reales permanecen en base privada.
- No publicar coordenadas o datos prediales sin autorización del equipo.
