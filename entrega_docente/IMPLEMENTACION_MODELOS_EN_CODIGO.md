# Implementación real de los modelos en el código

Fragmentos reales del repositorio (rama `experimental/valor-terreno-ha`).
No son implementaciones genéricas: son los archivos ejecutados.

## 1. Definición de los cinco algoritmos (experimento proxy, Fase 2)

Archivo: `ml/src/yacopi_ml/models.py`

```python
def get_models() -> dict:
    return {
        "dummy": (DummyRegressor(strategy="median"), {}, False),
        "ridge": (
            Pipeline([
                ("preprocess", preprocess_sklearn(with_scaler=True)),
                ("model", Ridge(random_state=SEED)),
            ]),
            {"model__alpha": {"dist": uniform, "kwargs": {"loc": 0.1, "scale": 200}}},
            False,
        ),
        "tree": (
            Pipeline([
                ("preprocess", preprocess_sklearn(with_scaler=False)),
                ("model", DecisionTreeRegressor(random_state=SEED)),
            ]),
            {"model__max_depth": {"dist": randint, "kwargs": {"low": 4, "high": 20}},
             "model__min_samples_leaf": {"dist": randint, "kwargs": {"low": 5, "high": 100}}},
            False,
        ),
        "forest": (
            Pipeline([
                ("preprocess", preprocess_sklearn(with_scaler=False)),
                ("model", RandomForestRegressor(random_state=SEED, n_jobs=6)),
            ]),
            {"model__n_estimators": {"dist": randint, "kwargs": {"low": 200, "high": 601}},
             "model__max_depth": {"choices": [None, 10, 20, 30]},
             "model__min_samples_leaf": {"dist": randint, "kwargs": {"low": 1, "high": 20}}},
            False,
        ),
        "catboost": (
            CatBoostWrapper(cat_features=CATEGORICAL_FEATURES),
            {"iterations": ..., "depth": ..., "learning_rate": ..., "l2_leaf_reg": ...},
            True,
        ),
    }
```

`CatBoostWrapper` (mismo archivo) envuelve `CatBoostRegressor` para
compatibilidad sklearn, con `cat_features` clonable y `verbose=0`.

## 2. Experimentos ZHG (Fase 5)

Archivos: `ml/src/yacopi_ml/zhg/train.py`, `zhg/splits.py`, `zhg/dataset.py`.
Mismos 5 algoritmos, con particiones `filas/predio/espacial/zona` y el
criterio de aceptación predefinido (MAE < mediana y MAE < moda zonal).

## 3. Experimentos VALOR_TERRENO_Ha (rama experimental)

Archivos: `ml/src/yacopi_ml/valor/train.py` (entrenamiento comparativo) y
`valor/audit_r2.py` (auditoría R²). Hiperparámetros reales:

| Algoritmo | Implementación | Hiperparámetros |
|---|---|---|
| Dummy | `DummyRegressor(strategy="mean")` | — |
| Ridge (log) | `Pipeline[ColumnTransformer(imputación mediana + StandardScaler, OHE min_frequency=10) → Ridge(alpha=1.0)]`, objetivo `log1p`, predicción `expm1` | alpha=1,0 |
| Árbol | `DecisionTreeRegressor(max_depth=6, random_state=20261023)` | max_depth=6 |
| Random Forest | `RandomForestRegressor(n_estimators=400, max_depth=18, min_samples_leaf=3, n_jobs=-1, random_state=20261023)` | 400 / 18 / 3 |
| CatBoost | `CatBoostRegressor(iterations=1000, depth=6, learning_rate=0.05, loss_function="RMSE", random_seed=20261023, cat_features=[índices de 16 categóricas])` | 1000 / 6 / 0,05 |

Preprocesamiento (solo ajustado con train):

```python
ColumnTransformer([
    ("num", Pipeline([SimpleImputer("median"), StandardScaler()]), NUMERICAS),
    ("cat", Pipeline([SimpleImputer(constant="SIN_DATO"),
                      OneHotEncoder(handle_unknown="ignore", min_frequency=10)]), CATEGORICAS),
], remainder="drop")
```

## 4. Por qué estos algoritmos y por qué comparar complejidades

- **Dummy:** referencia mínima; si ningún modelo lo supera, no hay señal.
- **Ridge:** modelo lineal regularizado; si la relación fuese
  aproximadamente lineal bastaría; no capta interacciones no lineales
  (evidencia: R² 0,30 en valor A vs 0,69–0,73 de los árboles).
- **Árbol de decisión:** particiona el espacio de features en cortes
  univariados (recursivos, minimizando el error por hoja); interpretable y
  capta no linealidad; un solo árbol es inestable.
- **Random Forest:** promedia cientos de árboles entrenados sobre muestras
  bootstrap y subconjuntos de features, reduciendo varianza y sobreajuste.
- **CatBoost:** boosting secuencial de árboles sobre residuos, con manejo
  nativo de categóricas (estadísticas ordenadas) y regularización.

## 5. Cómo se evitó el sobreajuste

- División de prueba sellada antes de entrenar (un predio nunca en ambos
  lados).
- Partición espacial y LOZO como controles de dependencia geográfica.
- Regularización explícita: `min_samples_leaf`, `max_depth`, `alpha`,
  `l2_leaf_reg`, `learning_rate` moderado.
- Semillas fijas y particiones versionadas (`data/splits/`).

## 6. Qué pasa cuando los modelos no generalizan

Evidencia directa: en ZHG, los mismos modelos con R² 0,77–0,82 en test por
predio pasan a **R² −1,70 (RF) y −2,18 (CatBoost)** cuando las zonas 01, 06
y 10 quedan completamente fuera del entrenamiento: el modelo memoriza
niveles zonales y no puede extrapolarlos. Por eso fueron rechazados.
