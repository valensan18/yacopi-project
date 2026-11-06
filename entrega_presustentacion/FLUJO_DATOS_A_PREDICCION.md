# Flujo completo: del predio a model.predict()

```
1. DATOS (fuera de Git, privados)
   data/raw/interseccion_terrenos_zhg_r1_yacopi.csv  (9.447 filas)
   data/raw/zhf_yacopi.csv                           (7.968 filas)
        │  scripts/preparar_datos.py + build_db.py (consolidación)
        ▼
2. DATASET ESCENARIO A  (ml/src/yacopi_ml/valor/dataset.py)
   4.676 predios · construcción == 0 · 19 features sin fuga
   target: VALOR_TERRENO_Ha = VALOR_AVALUO × 10000 / AREA_TERRENO_M2
        │  export_v1.py: pipeline (imputación + escalado + one-hot) + RF(400/18/3)
        ▼
3. ARTEFACTO deploy-model/exp-valor-v1/
   model.joblib + features.json + schema + stats + manifest + metrics
        │  se transfiere por scp a la VPS (igual que la base de datos)
        ▼
4. BACKEND (backend/app/services/valor_v1.py)
   ValorV1Service.load(): verifica manifiesto (rol/status) y deserializa
   el pipeline UNA vez al iniciar (si VALOR_V1_ENABLED=true)
        │  POST /api/v1/predictions/valor-terreno-v1  {"public_id": "p_…"}
        │  1. existe en la base (404 si no)
        │  2. está en features.json del artefacto (422 si no: cohorte A)
        │  3. construcción == 0 y área > 0 (422 si no)
        │  4. features dentro del dominio del entrenamiento (422 si no)
        ▼
5. INFERENCIA REAL
   frame = pd.DataFrame([features][orden])
   prediction = float(self.model.predict(frame)[0])   ← Random Forest real
        ▼
6. RESPUESTA API (ValorV1Response)
   predicted_cop_ha + reference_zhg_cop_ha (dato, diferenciado) +
   evaluación + limitaciones + disclaimer (sin IDs privados ni avalúos)
        ▼
7. INTERFAZ (/prediccion — frontend/src/pages/Prediction.tsx)
   Sección "Estimación con Machine Learning — Demostración académica"
   A. Referencia ZHG (dato)  |  B. Estimación Random Forest (predicción)
```

## Puntos de control de seguridad en el flujo

- El modelo se carga **solo** desde `MODEL_DIR/exp-valor-v1` (montaje
  read-only en Docker) y exige manifiesto `rol=demostracion_academica` y
  `status=experimental_demo`.
- La consulta usa únicamente `public_id` opaco; el artefacto no contiene
  `numero_predial` ni avalúos.
- Cada respuesta declara el carácter demostrativo y las métricas reales.
