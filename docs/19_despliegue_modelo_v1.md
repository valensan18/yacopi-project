# Doc 19 — Procedimiento de despliegue y rollback del modelo RF v1 (demostración académica)

**Rama de integración:** `feature/valor-modelo-v1` (desde `dev`). Esta rama
NO incluye el artefacto ni datos privados; ambos se transfieren por
separado, igual que la base de datos. La funcionalidad queda **desactivada
por defecto** (`VALOR_V1_ENABLED=false`).

## 0. Precondiciones

- Revisar y autorizar el informe final de esta entrega.
- Disponer del artefacto local `deploy-model/exp-valor-v1/` (7 archivos:
  model.joblib, features.json, feature_schema.json, training_stats.json,
  manifest.json, metrics_evaluacion.json, MODEL_CARD.md).

## 1. Despliegue (paso a paso, en la VPS)

```bash
cd /home/atlasadmin/atlas

# 1.1 Estado actual y respaldo
git status --short
docker compose ps
FRONT_IMG=$(docker image inspect --format '{{index .RepoTags 0}}' $(docker compose ps -q frontend))
docker image tag "$FRONT_IMG" atlas-frontend-rollback:$(date +%Y%m%d-%H%M)
BACK_IMG=$(docker image inspect --format '{{index .RepoTags 0}}' $(docker compose ps -q backend))
docker image tag "$BACK_IMG" atlas-backend-rollback:$(date +%Y%m%d-%H%M)

# 1.2 Obtener la rama de integración (sin tocar dev)
git fetch origin
git checkout -b feature/valor-modelo-v1 origin/feature/valor-modelo-v1

# 1.3 Transferir el artefacto (desde la máquina local, NO en Git)
#   scp -r deploy-model/exp-valor-v1 atlasadmin@<IP>:/home/atlasadmin/atlas/deploy-model/
#   (conserva exp-zhg-001-demo: el backend lo ignora mientras su flag siga en false)

# 1.4 Verificar integridad del artefacto en la VPS
ls -la deploy-model/exp-valor-v1/
python3 -c "import json; m=json.load(open('deploy-model/exp-valor-v1/manifest.json')); \
print(m['model_id'], m['model_version'], m['rol'], m['status'], m['n_fit'])"
# esperado: atlas-vivo-rf-v1 1.0.0 demostracion_academica experimental_demo 4676

# 1.5 Reconstruir y recrear (backend y frontend; la DB y el modelo se montan ro)
docker compose build
docker compose up -d --force-recreate
docker compose ps   # ambos healthy

# 1.6 Verificar DESACTIVADO por defecto
curl -s https://atlasvivo.xyz/api/v1/system/status | grep -o '"valor_v1":{[^}]*}'
# esperado: habilitado:false
curl -s -o /dev/null -w "%{http_code}" -X POST https://atlasvivo.xyz/api/v1/predictions/valor-terreno-v1 \
     -H "Content-Type: application/json" -d '{"public_id":"p_6049c425ce3cf79d"}'
# esperado: 503 (VALOR_V1_DISABLED)
```

## 2. Habilitación de la demostración (solo tras revisión del informe)

```bash
cd /home/atlasadmin/atlas
# Añadir a .env (NO commitear):
#   VALOR_V1_ENABLED=true
docker compose up -d backend        # recrea el backend con el flag activo
docker compose ps                   # healthy

# Verificación funcional
curl -s -X POST https://atlasvivo.xyz/api/v1/predictions/valor-terreno-v1 \
     -H "Content-Type: application/json" \
     -d '{"public_id":"p_6049c425ce3cf79d"}' | head -c 400
# esperado: predicted_cop_ha ≈ 198.093,45 y reference_zhg_cop_ha = 182.414,3
curl -s -o /dev/null -w "%{http_code}" -X POST https://atlasvivo.xyz/api/v1/predictions \
     -H "Content-Type: application/json" -d '{"features":{}}'
# esperado: 503 MODEL_NOT_READY (el oficial sigue bloqueado)
```

Comprobar en navegador (escritorio y móvil): la sección "Estimación con
Machine Learning — Demostración académica" en /prediccion muestra los dos
valores separados (referencia ZHG vs estimación RF) y las métricas reales.

## 3. Rollback

```bash
cd /home/atlasadmin/atlas

# 3.1 Rollback de la aplicación (imágenes anteriores)
docker image tag atlas-backend-rollback:<FECHA>  <nombre-imagen-backend-actual>
docker image tag atlas-frontend-rollback:<FECHA> <nombre-imagen-frontend-actual>
docker compose up -d --force-recreate
docker compose ps

# 3.2 Rollback solo de la funcionalidad (más frecuente)
# Quitar VALOR_V1_ENABLED=true de .env (o poner false) y recrear backend:
docker compose up -d backend
curl -s -o /dev/null -w "%{http_code}" -X POST https://atlasvivo.xyz/api/v1/predictions/valor-terreno-v1 \
     -H "Content-Type: application/json" -d '{"public_id":"p_6049c425ce3cf79d"}'
# esperado: 503 VALOR_V1_DISABLED

# 3.3 Rollback de Git (sin reseteos destructivos)
git checkout dev -- backend frontend compose.yaml .env.example   # NO recomendado en caliente
# Preferido: volver a la rama dev
git checkout dev
docker compose build && docker compose up -d --force-recreate
```

## 4. Checklist de seguridad post-despliegue

- [ ] HTTPS con certificado válido (sin cambios en Nginx del host).
- [ ] `VALOR_V1_ENABLED` en el estado deseado (default false).
- [ ] Endpoint oficial sigue 503 MODEL_NOT_READY.
- [ ] Demo ZHG sigue desactivada (EXPERIMENTAL_ZHG_ENABLED=false).
- [ ] La respuesta no contiene `numero_predial` ni `valor_avaluo`.
- [ ] Los logs no exponen datos confidenciales.
- [ ] Respaldo de imágenes conservado (tags `*-rollback`).

## 5. Notas de seguridad

- El artefacto se carga solo desde `MODEL_DIR` (montaje read-only
  `deploy-model:/app/model:ro`) y exige `rol=demostracion_academica` y
  `status=experimental_demo` en el manifiesto.
- No publicar en Git: CSV, `data/splits/valor/`, artefacto ni `.env`.
- La demostración NO sustituye la predicción oficial ni la referencia ZHG
  consultable.
