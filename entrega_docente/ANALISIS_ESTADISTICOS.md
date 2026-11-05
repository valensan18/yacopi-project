# Análisis estadísticos realizados

Todos los análisis se ejecutaron con pandas/numpy/scipy/scikit-learn sobre
los CSV normalizados y el consolidado (ver `PROCEDIMIENTO_COMPLETO_DATOS.md`).
Código: `scripts/audit_data.py`, `scripts/analisis_valor_terreno.py`,
`scripts/audit_valor_terreno.py`, `ml/src/yacopi_ml/valor/evaluate.py` y los
cuadernos de reproducción.

## 1. Descriptivos generales

- Predios consolidados: 7.709 (7.694 con coordenadas; 7.694 con coincidencia
  ZHF; 15 sin dato ZHF).
- Destinos económicos: Agropecuario 6.746, Religioso 627, Habitacional 225,
  Institucional 88, Comercial 10, otros 13.
- Construcción: 3.033 predios con área construida > 0 (máx 2.016 m²).
- Zonas ZHG: 11; valor zonal 91.206,6 – 3.192.276,7 COP/ha (mediana
  456.041,7).

## 2. Avalúo y área

| Variable | n | min | p05 | mediana | p95 | máx |
|---|---|---|---|---|---|---|
| valor_avaluo (COP) | 9.447 | 4.000 | 231.000 | 2.818.000 | 33.277.200 | 878.808.000 |
| area_terreno_m2 | 9.447 | 10 | 977,4 | 50.000 | 456.390 | 8.306.726 |
| area_construida_m2 | 9.447 | 0 | 0 | 0 | 100 | 2.016 |

## 3. VALOR_TERRENO_Ha (rama experimental)

| Estadístico | Escenario A (n=5.793 filas / 4.676 predios) | Escenario B (n=1.184 / 986) |
|---|---|---|
| min | 92.000 | 105.571 |
| p05 | 191.697 | 230.314 |
| mediana | 481.333 | 522.581 |
| p95 | 1.922.500 | 5.934.797 |
| máx | 22.278.481 | 1.154.000.000 |

- Valores únicos: 5.654 en total (2.737 en A; 958 en B) frente a 11 zonales.
- 46 filas con área ≤ 100 m²; cociente máximo 1.354.285.714 COP/ha.

## 4. Relación con la referencia ZHG

- Ratio valor predial / valor zonal: A mediana 1,056 (p05–p95: 0,53–3,17;
  86,4 % dentro de 0,5–2×); B mediana 1,435 (0,80–8,01; 69,4 % dentro).
- MAE vs zonal: A 387.225 COP/ha; B 3.808.115 COP/ha.
- Igualdad exacta con zonal×área: 0 %. Correlación avalúo vs zonal×área:
  0,728 (todas las filas); 0,912 (predios de una sola zona).

## 5. Correlaciones feature–objetivo

Todas débiles: |r| ≤ 0,07 en A; en B la mayor es latitud (0,18). La señal
está en interacciones geográficas (importancia CatBoost: area_terreno 27,6;
area_zhf 18,8; latitud 12,4; destino económico 9,0).

## 6. Comparaciones de áreas

- Área geoeconómica por fila: mediana 98,3 % del terreno; suma por predio
  103,1 %; 4.210 filas con intersección > terreno.
- Área ZHF: mediana 103,2 % del terreno; 64,4 % de filas con ZHF > terreno;
  4.924 predios con diferencia > 5 % vs catastral.
- Área geométrica vs catastral: 7.548 predios dentro del 1 %; 106 difieren
  > 5 %.

## 7. Resultados reproducidos (fecha de ejecución en el manifiesto)

Ver `AUDITORIA_R2_ATLAS_VIVO.md` para las métricas recalculadas (protocolo
v2 con validaciones independientes) y `RESULTADOS_Y_LIMITACIONES.md` para su
interpretación.

## 8. Sensibilidad a `area_terreno_m2` como predictor

`area_terreno_m2` está en el denominador de VALOR_TERRENO_Ha y también como
feature. Repitiendo el protocolo v2 (escenario A) **sin** esa variable, las
métricas apenas cambian:

| Modelo | con área (R² predio / espacial) | sin área (R² predio / espacial) |
|---|---|---|
| Random Forest | 0,689 / 0,171 | 0,683 / 0,128 |
| CatBoost | 0,725 / −0,075 | 0,727 / −0,011 |

No hay inflación mecánica relevante por tener el área en X (resultado en
`ml/artifacts/exp-valor-terreno-001/sensibilidad/`).
