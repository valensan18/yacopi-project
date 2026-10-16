# Despliegue de Atlas Vivo — VPS (Docker Compose)

Objetivo: Contabo Cloud VPS 4 (Ubuntu 24.04, 4 vCPU / 8 GB RAM), con SSH por
llaves, UFW y Nginx ya configurados. **Este documento es el runbook; el
despliegue real requiere autorización.**

## 1. Arquitectura

```
Internet → Nginx del host (80/443, TLS) → 127.0.0.1:8080 → contenedor frontend
                                                            └─ /api/* → contenedor backend (red interna, sin puertos)
```

- `frontend`: Nginx interno que sirve la SPA compilada y proxifica `/api/`.
- `backend`: FastAPI/Uvicorn (1 worker), SQLite y artefacto ML montados en
  **solo lectura**.
- Ningún puerto interno (8000, 5173) se publica en 0.0.0.0.

## 2. Recursos que se transfieren POR SEPARADO (nunca a Git)

| Recurso | Origen local | Destino en VPS |
|---|---|---|
| Base de datos | `deploy-data/parcels.db` | `~/atlas/deploy-data/parcels.db` |
| Artefacto ML | `deploy-model/exp-zhg-001-demo/` | `~/atlas/deploy-model/exp-zhg-001-demo/` |

Transferencia segura (ejemplos):

```bash
scp deploy-data/parcels.db usuario@ip-vps:~/atlas/deploy-data/
scp -r deploy-model/exp-zhg-001-demo usuario@ip-vps:~/atlas/deploy-model/
```

Backup local antes de actualizar:

```bash
cp deploy-data/parcels.db deploy-data/parcels.db.bak-$(date +%F)
```

## 3. Variables de entorno en la VPS

Crear `~/atlas/.env` (nunca en Git) basado en `.env.example`:

```bash
APP_ENV=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://tu-dominio
EXPERIMENTAL_INFERENCE_ENABLED=false
EXPERIMENTAL_ZHG_ENABLED=false   # cambiar a true SOLO con decisión explícita
```

## 4. Comandos (Docker Engine + Compose Plugin)

```bash
cd ~/atlas
docker compose build              # construir imágenes
docker compose up -d              # iniciar en segundo plano
docker compose ps                 # estado y healthchecks
docker compose logs -f backend    # logs del backend
docker compose restart            # reiniciar servicios
docker compose down               # detener (conserva volúmenes/datos)
docker compose down -v            # OJO: elimina volúmenes; no usarlo con datos
```

Recuperación ante fallos: `restart: unless-stopped` reinicia los
contenedores automáticamente; verificar con `docker compose ps` que ambos
estén `healthy`.

## 5. Actualización

1. Reconstruir la base localmente: `python scripts/build_db.py` (offline).
2. Backups: copiar `parcels.db` y `exp-zhg-001-demo` actuales a respaldo.
3. Subir por scp los recursos nuevos a rutas TEMPORALES y verificar hashes.
4. `git pull` + `docker compose build && docker compose up -d`.
5. Sustituir los recursos por los nuevos y reiniciar `docker compose restart backend`.
6. Verificar: `curl -s https://dominio/api/v1/system/status` y navegación.

## 6. Nginx del host (ejemplo de server block; NO aplicar sin autorización)

```nginx
server {
    listen 443 ssl;
    server_name dominio;
    ssl_certificate /etc/letsencrypt/live/dominio/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dominio/privkey.pem;

    client_max_body_size 2m;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

Opcional (antes de exponer la demo): `limit_req` para limitar la tasa de
inferencias.

## 7. Seguridad

- Los puertos 8000/5173/8080 solo en loopback (8080 lo fija compose.yaml).
- Base de datos y artefacto montados en read-only; el backend solo lee.
- Sin credenciales en imágenes ni en Git (`.dockerignore`, `.gitignore`).
- TLS termina en el Nginx del host.
- La demostración experimental queda desactivada por defecto.

## 8. Recursos estimados

- Medido localmente: inferencia demo p50 81,8 ms; consultas API 1,4–8,2 ms;
  artefacto 51 MB en disco; imagen backend ~1,2 GB (con CatBoost/pandas),
  frontend ~40 MB.
- Recomendado: 2 vCPU / 4 GB mínimos; la VPS (4 vCPU / 8 GB) es suficiente.
- RAM real del proceso con modelo cargado: medir en la VPS
  (`docker stats`) antes de activar la demo.
