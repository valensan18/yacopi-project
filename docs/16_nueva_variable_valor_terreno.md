# Doc 16 — Nueva variable objetivo predial VALOR_TERRENO_Ha y reevaluación del ML

**Fecha:** 2026-10-23 · **Rama:** `experimental/valor-terreno-ha` (NO fusionada, sin push)
**Alcance:** experimental. No modifica SQLite de producción, modelos desplegados,
`.env` de Contabo ni la VPS.

> **CORRECCIÓN METODOLÓGICA (revisión independiente, protocolo v2):** la
> validación espacial original evaluaba modelos entrenados con la partición
> aleatoria sobre el test espacial (contaminación: 81,3 % del test espacial de
> A y 79,7 % del de B estaba en el entrenamiento). Se corrigió con dos
> protocolos independientes (cada uno entrena con su propio conjunto) y
> asserts de disjuntez; las métricas v1 quedaron en
> `ml/artifacts/exp-valor-terreno-001/historial_no_independiente_v1/` como
> históricas no independientes. Métricas espaciales v2 (A): RF R² 0,171,
> CatBoost −0,075 (antes 0,883/0,930). El protocolo por predio no cambió.
> Detalles y matriz ANTES/DESPUÉS: `entrega_docente/AUDITORIA_R2_ATLAS_VIVO.md`.
> También se corrigió el ejemplo didáctico de R² negativo (ahora con
> entrenamiento y prueba separados: R² prueba = −18,55) y se separaron los
> baselines (mediana zonal del objetivo en train ≠ referencia ZHG del
> dataset). Auditoría de consolidación: avalúo/áreas constantes por predio
> (0 inconsistentes), sin crossover A/B, zona dominante por área (12 predios
> corregidos). Sensibilidad: quitar `area_terreno_m2` de X casi no cambia las
> métricas (sin inflación mecánica relevante).

---

## 1. Contexto

Aclaración metodológica del profesor Jesús: la variable de respuesta de su
trabajo de valoración fue:

```
VALOR_TERRENO_Ha = (VALOR_AVALUO * 10000) / AREA_TERRENO_M2   [COP/ha]
```

con un filtro de predios sin construcción o con construcción reducida
(**hasta 32 m²**) para disminuir la influencia de las edificaciones.
Se verificó y confirmó que el umbral aplica a **area_construida_m2**
(NO a la superficie del terreno).

## 2. Diagnóstico de la variable (Fase 1)

### 2.1 Origen y significado

- `valor_avaluo` (CSV `interseccion_terrenos_zhg_r1_yacopi.csv`): avalúo
  **total** del predio en COP, incluida la construcción. **No existe** un campo
  de avalúo exclusivo del terreno por predio; el único valor de terreno
  disponible es el zonal (`valor_hectarea_agropecuario`, 11 valores).
- **No** debe presentarse como valor comercial observado: es avalúo catastral.
- Sin campos de fecha ni procedencia del avalúo en los CSV → confirmar con el
  profesor (vigencia y fuente del avalúo).

### 2.2 Calidad

| Campo | n | nulos | ceros | negativos | rango |
|---|---|---|---|---|---|
| valor_avaluo (COP) | 9.447 | 0 | 0 | 0 | 4.000 – 878.808.000 |
| area_terreno_m2 | 9.447 | 0 | 0 | 0 | 10 – 8.306.726 |
| area_construida_m2 | 9.447 | 0 | 5.793 | 0 | 0 – 2.016 |

Nota: 5.793 filas con construcción = 0 **registradas**; la ausencia de dato de
construcción no se interpretó como ausencia comprobada de edificaciones
(en este CSV no hay nulos de construcción, pero el criterio se mantiene).

### 2.3 Escenarios

| Escenario | Criterio | Filas | Predios |
|---|---|---|---|
| A | area_construida_m2 == 0 | 5.793 | **4.676** |
| B | 0 < area_construida_m2 ≤ 32 | 1.184 | **986** |
| Excluidos | area_construida_m2 > 32 | 2.470 | — |

### 2.4 Distribución del objetivo

| Estadístico | Escenario A | Escenario B |
|---|---|---|
| n | 5.793 | 1.184 |
| min | 92.000 | 105.571 |
| p05 | 191.697 | 230.314 |
| mediana | 481.333 | 522.581 |
| p95 | 1.922.500 | 5.934.797 |
| máx | 22.278.481 | **1.154.000.000** |
| valores únicos | 2.737 | 958 |

Valores atípicos por área pequeña: 46 filas con área ≤ 100 m²; el cociente
llega a 1.354.285.714 COP/ha (inflación del cociente con áreas mínimas).

### 2.5 ¿Derivada de los 11 valores zonales?

- Igualdad exacta con `valor_hectarea_agropecuario`: **0 %**.
- Igualdad exacta con `valor_hectarea_agropecuario × area_terreno/10000`: **0 %**.
- Correlación avalúo vs zonal×área: **0,728** (todas las filas) y **0,912**
  (predios de una sola zona) → la variable **no es una copia** del valor
  zonal, pero está fuertemente asociada (avaluos probablemente construidos
  sobre la zonificación geoeconómica con ajustes prediales).
- Valores distintos del objetivo: **5.654** (frente a 11 zonales) → variación
  genuinamente predial.

### 2.6 Comparación con la referencia ZHG

| | Escenario A | Escenario B |
|---|---|---|
| ratio valor_predial/zonal (mediana) | 1,056 | 1,435 |
| ratio p05 – p95 | 0,53 – 3,17 | 0,80 – 8,01 |
| % dentro de 0,5–2× del zonal | 86,4 % | 69,4 % |
| MAE vs zonal (COP/ha) | 387.225 | 3.808.115 |

En el escenario A el valor predial orbita la referencia zonal (± 5,6 %
mediano); en el B se desvía mucho más (componente de construcción y casos
extremos).

### 2.7 Áreas

- Área geoeconómica por fila: mediana **98,3 %** del terreno; la suma por
  predio llega a 103,1 % (predios en varias zonas); 4.210 filas con
  intersección > terreno.
- Área ZHF: unión en 9.428/9.447 filas; mediana **103,2 %** del terreno;
  64,4 % de las filas con ZHF > terreno (solapamientos de polígonos).

## 3. Fase 2 — Dataset, features y particiones

- Dataset: **una fila por predio** (`numero_predial`); atributos ZHF del
  polígono dominante por área; predios sin ZHF con imputación `SIN_DATO`.
- Features estrictas (sin fuga): `area_terreno_m2`, `area_construida_m2`,
  `area_zhf_m2`, `tr_latitud`, `tr_longitud`, `destino_economico`,
  `zhf_codigo`, `zhf_dispon`, `zhf_influe`, `zhf_uso_ac`, `aht_vpoten`,
  `fa_element`, `vus_vocaci`, `ups`, `clc_nivel1..6`.
- **Excluidas por fuga:** `valor_avaluo`, `valor_terreno_ha`,
  `valor_hectarea_agropecuario`, `codigo_zona_geoeconomica`,
  `area_en_zonageoeconomica_m2`, `porcentaje_en_zonageo`, `zhg_codigo`,
  `zhg_valor_`, `zhg_valor1`, `zhg_subzon`.
- Correlación feature-objetivo: todas débiles (|r| ≤ 0,07 en A; ≤ 0,18 en B,
  latitud) → la señal vive en interacciones, principalmente geográficas.
- Particiones **reproducibles** (seed 20261023) versionadas en
  `data/splits/valor/valor_terreno_ha_{A|B}_n<size>/`:
  - `train/test_predio` (80/20 por predio; un predio nunca en ambos).
  - `train/test_espacial` (bloques geográficos 6×6, 20 % de bloques fuera).
  - Transformaciones (imputación, estandarización, one-hot) ajustadas solo
    con entrenamiento.

## 4. Fase 3 — Resultados comparativos reales

### 4.1 Escenario A (construcción = 0; 4.676 predios; test predio n=936, espacial n=689)

| Modelo | MAE predio | R² predio | MdAPE predio | MAE espacial | R² espacial |
|---|---|---|---|---|---|
| Dummy (media) | 758.752 | −0,00 | 0,887 | 1.276.465 | −0,00 |
| Ridge (log) | 392.022 | 0,30 | 0,190 | 798.278 | 0,11 |
| Árbol (prof 6) | 343.025 | 0,46 | 0,146 | 216.043 | 0,90 |
| **Random Forest** | **248.296** | **0,69** | **0,067** | 288.241 | 0,88 |
| **CatBoost** | 279.284 | **0,73** | 0,169 | **246.137** | **0,93** |
| *Contexto: mediana zonal (train)* | *311.045* | *0,05* | — | — | — |

- Todos los modelos superan al dummy; RF/CatBoost superan la mediana zonal en
  MAE (248–279 k vs 311 k) y claramente en R².
- Desglose por zona (CatBoost, MAE COP/ha): 133 k – 563 k.
- Desglose por área: < 0,2 ha → 2,19 M; 0,2–2 ha → 309 k; 2–10 ha → 152 k;
  ≥ 10 ha → 204 k.
- Importancia CatBoost (top): area_terreno_m2 (27,6), area_zhf_m2 (18,8),
  tr_latitud (12,4), destino_economico (9,0).

### 4.2 Escenario B (0 < construcción ≤ 32 m²; 986 predios; test predio n=198)

| Modelo | MAE predio | R² predio | MAE espacial | R² espacial |
|---|---|---|---|---|
| Dummy (media) | 15.347.647 | −0,02 | 3.768.114 | −0,00 |
| Ridge (log) | 12.726.825 | 0,05 | 1.593.803 | 0,54 |
| Árbol (prof 6) | 11.846.090 | 0,12 | 297.691 | 0,99 |
| Random Forest | 11.487.894 | 0,15 | 589.333 | 0,94 |
| CatBoost | 11.670.499 | 0,12 | 308.948 | 0,98 |

- El test por predios contiene **7 casos > 50 M COP/ha (máx 1.154 M)**; sin
  esos casos CatBoost da MAE 727.710 y R² 0,506.
- El test espacial no incluye esos extremos, por eso sus métricas parecen
  buenas; el desglose < 0,2 ha llega a 120 M de MAE.

### 4.3 Generalización con zonas completas fuera (LOZO, CatBoost)

| | MAE por zona (COP/ha) |
|---|---|
| Escenario A | 210 k – 1,13 M (peor en zonas con nivel propio: 2 y 3) |
| Escenario B | 753 k – 8,18 M |

Cuando una zona entera falta en entrenamiento, el error crece de forma
importante: buena parte del desempeño proviene de la geografía/zona presente
en el entrenamiento.

## 5. Fase 4 — Selección

**No se recomienda un modelo definitivo todavía.** Motivos:

1. El objetivo representa **avalúo catastral total/hectárea**, no valor
   comercial; su sustentación exige confirmar con el profesor: fecha y
   procedencia de los avalúos, y si `valor_avaluo` incluye construcción.
2. El desempeño depende de la zona presente en entrenamiento (LOZO);
   la mejora sobre la consulta de mediana zonal es real pero modesta en MAE
   (≈ 10–20 % en el escenario A).
3. El escenario B está contaminado por cocientes extremos de áreas mínimas;
   requiere una regla explícita de tratamiento (área mínima, truncamiento o
   exclusión) acordada con el profesor.
4. La variable está correlacionada con el valor zonal (r ≈ 0,91 en predios de
   una zona); un modelo individual no es una fuente independiente de la
   referencia ZHG, la refina.

**Línea viable si se confirman los puntos anteriores:** escenario A con
CatBoost/RandomForest como interpolador experimental del avalúo catastral
por hectárea (nunca como avalúo oficial ni valor de mercado).

## 6. Limitaciones metodológicas

- Sin fecha de vigencia de los avalúos.
- Áreas ZHF con solapamientos (sumas > terreno).
- 12–32 predios sin dato ZHF por escenario (imputados).
- Umbral de 32 m² sin documento fuente en los datos (confirmar con el
  profesor).
- Extremos por área mínima no tratados (pendiente de criterio).

## 7. Información a confirmar con el profesor

1. Fecha y procedencia de `valor_avaluo` (¿avalúo catastral vigente?).
2. ¿`valor_avaluo` incluye construcción? (define el sesgo del escenario B).
3. Criterio oficial para predios con área de terreno mínima (¿excluir
   < 100 m²? ¿acotar el cociente?).
4. Confirmación del umbral de 32 m² sobre construcción.
5. Si acepta que el modelo se presente como interpolación del avalúo
   catastral (no como valor comercial ni avalúo individual certificado).

## 8. Recomendación

- **No** pasar a modelo definitivo ni a producción con esta variable sin las
  confirmaciones del punto 7.
- Continuar como experimento (rama `experimental/valor-terreno-ha`) con el
  escenario A; el escenario B queda documentado pero no recomendado.
- La etiqueta oficial del endpoint de producción sigue siendo
  `pending_verification` (503 MODEL_NOT_READY). No se activó nada.

## 9. Reproducibilidad

```powershell
.\.venv\Scripts\python.exe scripts/audit_valor_terreno.py      # Fase 1 (auditoría)
.\.venv\Scripts\python.exe scripts/analisis_valor_terreno.py   # Fase 1 (comparación ZHG)
$env:PYTHONPATH="ml/src"; .\.venv\Scripts\python.exe ml/src/yacopi_ml/valor/train.py      # Fases 2-3
$env:PYTHONPATH="ml/src"; .\.venv\Scripts\python.exe ml/src/yacopi_ml/valor/evaluate.py   # desgloses + LOZO
```

Salidas: `data/processed/09_auditoria_valor_terreno.json`,
`data/processed/10_analisis_valor_terreno.json` (ignorados por Git),
`data/splits/valor/` (versionado) y `ml/artifacts/exp-valor-terreno-001/`
(ignorado).

## 10. Restricciones cumplidas

Sin cambios en SQLite de producción, sin reemplazo de experimentos históricos,
sin activación de predicción pública, sin cambios en `.env` de Contabo, sin
reconstrucción de contenedores, sin push y sin cambios en la VPS.
