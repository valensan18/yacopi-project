# Entrega docente — Auditoría científica de Atlas Vivo

Paquete de reproducibilidad preparado para la revisión del profesor director.

**Proyecto:** Atlas Vivo — estimación académica del valor del suelo rural de
Yacopí (Cundinamarca). Sitio público: https://atlasvivo.xyz

**Rama de trabajo:** `experimental/valor-terreno-ha` (commit `5b2fca7`).
**Fecha de preparación de este paquete:** 2026-10-23.
**Estado de producción:** intacto (predicción oficial 503, demo desactivada).

## Cómo leer este paquete (orden sugerido)

1. `README_LEER_PRIMERO.md` — este documento.
2. `INVENTARIO_EXPERIMENTOS.md` — todos los experimentos, sus variables y sus
   resultados, con la distinción entre experimentación y modelo definitivo.
3. `PROCEDIMIENTO_COMPLETO_DATOS.md` — cada transformación aplicada a los CSV
   originales, con conteos reales y trazabilidad.
4. `MATRIZ_VARIABLES_OBJETIVO.md` — qué se predijo exactamente en cada etapa.
5. `ANALISIS_ESTADISTICOS.md` — análisis descriptivos y de calidad.
6. `AUDITORIA_R2_ATLAS_VIVO.md` — **documento prioritario**: de dónde salen
   todos los R² negativos/bajos del software, recálculo y causas con evidencia.
7. `IMPLEMENTACION_MODELOS_EN_CODIGO.md` — código real de Dummy, Ridge,
   Árbol, Random Forest y CatBoost (rutas, clases, hiperparámetros).
8. `MATRIZ_DECISIONES.md` — decisiones metodológicas cronológicas con
   justificación.
9. `RESULTADOS_Y_LIMITACIONES.md` — qué resultados son válidos y en qué
   alcance.
10. `GUIA_REPRODUCIBILIDAD.md` — cómo ejecutar todo desde cero.
11. `PREGUNTAS_PARA_EL_PROFESOR.md` — decisiones metodológicas pendientes de
    confirmación docente.
12. `ATLAS_VIVO_INFORME_ACADEMICO.pdf` — resumen académico con código y
    métricas.
13. `notebooks/` — 13 cuadernos de reproducción **ejecutados** (nuevos,
    identificados como posteriores; los cuadernos originales no existían).
14. `figuras/` — 11 gráficas generadas por código reproducible.
15. `manifiesto_reproducibilidad.json` — commit, hashes de entradas,
    versiones, semillas y resultados.

## Aviso de privacidad

- Este paquete **no incluye** los CSV originales, la base SQLite ni los
  artefactos ML: contienen identificadores prediales catastrales privados.
  Se referencian por ruta y hash SHA-256 (ver manifiesto); los cuadernos
  asumen que los archivos están en la máquina del evaluador (ver
  `GUIA_REPRODUCIBILIDAD.md`).
- Las figuras y tablas contienen únicamente agregados, sin `numero_predial`.

## Lo que el paquete demuestra

1. Los datos utilizados, su origen y su calidad.
2. Las transformaciones aplicadas y su efecto en los conteos.
3. Que la variable predicha **no fue la misma** en cada experimento:
   - Experimento proxy histórico (Fase 2): avalúo catastral **total** por
     hectárea (incluye construcciones).
   - Experimentos ZHG (Fase 5): valor unitario de referencia zonal (11
     valores posibles).
   - Experimentos VALOR_TERRENO_Ha (rama experimental): avalúo catastral
     total ÷ área del terreno, con filtros de construcción (0 y ≤ 32 m²).
   - Demo Random Forest: referencia ZHG, ajustada a los 7.709 predios, sin
     evaluación independiente.
   - Predicción oficial: no existe; sigue 503.
4. Cómo se implementó, entrenó y evaluó cada algoritmo.
5. Por qué aparecen R² negativos y bajos, con recálculo y evidencia.
6. Qué decisiones se tomaron y con qué justificación.
