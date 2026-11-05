# Atlas Vivo — Rama de revisión docente (valor del suelo rural de Yacopí)

Rama: `revision-docente/valor-terreno-v2` · Repositorio privado
`valensan18/yacopi-project`. Esta rama contiene **solo el trabajo académico
revisable**; no modifica la aplicación desplegada en https://atlasvivo.xyz.

> **Estado del modelo:** NO existe un modelo predictivo definitivo aprobado.
> El endpoint oficial de predicción permanece en 503 MODEL_NOT_READY y la
> demostración experimental permanece desactivada. Esta rama documenta los
> experimentos y su auditoría, no habilita ninguna predicción.

## Objetivo de la investigación

Determinar si es viable un modelo de regresión supervisada para el valor del
suelo rural de Yacopí (Cundinamarca), partiendo de los datos catastrales
aportados por el equipo y de la variable comunicada por el profesor:

```
VALOR_TERRENO_Ha = (VALOR_AVALUO × 10000) / AREA_TERRENO_M2   [COP/ha]
```

con dos escenarios de construcción: A (construcción = 0; 4.676 predios) y
B (0 < construcción ≤ 32 m²; 986 predios).

## Estructura de la entrega

| Ruta | Contenido |
|---|---|
| `README_PROFESOR.md` | Este documento |
| `entrega_docente/README_LEER_PRIMERO.md` | Punto de entrada del paquete |
| `entrega_docente/INVENTARIO_EXPERIMENTOS.md` | Todos los experimentos con sus variables, algoritmos, métricas y estado |
| `entrega_docente/PROCEDIMIENTO_COMPLETO_DATOS.md` | Transformaciones desde los CSV con tabla de trazabilidad |
| `entrega_docente/MATRIZ_VARIABLES_OBJETIVO.md` | Qué se predijo exactamente en cada experimento |
| `entrega_docente/ANALISIS_ESTADISTICOS.md` | Descriptivos, calidad y sensibilidad |
| `entrega_docente/AUDITORIA_R2_ATLAS_VIVO.md` | **Documento prioritario**: origen, recálculo y causas de los R² negativos/bajos |
| `entrega_docente/IMPLEMENTACION_MODELOS_EN_CODIGO.md` | Código real de Dummy, Ridge, Árbol, Random Forest y CatBoost |
| `entrega_docente/MATRIZ_DECISIONES.md` | Decisiones metodológicas cronológicas |
| `entrega_docente/RESULTADOS_Y_LIMITACIONES.md` | Qué es válido y en qué alcance |
| `entrega_docente/GUIA_REPRODUCIBILIDAD.md` | Cómo ejecutar todo desde cero |
| `entrega_docente/PREGUNTAS_PARA_EL_PROFESOR.md` | Decisiones pendientes de confirmación docente |
| `entrega_docente/GUION_EXPOSICION_10MIN.md` | Guion de exposición técnica |
| `entrega_docente/ATLAS_VIVO_INFORME_ACADEMICO.pdf` | Resumen académico con código y métricas |
| `entrega_docente/manifiesto_reproducibilidad.json` | Commit, hashes de entrada, versiones, semillas y resultados |
| `entrega_docente/notebooks/` | 13 cuadernos ejecutados (ver orden abajo) |
| `entrega_docente/figuras/` | 17 figuras generadas por código reproducible |
| `ml/src/yacopi_ml/valor/` | Código del experimento VALOR_TERRENO_Ha (protocolo v2) |
| `ml/tests/test_valor_splits.py` | Pruebas automatizadas de separación de conjuntos |
| `scripts/` | Auditorías, evidencias y generadores de la entrega |
| `docs/16_nueva_variable_valor_terreno.md` | Documento de fase del experimento |
| `docs/17_propuesta_integracion_produccion.md` | Análisis de seguridad para producción |

## Orden recomendado de lectura

1. `entrega_docente/README_LEER_PRIMERO.md`
2. `entrega_docente/INVENTARIO_EXPERIMENTOS.md`
3. `entrega_docente/MATRIZ_VARIABLES_OBJETIVO.md`
4. `entrega_docente/PROCEDIMIENTO_COMPLETO_DATOS.md`
5. `entrega_docente/AUDITORIA_R2_ATLAS_VIVO.md`
6. `entrega_docente/IMPLEMENTACION_MODELOS_EN_CODIGO.md`
7. `entrega_docente/RESULTADOS_Y_LIMITACIONES.md` y `MATRIZ_DECISIONES.md`
8. Los cuadernos (orden abajo) y el PDF académico.

## Variable objetivo de cada experimento

| Experimento | Variable Y | Estado |
|---|---|---|
| exp-proxy-001 (Fase 2, histórico) | avalúo catastral **total** por hectárea (incluye construcciones) | comparación metodológica; nunca elegible |
| exp-zhg-001 / ponderado (Fase 5) | valor unitario de referencia ZHG (11 valores zonales / 651 ponderados) | **rechazados** (no generalizan a zonas nuevas) |
| exp-zhg-001-demo | referencia ZHG | demostración de software, desactivada; sin evaluación independiente |
| exp-valor-terreno-001 A/B (protocolo v2) | VALOR_TERRENO_Ha (avalúo catastral ÷ área) | experimental; **sin modelo definitivo** |
| Modelo oficial | valor exclusivo de suelo validado | no existe; 503 MODEL_NOT_READY |

## Cómo ejecutar los notebooks

Los cuadernos son **reproducibles localmente** y declaran su tipo en el
encabezado: `ENTRENA` (08 y el ejemplo didáctico del 10 ajustan modelos;
puede tardar minutos) frente a `CONSULTA`/`CARGA`/`RECÁLCULO` (leen datos o
resultados pre-generados). La raíz del repositorio se resuelve en ejecución
buscando la carpeta `data/raw`.

Requisitos: Python 3.13+ con `ml/requirements.txt` +
`backend/requirements.txt` (+ `nbformat nbclient ipykernel`), y los **datos
originales en su lugar** (ver abajo). Orden sugerido: 00 → 12. Ejecución:
Jupyter, o en lote con `python scripts/ejecutar_notebooks.py`.

## Dónde está el código de entrenamiento

- Protocolo v2 actual: `ml/src/yacopi_ml/valor/modelos.py`
  (`preprocesador`, `entrenar_modelos`, `predecir`), `train.py` (dos
  protocolos independientes), `audit_r2.py` (recálculos y figuras),
  `evaluate.py` (desgloses y LOZO), `splits.py` (particiones reproducibles),
  `dataset.py` (consolidación y features sin fuga).
- Histórico Fase 2: `ml/src/yacopi_ml/models.py` (búsqueda de
  hiperparámetros, seed 42) — NO es el protocolo actual.

## Cómo interpretar los R² negativos

`R² = 1 − Σ(y−ŷ)² / Σ(y−ȳ)²`. R² < 0 significa que el modelo tiene más error
cuadrático que predecir la media del conjunto evaluado; no es un porcentaje
de aciertos. Causas reales en Atlas Vivo (ver `AUDITORIA_R2_ATLAS_VIVO.md`):
baselines (≈0 por construcción), zonas o bloques geográficos nunca vistos
en entrenamiento (ZHG −1,70/−2,18; v2 espacial A CatBoost −0,075), valores
extremos por áreas mínimas (escenario B) y subconjuntos con varianza casi
nula (LOZO −1e30/NaN). Ninguno proviene de un error aritmético; el único
defecto de evaluación encontrado (validación espacial v1 contaminada) fue
corregido en el protocolo v2.

## Decisiones pendientes de aprobación docente

1. Fecha y procedencia de `valor_avaluo` (¿avalúo catastral vigente?).
2. ¿El avalúo incluye construcción? (define el sesgo del escenario B).
3. Criterio para predios con área mínima (cocientes extremos).
4. Confirmación del umbral de 32 m² sobre construcción.
5. Alcance interpretativo: ¿refinar la referencia zonal o fuente
   independiente? (ver `PREGUNTAS_PARA_EL_PROFESOR.md`).

## Datos que NO están en GitHub (privados)

Por protección de identificadores catastrales, esta rama **no incluye**:

- Los CSV originales (`data/raw/`): `interseccion_terrenos_zhg_r1_yacopi.csv`
  y `zhf_yacopi.csv` (hashes SHA-256 en `data_manifest.json` local y en el
  manifiesto de reproducibilidad).
- La base SQLite y los artefactos ML (`ml/artifacts/`).
- Las particiones con identificadores prediales (`data/splits/valor/`).

Para reproducir los cuadernos, copie esos archivos a sus rutas originales
(`data/raw/…`) mediante el canal autorizado del equipo; `scripts/verify_inputs.py`
verifica los hashes.

## Estado de la plataforma pública

Sin cambios en esta rama: https://atlasvivo.xyz sigue mostrando que no
existe modelo definitivo (endpoint oficial 503; demo desactivada; la página
/modelos identifica los experimentos históricos verificados).
