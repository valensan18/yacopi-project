# Backend FastAPI de Atlas Vivo (producción).
# Imagen base Python 3.14 slim (misma versión verificada localmente).
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# libgomp1 es requerido por catboost en imágenes slim.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.lock.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY backend/app ./app

# Valores de producción por defecto; se sobreescriben con variables del
# despliegue. La demostración experimental permanece DESACTIVADA.
ENV APP_ENV=production \
    LOG_LEVEL=INFO \
    DATABASE_PATH=/app/data/parcels.db \
    MODEL_DIR=/app/model \
    EXPERIMENTAL_INFERENCE_ENABLED=false \
    EXPERIMENTAL_ZHG_ENABLED=false \
    VALOR_V1_ENABLED=false \
    CORS_ORIGINS=http://localhost

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=3)" || exit 1

# Sin --reload en producción; un solo worker para cargar el modelo UNA vez.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
