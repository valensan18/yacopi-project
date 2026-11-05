# Auditoría de los R² negativos y bajos de Atlas Vivo

Documento prioritario: para cada R² mostrado en el software (o en los
artefactos) se identifica su origen, se recalcula y se explica la causa con
evidencia. Fecha: 2026-10-23 (revisión v2 de la validación espacial incluida).
Rama `experimental/valor-terreno-ha`.

## 0. CORRECCIÓN METODOLÓGICA DE ESTA REVISIÓN (validación espacial)

La revisión independiente detectó que en la versión anterior (v1) del
experimento VALOR_TERRENO_Ha los modelos se entrenaban con la partición
aleatoria (`tr_predio`) y se evaluaban sobre el test espacial (`te_esp`).
Eso **contaminaba** la validación espacial: una parte de `te_esp` ya había
sido vista en entrenamiento.

### Evidencia del solapamiento (calculada antes de corregir)

| Escenario | n te_esp | IDs de te_esp presentes en tr_predio | % de te_esp |
|---|---|---|---|
| A | 689 | **560** | **81,28 %** |
| B | 177 | **141** | **79,66 %** |

(`ml/artifacts/exp-valor-terreno-001/historial_no_independiente_v1/evidencia_solapamiento.json`;
el split espacial en sí era correcto: tr_esp ∩ te_esp = 0.)

### Corrección aplicada

Dos protocolos independientes en `ml/src/yacopi_ml/valor/train.py` y
`audit_r2.py`:

- **Protocolo predio:** entrena con `tr_predio`, evalúa con `te_predio`.
- **Protocolo espacial:** entrena una instancia **nueva** con `tr_esp`,
  evalúa con `te_esp`.

Con asserts de disjuntez (IDs y bloques geográficos) y pruebas automatizadas
en `ml/tests/test_valor_splits.py` (8 tests) que impiden reintroducir el
solapamiento.

### Matriz ANTES / DESPUÉS (test espacial, escenario A)

| Modelo | R² ANTES (v1, contaminada) | R² DESPUÉS (v2, independiente) | MAE ANTES | MAE DESPUÉS |
|---|---|---|---|---|
| Random Forest | +0,883 | **+0,171** | 288.241 | **767.064** |
| CatBoost | +0,930 | **−0,075** | 246.137 | **897.642** |
| Árbol | +0,901 | +0,092 | 216.043 | 805.690 |
| Ridge (log) | +0,111 | +0,011 | 798.278 | 838.996 |
| Dummy (media) | −0,004 | −0,006 | 1.276.465 | 1.237.011 |

(Escenario B espacial: RF 0,939→0,863; CatBoost 0,982→0,646. El protocolo
predio no cambió: ya era independiente.)

**Lectura:** las métricas espaciales anteriores estaban infladas porque el
81 % del test había sido visto en entrenamiento. Las cifras v2 son las
defendibles. Se conservan las v1 en
`historial_no_independiente_v1/` marcadas como NO independientes, sin
eliminarlas.

## 4.1 Dónde aparece cada R² en el software

| # | Lugar visible | R² mostrados | Origen del dato |
|---|---|---|---|
| 1 | `/modelos`, tabla "Validación espacial" (`frontend/src/pages/Models.tsx`, `DOCUMENTED_TEST_SPATIAL`) | Baseline −0,03 · Ridge −0,11 · Árbol 0,53 · RF 0,74 · CatBoost 0,76 | `ml/artifacts/exp-proxy-001/metrics.json` (proxy Fase 2; validación correcta) |
| 2 | `/modelos`, tabla "Validación aleatoria" | Baseline −0,02 · Ridge 0,40 · Árbol 0,66 · RF 0,82 · CatBoost 0,81 | ídem |
| 3 | `/modelos`, tarjeta del registro | RF 0,74 | `registry.json` → `GET /api/v1/models` |
| 4 | `/glosario` | definición de R² (sin número) | `frontend/src/lib/glossary.ts` |
| 5 | Artefactos/docs (no en UI) | ZHG zona fuera −1,70/−2,18; LOZO −1e30/NaN | `exp-zhg-001/metrics.json` |
| 6 | Rama experimental (no en UI) | v2: espacial A CatBoost −0,075, dummy ≈ 0; B test predio 0,05–0,15 | `exp-valor-terreno-001/audit_r2/` |

## 4.2 Fórmula y significado

```
R² = 1 − Σ(y_real − y_pred)² / Σ(y_real − media(y_real))²
```

- R² = 1: perfecta. R² ≈ 1: error cuadrático ≪ media. R² = 0: igual a la
  media. R² < 0: peor que la media. R² muy negativo: mala generalización,
  extremos o poca variación. R² indefinido: denominador 0 (en la práctica,
  valores como −1e30 o NaN). **R² no es porcentaje de aciertos** y un valor
  negativo no implica error de programación.

## 4.3 Recálculo

- **exp-valor-terreno-001 (v2):** recalculado con `ml/src/yacopi_ml/valor/audit_r2.py`
  (protocolos independientes; predicciones alineadas guardadas en
  `audit_r2/preds_*.csv`).
- **exp-proxy-001:** verificado por reentrenamiento completo
  (`exp-proxy-rerun`): las 10 cifras de `/modelos` se reproducen exactamente
  (−0,0253 / −0,1140 / −0,0153 incluidos).
- **exp-zhg-001:** verificado por reentrenamiento completo (`exp-zhg-rerun`):
  reproduce exactamente Fase 5 (zona fuera −1,704/−2,178; `aceptado: false`).

### Tabla recalculada (exp-valor-terreno-001, protocolo v2)

| MODELO | EXPERIMENTO | Y | PARTICIÓN | N | R² | MAE | RMSE | CAUSA INVESTIGADA | CONCLUSIÓN |
|---|---|---|---|---|---|---|---|---|---|
| random_forest | valor A | VALOR_TERRENO_Ha | test predio | 936 | +0,689 | 248.296 | 1.111.207 | — | mejor balance predio |
| catboost | valor A | idem | test predio | 936 | +0,725 | 279.284 | 1.044.694 | — | mejor R² predio |
| random_forest | valor A | idem | test espacial | 689 | **+0,171** | **767.064** | 3.450.751 | bloques geográficos no vistos | independiente, baja generalización |
| catboost | valor A | idem | test espacial | 689 | **−0,075** | 897.642 | 3.929.402 | ídem | peor que la media en bloques nuevos |
| ridge_log | valor A | idem | test espacial | 689 | +0,011 | 838.996 | 3.769.143 | lineal | ≈ media |
| dummy_media | valor A | idem | test espacial | 689 | −0,006 | 1.237.011 | 3.800.735 | referencia media | esperado |
| arbol | valor A | idem | test espacial | 689 | +0,092 | 805.690 | 3.610.640 | interacciones limitadas | — |
| random_forest | valor B | idem | test predio | 198 | +0,146 | 11.487.894 | 89.451.275 | **7 extremos >50 M (máx 1.154 M) por áreas mínimas** | extremos dominan |
| catboost | valor B | idem | test predio | 198 | +0,118 | 11.670.499 | 90.899.537 | ídem | ídem |
| random_forest | valor B | idem | test espacial | 177 | +0,863 | 932.873 | 3.423.955 | — | bloques de test sin extremos |
| catboost | valor B | idem | test espacial | 177 | +0,646 | 1.777.243 | 5.496.009 | — | — |
| dummy_media | valor B | idem | test predio | 198 | −0,015 | 15.347.647 | 97.517.767 | referencia media | esperado |

### Baselines (renombrados y separados, mismo n que los modelos)

| Baseline | Definición | A predio | A espacial |
|---|---|---|---|
| `_baseline_mediana_zonal_objetivo_train` | mediana de **VALOR_TERRENO_Ha** por zona calculada con train | MAE 311.046, R² +0,053 | MAE 806.989, R² −0,034 |
| `_baseline_mediana_global_train` | mediana global del objetivo en train | MAE 580.341, R² −0,039 | MAE 973.333, R² −0,031 |
| `_referencia_zhg_del_dataset` | **referencia económica ZHG** del dataset (zona dominante por área) | MAE 335.614, R² +0,048 | MAE 817.030, R² −0,036 |

Antes se llamaba "contexto zonal" y podía confundirse con la referencia ZHG;
ahora se reportan por separado y sobre los mismos registros de test.

## 4.4 Causas investigadas (hipótesis A–L)

| Hipótesis | ¿Contribuyó? | Dónde | Evidencia |
|---|---|---|---|
| A. Zonas no vistas en entrenamiento | **SÍ (principal en ZHG y en v2 espacial)** | ZHG −1,70/−2,18; v2 espacial A 0,171/−0,075 | metrics.json; resumen v2 |
| B. Referencias zonales poco representativas | SÍ | ZHG 11 valores | metrics.json |
| C. Valores extremos | **SÍ (B)** | 7 test obs > 50 M | desgloses B |
| D. Áreas pequeñas → cocientes altos | **SÍ (B)** | 46 filas ≤ 100 m² | fig08 |
| E. Diferencia train/test | SÍ | R² train > test en todos | audit_r2 |
| F. Dependencia espacial | **SÍ** | aleatoria > espacial en v2 | tabla v2 |
| G. Features con poca información | SÍ (parcial) | corr ≤ 0,07–0,18 | desgloses |
| H. Fuga directa/indirecta | **No detectada** | zonales/avalúo excluidos de X | `FEATURES_EXCLUIDAS` |
| I. Transformación incorrecta de Y | No | log1p/expm1 verificados | modelos.py |
| J. Varianza muy baja | **SÍ** | LOZO −1e30/NaN | metrics ZHG |
| K. Alineación de registros | No | splits por ID | audit_r2 |
| L. Hiperparámetros/sobreajuste | No determinante | RF 400/18/3 | tabla train/test |

**El único defecto de evaluación identificado fue la validación espacial v1
(métricas infladas por test contaminado; no eran R² negativos). Todos los
R² negativos reportados —v2, proxy y ZHG verificados por reentrenamiento
completo— están calculados correctamente con `sklearn.metrics.r2_score`
sobre pares alineados y responden a causas científicas (baselines por
construcción, zonas/bloques no vistos, extremos, varianza casi nula): no
son errores aritméticos ni de programación.**

## 4.5 Comparación entre particiones (v2)

| Modelo | R² train | R² test predio | R² test espacial | LOZO (MAE por zona) |
|---|---|---|---|---|
| RF (valor A) | 0,904 | 0,689 | **0,171** | 175 k–1,19 M |
| CatBoost (valor A) | 0,934 | 0,725 | **−0,075** | ídem |
| RF (ZHG Fase 5) | — | 0,825 | 0,791 (bloques) | −1,704 (zonas fuera) |

Con protocolos independientes, la partición espacial es claramente más dura
que la aleatoria (RF A: 0,689 → 0,171); esto confirma la dependencia
espacial y la necesidad de evaluar ambos protocolos por separado.

### Diferencia entre test aleatorio y espacial del escenario B

Los **7 valores extremos** (> 50 M COP/ha, máximo 1.154 M, por áreas
mínimas) caen en el test por predios (n=198) y no en el test espacial
(n=177). Por eso el protocolo predio muestra MAE ≈ 11,5–15,3 M y R²
0,12–0,15, mientras el espacial independiente alcanza MAE 0,93 M (RF) con
R² 0,86. No es que el modelo sea "mejor" en la partición espacial: son
conjuntos de prueba con composición distinta, y el test por predios
contiene los casos más difíciles. La comparación honesta exige reportar
ambos y el análisis de sensibilidad sin extremos (B sin extremos: MAE
727.710, R² 0,506).

### 4.9 Comparación espacial A sobre los mismos 689 predios

| Referencia | MAE (COP/ha) | MdAPE |
|---|---|---|
| Random Forest | 767.064 | 11,69 % |
| Referencia ZHG del dataset | 817.030 | **5,65 %** |
| CatBoost | 897.642 | 25,64 % |

**Por qué el menor MAE no implica el menor MdAPE:** el MAE promedia errores
absolutos y es sensible a unos pocos errores grandes; el MdAPE es la mediana
del error relativo y es robusto a esos extremos. RF gana el MAE (menor error
absoluto promedio) pero pierde el MdAPE frente a la referencia ZHG: en la
mayoría de los predios el error relativo del RF (11,69 %) es mayor que el del
dato zonal (5,65 %). **La mejora del RF sobre la referencia ZHG es
limitada**: −6 % en MAE y peor MdAPE; la referencia económica zonal es un
competidor muy fuerte en este test y el modelo no aporta un margen claro.

## 4.6 Ejemplo didáctico (corregido)

Versión anterior: se ajustaba y evaluaba sobre los mismos datos (R² ≈ +0,0027,
NO negativo). **Corregido** con entrenamiento y prueba separados: recta
ajustada en x ∈ [0, 2] de una parábola y evaluada en x ∈ [6, 10] →
**R² prueba = −18,55** (calculado por el código, verificado con
`assert r2 < 0`). Figuras: `figuras/fig00_ejemplo_r2_negativo.png`,
notebook 10.

## 4.7 Auditoría de la interfaz `/modelos`

La página muestra correctamente: experimento identificado (proxy histórico),
variable objetivo (`proxy_avaluo_total_cop_ha`), particiones ("test espacial
sellado"/"aleatoria"), fuente (`docs/04`), distinción demo/modelo validado,
R² negativos fieles (sin sustituir por 0) y explicación en HelpTip. Las
cifras del proxy son las verificadas por el rerun. Mejoras propuestas (no
implementadas): n visible por tabla y aclarar "R² indefinido ≠ 0" en el
glosario.

## 4.8 Conclusión

1. Los R² negativos del software están **correctamente calculados** (verificados
   por reentrenamiento completo y recálculo con sklearn); sus causas son
   científicas, no aritméticas. El único defecto de evaluación encontrado fue
   la validación espacial contaminada de v1 (métricas infladas, corregidas y
   archivadas como no independientes).
2. La validación espacial del experimento VALOR_TERRENO_Ha estaba
   contaminada (81 % / 80 % del test visto en train) y fue **corregida** a
   protocolos independientes.
3. Con la corrección, el desempeño espacial cae (RF A: R² 0,171; CatBoost:
   −0,075): la generalización a bloques no vistos es limitada y la referencia
   ZHG del dataset es un competidor muy fuerte (mejor MdAPE que RF). La
   conclusión científica se mantiene: **no hay modelo definitivo**; la
   predicción oficial sigue 503.
