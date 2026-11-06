# Métricas reales de la demostración (RF v1, escenario A)

Fuente: `deploy-model/exp-valor-v1/metrics_evaluacion.json` (incluida en cada
respuesta del endpoint bajo `evaluation_context`).

## Test espacial sellado (protocolo v2, 689 predios)

| Referencia | MAE (COP/ha) | MdAPE | RMSE | R² |
|---|---|---|---|---|
| Random Forest | 767.064 | 11,69 % | 3.450.751 | 0,171 |
| Referencia ZHG (dato) | 817.030 | **5,65 %** | — | — |

## Estabilidad: 5 particiones espaciales independientes (semillas 101–505)

| Pliegue | RF MAE | RF MdAPE | RF R² | ZHG MAE | ZHG MdAPE |
|---|---|---|---|---|---|
| 101 | 264.898 | 12,3 % | +0,566 | **196.891** | **5,4 %** |
| 202 | 259.492 | 21,4 % | +0,787 | **234.250** | **5,4 %** |
| 303 | 241.648 | 21,4 % | −2,634 | **76.114** | **5,4 %** |
| 404 | 154.331 | 15,2 % | −0,009 | **107.948** | **5,4 %** |
| 505 | 260.063 | 25,5 % | +0,722 | **218.568** | **5,4 %** |

- RF gana en MAE: **0/5** · gana en MdAPE: **0/5**.
- Mediana: RF MAE ≈ 259.492 vs ZHG ≈ 196.891 COP/ha.

## Lectura honesta para la sustentación

1. El modelo produce predicciones reales y deterministas (verificado).
2. Su desempeño es **limitado y depende del territorio**: no supera a la
   referencia ZHG en error típico en ninguna partición espacial
   independiente.
3. Por eso se presenta como **demostración académica**, siempre junto a la
   referencia ZHG, y no como predictor recomendado ni herramienta de
   avalúo.
4. La variable objetivo es un cociente del avalúo catastral total, sin
   fecha de vigencia verificable.
5. No existe todavía un modelo definitivo aprobado (el endpoint oficial
   sigue en 503 MODEL_NOT_READY).

Detalle completo: `docs/18_diagnostico_modelo_operativo_v1.md` y
`ml/artifacts/exp-valor-terreno-001/estabilidad_rf_v1.json` (local).
