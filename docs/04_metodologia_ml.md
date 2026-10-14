# Metodología ML y resultados del experimento proxy (Fase 2)

Fecha: 2026-10-14 · Experimento: `exp-proxy-001` · Modo: `research-proxy`
(Ruta B). Todos los números de este documento provienen de
`ml/artifacts/exp-proxy-001/metrics.json` generado por la ejecución real del
pipeline. **Ninguna métrica es inventada ni copiada del antecedente.**

## 1. Variable proxy: definición, justificación y limitaciones

- **Nombre:** `proxy_avaluo_total_cop_ha` (COP/ha).
- **Cálculo:** `valor_avaluo_total_cop / area_terreno_catastral_m2 × 10.000`
  (columna `referencia_avaluo_total_por_ha_cop` del consolidado).
- **Justificación experimental:** permite comparar metodológicamente los
  algoritmos y construir todo el software sin esperar la etiqueta verificada.
  Es explícitamente un **experimento académico separado**, no el producto de
  estimación del valor exclusivo del suelo.
- **Limitaciones (críticas):**
  1. El avalúo catastral total **incluye potencialmente construcciones**;
     3.030 de 7.694 predios de la cohorte tienen `area_construida_m2 > 0`.
     No es valor exclusivo de terreno.
  2. **Relación mecánica con el denominador:** el proxy tiene el área en el
     denominador y el modelo recibe esa misma área como predictor; parte de
     la "capacidad" observada es tautológica y no demuestra capacidad de
     valoración independiente (confirmado por la importancia de variables:
     ver §6).
  3. Fecha de valoración desconocida; sin diccionario oficial de códigos.
- **Validación de unidades/área:** área catastral > 0 (0 inválidas en la
  cohorte); objetivo finito y ≥ 1 COP/ha (0 inválidos). Predicciones en
  COP/ha, nunca se reinterpreta como avalúo oficial.

## 2. Cohorte y particiones

- Cohorte ML: **7.694 predios** (coincidentes entre fuentes; los 15
  solo-intersecciones se excluyen por ausencia de atributos ZHF/coordenadas).
- Variables: 19 (5 numéricas: 3 áreas + lat/lon; 14 categóricas ZHF/UPS/CLC
  con marcador `SIN_DATO` para faltantes). `fa_element` quedó excluido del
  experimento por cobertura (471 vacíos) — ver `features.yaml`.
- Particiones congeladas (seed 42, `data/splits/`):
  - **Aleatoria** (por predio): train 6.539 / test 1.155.
  - **Espacial** (KMeans 25 grupos sobre coordenadas, construidos sin mirar
    la etiqueta; GroupShuffleSplit): train 6.341 / test 1.353; ningún grupo
    espacial se comparte entre train y test.
- Tuning: `RandomizedSearchCV` con `GroupKFold(5)` **solo dentro del
  train espacial** (12 ensayos/modelo; `DummyRegressor(median)` sin tuning).
  El test solo se evaluó al cerrar cada modelo.

## 3. Resultados reales — test espacial (protocolo principal)

| Modelo | n | MAE (COP/ha) | RMSE (COP/ha) | R² | MdAPE (%) | % err<30 |
|---|---|---:|---:|---:|---:|---:|
| Dummy (mediana) | 1.353 | 6.592.762 | 41.202.882 | −0,03 | 57,6 | 23,4 |
| Ridge | 1.353 | 15.196.282 | 42.947.830 | −0,11 | 703,8 | 3,5 |
| Árbol | 1.353 | 4.215.432 | 27.823.728 | 0,53 | 24,1 | 55,5 |
| **Random Forest (seleccionado)** | 1.353 | **3.226.230** | 20.940.129 | **0,74** | 24,6 | **57,2** |
| CatBoost | 1.353 | 3.730.373 | 20.126.722 | **0,76** | 47,6 | 38,6 |

## 4. Resultados reales — test aleatorio (referencia metodológica)

| Modelo | n | MAE (COP/ha) | R² | MdAPE (%) | % err<30 |
|---|---|---:|---:|---:|---:|
| Dummy (mediana) | 1.155 | 7.889.929 | −0,02 | 57,1 | 28,9 |
| Ridge | 1.155 | 13.581.815 | 0,40 | 807,6 | 2,6 |
| Árbol | 1.155 | 4.176.143 | 0,66 | 13,9 | 69,8 |
| Random Forest | 1.155 | **2.674.886** | **0,82** | 7,3 | **80,8** |
| CatBoost | 1.155 | 3.336.590 | 0,81 | 46,4 | 34,8 |

CV aleatorio (MAE media, train aleatorio): ridge 14,9 M; árbol 5,4 M;
forest 4,6 M; catboost 5,2 M (COP/ha).

**Lectura honesta:** la validación espacial es claramente más exigente que
la aleatoria (forest: MAE 2,67 M → 3,23 M; R² 0,82 → 0,74). Ambas se
reportan como escenarios distintos, como exige la guía.

## 5. Modelo seleccionado y justificación

- **Random Forest** (n_estimators 349, max_depth 30, min_samples_leaf 3),
  seleccionado por **menor MAE en test espacial** (3.226.230 COP/ha).
- Mejora al dummy en un 51 % de MAE espacial; comparable a CatBoost en R²
  (0,74 vs 0,76) pero con MdAPE mucho menor (24,6 % vs 47,6 %).
- **Ridge colapsa** en ambas particiones (MAE > dummy, MdAPE > 700 %):
  hallazgo real de incapacidad de extrapolación lineal con colas pesadas y
  holdout espacial; se reporta sin ocultarlo.
- Estado: **experimental**; no promovido a producción (etiqueta pendiente).

## 6. Interpretabilidad (modelo seleccionado, test espacial)

- **Importancia por permutación** (aumento de MAE al permutar):
  `area_terreno_catastral_m2` (4,58 M), `area_construida_m2` (3,99 M),
  `zhf_influe` (0,16 M), `tr_latitud` (0,15 M), `tr_longitud` (0,07 M)…
- **SHAP** (TreeExplainer, muestra de 300): dominio de
  `area_terreno_catastral_m2` y `area_construida_m2`, seguidos de
  `area_zhf_m2` y categorías de `zhf_influe`/`destino_economico`.
- **Interpretación prudente:** el peso del área es en parte mecánico (el
  proxy se divide por ella). SHAP describe contribuciones al modelo, no
  causalidad.

## 7. Análisis de errores por segmento (forest, test espacial)

| Segmento | n | MAE (COP/ha) | MdAPE (%) |
|---|---:|---:|---:|
| Subzona 14 | 437 | 939.332 | 12,1 |
| Subzona 05 | 797 | 4.617.343 | 27,6 |
| Subzona 17 | 92 | 2.708.158 | 43,1 |
| Subzona 08 | 27 | 941.761 | 202,1 |
| ≤5 ha | 787 | 5.386.254 | 22,4 |
| 5–20 ha | 393 | 197.223 | 24,8 |
| 20–100 ha | 163 | 277.811 | 39,5 |
| >100 ha | 10 | 331.517 | 130,2 |
| Agropecuario | 1.208 | 1.503.728 | 22,6 |
| Habitacional | 75 | 15.792.198 | 44,8 |
| Religioso | 55 | 16.556.455 | 39,6 |
| Con construcción | 377 | 8.521.425 | 21,5 |
| Sin construcción | 976 | 1.180.852 | 25,3 |
| Sin alertas de calidad | 265 | 2.974.682 | 23,5 |
| Con alertas de calidad | 1.088 | 3.287.498 | 24,7 |

**Hallazgos:** el error en predios pequeños (≤5 ha) domina el MAE agregado;
los destinos no agropecuarios concentran los errores absolutos mayores;
la presencia de construcción casi multiplica por 7 el MAE — evidencia
adicional de que el proxy NO es valor exclusivo de terreno. Los grupos con
n pequeño (p. ej. subzona 08, >100 ha) se leen con cautela.

## 8. Sobreajuste y estabilidad

- No se observa sobreajuste severo: el error de test (aleatorio y espacial)
  supera el error CV de entrenamiento en todos los modelos, y el dummy no es
  superado por artefactos de memorización (excepto el colapso de Ridge, que
  es un problema de extrapolación, no de overfitting).
- El test espacial se usó **una sola vez** al cerrar el experimento; el
  tuning solo vio validación agrupada del entrenamiento.

## 9. Reproducibilidad

- Comando único: `python -m yacopi_ml.train --mode research-proxy
  --output ml/artifacts/exp-proxy-001` (con `PYTHONPATH=ml/src`).
- Dos corridas smoke producen métricas idénticas (prueba automatizada).
- `training_manifest.json` registra commit, seed, versiones de paquetes,
  esquema de variables e hiperparámetros.
- Artefactos: `model.joblib` (54 MB), `metrics.json`, `feature_schema.json`,
  `training_manifest.json`, `predictions_test.csv`, `MODEL_CARD.md`
  (estado experimental) y 6 figuras reales (ver `ml/artifacts/exp-proxy-001/`).

## 10. Conclusiones de la fase

1. El diseño experimental funciona de extremo a extremo y es reproducible.
2. Los árboles/ensambles superan al baseline; la comparación espacial vs
   aleatoria confirma que la vecindad infla las métricas si no se controla.
3. La etiqueta proxy permite la ingeniería completa del software, pero sus
   métricas **no deben presentarse como capacidad de valorar el suelo**:
   el área como predictor y la construcción incluida lo impiden.
4. El producto NO publica un modelo definitivo: `label_contract.yaml` sigue
   en `pending_verification` y `POST /predictions` deberá responder 503
   (Fase 3) hasta que exista una etiqueta validada.
