# Capas de datos

| Carpeta | Contenido | Versionado |
|---|---|---|
| `raw/` | CSV originales inmutables + `data_manifest.json` (SHA-256) | NO |
| `processed/` | Salidas de `scripts/` (consolidados, banderas, SQLite) | NO |
| `external/` | Etiquetas verificadas de suelo si llegan | NO |
| `splits/` | Particiones congeladas (IDs + hashes) | NO |
| `maps/` | GeoJSON/teselas derivados autorizados | NO |

Los originales de trabajo viven fuera del repo (aporte del equipo). Aquí solo
copian los archivos necesarios para reproducir el pipeline, nunca se
sobrescriben.
