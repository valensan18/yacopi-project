# Resultados válidos y limitaciones

## Qué resultados son confiables y en qué alcance

| Resultado | Alcance de validez |
|---|---|
| Descriptivos y calidad de datos (conteos, nulos, áreas, destinos) | Confiables; reproducibles con los scripts de auditoría |
| exp-proxy-001 (Fase 2): RF espacial MAE 3.226.230, R² 0,74 | Confiable **solo** como comparación metodológica sobre el proxy avalúo total/ha; no describe el valor del suelo |
| exp-zhg-001/ponderado (Fase 5): métricas por protocolo y rechazo | Confiables y verificadas por reentrenamiento; el rechazo es robusto |
| exp-valor-terreno-001 A (v2): RF test predio MAE 248.296, R² 0,69; **test espacial independiente R² 0,171 (CatBoost −0,075)** | Confiable dentro de la rama experimental; la generalización espacial es limitada; no es modelo definitivo |
| exp-valor-terreno-001 B: test predio R² 0,12–0,15 (extremos); espacial independiente RF 0,863/CatBoost 0,646 | Dominadas por extremos de áreas mínimas en el test predio; usar con análisis de sensibilidad |
| Métricas espaciales v1 (R² 0,88–0,93 en A) | **HISTÓRICAS — EVALUACIÓN NO INDEPENDIENTE** (81 %/80 % del test estaba en el entrenamiento); conservadas en `historial_no_independiente_v1/`, no se presentan como válidas |
| Demo RF | Sin evaluación independiente por diseño; solo demostración funcional |

## Qué NO es confiable

- Cualquier lectura de las cifras proxy como "predicción del valor del
  suelo".
- Comparar R² entre experimentos o particiones sin su contexto (n, cohorte,
  variable distinta).
- El R² del test espacial como indicador único: la composición de bloques
  del test cambia el resultado (ver `AUDITORIA_R2_ATLAS_VIVO.md`).

## Limitaciones metodológicas principales

1. Sin fecha ni procedencia documentada de los avalúos y de la referencia
   ZHG (confirmar con el profesor).
2. `valor_avaluo` es avalúo catastral **total**; no hay valor exclusivo de
   terreno por predio en los datos.
3. Áreas inconsistentes entre fuentes (ZHF 103 % mediana del terreno; 4.924
   predios > 5 % de diferencia).
4. Predios multizona (1.601) requieren imputación dominante/ponderada.
5. Cocientes extremos por áreas mínimas (46 filas ≤ 100 m²) sin tratamiento
   acordado.
6. Dependencia espacial fuerte: el desempeño depende de que la zona esté
   representada en el entrenamiento (LOZO).
7. Umbral de 32 m² de construcción sin documento fuente en los datos.

## Resultados no reproducibles exactamente

- Métricas de Fase 5 (ZHG dominante): **verificadas hoy** — un reentrenamiento
  completo con las particiones congeladas actuales reproduce exactamente las
  cifras históricas (incluidos los R² negativos de zonas fuera; ver
  `AUDITORIA_R2_ATLAS_VIVO.md`).
- Métricas del proxy (Fase 2): **verificadas hoy** — reentrenamiento completo
  (`exp-proxy-rerun`) reproduce exactamente las 10 cifras de la interfaz
  `/modelos` (R² −0,0253/−0,1140 espacial; −0,0153 aleatoria; mismos MAE y n).
- Variante ponderada (2.785 predios): no reentrenada en esta entrega; sus
  métricas provienen de `exp-zhg-001-ponderado/metrics.json`.
- Resultados de la demo (ajuste a 7.709) no son una evaluación.
