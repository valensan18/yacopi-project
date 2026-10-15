# Fase 5 — Modelo del valor catastral del suelo rural: experimento ZHG

Fecha: 2026-10-14 · Modo: research (experimental). **Ningún modelo fue
promovido; la predicción oficial sigue bloqueada (503).**

## 1. Objetivo de la Fase 5

Resolver con rigor el componente predictivo del anteproyecto: decidir si los
datos actuales permiten entrenar un modelo defendible para el valor
catastral del suelo rural (COP/ha), inspeccionando el software anterior de
Valentina como evidencia.

## 2. Fuentes de información

- Anteproyecto original (Word) en `yacopi-referencias/` (documento rector).
- Software anterior de Valentina: `yacopi-referencias/software valentina/`.
- Datos actuales de Atlas Vivo: `data/raw/` + `data/processed/` + SQLite.

## 3. Estructura del software de Valentina (inspección real)

Carpeta única `Proyecto_Grado_Yacopi_Yeimy_Valentina_Sanchez_Leguizamon`:
`src/config.py`, `src/preprocessing/{cleaning,build_datasets}.py`,
`src/models/{features,train_models,predict}.py`,
`src/evaluation/{metrics,model_diagnostics,advanced_plots,plots,build_figures}.py`,
`src/functions/{eda,io_utils}.py`, notebooks CRISP-DM (01–06),
`docs/diccionario_variables.csv` + `decisiones_datos.md`,
`results/{models,metrics,figures}`, `reports/{model_card,articulo}`,
app de escritorio (tkinter) y web estática. Conserva los CSV originales
idénticos a los nuestros (mismos tamaños: 35.320.477 y 17.306.426 bytes).

## 4. Linaje de la variable objetivo en el software anterior

| Pregunta | Respuesta verificada en código |
|---|---|
| A. Variable objetivo | `valor_hectarea_agropecuario` (COP/ha), presentada como `VALOR_TERRENO_Ha` |
| B. Procedencia | Columna del CSV de intersecciones predio-zona; filtrada `> 0` |
| C. Preparación | Códigos de zona normalizados (`zfill(2)`), transformación `log1p` del objetivo |
| D. Predictoras | Base intersección (áreas/log, destino, construcción) + perfil agregado ZHF **por zona** (promedios, modas, conteos) en el dataset "integrado" |
| E. Control de fuga | Lista `LEAKAGE_COLUMNS` correcta para valores/códigos directos, **pero omitió los estadísticos zonales** (`latitud_promedio`, `n_registros_zhf`, modas, etc.) que identifican la zona |
| F. Algoritmos | Dummy(mediana), Regresión lineal, Árbol, Random Forest, CatBoost |
| G. Separación de datos | `train_test_split` por filas (sin agrupación por predio ni por zona) |
| H. Métricas | RMSE, MAE, R², bias, RMSLE, MdAE, MdAPE, MAPE, %err<20/30 |
| I. Modelos serializados | `results/models/*.joblib` (integrado_* e interseccion_*) |
| J. Limitaciones | Model card genérico; no detectó la memorización zonal del dataset integrado |
| K. Resultados de referencia | `comparacion_modelos.csv`: **integrado R²=1.0 con RMSE≈0** (fuga); **interseccion** honesto: ningún modelo supera al baseline (R²≈−0,01) |
| L. Reutilizable conceptualmente | Elección de objetivo, normalización de códigos, batería de métricas, transformación log1p, diccionario de variables |

## 5. Cruces verificados con nuestros datos (Fase 5A)

| Verificación | Resultado |
|---|---:|
| Zonas en intersecciones / valores únicos | 11 / 11 |
| Zonas en ZHF / valores únicos | 11 / 11 |
| ¿Una zona con varios valores? | No (biunívoca en ambas fuentes) |
| **Equivalencia `valor_hectarea_agropecuario` = `ZHG_VALOR_`** | **SÍ, exacta en las 11 zonas** (tras normalizar códigos a 2 dígitos; en crudo los códigos difieren en formato "1" vs "01") |
| Predios únicos | 7.709 |
| Predios multizona (varias intersecciones) | 1.601 |
| Predios con dif. >20 % (suma intersecciones vs área catastral) | 1.874 (reproducido) |
| Cobertura ≤1 % / 1–5 % / >5 % | 744 / 2.041 / 4.924 |
| `ZHG_VALOR1` ≠ `ZHG_VALOR_` | en todas las 7.968 filas (referencia distinta) |
| Vigencia/procedencia oficial de `ZHG_VALOR_` | **Sin documento que la certifique** (limitación registrada) |

## 6. Avalúo total vs. valor unitario de suelo (tres conceptos)

- **A. Avalúo catastral total** (`valor_avaluo_total_cop`): valora el
  inmueble; 3.033 predios registran construcción. No es suelo exclusivo.
- **B. Valor catastral exclusivo del terreno por predio**: **no existe** en
  los datos.
- **C. Valor unitario de referencia zonal** (`valor_hectarea_agropecuario` =
  `ZHG_VALOR_`): 11 valores, uno por zona geoeconómica. Es una referencia
  de zona, **no** un avalúo individual observado; su vigencia oficial no
  está acreditada.

## 7. Predios multizona (Fase 5B)

- 1.601 predios intersectan más de una zona (6.108 de una sola).
- Reglas adoptadas y documentadas en `yacopi_ml/zhg/dataset.py`:
  - `cobertura_consistente`: dif ≤1 % (744) → apta para ponderación.
  - `cobertura_dudosa`: 1–5 % (2.041) → ponderación con bandera.
  - `no_apta`: >5 % (4.924) → excluida de la variante ponderada.
- Objetivos consolidados a nivel predio:
  - `valor_zona_dominante_cop_ha` (zona con mayor participación; 11 valores).
  - `valor_ponderado_cop_ha` = Σ(valor_zona × área_intersección) /
    Σ(área_intersección), solo cobertura ≤5 % (2.785 predios; 651 valores).
  - Nunca se toma la "primera" zona; la ponderación usa solo áreas de
    intersección (sin duplicar el área total del terreno).

## 8. Auditoría de fuga (Fase 5C)

`ml/config/features_zhg.yaml` fija la allowlist (**19** variables: 5
numéricas — áreas y coordenadas reales del predio — y 14 categóricas
ZHF/UPS/CLC) y **57 bloqueadas**: identificadores, objetivo y equivalentes
(`ZHG_VALOR_`, `ZHG_VALOR1`, `valor_hectarea_agropecuario`), avalúo total y
derivados, códigos/subzonas geoeconómicas, derivados de intersección,
coordenadas proyectadas, geometrías y **todos los estadísticos zonales del
software anterior** (`latitud_promedio`, `n_registros_zhf`, modas zonales…),
cuya fuga está demostrada por el R²=1.0 del experimento integrado de
Valentina.

Diferencias clave:
- **Coordenadas reales del predio** (`tr_latitud/tr_longitud`): permitidas
  (disponibles en inferencia, son dato del predio).
- **Promedios zonales precalculados**: prohibidos (identifican la zona).

Pruebas automatizadas: `test_zhg.py` (fuga detectada si entra una bloqueada;
lista incluye los estadísticos zonales del software anterior).

## 9. Estrategia de entrenamiento y validación (Fase 5D)

Tuning con `RandomizedSearchCV` + `GroupKFold(5)` agrupado **por predio**
(solo dentro del train del escenario predio; 8 ensayos). Escenarios:

| # | Escenario | Propósito |
|---|---|---|
| 1 | Filas (aleatoria) | Solo referencia comparativa con el software anterior |
| 2 | Agrupado por predio | Ningún predio aparece en train y test |
| 3 | Espacial (KMeans 25 bloques, predios con coordenadas) | Generalización territorial |
| 4 | Zonas completas fuera | Generalización a zonas no observadas |
| + | Leave-one-zone-out (11 folds) | Error por zona y variabilidad |
| 5 | Baselines: mediana y "valor de zona más frecuente" | Referencias triviales |
| 6 | Consulta directa de la tabla zonal | Referencia no-ML (no es predicción) |

**Criterio de aceptación PREDEFINIDO** (antes de ver resultados): el
candidato debe tener MAE menor que la mediana en test predio Y espacial, y
menor que la "moda zonal" en el test con zonas fuera.

## 10. Métricas obtenidas (reales; dominante n=7.709 · ponderado n=2.785)

MAE (COP/ha) por escenario:

| Modelo | filas | predio | espacial | zona (dominante) | zona (ponderado) |
|---|---:|---:|---:|---:|---:|
| Mediana (baseline) | 302.075 | 307.103 | 374.824 | 252.507 | 244.673 |
| Moda zonal (baseline) | 305.506 | 313.018 | 395.589 | **168.954** | **159.665** |
| Ridge | 169.999 | 168.433 | 255.590 | 238.760 | 230.052 |
| Árbol | 103.314 | 93.033 | 207.598 | 273.318 | 290.435 |
| Random Forest | 79.782 | 73.765 | 132.183 | 423.363 | 288.973 |
| CatBoost | 104.549 | 98.707 | 222.561 | 423.863 | 372.833 |

R² en el escenario zona: todos los modelos **negativos** (−0,19 a −2,18 en
dominante; −0,26 a −1,93 en ponderado).

**Corrección documental (2026-10-14):** el R² del *leave-one-zone-out* **no
es interpretable** y se retira de la interpretación: cada test contiene un
único valor objetivo constante (una zona), por lo que la suma de cuadrados
total es ≈0 (ruido de punto flotante de 1e-17 a 1e-20). Los valores
astronómicos (−10²⁸) registrados en `metrics.json` son artefactos
numéricos, no métricas científicas; el código de métricas ahora devuelve
R² indefinido (NaN) cuando el objetivo es constante (con prueba
automatizada). Para LOO se reportan **MAE y MdAPE** únicamente: MAE por
zona de 106.605 a 2.543.423 COP/ha.

**Lectura:** en escenarios con zonas compartidas (1–3) los modelos "aprenden
la zona" a través de coordenadas reales y atributos físicos y reducen el
MAE frente a la mediana (R² 0,77–0,82); pero ante zonas nunca vistas (4 y
LOO) **ningún modelo supera la referencia trivial de "valor de zona más
frecuente"** y el rendimiento colapsa.

## 11. Comparación con baselines y decisión (Fases 5F/5G)

- Criterio predefinido: `beats_median = true` (escenarios 2–3),
  `beats_mode = false` (escenario 4) → **aceptado: false**.
- **No se elige modelo ganador.** Con los datos actuales, un modelo de ML
  no demuestra capacidad de valoración independiente: solo reproduce la
  tabla zonal cuando la zona es identificable, y falla fuera de ella.
- Alternativas presentadas (documentadas, sin implementar):
  - **A.** Mostrar directamente el valor unitario ZHG cuando la zona sea
    conocida, rotulado como dato de referencia (no predicción ML).
  - **B.** Mantener un modelo experimental con limitaciones visibles
    (justificado solo como demostración de ingeniería).
  - **C.** Documentar los datos necesarios: valores exclusivos de terreno
    por predio (método, fecha, superficie) o variables físicas adicionales
    (suelos, distancias de acceso, mercados).

## 12. Limitaciones abiertas

- Objetivo con solo 11 valores zonales; sin vigencia certificada.
- 4.924 predios no aptos para ponderación por incoherencia de áreas.
- Sin diccionario oficial ni fechas de valoración (pendientes #2–3).
- La definición económica final del "valor del suelo rural" sigue como
  decisión pendiente del director (no se tomó aquí).

## 13. Recomendación para la integración futura (Fase 5G)

Mantener `POST /api/v1/predictions` en **503 MODEL_NOT_READY** (verificado:
sin cambios en el backend). Propuesta de contrato futuro, para cuando exista
un modelo autorizado:

```json
{
  "status": "reference_or_ml",
  "kind": "referencia_zonal_zhg | estimacion_ml_experimental",
  "unit": "COP/ha",
  "value_cop_ha": 547247.2,
  "zone_code": "06",
  "zone_value_known": true,
  "model_version": null,
  "dataset_version": "dataset-v1",
  "valuation_date": null,
  "warnings": ["referencia zonal, no avaluo individual"],
  "disclaimer": "Estimacion academica de apoyo; no constituye avaluo oficial"
}
```

Si se aprueba la alternativa A, es un endpoint de **consulta de referencia**
(no `POST /predictions`), claramente separado del predictivo. No mostrar
errores medidos como intervalos de confianza individuales.

## 14. Pruebas realizadas

- `ml/tests/test_zhg.py` (8): equivalencia zona→valor (11 zonas exactas),
  dataset predio único 7.709 y reglas de cobertura, splits sin solapes y
  reproducibles, smoke con métricas finitas y 11 folds LOO, fuga
  (intrusión detectada; estadísticos zonales bloqueados), métricas
  sintéticas.
- Suite completa: **66/66 tests** (incluye backend: el 503 oficial sigue
  intacto), `ruff` limpio.
- Experimentos completos ejecutados: `exp-zhg-001` (dominante) y
  `exp-zhg-001-ponderado` (sensibilidad) — ambos rechazados por criterio
  predefinido; artefactos locales en `ml/artifacts/` (no versionados).

## 15. Archivos y commits

Ver `docs/ESTADO_PROYECTO.md` (sección Fase 5) y el registro de commits
locales de la fase (rama dev, sin push). El software de Valentina solo se
leyó; no se modificó, movió ni copió a Atlas Vivo.
