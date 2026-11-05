# Inventario de experimentos y código existente

Cada experimento se identifica, se distingue de los demás y se referencia con
sus archivos reales. **No se mezclan métricas entre experimentos.**

## Distinciones explícitas

| Tipo | Definición |
|---|---|
| 1. Experimentación ZHG (Fase 5) | Intentos de predecir el valor unitario zonal de referencia con 5 algoritmos. Rechazados como candidatos. |
| 2. Experimentación avalúo/ha (Fase 2 proxy y rama experimental) | Predicción del avalúo catastral total dividido por área. Experimental; no es valor de suelo. |
| 3. Demostración Random Forest (demo) | Artefacto para mostrar el software; ajustado a todos los datos; sin evaluación independiente. |
| 4. Modelo predictivo oficial | NO existe. Endpoint oficial 503 MODEL_NOT_READY. |

## Tabla maestra de experimentos

### exp-proxy-001 (Fase 2, histórico)
| Campo | Valor |
|---|---|
| Objetivo | Comparar metodológicamente 5 algoritmos con una variable proxy |
| Variable de respuesta | `proxy_avaluo_total_cop_ha` = avalúo catastral TOTAL × 10000 / área catastral (incluye construcciones) |
| Fuente | `data/processed/03_predios_consolidados.csv` (columna `referencia_avaluo_total_por_ha_cop`) |
| Registros | 7.694 predios (n_train_espacial 6.341 / test 1.353; random 6.539 / 1.155) |
| Unidad de análisis | predio |
| Predictoras | 19 features (5 numéricas: áreas, lat, lon; 14 categóricas ZHF/CLC/destino) |
| Algoritmos | Dummy (mediana), Ridge, Árbol, RandomForest, CatBoost (tuning 12 ensayos, seed 42) |
| Código | `ml/src/yacopi_ml/train.py`, `evaluate.py`, `models.py`; config `ml/config/training.yaml`, `features.yaml`, `label_contract_proxy.yaml` |
| Validación | test espacial sellado + test aleatorio (particiones en `data/splits/`) |
| Métricas (test espacial) | Baseline MAE 6.592.762, R² −0,03 · Ridge 15.196.282, R² −0,11 · Árbol 4.215.432, R² 0,53 · RF 3.226.230, R² 0,74 · CatBoost 3.730.373, R² 0,76 |
| Resultados | `ml/artifacts/exp-proxy-001/metrics.json`, `MODEL_CARD.md`, `registry.json` |
| Estado | experimental, `production_eligible: false` (el objetivo no es valor de suelo) |

### exp-zhg-001 (Fase 5, dominante)
| Campo | Valor |
|---|---|
| Objetivo | Evaluar si es posible predecir la referencia ZHG zonal |
| Variable de respuesta | `valor_zona_dominante_cop_ha` (COP/ha; solo **11 valores posibles**, uno por zona) |
| Fuente | `01_intersecciones_normalizadas.csv` + `02_zhf_normalizadas.csv` |
| Registros | 7.709 predios (filas 6.167/1.542; predio 6.167/1.542; espacial 6.060/1.634; zona 5.934/1.775 con zonas 01, 06, 10 fuera) |
| Algoritmos | Dummy, Ridge, Árbol, RF, CatBoost |
| Código | `ml/src/yacopi_ml/zhg/{dataset,splits,train}.py` |
| Validación | 4 protocolos: filas, por predio, espacial, dejando zonas completas fuera |
| Métricas clave | RF: MAE predio 73.765, espacial 132.183, zonas fuera 423.363 COP/ha; R² zona −1,70; CatBoost R² zona −2,18 (negativos) |
| Criterio predefinido | MAE < mediana (predio y espacial) y MAE < moda zonal (zonas fuera) → **beats_mode: false → rechazado** |
| Resultados | `ml/artifacts/exp-zhg-001/metrics.json` |
| Estado | rechazado como candidato; histórico |

### exp-zhg-001-ponderado (Fase 5)
Igual que el anterior con `target: valor_ponderado_cop_ha` (651 valores
únicos; n = 2.785 predios). RF MAE predio 88.865, espacial 145.604, zonas
fuera 288.973; R² zona −0,55. **Rechazado** (beats_mode: false).

### exp-zhg-001-demo (Fase 7B, artefacto de demostración)
| Campo | Valor |
|---|---|
| Variable de respuesta | `valor_zona_dominante_cop_ha` (referencia ZHG) |
| Algoritmo | RandomForestRegressor en Pipeline de sklearn; max_depth 30, min_samples_leaf 1, n_estimators 513 (búsqueda GroupKFold(5) por predio, seed 42) |
| Ajuste | **los 7.709 predios** (ajuste final determinístico) |
| Evaluación independiente | **NO tiene**; las métricas de Fase 5 no evalúan este artefacto (nota en `manifest.json`) |
| Código | `ml/src/yacopi_ml/zhg/export_demo.py` |
| Estado | experimental; desactivada por defecto en producción (`EXPERIMENTAL_ZHG_ENABLED=false`) |

### exp-valor-terreno-001 (rama experimental actual)
| Campo | Valor |
|---|---|
| Variable de respuesta | `VALOR_TERRENO_Ha = valor_avaluo × 10000 / area_terreno_m2` (avalúo catastral TOTAL; no hay campo de avalúo exclusivo de terreno) |
| Escenarios | A: construcción = 0 (4.676 predios) · B: 0 < construcción ≤ 32 m² (986 predios) |
| Predictoras | 19 features sin fuga (sin avalúo, sin valores/códigos zonales) |
| Algoritmos | Dummy, Ridge (log), Árbol, RF, CatBoost (implementados en `ml/src/yacopi_ml/valor/`) |
| Validación | protocolo v2: por predio y espacial **independientes** + LOZO (dejar zona fuera) |
| Métricas (v2) | A: RF test predio MAE 248.296 R² 0,69; **test espacial independiente R² 0,171**; CatBoost predio 279.284 R² 0,73, espacial −0,075. B: test predio R² 0,12–0,15 por extremos de áreas mínimas; espacial RF 0,863/CatBoost 0,646 |
| Nota | Las métricas espaciales v1 (R² 0,88–0,93 en A) eran **no independientes** (81 %/80 % del test estaba en el entrenamiento) y quedaron archivadas como históricas |
| Estado | experimental; **no hay candidato definitivo** |

## Evidencia por commit

| Commit | Contenido |
|---|---|
| `7b30233` | Fase 1–2 (manifest exp-proxy-001 referencia este commit) |
| fases posteriores | Fase 5 (`docs/06`), demo (`docs/10`), dockerización (`3dcdf3b`, `af4b7c5`), mapa (`9429da3`) |
| `5b2fca7` | experimento VALOR_TERRENO_Ha (rama experimental) |

## Inventario de notebooks originales

`notebooks/` contiene únicamente `README.md` (180 bytes) que declara:
"Análisis exploratorio de las fases 0–2... sin notebooks versionados". **No
existían cuadernos originales**: los análisis se hicieron como scripts Python
(`scripts/*.py`) y módulos (`ml/src/yacopi_ml/*`). Los 13 cuadernos de este
paquete son de reproducción y están marcados como posteriores.
