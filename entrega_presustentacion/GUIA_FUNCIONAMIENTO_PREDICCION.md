# Guía de funcionamiento — Estimación con Machine Learning (demostración académica)

## Qué hace la funcionalidad

Desde la página **Predicción** de Atlas Vivo, un usuario puede consultar un
predio por su identificador público y obtener **dos valores separados**:

- **A. Referencia geoeconómica ZHG**: dato territorial consultado de las
  fuentes (NO es una predicción).
- **B. Estimación Random Forest**: valor calculado en el momento por el
  modelo `atlas-vivo-rf-v1` mediante `model.predict()` real.

## Flujo de uso

1. Abrir `https://atlasvivo.xyz/prediccion` (o el entorno local).
2. Buscar la sección **"Estimación con Machine Learning — Demostración
   académica"**.
3. Escribir el identificador público de un predio (ejemplo verificado:
   `p_6049c425ce3cf79d`).
4. Pulsar **"Estimar con Random Forest"**.
5. Leer el resultado: estimación en COP/ha, referencia ZHG, diferencia,
   condiciones de aplicación, métricas de validación reales y limitaciones.

## Qué muestra el resultado

| Elemento | Contenido |
|---|---|
| Predio | public_id (opaco; nunca el número predial) |
| Valor estimado | COP/ha, redondeado a enteros |
| Modelo | `atlas-vivo-rf-v1` · versión `1.0.0` · rol `demostracion_academica` |
| Variable objetivo | `VALOR_TERRENO_Ha = VALOR_AVALUO × 10000 / AREA_TERRENO_M2` |
| Referencia ZHG | valor de la zona dominante (dato), con nota que la distingue de la predicción |
| Diferencia | absoluta y relativa entre B y A |
| Evaluación | MAE/R²/MdAPE del test espacial sellado v2 + estabilidad en 5 pliegues |
| Limitaciones | incluye: no superó a ZHG en MAE ni MdAPE en las 5 particiones |
| Aviso | "Estimación orientativa… no constituye un avalúo oficial, precio de mercado ni valor exclusivo de suelo verificado" |

## Estados posibles

| Estado | Respuesta |
|---|---|
| Desactivada (default) | 503 `VALOR_V1_DISABLED` — la sección muestra que la funcionalidad está implementada pero desactivada en el entorno |
| Artefacto no cargado | 503 `VALOR_V1_UNAVAILABLE` |
| Predio inexistente | 404 `PROPERTY_NOT_FOUND` |
| Predio no admitido (con construcción / fuera de la cohorte A) | 422 `UNSUPPORTED_PARCEL` con el motivo |
| Valores fuera de dominio | 422 `OUT_OF_DOMAIN` con los campos afectados |
| Predio admitido | 200 con la respuesta completa |

## Cómo se habilita (solo servidor)

```bash
# En la VPS: después de transferir el artefacto (ver docs/19)
VALOR_V1_ENABLED=true docker compose up -d backend
```

La predicción oficial sigue respondiendo 503 MODEL_NOT_READY y la
demostración ZHG permanece desactivada: esta funcionalidad no las sustituye.

## Capturas

- `capturas/captura_01_seccion_desactivada.png` — sección con la
  funcionalidad desactivada (estado por defecto).
- `capturas/captura_02_resultado_estimacion.png` — resultado real de
  `p_6049c425ce3cf79d` (estimación 198.093 COP/ha vs referencia ZHG
  182.414 COP/ha).
- `evidencias/respuesta_api_ejemplo.json` — respuesta JSON completa del
  endpoint `POST /api/v1/predictions/valor-terreno-v1`.
