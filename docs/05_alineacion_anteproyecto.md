# Informe de alineación con el anteproyecto — ATLAS VIVO

Fecha: 2026-10-14 · Auditoría técnica (sin cambios de código, sin reentrenamiento).

## 1. Fuente y método de lectura

- Documento rector: anteproyecto en Word, ubicado en
  `C:\Users\DIEGHOST\Documents\yacopi-referencias\`. Nota de trazabilidad: el
  archivo con el nombre exacto indicado ("…(1).docx") no existe; en esa
  carpeta está `ANTEPROYECTO ARTICULO JULIAN Y VALENTINA.docx` (149.770
  bytes), cuyo contenido extraído corresponde íntegramente al anteproyecto
  del proyecto (19 páginas según su paginado; secciones idénticas a las
  citadas en `docs/00_contexto_maestro.md` §19.1). Se usó este archivo tras
  verificar contenido; el PDF convertido citado previamente no está en el
  repositorio.
- Los números de página que se citan provienen de la cartografía de la guía
  maestra (`docs/00_contexto_maestro.md` §19.1), que ya relaciona secciones
  con páginas del anteproyecto; se complementan con líneas de la extracción
  de texto (anexo local, no versionado).

## 2. Requisitos extraídos fielmente

| # | Requisito | Texto del anteproyecto (fiel) | Páginas aprox. |
|---|---|---|---|
| R1 | Título | "Implementación de un software predictivo para estimar el valor del suelo rural: caso de estudio Yacopí, Cundinamarca" | p. 3 |
| R2 | Objetivo general | "Desarrollar un software predictivo para la estimación del valor del suelo rural mediante modelos de aprendizaje supervisado, a partir de variables catastrales, físicas y territoriales, usando datos reales del municipio de Yacopí, Cundinamarca, e integrando sus resultados en un prototipo de consulta y visualización." | p. 5 |
| R3 | OE1 | "Caracterizar las variables catastrales, físicas y territoriales disponibles para el estudio, mediante análisis exploratorio, depuración inicial y revisión de su relación con el valor del suelo rural." | p. 5 |
| R4 | OE2 | "Comparar modelos de aprendizaje supervisado orientados a la estimación del valor del suelo rural, mediante métricas de desempeño, validación y análisis de interpretabilidad." | p. 5 |
| R5 | OE3 | "Implementar un prototipo de software predictivo con backend en FastAPI y frontend en React, integrando el modelo seleccionado, la consulta de predios, la visualización de estimaciones, gráficas, mapas y métricas de evaluación." | p. 5 |
| R6 | Variable objetivo | "En este proyecto, la variable objetivo será el valor del suelo rural…" · Marco conceptual: "Valor del suelo: representa la estimación económica de un terreno, determinada a partir de sus características físicas, ubicación, uso y condiciones del entorno." | p. 7 |
| R7 | Metodología | CRISP-DM para el componente analítico + enfoque ágil iterativo e incremental tipo Scrum para el software; fases de comprensión, preparación, modelado, evaluación, prototipo y despliegue. | p. 9–10 |
| R8 | Algoritmos | "regresión lineal regularizada, árboles de decisión, bosques aleatorios y métodos de ensamble"; stack scikit-learn. | p. 10, 11 |
| R9 | Métricas | "error absoluto medio (MAE), raíz del error cuadrático medio (RMSE) y coeficiente de determinación (R2)"; además generalización, interpretabilidad y "coherencia territorial". | p. 11 |
| R10 | Resultados esperados | 1) conjunto de datos depurado/estructurado/documentado; 2) modelo entrenado, evaluado y seleccionado con métricas, generalización e interpretabilidad; 3) prototipo FastAPI+React con consulta, estimaciones, gráficas, mapas, métricas y comparación de modelos; 4) artículo científico y documentación técnica. | p. 12–13 |
| R11 | Entregables | Base depurada; modelo serializado; prototipo web; artículo; presentación y documentación técnica. | p. 13 |
| R12 | Despliegue | "Docker para empaquetar dependencias, mejorar la reproducibilidad" (metodología, fase despliegue). | p. 11 |

## 3. Matriz de trazabilidad y cumplimiento

| Req. | Estado | Evidencia en el repositorio | Brecha |
|---|---|---|---|
| R1 Título | Cumplido | Identidad ATLAS VIVO coherente; portada y About describen el mismo propósito | — |
| R2 Objetivo general | **Parcial** | Software completo Fases 0–4.1; consulta/visualización operativas | El componente predictivo **oficial** no existe: `POST /predictions` = 503 por etiqueta pendiente |
| R3 OE1 Caracterizar | **Parcial** | Fase 1: diccionario (`docs/02`), banderas, EDA en `/exploracion`, SQLite documentada | "Revisión de su relación con el valor del suelo rural": la relación con la variable objetivo real no se ha medido (no hay etiqueta validada) |
| R4 OE2 Comparar modelos | **Parcial** | Fase 2 (exp-proxy-001): baseline/Ridge/Árbol/Forest/CatBoost, MAE/RMSE/R²/MdAPE, validación espacial y aleatoria, SHAP + permutación | Todo se ejecutó sobre un **proxy** (avalúo total/ha), no sobre el valor del suelo del anteproyecto; no hay modelo seleccionado oficialmente |
| R5 OE3 Prototipo | **Parcial** | Backend Fase 3 + frontend Fase 4–4.1: consulta, detalle, mapa, análisis, modelos, metodología | "Integrando el modelo seleccionado": la integración de estimaciones está construida pero **bloqueada** (503) a la espera del modelo validado |
| R6 Variable objetivo | **No verificable / pendiente de decisión** | `label_contract.yaml` en `pending_verification`; informe Fase 1/2 documenta la ausencia de columna validada | El anteproyecto no define si "valor del suelo rural" es avalúo catastral, valor comercial o valor exclusivo del terreno (ver §7) |
| R7 Metodología CRISP-DM/Scrum | Cumplido (analítico) / Parcial (Scrum) | ADRs y `docs/04_metodologia_ml.md` siguen CRISP-DM; sprint log informal en ESTADO | No hay artefacto Scrum formal (backlog/sprint review); aceptable para modalidad artículo pero no evidenciado |
| R8 Algoritmos | Cumplido | Los 4 exigidos + CatBoost implementados en `ml/src/yacopi_ml` | Ejecutados solo sobre proxy |
| R9 Métricas | Cumplido (implementación) | `metrics.py` calcula MAE/RMSE/R² + MdAPE/%err; resultados reales en `docs/04` | Aplicadas al proxy; faltan sobre el objetivo real |
| R10a Base depurada | Cumplido | Fase 1: 7.709 predios, SQLite 7 tablas, diccionario, banderas, hashes | — |
| R10b Modelo seleccionado | **Parcial** | exp-proxy-001 serializado (joblib), MODE CARD experimental, registro | Es experimental; no es el modelo del objetivo del anteproyecto |
| R10c Prototipo web | Cumplido | FastAPI + React + Leaflet + Plotly, todo con datos reales | — |
| R10d Artículo científico | **Pendiente** | No iniciado | Depende de resultados con etiqueta real |
| R11 Entregables | Parcial | Base, prototipo y docs técnicas existen; falta artículo y presentación final | — |
| R12 Docker/deploy | **Pendiente** | `deploy/` solo con README; sin Dockerfiles | Fase 7 diferida |

## 4. Variables reales: qué es cada columna

Clasificación sobre los CSV originales y SQLite (verificada en Fase 1; sin modificar datos):

| Rol | Columnas reales | Naturaleza |
|---|---|---|
| Avalúo catastral **total** | `valor_avaluo` → `valor_avaluo_total_cop` (COP, total inmueble) | Incluye potencialmente construcciones; **no es suelo exclusivo** |
| Valor **exclusivo del suelo** | **No existe** en ningún CSV/DB | Ninguna columna documenta un valor solo-terreno por predio |
| Valor unitario (por ha/m²) | `referencia_avaluo_total_por_ha_cop` (derivado: avalúo total/área); `valor_hectarea_agropecuario` (COP/ha, precio de zona preasignado) | El primero mezcla suelo+obra; el segundo es referencia zonal |
| Zonas homogéneas geoeconómicas (ZHG) | `codigo_zona_geoeconomica`, `ZHG_CODIGO`, `ZHG_VALOR_`, `ZHG_VALOR1`, `ZHG_SUBZON`, derivados `referencia_zhg_*` | Precios zonales IGAC (valor unitario de terreno por zona) y códigos de zona |
| Físicas y territoriales | `area_terreno_m2`, `area_construida_m2`, `destino_economico`, `ZHF_*`, `AHT_VPOTEN`, `FA_ELEMENT`, `VUS_VOCACI`, `UPS`, `CLC_NIVEL1..6`, coordenadas, geometrías | Variables explicativas candidatas (allowlist Fase 1) |

## 5. ¿Existe hoy una variable objetivo válida para el anteproyecto?

**No, como columna verificada.** Ninguna de las fuentes trae un valor exclusivo
del suelo por predio con método, fecha y superficie documentados. Tres rutas
posibles, sin tomar aún la decisión:

- **Ruta A (preferida por la guía):** conseguir con el equipo académico/gestor
  catastral una columna de valor de terreno independiente (COP, por predio,
  con fecha y método). Única que sostiene sin reparos el OE2 sobre el objetivo
  real.
- **Ruta B (implementada como experimento):** proxy avalúo total/ha.
  Explícitamente experimental; **no cumple** el objetivo del anteproyecto
  porque incluye construcciones.
- **Ruta C (defendible con datos actuales):** usar el valor unitario de zona
  geoeconómica (`ZHG_VALOR_`/`valor_hectarea_agropecuario`, que corresponden
  al "valor unitario del terreno" del estudio de zonas homogéneas que el
  propio anteproyecto cita — IGAC 2024a) como objetivo de "estimación de
  referencia zonal", con reglas estrictas: excluir códigos/precios zonales
  de X, validación con grupos espaciales por zona, etiquetado explícito como
  referencia, no como observación independiente de mercado.

## 6. ¿Sirve el modelo experimental actual para el objetivo?

**No directamente.** El modelo exp-proxy-001 predice `proxy_avaluo_total_cop_ha`
(COP/ha): 3.030 de 7.694 predios de la cohorte tienen área construida > 0, y
el área (denominador del proxy) es además predictor, lo que produce una
relación mecánica parcial (importancia dominante de áreas, documentada en
Fase 2). Presentarlo como "valor del suelo rural" sería metodológicamente
incorrecto. Su valor real es: (a) valida la ingeniería completa del pipeline
(particiones, tuning, interpretabilidad, artefactos) y (b) sirve como
comparación metodológica citada con honestidad en el artículo.

## 7. Riesgos identificados (con evidencia)

| Riesgo | Evidencia | Severidad |
|---|---|---|
| Fuga de información | Precios zonales y códigos ZHG en los CSV; bloqueados en `features.yaml` (31 columnas) y probado anti-leakage | Alta (controlada) |
| Inclusión de construcciones | 3.033/7.709 predios con `area_construida_m2 > 0`; el proxy los mezcla | **Crítica** para el objetivo real |
| Registros incompletos | 15 predios sin ZHF/coordenadas; `fa_element` 471 vacíos; `aht_vpoten` 40 | Media (documentada) |
| Validación espacial | Fase 2: R² 0,82 (aleatoria) → 0,74 (espacial) en Forest; Ridge colapsa en espacial | Alta (ya controlada con partición espacial) |
| Ausencia de diccionario/fechas | Sin diccionario oficial ni fecha de valoración | Alta (pendientes #2–3) |
| Ambigüedad económica del objetivo | El anteproyecto no especifica avalúo catastral vs comercial vs exclusivo de terreno | **Crítica** → decisión pendiente |

## 8. Decisión metodológica pendiente (no resuelta aquí, por instrucción)

El anteproyecto define el objetivo como "estimación del **valor del suelo
rural**" y en el marco conceptual como "estimación económica de un **terreno**"
(lo que sugiere suelo sin construcciones), pero **no** precisa si ese valor
debe ser catastral, comercial o de otra base, ni cómo separarlo de las
edificaciones. No existe en los datos una columna que permita dirimir esto
de forma inequívoca. **Se requiere confirmación del director disciplinar**
(pendiente #1 de `docs/pendientes.md`), con impacto en R2/R4/R10b.

## 9. Plan concreto para completar el componente predictivo (CRISP-DM)

Orden priorizado, usando la tecnología ya implementada (sin reentrenar hasta autorización):

1. **Decisión de objetivo (bloqueante, ≤1 reunión):** confirmar con el
   director cuál de las rutas A/B/C define "valor del suelo rural" y obtener
   la fuente correspondiente (o el aval formal para C). Actualizar
   `label_contract.yaml` a `verified` SOLO con esa evidencia.
2. **Contrato y datos:** columna de etiqueta + fecha + método; verificar
   cobertura y unidad COP/ha; reglas anti-fuga y allowlist final (Fase 1
   lista: 20 permitidas, 31 bloqueadas).
3. **Modelado (reuso de `yacopi_ml.train --mode production`):** baseline,
   Ridge, Árbol, Forest, CatBoost; tuning solo con GroupKFold espacial;
   test sellado intacto (no reutilizar para ajustes).
4. **Evaluación (OE2):** MAE/RMSE/R² (+MdAPE), tablas espacial/aleatoria,
   errores por subzona/tamaño/uso, SHAP/permutación; selección por MAE
   espacial; modelo serializado + MODEL_CARD + registro `validated`.
5. **Integración (OE3):** activar `POST /predictions` con el artefacto
   validado (cambio de backend **requiere tu autorización**, pendiente #13
   ya tiene el diseño); el frontend `/prediccion` y `/modelos` ya están
   preparados para consumirlo (formulario tipado y tablas reales).
6. **Cierre académico:** artículo científico con resultados ejecutados,
   presentación de sustentación, Docker/deploy (Fase 7) y pruebas finales.

**Riesgo residual:** si el director no define la etiqueta, el proyecto puede
sustentarse con honestidad como "software + experimento proxy documentado",
pero **no** como modelo validado del valor del suelo; esa diferencia debe
quedar explícita en el artículo (así lo exige el propio anteproyecto:
"las estimaciones… no reemplazarán una valoración catastral o comercial
oficial").

## 11. ACTUALIZACIÓN — Fase 5 (evidencia del software de Valentina)

Añadido el 2026-10-14, sin borrar la auditoría original. La inspección del
software anterior confirmó y refinó los hallazgos:

- Su objetivo era `valor_hectarea_agropecuario` (COP/ha) y la equivalencia
  con `ZHG_VALOR_` por zona quedó **verificada exactamente** (11 zonas, 11
  valores; códigos normalizados a 2 dígitos).
- Su experimento "integrado" alcanzó **R²=1.0 con RMSE≈0**: memorización de
  la zona mediante estadísticos zonales no bloqueados (`latitud_promedio`,
  modas, conteos). Su experimento honesto "interseccion" no superó el
  baseline (R²≈−0,01).
- El nuevo experimento ZHG de Atlas Vivo (Fase 5, bloqueando 44 columnas
  con fuga y usando 4 escenarios de validación + leave-one-zone-out)
  confirma: **ningún modelo de ML supera la referencia trivial en zonas no
  observadas**; el criterio de aceptación predefinido resultó `false` y no
  se eligió ganador. Ver `docs/06_fase5_modelo_valor_suelo_zhg.md`.
- Implicación para la matriz (§3): OE2 permanece **Parcial** y se documenta
  con más rigor: con los datos actuales la predicción ML defendible del
  valor del suelo no es alcanzable; quedan abiertas las opciones A
  (consulta directa de referencia zonal, no-ML), B (modelo experimental con
  limitaciones) y C (nuevos datos), a decisión del director.

## 12. Restricciones cumplidas en esta auditoría

Sin cambios en frontend/backend/modelos/CSV; sin reentrenamiento; sin push;
el documento rector y los datos personales de sus autores **no** se
incorporaron al repositorio (este informe solo cita textos técnicos).
