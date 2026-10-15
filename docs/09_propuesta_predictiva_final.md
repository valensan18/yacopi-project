# Fase 7A — Propuesta final de la funcionalidad predictiva

Fecha: 2026-10-14 · Estado: **propuesta para revisión** (nada implementado).

## 1. Objetivo

Definir la forma técnicamente más defendible de incorporar aprendizaje
automático a Atlas Vivo conforme al anteproyecto, sin reabrir criterios ya
cerrados y sin activar nada sin autorización.

## 2. Evidencia revisada (Fases 5, 6A, 6B)

| Hecho | Fuente |
|---|---|
| Objetivo ZHG = 11 zonas, 11 valores COP/ha; equivalencia `valor_hectarea_agropecuario` = `ZHG_VALOR_` verificada | Fase 5A (`docs/06` §5) |
| Forest: MAE predio 73.765 / espacial 132.183 / zonas fuera 423.363 COP/ha; R² zonas fuera −1,70 | `ml/artifacts/exp-zhg-001/metrics.json` |
| Ningún modelo superó el criterio predefinido (`aceptado=false`); la "moda zonal" trivial gana en zonas nuevas | Fase 5G |
| Consulta de referencias ZHG implementada y verificada (dato, no predicción) | Fase 6B (`docs/08`) |
| Predicción oficial en 503 MODEL_NOT_READY; experimental del proxy desactivada | Fase 3/6B |

## 3. Conciliación 9.447 → 9.434 (evidencia)

- Filas originales del CSV de intersecciones: **9.447**.
- **13 filas colapsadas** por agregación (predio, zona): incluyen las 3
  filas exactamente duplicadas ya documentadas en la Fase 1 y 13 pares
  predio-zona repetidos (un predio puede tener varias filas para la misma
  zona). 9.447 − 13 = **9.434 pares (predio, zona) distintos**.
- `parcel_zhg_references` en SQLite contiene **9.434 filas**, una por par
  distinto, con áreas y participaciones sumadas por zona. La agregación
  nunca repite el área total del predio por cada zona. Conciliación
  cerrada y verificada (script de comprobación en el historial de la fase).

## 4. Qué puede demostrarse honestamente con los datos actuales

1. **Referencia ZHG conocida** (ya operativa): dato verificable por predio.
2. **Estimación ML en zonas conocidas**: los modelos reproducen la zona
   mediante coordenadas y atributos físicos (R² 0,82, MAE 73,8k COP/ha en
   test por predio). Es un resultado real pero su utilidad práctica frente
   a la consulta directa es **marginal**: la referencia ya está disponible.
3. **Generalización a zonas no observadas**: **no demostrada** (falla el
   criterio de Fase 5; no se reclama).

## 5. ¿Aporta valor el ML frente a la consulta directa?

- **Como estimador independiente del valor del suelo: no**, con los datos
  actuales. Para zonas conocidas duplica la tabla zonal; para zonas nuevas
  no generaliza. Decirlo explícitamente es parte de la entrega honesta.
- **Como cumplimiento del anteproyecto (OE2 y OE3) y como evidencia
  científica:** sí, en forma de **demostración experimental acotada**, en
  la que el ML se muestra SIEMPRE junto a la referencia consultable y con
  su diferencia. El valor es pedagógico y de trazabilidad metodológica, no
  de estimación adicional.

## 6. Recomendación concreta

**Opción recomendada: "Demostración ML experimental acotada a zonas
conocidas", subordinada a la consulta de referencia ZHG.**

Características:

- **Nada nuevo que evaluar**: se usa el Random Forest ya ajustado en Fase 5
  (hiperparámetros documentados). Solo se requiere **serializar una vez** un
  artefacto determinístico ajustado al conjunto completo de zonas conocidas
  (fit, no experimento de evaluación), empaquetado con `feature_schema.json`
  y con los **rangos de entrenamiento** (min/max numéricos y categorías
  vistas) para controles de dominio. Identificador sugerido:
  `exp-zhg-001-demo`.
- **Endpoint nuevo y separado** (no toca el 503 oficial):
  `POST /api/v1/predictions/experimental-zhg`, desactivado por defecto con
  `EXPERIMENTAL_ZHG_ENABLED=false` (mismo patrón que el proxy).
- **Solicitud por `public_id`**, nunca por características crudas: el
  backend deriva las 19 variables desde SQLite con el **mismo
  preprocesamiento del entrenamiento** (evita divergencias y fuga manual).
- **Guards obligatorios** (ver §7).

## 7. Contrato propuesto (no implementado)

```json
{
  "status": "experimental_ml_zhg_estimation",
  "kind": "estimacion_ml_experimental",
  "zone_known": true,
  "public_id": "p_…",
  "unit": "COP/ha",
  "reference": {
    "zone_code": "07",
    "value_cop_ha": 456041.7,
    "source": "referencia ZHG consultada (dato)"
  },
  "estimate": {
    "value_cop_ha": 452000.0,
    "model_version": "exp-zhg-001-demo",
    "delta_vs_reference_cop_ha": -4041.7
  },
  "warnings": [
    "válida solo para predios de zonas conocidas del municipio",
    "la referencia ZHG ya era consultable; esta estimación no la reemplaza"
  ],
  "no_confidence_interval": true,
  "disclaimer": "Estimación experimental de apoyo académico. No constituye avalúo oficial ni valor comercial."
}
```

Errores definidos: `ZONE_UNKNOWN` (409) cuando el predio no tiene zona
conocida; `OUT_OF_DOMAIN` (422) con avisos cuando alguna característica
queda fuera de los rangos/categorías de entrenamiento;
`EXPERIMENTAL_ZHG_DISABLED` (503) por defecto.

## 8. Controles para evitar malinterpretaciones

1. Solo predios con zona conocida (referencia ZHG presente).
2. Siempre se responde la referencia y la estimación **juntas** (nunca la
   estimación sola).
3. Sin intervalos de confianza (no hay calibración que los respalde).
4. Detección de fuera de dominio con rangos/categorías almacenados en el
   artefacto; aviso visible, nunca silencioso.
5. Rótulos permanentes: "experimental", "no sustituye la referencia", "no
   es avalúo". La UI muestra el delta estimación−referencia.
6. Desactivada por defecto; solo desarrollo local hasta autorización.

## 9. Ruta /prediccion (conservando los tres conceptos)

Ya implementado y se conserva:
- **Referencia ZHG** — dato económico territorial (bloque principal).
- **Predicción ML** — bloqueo oficial real (503) y explicación.
- **Avalúo oficial** — no emitido por este software.

Añadiría (solo si se aprueba): dentro del bloque ML, una subsección
"Demostración experimental (zonas conocidas)" que solo aparece cuando
`EXPERIMENTAL_ZHG_ENABLED=true`: entrada de `public_id`, resultado
estimación + referencia + delta + advertencias. Sin cambios de diseño de
Fase 6B.

## 10. Evaluación independiente futura: qué datos harían falta

Una repartición nueva de los mismos 11 valores zonales **no** es validación
externa. Para demostrar capacidad real de valoración independiente se
necesitaría **datos nuevos**, p. ej.:
- valores individuales de terreno por predio (fecha, método, superficie) de
  una fuente distinta, o
- territorios/zonas adicionales no incluidas en los 11 valores actuales,
  o
- variables físicas no disponibles hoy (suelos, pendiente, distancias de
  acceso a mercados).

Sin esto, el estado científico queda como está: referencia consultable +
demostración experimental honesta.

## 11. Lo que NO se hará

- No se cambian los criterios de aceptación de Fase 5 ni se declara
  validado ningún modelo.
- No se activa `POST /api/v1/predictions` (sigue 503).
- No se activa la inferencia experimental sin autorización.
- No se presentan avalúos ni se inventan métricas.

## 12. Plan de implementación si se aprueba (orden)

1. `ml/src/yacopi_ml/zhg/export_demo.py`: fit determinístico del Forest con
   los hiperparámetros de Fase 5 sobre el conjunto de zonas conocidas +
   empaquetar artefacto con feature_schema y rangos (sin re-evaluar).
2. Backend: flag `EXPERIMENTAL_ZHG_ENABLED`, carga verificada del artefacto,
   endpoint `experimental-zhg` con guards y contrato §7.
3. Frontend: subsección de demostración en `/prediccion` con
   estimación+referencia+delta y advertencias.
4. Pruebas: guards (ZONE_UNKNOWN, OUT_OF_DOMAIN, desactivado por defecto),
   serialización/carga, contrato tipado, tests de UI; suites existentes
   intactas.
5. Commit local; **sin push y sin activar en producción** hasta revisión.

**Se solicita revisión y aprobación de esta propuesta antes de implementar.**
