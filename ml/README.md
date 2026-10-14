# ML offline — Yacopí

Pipeline reproducible separado del backend. El entrenamiento NO ocurre en
peticiones HTTP; solo se despliegan artefactos aprobados.

```
config/            label_contract.yaml (BLOQUEANTE), features.yaml, training.yaml
src/yacopi_ml/     schema, labels, features, split, preprocess, train, tune,
                   evaluate, explain, export, registry (Fase 2)
tests/             pruebas de datos/ML (sin métricas ficticias)
artifacts/         modelos serializados (NO versionados)
```

Modos de entrenamiento:

- `--mode production`: rechaza si `label_contract.source_status != verified`.
- `--mode research-proxy` (Ruta B): experimentos con avalúo total/ha,
  artefactos marcados `experimental`, sin promoción a producción.
