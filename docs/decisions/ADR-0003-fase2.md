# ADR-0003 — Diseño experimental del proxy (Fase 2, Ruta B)

- **Fecha:** 2026-10-14
- **Estado:** Aceptado

## Contexto

La etiqueta de valor exclusivo de suelo sigue pendiente. Se requería un
pipeline ML reproducible sin publicar un modelo definitivo.

## Decisiones

1. **Proxy explícito** `proxy_avaluo_total_cop_ha` (avalúo total / área
   catastral), contrato separado `label_contract_proxy.yaml` con
   `source_kind: proxy` y `production_eligible: false`. El contrato principal
   permanece `pending_verification`; `--mode production` rechaza el
   entrenamiento por diseño (probado).
2. **Cohorte = 7.694 predios coincidentes** (15 sin ZHF excluidos por
   cobertura, documentado). Faltantes categóricos marcados con `SIN_DATO`
   (compatible con sklearn y CatBoost, sin inventar valores).
3. **Doble partición congelada** (seed 42, `data/splits/` con hashes):
   aleatoria por predio 85/15 y espacial KMeans(25)+GroupShuffleSplit 85/15.
   Tuning solo con `GroupKFold(5)` dentro del train espacial
   (RandomizedSearchCV, 12 ensayos). Test sellado evaluado una sola vez.
4. **Selección por MAE en test espacial** (métrica primaria). Se reportan
   ambas particiones y el CV aleatorio como referencia metodológica.
5. **CatBoost envuelto** (`CatBoostWrapper`) para cumplir el contrato de
   clonado de sklearn (cat_features en constructor); SHAP desenvuelve
   pipeline/wrapper (`tree_path_dependent`, muestra de 300).
6. **Interpretación honesta del peso del área:** al estar el área en el
   denominador del proxy, su alta importancia es parcialmente mecánica; se
   declara en el informe y en el MODEL_CARD.

## Alternativas rechazadas

- Entrenar en escala log(y): se descartó para mantener comparabilidad directa
  de MAE/RMSE/MdAPE en COP/ha en este primer experimento (evaluable después).
- Imputar mediana de área o construir valores: no se inventa información.
- Usar subzona como grupo espacial: es contexto geoeconómico (bloqueado como
  X); los grupos se construyen con KMeans sobre coordenadas sin la etiqueta.

## Riesgos

- Sobreinterpretar métricas del proxy como capacidad de valoración de suelo
  (mitigado: etiquetas, MODEL_CARD y 503 en inferencia).
- Grupos espaciales con poca representación de precios extremos; se reportan
  tamaños `n` por segmento.

## Pruebas asociadas

- `ml/tests/test_ml_pipeline.py`: anti-leakage, contrato, splits,
  métricas sintéticas, smoke reproducible, manifest de versiones.
