# ADR-0002 — Reutilización del pipeline, esquema SQLite y mapas (Fase 1)

- **Fecha:** 2026-10-14
- **Estado:** Aceptado

## Contexto

La Fase 1 debía validar los datos sin rehacer el trabajo previo, verificar
CRS, generar mapas para Leaflet y construir la base de consulta.

## Decisiones

1. **Reutilizar `preparar_datos.py` sin cambios funcionales.** Se copió a
   `scripts/` y se conserva byte-idéntico como referencia de reproducibilidad;
   queda excluido del lint en `pyproject.toml` (estilo heredado). La
   reproducibilidad se prueba comparando 24 claves contra
   `tests/fixtures/reference_diagnostico.json` (0 diferencias) y ejecutando
   el pipeline dos veces (JSON idénticos).
2. **Verificación de CRS por evidencia, no por supuesto:** SRID 9377 en las
   geometrías de la primera fuente y 3116 en `geom` ZHF, auditados en todas
   las filas ZHF y en una muestra de intersecciones. Los polígonos se
   reproyectan a EPSG:4326 con pyproj y se simplifican 15 m preservando
   topología; geometrías inválidas se reparan con `make_valid` (0 casos en
   la práctica) y se registran.
3. **SQLite con 7 tablas** (`parcels`, `parcel_features`,
   `parcel_value_references`, `quality_flags`, `model_targets`,
   `zhf_only_parcels`, `dataset_meta`). `public_id` opaco determinista
   (`p_` + SHA-256[:16]); `parcel_source_id` (numero_predial) vive solo en
   esta base local no versionada. Las referencias económicas se guardan con
   `es_etiqueta_validada = 0` y `valuation_date = NULL`.
4. **Allowlist en `features.yaml`**: 20 candidatas permitidas (auditadas con
   cardinalidad/cobertura real) y 31 columnas bloqueadas (identificadores,
   precios zonales, derivadas de área y contexto geoeconómico). La variable
   objetivo permanece `pending_verification` (Ruta B solo experimental).

## Alternativas rechazadas

- Reescribir el pipeline: rompería la trazabilidad con la auditoría previa.
- Corregir silenciosamente áreas o zonas discordantes: se conservan como
  banderas sin eliminar registros.
- Guardar `numero_predial` en rutas públicas: se usará `public_id` opaco.

## Riesgos

- Sin diccionario oficial, la semántica de códigos ZHF/CLC sigue como
  pendiente #2; no afecta la estructura de datos.
- El reprocesamiento de EWKB en cada petición está prohibido: los mapas se
  preprocesan (5,2 MB polígonos + 1,7 MB puntos), a servir con bbox/límites
  en Fase 3.

## Pruebas asociadas

- `ml/tests/test_data_integrity.py` (17 pruebas en total de la fase).
