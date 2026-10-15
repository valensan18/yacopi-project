# Fase 6B — Implementación de referencias ZHG

Fecha: 2026-10-14 · Rama dev · Autorización: aprobada (Fase 6B).

## 1. Arquitectura implementada

Consulta de **referencias ZHG** (dato económico territorial) separada
explícitamente de la estimación ML (no habilitada) y del avalúo oficial (no
emitido). Capas:

- **Datos**: tablas `zhg_zones` y `parcel_zhg_references` en SQLite,
  construidas offline por `scripts/build_db.py` (idempotente).
- **Backend**: router `references.py` con dos endpoints; repositorio
  extendido; schemas Pydantic; errores normalizados; `POST /predictions`
  intacto en 503.
- **Frontend**: `ZhgReferenceCard` (ficha del predio y pantalla
  Predicción), sección de consulta por `public_id` con los tres conceptos
  diferenciados visualmente.

## 2. Origen de los datos

- `valor_hectarea_agropecuario` (CSV de intersecciones), equivalente a
  `ZHG_VALOR_` por zona (equivalencia verificada en Fase 5A para las 11
  zonas, normalizando códigos a 2 dígitos).
- Fuente normalizada usada: `01_intersecciones_normalizadas.csv` (no se
  modifican los CSV originales).
- `reference_date = null` en todas las respuestas (vigencia no acreditada).

## 3. Tablas y relaciones SQLite

| Tabla | Contenido |
|---|---|
| `zhg_zones` | 11 zonas: `zone_code` (PK), `value_cop_ha`, `source_column`, `source_file` |
| `parcel_zhg_references` | 9.434 filas predio-zona: `public_id` (FK→parcels), `zone_code`, `value_cop_ha`, `area_intersection_m2`, `share_pct`, `coverage_status`, `source_file`, `dataset_version`; `UNIQUE(public_id, zone_code)` |

`coverage_status` por predio: `consistente` (dif ≤1 %), `dudosa` (1–5 %),
`no_apta` (>5 %) entre la suma de áreas de intersección y el área catastral.
La reconstrucción es reproducible (`python scripts/build_db.py`).

## 4. Endpoints

| Método | Ruta | Comportamiento |
|---|---|---|
| GET | `/api/v1/references/zhg/zones` | 11 zonas con valor unitario y procedencia |
| GET | `/api/v1/properties/{public_id}/zhg-reference` | Referencias ZHG del predio; 404 si no existe; `zones: []` + limitation si no tiene referencias |

## 5. Contratos JSON (ejemplos reales verificados)

**Zonas (fragmento):**
```json
{
  "items": [
    {"zone_code": "01", "value_cop_ha": 3192276.7, "source_column": "valor_hectarea_agropecuario"},
    {"zone_code": "11", "value_cop_ha": 91206.6, "source_column": "valor_hectarea_agropecuario"}
  ],
  "unit": "COP/ha",
  "reference_type": "zhg_zonal_reference",
  "source_description": "valor_hectarea_agropecuario (CSV de intersecciones), equivalente a ZHG_VALOR_ por zona geoeconómica (equivalencia verificada en Fase 5A).",
  "reference_date": null,
  "limitations": [
    "Referencia zonal catastral; no es un avalúo individual certificado del predio.",
    "La vigencia oficial del valor zonal no está acreditada en los datos recibidos (reference_date = null).",
    "No es una predicción de aprendizaje automático."
  ]
}
```

**Predio multizona (real, cobertura no_apta):**
```json
{
  "public_id": "p_002deb3e2c747750",
  "unit": "COP/ha",
  "reference_type": "zhg_zonal_reference",
  "zones": [
    {"zone_code": "02", "value_cop_ha": 1824156.1, "area_intersection_m2": 300505.7, "share_pct": 12.63},
    {"zone_code": "07", "value_cop_ha": 456041.7, "area_intersection_m2": 2078826.4, "share_pct": 87.37}
  ],
  "dominant_zone": {
    "zone_code": "07",
    "value_cop_ha": 456041.7,
    "share_pct": 87.37,
    "note": "zona con mayor participación del predio; no representa automáticamente el valor unitario de toda la propiedad cuando hay varias zonas"
  },
  "weighted_reference": null,
  "provisional_weighted_reference": null,
  "coverage_status": "no_apta",
  "source_description": "…",
  "reference_date": null,
  "limitations": ["…", "…", "…"]
}
```

## 6. Reglas multizona implementadas

- **Monozona**: valor único + zona + cobertura; rótulo "dato · no predicción".
- **Multizona**: tabla zona | COP/ha | área | participación; fila dominante
  resaltada; nota de que la zona predominante no representa el valor de
  toda la propiedad.
- **Ponderación** (Σ valor×área / Σ área, solo áreas de intersección):
  - `weighted_reference`: solo `consistente` (≤1 %).
  - `provisional_weighted_reference`: `dudosa` (1–5 %), marcada PROVISIONAL.
  - `no_apta` (>5 %): **ningún ponderado** (decisión de Fase 6B, más
    estricta que la propuesta 6A que permitía dudosa como consolidación).
- Zonas sin valor o sin área se excluyen de la ponderación con aviso (nunca
  se completan con cero).

## 7. Control de calidad de superficies

La cobertura se calcula contra el área catastral de cada predio; el
denominador de la ponderación es la suma de áreas de intersección (nunca el
área total repetida). Los estados se exponen en `coverage_status` y en las
etiquetas de los objetos ponderados.

## 8. Comportamiento del frontend

- **Ficha del predio** (`/predios/:public_id`): tarjeta
  `ZhgReferenceCard` con valor, zonas, cobertura, consolidación admisible y
  limitaciones; estados de carga/error/sin datos.
- **Pantalla Predicción** (`/prediccion`): sección de consulta por
  `public_id` con etiquetas diferenciadas: "Referencia ZHG · dato económico
  territorial", "Predicción ML · no habilitada oficialmente" (bloqueo real
  503) y "Avalúo oficial · no emitido por este software".

## 9. Advertencias y limitaciones comunicadas

1. Referencia zonal, no avalúo individual certificado.
2. Vigencia no acreditada (`reference_date: null`).
3. No es predicción de aprendizaje automático.
4. Sin consolidación ponderada cuando la cobertura es inconsistente.

## 10. Pruebas ejecutadas

- Backend: 37 pruebas (9 nuevas de referencias: zonas, monozona,
  multizona dudosa con provisional, no_apta sin ponderado, predio sin
  referencias, 404, sin IDs privados, 503 intacto).
- Frontend: 17 pruebas (2 actualizadas/creadas: ficha con tarjeta ZHG y
  consulta en Predicción con separación de conceptos).
- Suite total: **77 pytest + 17 vitest**; `ruff` y `oxlint` limpios; build
  TS/Vite OK.
- Verificación funcional con la base real: 11 zonas correctas, monozona y
  multizona responden según reglas, 404 y 503 intactos.

## 11. Consideraciones para futura integración ML

- El contrato de respuesta evita cualquier propiedad que permita leer las
  referencias como predicciones (`reference_type: zhg_zonal_reference`,
  sin `prediction_*`).
- Para una futura estimación ML (solo con autorización) se mantiene el
  contrato de `docs/07_propuesta_sistema_valoracion.md` §3 y el protocolo
  prospectivo allí definido.
- `label_contract.yaml` permanece `pending_verification`; ningún artefacto
  se promovió.
