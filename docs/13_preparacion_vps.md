# Preparación del módulo de Predicción para VPS (Fase 8.5)

Fecha: 2026-10-15 · Rama dev · **Propuesta técnica; sin despliegue realizado.**

## 1. Alcance y decisiones

- La funcionalidad de Predicción queda **visible desde la navegación
  principal** (enlace "Predicción" en escritorio y móvil) y es operable
  desde el navegador: selector de predios + consulta ZHG + demostración
  experimental cuando el servidor la habilita.
- El control de activación sigue en el backend
  (`EXPERIMENTAL_ZHG_ENABLED`); el frontend la detecta vía
  `/system/status` (`experimental_zhg.habilitado/disponible`).
- Predicción oficial: **503 MODEL_NOT_READY** permanente hasta autorización
  y etiqueta verificada (sin cambios).

## 2. Cambios implementados en esta fase

### Frontend
- Enlace **Predicción** en la navegación principal (escritorio y móvil).
- **Selector de predios** (`ParcelSelector`): buscador con autocompletado
  que reutiliza el catálogo vía el nuevo filtro `public_id_prefix`
  (combobox accesible: teclado, lista de opciones con destino y área).
  Sustituye la copia manual del identificador en Predicción (consulta ZHG
  y demostración).
- **Timeouts de red** (15 s) en el cliente API; errores de red mapeados.
- Sin direcciones `localhost` codificadas: las llamadas usan `/api/v1`
  relativo (mismo origen tras el proxy inverso). El proxy de Vite solo
  aplica en desarrollo.

### Backend
- **`GET /properties` admite `public_id_prefix`** (aditivo y compatible;
  validado con patrón `^p_[0-9a-f]{0,16}$` y longitud máxima).
- **Errores sin rutas del servidor**: los detalles de error ya no incluyen
  rutas internas de la base ni del artefacto (corregido en
  `services/demo.py`, `services/prediction.py` y routers de consulta).

## 3. Comportamiento esperado en la web

| Estado del servidor | Comportamiento |
|---|---|
| Demo deshabilitada (por defecto) | Sección Predicción visible; explica que la demostración no está disponible; consulta ZHG y bloqueo oficial operativos |
| Demo habilitada + artefacto cargado | Formulario funcional con selector; referencia + estimación + diferencias en COP/ha + interpretación + limitaciones |
| Demo habilitada sin artefacto | Error comprensible (503 `EXPERIMENTAL_ZHG_UNAVAILABLE`, sin rutas internas) |
| Predio fuera de dominio / multizona | Rechazo con explicación (422 `OUT_OF_DOMAIN` / `UNSUPPORTED_MULTIZONE`) |
| Sin conexión | Estados de error y reintento; timeout de 15 s |

## 4. Medidas de seguridad reales (existentes y pendientes)

**Existentes (comprobadas):**
- `public_id` opacos en todas las respuestas; identificadores privados
  nunca se exponen (probado).
- Errores normalizados sin trazas ni rutas internas (corregido en esta
  fase).
- Entradas validadas con Pydantic (rangos, patrones, longitudes).
- Modelos solo desde el directorio local configurado (`MODEL_DIR`); no hay
  endpoint de carga de archivos.
- CORS restringido por variable de entorno (innecesario en same-origin).
- La correspondencia `public_id ↔ identificador interno` vive en archivos
  locales fuera de Git (artefacto), nunca en el frontend.

**Pendientes (a configurar en la VPS, no ficticios):**
- **Limitación de tasa** de `POST` de inferencia y consultas: implementar
  con Nginx (`limit_req`) o middleware; hoy no existe en la app.
- **HTTPS**: certificado TLS en el proxy (Let's Encrypt); la app no termina
  TLS por sí misma.
- No exponer directorios de datos/artefactos en la raíz web del proxy.
- Autenticación: no requerida para consulta pública del prototipo; si la
  demostración se expone públicamente, evaluar una clave de acceso simple o
  dejar la demo desactivada (decisión del equipo).

## 5. Activación en el servidor (cuando se decida)

```
EXPERIMENTAL_ZHG_ENABLED=true   # entorno del proceso FastAPI
MODEL_DIR=/srv/atlas/model       # contiene exp-zhg-001-demo/
DATABASE_PATH=/srv/atlas/data/parcels.db
```
El frontend no cambia: detecta `experimental_zhg` en `/system/status`.
La configuración por defecto del repositorio permanece desactivada.

## 6. Arquitectura propuesta para la VPS

```
Internet → Nginx (443, TLS, sirve React compilado, /api/v1 → proxy)
              └→ Uvicorn (127.0.0.1:8000, 1 worker, FastAPI)
                    ├─ SQLite parcels.db (solo lectura)
                    └─ MODEL_DIR/exp-zhg-001-demo (solo lectura)
```

| Elemento | Detalle |
|---|---|
| Servicios | Nginx + Uvicorn (1 worker) |
| Frontend | `dist/` compilado servido por Nginx |
| Backend | FastAPI en puerto interno 8000 |
| Base de datos | SQLite montada read-only (la app solo lee) |
| Artefacto ML | Montado read-only; 51 MB en disco (model.joblib 45,6 MB + features.json 5,1 MB) |
| Variables de entorno | `APP_ENV=production`, `DATABASE_PATH`, `MODEL_DIR`, `EXPERIMENTAL_ZHG_ENABLED`, `CORS_ORIGINS`, `LOG_LEVEL` |
| HTTPS | Terminación TLS en Nginx (Let's Encrypt) |
| Recursos | **Medido**: inferencia demo p50 81,8 ms / p95 84,0 ms (local i7-9700); consultas API p50 1,4–8,2 ms (Fase 3). **Pendiente de medir en VPS**: RAM real del proceso con modelo cargado y CPU en carga concurrente. Punto de partida recomendado: 2 vCPU / 4 GB (consistente con la guía §14.2) |
| Persistencia | DB y artefacto en volúmenes; backup diario de la DB; los archivos de código se reemplazan por versión |
| Actualización | 1) reconstruir DB offline (`scripts/build_db.py`); 2) subir DB/artefacto a rutas nuevas; 3) desplegar código; 4) reiniciar servicio; 5) verificar `/system/status` y smoke |

## 7. Riesgos de seguridad y disponibilidad

- Exponer el directorio `ml/artifacts/` o la DB vía web → **no montarlos en
  la raíz pública**; solo el backend los lee.
- Abuso de la inferencia (peticiones repetidas) → limitación de tasa en
  Nginx antes de exponer la demo.
- Servidor con demo habilitada y artefacto ausente → 503 controlado y claro.
- Sin HTTPS no se expondrá el servicio (requisito previo).
- El modelo sigue siendo experimental: las advertencias científicas se
  mantienen en UI y API.

## 8. Verificaciones realizadas

- Pruebas: 94 pytest (2 nuevas del filtro `public_id_prefix`), 28 vitest
  (selector y flujos actualizados), ruff/oxlint limpios, build OK.
- Medición real de inferencia demo (aislado, artefacto real): n=60,
  p50 81,8 ms, p95 84,0 ms, max 102,6 ms.
- Navegación y selector verificados con Playwright (escritorio y móvil):
  enlace "Predicción" presente, combobox con opciones, selección y consulta
  real; demo desactivada por defecto mostrada correctamente.
- Oficial 503 verificado de nuevo tras los cambios.

## 9. Pendientes reales para exponer públicamente

1. Contratar/proveer VPS, dominio y DNS (no realizados).
2. Configurar Nginx + TLS + limitación de tasa (no existe aún en la app).
3. Medir RAM/CPU reales en la VPS con carga.
4. Decidir si la demo se activa públicamente o permanece apagada.
5. Etiqueta de suelo verificada para, con autorización, habilitar la
   predicción oficial (fuera del alcance actual).
