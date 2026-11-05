# Guía de reproducibilidad

Cómo reconstruir todo el procedimiento desde cero.

## Requisitos

- Windows PowerShell (o Linux con rutas equivalentes).
- Python 3.13+ (probado con 3.14.4) y Node 24.
- Archivos de datos **en su sitio**: `data/raw/interseccion_terrenos_zhg_r1_yacopi.csv`
  y `data/raw/zhf_yacopi.csv` (hashes en `manifiesto_reproducibilidad.json`;
  no se incluyen en este paquete por privacidad).

## Pasos

```powershell
# 1. Dependencias
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r ml/requirements.txt -r backend/requirements.txt

# 2. Verificar entradas (hashes)
python scripts/verify_inputs.py

# 3. Auditoria de datos y consolidacion
python scripts/preparar_datos.py      # normalizacion (historico)
python scripts/build_db.py            # consolidado + SQLite local
python scripts/audit_data.py          # banderas y resumen

# 4. Auditoria de la variable VALOR_TERRENO_Ha
python scripts/audit_valor_terreno.py
python scripts/analisis_valor_terreno.py

# 5. Experimento VALOR_TERRENO_Ha (entrenamiento comparativo, protocolo v2)
$env:PYTHONPATH = "ml\src"
python -m yacopi_ml.valor.train
python -m yacopi_ml.valor.evaluate
python -m yacopi_ml.valor.audit_r2      # recalculos + figuras (protocolos independientes)
python -m yacopi_ml.valor.sensibilidad_area   # sensibilidad a area_terreno_m2

# 5b. Auditorias de la revision metodologica
python scripts/evidencia_solapamiento.py      # solapamiento v1 (historico)
python scripts/audit_consolidacion_predial.py # consistencia por predio
python -m pytest ml/tests/test_valor_splits.py  # pruebas anti-solapamiento

# 6. Experimento proxy historico (Fase 2, ~25 min)
python -m yacopi_ml.train --mode research-proxy --output ml\artifacts\exp-proxy-001

# 7. Experimento ZHG (Fase 5)
python -m yacopi_ml.zhg.train --target dominante --output ml\artifacts\exp-zhg-001
python -m yacopi_ml.zhg.train --target ponderado --output ml\artifacts\exp-zhg-001-ponderado

# 8. Cuadernos
pip install nbformat nbclient ipykernel
python scripts/ejecutar_notebooks.py    # regenera y ejecuta los 13 cuadernos

# 9. Pruebas
pytest
cd frontend; npm ci; npm run lint; npm run test; npm run build
```

## Semillas y particiones

- Proxy (Fase 2): seed 42; particiones en `data/splits/{train,test}_{random,spatial}.json`.
- ZHG (Fase 5): particiones en `data/splits/zhg/<objetivo>_n<size>/`.
- VALOR_TERRENO_Ha: seed 20261023; particiones en `data/splits/valor/valor_terreno_ha_{A|B}_n<size>/`.

## Verificación de consistencia

`manifiesto_reproducibilidad.json` registra commit, hashes de entrada,
versiones, semillas y resultados clave; compare sus números con los del
manifiesto tras ejecutar.
