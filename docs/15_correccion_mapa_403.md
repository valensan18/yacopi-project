# Doc 15 — Corrección del mapa base en producción (HTTP 403 de teselas)

**Fecha:** 2026-10-15 · **Rama:** `dev` · **Alcance:** Nginx interno del contenedor frontend.

## 1. Descripción del fallo

En producción (https://atlasvivo.xyz/mapa) las teselas del mapa base se mostraban
como imágenes de error con el mensaje:

> 403 Access blocked
> "App is not following the tile usage policy of OpenStreetMap's volunteer-run servers."

Los puntos territoriales (predios, ZHF, ZHG) sí cargaban: solo fallaba el mapa base.

## 2. Condiciones donde ocurre

- Solo en el entorno Docker de producción; en desarrollo local no se reproducía.
- Afecta a la capa base `TileLayer` de Leaflet, no a los marcadores ni a la API.

## 3. Proveedor y URL de las teselas

El frontend usa `frontend/src/lib/basemap.ts`:

- Si existe `VITE_CARTO_BASEMAPS_KEY` → CARTO Dark Matter (`basemaps.cartocdn.com`).
- Sin clave (caso de producción, porque `.env.local` no se copia al build) →
  respaldo OpenStreetMap estándar:

```
https://tile.openstreetmap.org/{z}/{x}/{y}.png
```

En producción no hay clave CARTO en el build, por lo que el proveedor afectado es
**OpenStreetMap (`tile.openstreetmap.org`)**.

## 4. Evidencia del HTTP 403

Capturado en producción por el equipo: respuesta 403 con el mensaje de la política
de teselas de OSM (ver §1). La cabecera efectiva en producción se verificó con:

```
curl -sSI https://atlasvivo.xyz/mapa | grep -i referrer-policy
→ Referrer-Policy: same-origin
```

## 5. Análisis de Referrer-Policy

- `deploy/nginx-app.conf` (Nginx interno del contenedor frontend) emitía
  `Referrer-Policy: same-origin`.
- Esa política elimina la cabecera `Referer` en todas las peticiones entre
  orígenes, incluidas las teselas de `tile.openstreetmap.org`.
- La [política oficial de teselas de OSM](https://operations.osmfoundation.org/policies/tiles/)
  exige: *"From web pages, ensure a valid HTTP Referer header is sent"* y prohíbe:
  *"Set a restrictive Referrer-Policy that prevents the HTTP Referer header being sent"*.
  El incumplimiento es motivo de bloqueo (403) sin aviso.
- El Nginx del host no añade su propia cabecera (solo aparece una instancia en la
  respuesta de producción); de todos modos debe verificarse tras el despliegue.

## 6. Causa confirmada

La cabecera `Referrer-Policy: same-origin` del Nginx interno eliminaba el
`Referer` de las peticiones de teselas, incumpliendo la política de uso de OSM.
El proveedor bloqueaba esas peticiones con HTTP 403.

## 7. Solución adoptada

En `deploy/nginx-app.conf`:

```nginx
add_header Referrer-Policy strict-origin-when-cross-origin always;
```

`strict-origin-when-cross-origin` (valor por defecto de los navegadores modernos)
envía el origen HTTPS (`https://atlasvivo.xyz`) a orígenes externos, sin filtrar
rutas completas de navegación. Cumple la política de OSM y mantiene el resto de
cabeceras de seguridad (`X-Content-Type-Options`, `X-Frame-Options`) intactas.
No hay CSP configurada que afecte imágenes externas.

Además se endureció `.dockerignore`: el patrón `.env.*` solo excluía archivos
en la raíz del contexto; se añadieron `**/.env` y `**/.env.*` para cubrir
archivos anidados (p. ej. `frontend/.env.local`). Sin este ajuste, una clave
CARTO presente localmente quedaba incrustada en el bundle de la imagen local
(verificado inspeccionando el asset compilado y reconstruyendo sin caché;
tras el ajuste la clave ya no aparece en la imagen).

## 8. Política de uso del proveedor

OpenStreetMap permite el uso interactivo normal (vista por un humano, teselas del
viewport actual, caché del navegador) siempre que haya: URL correcta HTTPS,
atribución visible (Leaflet la muestra en la esquina inferior), y `Referer`/UA
válidos. No permite descargas masivas, prefetch ni proxies que oculten la
identidad. Para tráfico alto recomienda un proveedor comercial o teselas propias.

Riesgo residual: para una aplicación pública con tráfico elevado, OSM puede
retirar el acceso sin aviso. Alternativa ya soportada por el código: CARTO Dark
Matter con `VITE_CARTO_BASEMAPS_KEY` (requiere cuenta y clave de uso en
navegador; el usuario decide si activarla).

## 9. Pruebas realizadas

- Cabecera OSM verificada: peticiones a `tile.openstreetmap.org/0/0/0.png`
  responden 200 con `Referer` válido (evidencia con curl).
- Vitest (frontend) completo, incluido `basemap.test.ts`.
- Oxlint sin hallazgos.
- Build de producción del frontend OK.
- `docker compose config` válido.
- Stack Docker local reconstruido (solo imagen frontend; backend sin cambios):
  navegación Playwright sobre `/mapa` verificando que las peticiones de teselas
  llevan `Referer` y responden 200, puntos territoriales visibles, zoom/pan y
  atribución cartográfica presentes, sin errores de consola.
- Regresiones de la API: `POST /api/v1/predictions` sigue en 503
  `MODEL_NOT_READY`; `POST /api/v1/predictions/experimental-zhg` sigue en 503
  `EXPERIMENTAL_ZHG_DISABLED`; `/api/v1/system/status` 200.
- Inspección de la imagen compilada: tras reconstruir sin caché con el
  `.dockerignore` corregido, la clave CARTO ya no aparece en los assets.

## 10. Riesgos pendientes

- La validación definitiva (403 resuelto en producción) requiere reconstruir la
  imagen del frontend en la VPS: ver procedimiento §11.
- Verificar que el Nginx del host no agregue una política más restrictiva
  (duplicada o contradictoria) después del despliegue.
- Si el número de visitas crece, evaluar CARTO (clave de navegador, con
  allowlist de dominio) u otro proveedor comercial.

## 11. Procedimiento de actualización (pendiente de autorización)

```bash
cd /home/atlasadmin/atlas
git fetch origin && git checkout dev && git pull --ff-only origin dev
docker compose build frontend
docker compose up -d frontend
curl -sSI https://atlasvivo.xyz/mapa | grep -i referrer-policy
# esperado: Referrer-Policy: strict-origin-when-cross-origin
```

Luego verificar en navegador real (escritorio y móvil) que las teselas carguen
con 200 y la atribución siga visible.
