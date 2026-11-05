# Matriz cronológica de decisiones metodológicas

D = decisión documentada en su momento (ADR/docs/commits). R = reconstruida
para explicar el trabajo (no había registro contemporáneo).

| # | Momento (evidencia) | Problema | Evidencia | Decisión | Justificación | Resultado | Estado |
|---|---|---|---|---|---|---|---|
| 1 | Fase 0 (ADR-0001) | Organizar el proyecto académico | anteproyecto | Monorepo con separación datos/ml/backend/frontend/docs | trazabilidad y separación de responsabilidades | estructura actual | D |
| 2 | Fase 1 (ADR-0002) | Datos sin limpiar; identificación de fuentes | CSV aportados | Normalizar sin sobrescribir originales; consolidar 1 fila/predio | reproducibilidad | 01–05 processed | D |
| 3 | Fase 1 | No existe etiqueta verificada de suelo | `data_manifest.json` (label_status pending) | No entrenar modelo "oficial" sin etiqueta | evitar pseudociencia | oficial 503 | D |
| 4 | Fase 2 (ADR-0003) | Comparar algoritmos pese a la ausencia de etiqueta | decisión ADR | Experimento proxy con avalúo total/ha (research-proxy) | comparación metodológica sin presentarlo como suelo | exp-proxy-001; nunca elegible | D |
| 5 | Fase 2 | Posible inflación por dependencia espacial | resultados aleatorios vs espaciales | Reportar ambas particiones; sellar test | honestidad de generalización | RF 0,82→0,74 | D |
| 6 | Fase 5 (docs/06) | Objetivo ZHG solo tiene 11 valores | conteo de valores únicos | Validación con zonas completas fuera + criterio predefinido (MAE < mediana y < moda zonal) | detectar memorización zonal | modelos colapsaron (R² −1,70/−2,18) | D |
| 7 | Fase 5 | Modelos no superan moda zonal en zonas fuera | metrics.json beats_mode=false | **Rechazo de los 5 modelos como candidatos** | no generalizan a zonas nuevas | ningún modelo aprobado | D |
| 8 | Fase 7B (docs/10) | Mostrar el flujo ML en el software | rechazo previo | Demo RF ajustada a todos los datos, off por defecto, con advertencias | demostración ≠ validación | exp-zhg-001-demo | D |
| 9 | Fase 7C | Particiones históricas sobrescritas | manifiesto demo | Versionar particiones en `data/splits/zhg/<target>_n<size>/` | reproducibilidad futura | splits versionados | D |
| 10 | Fase 8–9 | UX y coherencia institucional | auditorías docs/11–14 | Fuente única de textos, advertencias, public_id opaco | transparencia | app pública | D |
| 11 | Rama experimental (5b2fca7) | Nueva variable del profesor (VALOR_TERRENO_Ha) | comunicación docente | Auditar antes de modelar; umbral de 32 m² sobre CONSTRUCCIÓN | aclaración metodológica | escenarios A/B | D |
| 12 | Rama experimental | B contaminado por áreas mínimas | 7 extremos > 50 M en test | Reportar y no tratar extremos sin criterio docente | no eliminar datos sin autorización | R² B 0,05–0,15 documentado | D |
| 13 | Rama experimental | ¿La variable es independiente de ZHG? | corr 0,73/0,91; LOZO | No declarar modelo definitivo; pedir confirmaciones al profesor | la variable refina la zona, no la reemplaza | sin candidato | D |
| 14 | Hoy (entrega docente) | El profesor pidió trazabilidad y explicación de R² | observaciones del director | Paquete de reproducibilidad + auditoría R² + notebooks | transparencia científica | este paquete | D |
| 15 | Revisión independiente (commit `f0554f9`) | La validación espacial v1 estaba contaminada: modelos entrenados con la partición aleatoria evaluados sobre el test espacial (560/689 predios de A y 141/177 de B ya estaban en entrenamiento) | `scripts/evidencia_solapamiento.py` → `historial_no_independiente_v1/evidencia_solapamiento.json` | **Corrección protocolo v2**: entrenamiento independiente por protocolo (tr_esp→te_esp) con asserts de disjuntez; métricas v1 archivadas como NO independientes | una evaluación contaminada no es defendible | métricas espaciales cambian: RF A R² 0,883→0,171; CatBoost 0,930→−0,075 | D |
| 16 | Revisión independiente (commit `f0554f9`) | Ejemplo didáctico evaluado sobre los mismos datos de entrenamiento (R² ≈ +0,003, no negativo) | auditoría del código | Rehacer el ejemplo con entrenamiento y prueba separados (parábola: ajuste en x∈[0,2], prueba en x∈[6,10]) | el ejemplo debe demostrar de verdad un R² negativo | R² prueba = −18,55 verificado con assert | D |
| 17 | Cierre de entrega | LOZO cubría 4.668 de 4.676 predios (zona 1 con 8 predios excluida por umbral n<30); `groupby().first()` podía mezclar atributos de filas ZHF distintas | `desgloses_esc_A.json`; `scripts/verificar_zhf_fix.py` | LOZO completo sin umbral (suma = 4.676); `first(skipna=False)` conserva la fila real del polígono dominante | cobertura total y sin mezcla de filas | LOZO suma 4.676/986; el fix ZHF produjo **0 cambios numéricos** (los NaN son por predio completo) | D |
| 18 | Cierre de entrega | Decisión de estado del modelo | métricas v2 + LOZO + referencia ZHG | **Mantener sin modelo definitivo aprobado** (predicción oficial 503) | la generalización espacial es limitada (RF A espacial R² 0,171; peor MdAPE que la referencia ZHG) y la etiqueta sigue pendiente de confirmación docente | oficial 503 MODEL_NOT_READY | D |

## Decisiones reconstruidas (R)

- Elección inicial de ZHG como referencia experimental (R, previo a Fase 5):
  era la única referencia de suelo por unidad de área presente en los datos;
  se documentó su carácter zonal desde el contrato de etiqueta.
- Elección de los 5 algoritmos (R): cubrir un gradiente de complejidad
  (constante → lineal → no lineal simple → ensamble → boosting) para
  contrastar si el problema requería modelos flexibles.
