# Scripts de datos (offline)

Ejecutar con el venv activo y los CSV originales presentes en `data/raw/`.

| Script | Función | Estado |
|---|---|---|
| `preparar_datos.py` | Normalización, cruce y auditoría (heredado del paquete de datos) | Fase 1 |
| `audit_data.py` | Reproduce `preparar_datos.py` y valida conteos contra `06_resumen_diagnostico.json` | Fase 1 |
| `build_db.py` | Construye SQLite curada | Fase 1 |
| `build_maps.py` | Exporta GeoJSON/teselas | Fase 1 |
| `verify_inputs.py` | Hashes y esquema de entradas | Fase 1 |
