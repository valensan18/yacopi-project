# Guion de exposición técnica (10–15 minutos)

Demostración en vivo abriendo el código. Tiempos orientativos.

## 1. Contexto (1 min)
- Atlas Vivo: estimación académica del valor del suelo rural de Yacopí.
- Sitio público atlasvivo.xyz; repo privado; rama experimental actual.
- Abrir `entrega_docente/README_LEER_PRIMERO.md` para orientar.

## 2. Datos (2 min)
- Abrir `PROCEDIMIENTO_COMPLETO_DATOS.md` y mostrar en vivo:
  `python scripts/audit_data.py` → conteos 9.447/7.968 → 7.709 predios.
- Mostrar la tabla de trazabilidad: qué se hizo, por qué, cuántos antes y
  después.
- Señalar: sin fecha de avalúos, áreas inconsistentes, 46 áreas mínimas.

## 3. Variables objetivo (2 min)
- Abrir `MATRIZ_VARIABLES_OBJETIVO.md`: cuatro cosas distintas:
  proxy avalúo total/ha · referencia ZHG (11 valores) · VALOR_TERRENO_Ha ·
  demo RF.
- Ejecutar en vivo `scripts/audit_valor_terreno.py`: 5.654 valores únicos,
  0 % igualdad con zonal, corr 0,73/0,91.

## 4. Implementación de los modelos (2 min)
- Abrir `ml/src/yacopi_ml/models.py` (Fase 2) y `ml/src/yacopi_ml/valor/train.py`
  (rama actual): Dummy, Ridge, Árbol, RF, CatBoost con sus hiperparámetros.
- Explicar por qué se comparan complejidades distintas.

## 5. Entrenamiento y validación (2 min)
- Mostrar las particiones: `data/splits/valor/` (predio y espacial) y el
  criterio predefinido de Fase 5 (zonas fuera).
- Ejecutar `python -m yacopi_ml.valor.audit_r2` (o mostrar la salida
  guardada).

## 6. R² negativos — el punto central (3 min)
- Abrir `AUDITORIA_R2_ATLAS_VIVO.md` y la figura
  `figuras/fig00_ejemplo_r2_negativo.png` (recta sobre seno, R² −0,51).
- Mostrar en el código dónde están los R² de `/modelos` (Models.tsx líneas
  28–42) y explicar cada negativo real:
  - Baseline −0,03/−0,02: referencia media/mediana (≈ 0 por construcción).
  - Ridge −0,11 (espacial): lineal sobre objetivo sesgado.
  - ZHG zonas fuera −1,70/−2,18: zonas nunca vistas.
  - LOZO −1e30/NaN: varianza casi nula en el subconjunto.
- Concluir: no son errores de código; se recalculan con sklearn.

## 7. Resultados y decisiones (1–2 min)
- `RESULTADOS_Y_LIMITACIONES.md` + `MATRIZ_DECISIONES.md`: qué es válido,
  qué fue rechazado y por qué.
- Estado: sin modelo definitivo; oficial 503; demo off.

## 8. Preguntas al profesor (1 min)
- `PREGUNTAS_PARA_EL_PROFESOR.md`: vigencia del avalúo, contenido del avalúo,
  umbral de 32 m², tratamiento de áreas mínimas, alcance interpretativo.

## Recursos de respaldo
- `notebooks/` (13 cuadernos ejecutados), `figuras/` (11 figuras),
  `manifiesto_reproducibilidad.json`, PDF académico.
