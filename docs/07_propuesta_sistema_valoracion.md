# Fase 6A — Propuesta funcional del sistema de valoración

Fecha: 2026-10-14 · Estado: **propuesta para revisión** (no implementada).

Base de evidencia: `docs/06_fase5_modelo_valor_suelo_zhg.md` y artefactos
reales `exp-zhg-001` (dominante) y `exp-zhg-001-ponderado`. Correcciones
documentales incorporadas en esta fase: la allowlist real es de **19
características** (5 numéricas + 14 categóricas) con **57 bloqueadas**, y el
R² del leave-one-zone-out se declara **no interpretable** (objetivo
constante por zona; solo se usan MAE/MdAPE en LOO).

## 1. Lo que la evidencia permite mostrar hoy (datos verificados)

1. **Mapa zona → valor unitario ZHG**: 11 zonas, 11 valores COP/ha,
   equivalencia `valor_hectarea_agropecuario` = `ZHG_VALOR_` verificada en
   la Fase 5A. Es un **dato de referencia** disponible en las fuentes.
2. **Composición zonal de cada predio**: zonas intersectadas, participación
   porcentual y área de intersección (auditadas; 1.601 predios multizona).
3. **Consolidación admisible**: valor dominante (siempre) y valor ponderado
   por área **solo** con cobertura ≤5 % (744 consistentes + 2.041 dudosas;
   4.924 no aptas).
4. **Estimación ML**: los modelos experimentales no superaron los criterios
   de generalización a zonas nuevas; **no se presentará ninguna predicción
   ML como funcionalidad pública** sin tu autorización expresa.

## 2. Funcionalidad A — Consulta de referencia ZHG (no-ML)

**Definición:** consultar el valor unitario ZHG conocido de un predio
(COP/ha), presentado como dato de referencia catastral zonal, nunca como
predicción de aprendizaje automático ni como avalúo.

**Reglas de presentación por granularidad:**
- **Predio de una sola zona:** valor único de esa zona.
- **Predio multizona:** tabla por zona (código de zona, participación %,
  área de intersección m², valor COP/ha). Consolidación:
  - `dominante`: valor de la zona con mayor participación (siempre
    calculable; se rotula como "zona predominante").
  - `ponderada`: solo si la suma de áreas de intersección difiere ≤5 % del
    área catastral; en caso contrario **no se muestra promedio** y se
    muestra la tabla con la advertencia de cobertura inconsistente.

**Endpoints propuestos (nuevos; no tocan los existentes):**

```text
GET /api/v1/references/zhg/zones
  → lista de zonas con su valor de referencia y aviso de procedencia
    { "items": [{"zone_code":"06","value_cop_ha":547247.2,"source":
      "valor_hectarea_agropecuario = ZHG_VALOR_ (verificado por zona)"}],
      "disclaimer": "Referencia zonal catastral; no es avalúo individual
      ni predicción de aprendizaje automático." }

GET /api/v1/properties/{public_id}/zhg-reference
  → referencia zonal del predio
    { "public_id": "...",
      "zones": [{"zone_code":"03","share_pct":100,"area_intersection_m2":...,
                 "value_cop_ha":1368119.6}],
      "consolidation": {"type":"dominante"|"ponderada"|null,
                        "value_cop_ha":..., "coverage_status":
                        "consistente"|"dudosa"|"no_apta"},
      "provenance": "...", "valuation_date": null, "disclaimer": "..." }
```

**Backend:** nueva tabla SQLite `parcel_zhg_references` (public_id, zone_code,
share_pct, area_intersection_m2, value_cop_ha, coverage_status), construida
offline en `scripts/build_db.py` desde `01_intersecciones_normalizadas.csv`.
No cambia el esquema ni el comportamiento de los endpoints actuales.

**Frontend:** componente reutilizable `ZhgReferenceCard` (ficha del predio) y
sección "Referencia de valor del suelo (ZHG)" en la pantalla Predicción,
con título "Dato de referencia, no predicción", tabla multizona cuando
aplique y avisos de cobertura.

## 3. Funcionalidad B — Estimación ML experimental (condicionada)

**Definición:** estimación generada por un modelo de ML **únicamente para
predios de zonas conocidas del municipio** (interpolación), con rótulo
permanente de experimental y sin capacidad declarada sobre zonas nuevas.

**Estado:** no se habilita. Los resultados de la Fase 5 no justifican
exponerla frente a la referencia trivial (moda zonal gana en zonas fuera;
en zonas conocidas el modelo reproduce la zona). Si en el futuro se desea
más evidencia, se exige un **protocolo prospectivo** (particiones nuevas,
criterios predefinidos, sin reutilizar los tests ya examinados de Fase 5).

**Contrato futuro si se autoriza (no implementado):**

```json
{ "status": "experimental_ml_estimation",
  "kind": "estimacion_ml_experimental",
  "zone_known": true,
  "model_version": "exp-...",
  "value_cop_ha": 550000.0,
  "reference_zhg_cop_ha": 547247.2,
  "warnings": ["solo valida para zonas conocidas del municipio"],
  "disclaimer": "Estimacion experimental de apoyo; no constituye avaluo
                 oficial ni valor comercial." }
```

## 4. Separación estricta de conceptos (UI y API)

| Concepto | Etiqueta | Tratamiento |
|---|---|---|
| Valor ZHG conocido | "Referencia catastral zonal" | Consulta directa; sin métricas de error |
| Estimación ML | "Estimación experimental" | Solo si se autoriza; con versión y limitaciones |
| Avalúo catastral oficial | — | **No lo expide este software** |

## 5. Cambios requeridos por capa

- **Backend (Fase B):** tabla `parcel_zhg_references` en `build_db.py`; 2
  endpoints nuevos en `routers/references.py`; schemas Pydantic; repositorio.
  `POST /api/v1/predictions` permanece **503 MODEL_NOT_READY**.
- **Frontend (Fase C):** `ZhgReferenceCard` en ficha; sección de referencia
  en `/prediccion`; textos de procedencia y cobertura; sin cambios en
  portada, mapa ni diseño.
- **Pruebas:** backend (zonas con valores correctos, predio monozona,
  multizona con consolidación admisible/no admisible, disclaimers,
  contrato tipado, 503 intacto); frontend (render monozona/multizona,
  aviso de cobertura, ausencia de lenguaje de predicción para la
  referencia); e2e (ficha → sección ZHG; predicción → sección referencia).

## 6. Limitaciones que deben comunicarse al usuario final

1. El valor ZHG es una referencia zonal: **no** es avalúo individual del
   predio ni valor comercial; su vigencia oficial no está certificada en
   los datos recibidos.
2. En predios multizona sin cobertura consistente no se muestra un valor
   consolidado (solo la tabla por zona).
3. La estimación ML experimental no generaliza a zonas no observadas y no
   está activa.
4. Nada de lo mostrado constituye avalúo oficial.

## 7. Orden de implementación recomendado (tras tu aprobación)

1. `build_db.py`: tabla `parcel_zhg_references` + pruebas de datos.
2. Backend: `references` router + schemas + tests (con 503 intacto).
3. Frontend: `ZhgReferenceCard` + sección en Predicción + tests.
4. Verificación end-to-end y commit local.
5. (Opcional, solo con autorización) estimación ML experimental con
   protocolo prospectivo.

**Se solicita aprobación de esta propuesta antes de implementar.**
