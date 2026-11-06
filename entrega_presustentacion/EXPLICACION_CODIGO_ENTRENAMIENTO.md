# Explicación del código de entrenamiento

Archivos reales (rama `feature/valor-modelo-v1` y rama científica
`experimental/valor-terreno-ha`):

- `ml/src/yacopi_ml/valor/dataset.py` — consolidación del escenario A y
  selección de features sin fuga.
- `ml/src/yacopi_ml/valor/modelos.py` — `preprocesador`,
  `entrenar_modelos` y `predecir` del protocolo v2.
- `ml/src/yacopi_ml/valor/export_v1.py` — entrenamiento FINAL y exportación
  del artefacto `exp-valor-v1`.

## 1. Cohorte y variable

```python
ds = construir_dataset("A")          # construcción registrada == 0
# target: VALOR_TERRENO_Ha = valor_avaluo * 10000 / area_terreno_m2
X, y, meta, _ = seleccionar_features(ds)   # 19 features, sin avalúo ni zonales
```

## 2. Preprocesamiento (ajustado con el entrenamiento)

```python
ColumnTransformer([
    ("num", Pipeline([SimpleImputer("median"), StandardScaler()]), NUMERICAS),
    ("cat", Pipeline([SimpleImputer(constant="SIN_DATO"),
                      OneHotEncoder(handle_unknown="ignore", min_frequency=10)]),
     CATEGORICAS),
], remainder="drop")
```

## 3. Modelo

```python
pipeline = Pipeline([
    ("enc", preprocesador(X)),
    ("reg", RandomForestRegressor(
        n_estimators=400, max_depth=18, min_samples_leaf=3,
        n_jobs=-1, random_state=20261023)),
])
pipeline.fit(X, y)   # 4.676 predios del escenario A
```

## 4. Qué se guarda en el artefacto (`deploy-model/exp-valor-v1/`)

| Archivo | Contenido |
|---|---|
| `model.joblib` | pipeline completo (preprocesamiento + Random Forest) |
| `features.json` | features por `public_id` (sin `numero_predial`, sin avalúos) |
| `feature_schema.json` | orden y tipo de columnas |
| `training_stats.json` | mín/máx numéricos y niveles categóricos (control de dominio) |
| `manifest.json` | id, versión, rol, hiperparámetros, semilla, hashes de datos, commit |
| `metrics_evaluacion.json` | métricas de validación INDEPENDIENTES (test sellado v2 + 5 pliegues de estabilidad), separadas del ajuste final |
| `MODEL_CARD.md` | ficha técnica |

## 5. Distinción clave

El **ajuste final** usa los 4.676 predios (sin validación posible sobre
ellos). Las **métricas de validación** provienen de evaluaciones anteriores
con particiones independientes (test espacial sellado v2 y 5 pliegues de
estabilidad) y se conservan como evidencia histórica separada. El artefacto
y el endpoint lo declaran explícitamente en cada respuesta.
