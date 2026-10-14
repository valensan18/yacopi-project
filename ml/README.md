# ML offline — Yacopí

Pipeline reproducible separado del backend. El entrenamiento NO ocurre en
peticiones HTTP; solo se despliegan artefactos aprobados.

```
config/            label_contract.yaml (BLOQUEANTE), label_contract_proxy.yaml,
                   features.yaml (allowlist + bloqueadas), training.yaml
src/yacopi_ml/     schema, labels, split, preprocess, models, metrics,
                   train, evaluate, explain, export, registry
tests/             pruebas de datos/ML (sin métricas ficticias)
artifacts/         modelos serializados (NO versionados)
```

## Modos de entrenamiento

- `--mode production`: rechaza si `label_contract.source_status != verified`.
- `--mode research-proxy` (Ruta B): experimentos con avalúo total/ha,
  artefactos marcados `experimental`, sin promoción a producción.

## Ejecución (Windows PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "ml\src"

# Corrida de humo (rápida, ~1 min)
python -m yacopi_ml.train --mode research-proxy --smoke

# Experimento completo (tuning 12 ensayos, ~25 min CPU)
python -m yacopi_ml.train --mode research-proxy --output ml\artifacts\exp-proxy-001

# Intento de producción (debe RECHAZAR mientras no haya etiqueta validada)
python -m yacopi_ml.train --mode production
```

## Experimento vigente

`exp-proxy-001` (RandomForest, test espacial MAE 3.226.230 COP/ha, R² 0,74).
Resultados completos y reales: `docs/04_metodologia_ml.md` y
`ml/artifacts/exp-proxy-001/` (local, no versionado).
