# Auditoría integral — ATLAS VIVO (Fase 8)

Fecha: 2026-10-15 · Rama dev · HEAD auditado: `bba21bb` (árbol limpio).
Ejecutada contra los servidores locales reales (backend y frontend) con
navegador automatizado (Playwright), suites de pruebas, lint y build.

## 1. Resumen ejecutivo

Atlas Vivo es un prototipo académico **funcional, comprensible y alineado
con el alcance aprobado del anteproyecto**, con limitaciones científicas
explícitas en su componente predictivo. No se encontraron defectos
críticos. Los tres criterios principales se responden con evidencia en §11.

## 2. Inventario de funcionalidades

| Componente | Estado |
|---|---|
| Portada 3D narrativa (puntos reales) | Operativa |
| Catálogo de 7.709 predios (paginación, filtros, orden, búsqueda) | Operativo |
| Ficha predial (superficies, ubicación, atributos, alertas, interpretación) | Operativa |
| Referencias ZHG (zonas, predio, monozona/multizona, consolidación) | Operativas |
| Mapa Leaflet + CARTO Dark Matter (bbox, capas, leyenda, panel) | Operativo |
| Análisis estadístico Plotly (4 gráficas con datos reales) | Operativo |
| Página de modelos (estado, métricas documentadas, distinciones) | Operativa |
| Predicción: bloqueo oficial real (503) + consulta ZHG + demo experimental desactivada | Operativa |
| Metodología (CRISP-DM) y Acerca de | Operativas |
| Glosario (56 términos, búsqueda, categorías) y ayudas contextuales | Operativos |
| Backend FastAPI (11 endpoints, errores normalizados, public_id opaco) | Operativo |
| ML experimental (artefacto exp-zhg-001-demo, guards de dominio) | Operativo, desactivado por defecto |

## 3. Revisión por ruta (evidencia Playwright, escritorio 1440×900 y móvil 390×844)

| Ruta | Carga | Errores consola | Interacciones verificadas |
|---|---|---|---|
| `/` | 200 | 0 | portada + cifras reales |
| `/predios` | 200 | 0 | filtro destino: 7.709 → 6.746 predios (coherente) |
| `/predios/:id` | 200 | 0 | ficha real con tarjeta ZHG e interpretación contextual |
| `/predios/:id` inexistente | 200 | 2 (404 esperados) | mensaje "No se encontró un predio" |
| `/mapa` | 200 | 0 | teselas CARTO: 44 OK / 0 fallidas (escritorio), 18/0 (móvil) |
| `/exploracion` | 200 | 0 | 4 gráficas Plotly renderizadas |
| `/modelos` | 200 | 0 | estado `label_pending`, tablas y distinciones |
| `/prediccion` | 200 | 1 (503 esperado) | botón "Comprobar estado oficial (real)" muestra el 503; demo muestra "desactivada"; consulta ZHG funciona |
| `/metodologia` | 200 | 0 | línea de tiempo CRISP-DM |
| `/acerca-de` | 200 | 0 | secciones completas |
| `/glosario` | 200 | 0 | búsqueda "MAE" filtra correctamente |

Los únicos mensajes de consola tipo error son las respuestas HTTP
intencionales **404** (predio inexistente) y **503** (predicción oficial
bloqueada), que el navegador registra como fallos de recurso: son el
comportamiento esperado, manejado por la UI, no defectos.

## 4. Integridad de datos (comprobada API ↔ SQLite)

12/12 verificaciones: total 7.709 predios; correspondencia exacta de
`public_id` entre API y base; sin identificadores privados en respuestas;
áreas positivas; coordenadas en rango; 11 zonas ZHG con valores finitos
positivos e idénticos a la tabla `zhg_zones`; detalle coherente con el
catálogo; referencia ZHG responde con `reference_date: null`; oficial 503
`MODEL_NOT_READY`; demo 503 `EXPERIMENTAL_ZHG_DISABLED` por defecto.

## 5. Auditoría del componente ML

| Verificación | Resultado |
|---|---|
| Carga del artefacto exp-zhg-001-demo (flag activo, pruebas aisladas) | OK (Fase 7C/7D) |
| Desactivado por defecto | OK (503 probado hoy) |
| Consulta por public_id opaco | OK |
| Predios monozona admitidos | OK (referencia+estimación+diferencia) |
| Multizona rechazado | OK (422 UNSUPPORTED_MULTIZONE) |
| Controles de dominio (rangos/categorías) | OK (422 OUT_OF_DOMAIN) |
| Información incompleta bloqueada | OK |
| Comparación con referencia ZHG y diferencia en COP/ha | OK |
| Advertencia de pertenencia al ajuste | OK (siempre presente) |
| Carácter experimental rotulado | OK |
| Métricas históricas identificadas como tales | OK (docs/06, docs/10) |
| Predicción oficial bloqueada | OK (503 MODEL_NOT_READY) |

Sin reentrenamientos, sin cambios de hiperparámetros, sin promoción.

## 6. Comprensión y accesibilidad (revisión heurística)

Se verificaron en vivo: interpretación contextual en ficha (con dato real
del predio), tarjeta ZHG con explicación, alertas interpretadas, glosario
con búsqueda y categorías, HelpTip operable por teclado (Enter/Escape,
aria-expanded), correcciones A/B/C en Predicción, distinciones en Modelos.
Los tres perfiles simulados (ciudadano, estudiante, persona sin ML) pueden
completar el flujo de consulta e interpretación sin ayuda externa, con las
limitaciones visibles. **Revisión heurística, no pruebas con usuarios
reales.**

## 7. Pruebas ejecutadas (evidencia fresca)

- pytest: **94/94** · vitest: **28/28** · ruff/oxlint: limpios · build
  TS+Vite: OK.
- Playwright: auditoría integral de 10 rutas en escritorio y móvil (tablas
  §3); verificaciones previas de fases 4.1–7E reproducibles.
- Integridad API↔DB: 12/12.

## 8. Hallazgos clasificados

| # | Clasificación | Hallazgo | Estado |
|---|---|---|---|
| F8-01 | No defecto | 404/503 intencionales registrados por el navegador | Documentado |
| F8-02 | Pendiente (metodológico) | Sin diccionario oficial de códigos territoriales | Pendiente #2 |
| F8-03 | Pendiente (metodológico) | Vigencia de la referencia ZHG no acreditada | Pendiente |
| F8-04 | Limitación científica | El modelo ML no generaliza a zonas nuevas ni tiene evaluación independiente | Documentado, no bloqueante para prototipo |
| F8-05 | Limitación científica | Etiqueta de valor exclusivo del suelo pendiente → predicción oficial 503 | Documentado |

**No se detectaron defectos críticos ni importantes que requieran
corrección de código.** No se encontraron controles decorativos ni datos
simulados.

## 9. Correcciones efectuadas en la fase

Ninguna de código (no se encontraron defectos). Se restauró el backend
local al estado por defecto (flags apagados) tras la activación temporal
de Fase 7D.

## 10. Matriz de cumplimiento del anteproyecto (objetivos específicos)

| Objetivo aprobado | Funcionalidades que lo respaldan | Estado |
|---|---|---|
| OE1. "Caracterizar las variables catastrales, físicas y territoriales… mediante análisis exploratorio, depuración inicial y revisión de su relación con el valor del suelo rural." | Fases 1–2: diccionario, banderas de calidad, EDA en `/exploracion`, experimentos con objetivo ZHG y análisis de relación | **IMPLEMENTADO** (caracterización y depuración) con la salvedad de que la "revisión de su relación con el valor del suelo" se hizo con la referencia zonal disponible, no con una etiqueta de suelo exclusivo verificada (**PARCIALMENTE DEMOSTRADO**) |
| OE2. "Comparar modelos de aprendizaje supervisado… mediante métricas de desempeño, validación y análisis de interpretabilidad." | Fases 2 y 5: baseline/Ridge/Árbol/Forest/CatBoost, MAE/RMSE/R²/MdAPE, validación espacial y aleatoria, SHAP/permutación | **DEMOSTRADO EXPERIMENTALMENTE** (ejecutado y documentado); la generalización a zonas nuevas **NO VALIDADA** (falló el criterio predefinido; no hay ganador) |
| OE3. "Implementar un prototipo… con backend en FastAPI y frontend en React, integrando el modelo seleccionado, la consulta de predios, la visualización de estimaciones, gráficas, mapas y métricas de evaluación." | Backend (11 endpoints), frontend (10 rutas), mapa, gráficas, métricas, referencia ZHG y demostración ML integrada | **IMPLEMENTADO** en su versión honesta: la "estimación" integrada es la demostración experimental condicionada; la predicción oficial permanece bloqueada porque no existe modelo seleccionado-validado (**PENDIENTE** solo ese acto de habilitación, que requiere autorización y etiqueta) |

Lectura: el software cumple el alcance del anteproyecto como prototipo; el
estado científico del predictor es experimental y así se declara en toda la
aplicación. No se reformularon los objetivos.

## 11. Evaluación de los tres criterios

### A. ¿FUNCIONA? — **SÍ**
Todas las rutas cargan (200), sin errores de aplicación en escritorio ni
móvil; catálogo, fichas, mapa (teselas CARTO reales), gráficas, glosario,
ayudas, referencias ZHG y bloqueo oficial verificados por ejecución real.
Pruebas: 94 pytest + 28 vitest + Playwright multi-ruta + integridad 12/12.

### B. ¿SE ENTIENDE? — **SÍ, SEGÚN REVISIÓN HEURÍSTICA**
Glosario, ayudas contextuales e interpretaciones con datos reales
verificadas en navegador; unidades y limitaciones visibles. Persisten
ambigüedades documentales (significado puntual de códigos y vigencia ZHG)
que no pueden resolverse sin documentación externa, y la revisión
heurística **no equivale** a pruebas de usabilidad con personas.

### C. ¿CUMPLE EL ANTEPROYECTO? — **SÍ (como prototipo), con limitaciones científicas explícitas**
OE1 implementado (caracterización; relación con valor: parcialmente
demostrada con referencia zonal), OE2 demostrado experimentalmente (sin
validación de generalización), OE3 implementado con la estimación en modo
demostración experimental y la predicción oficial pendiente de etiqueta y
autorización. Ningún objetivo fue reformulado.

## 12. DECISIÓN FINAL DE ENTREGA

**LISTO PARA ENTREGA CON LIMITACIONES EXPLÍCITAS.**

El software funciona, se entiende y responde al alcance aprobado. Las
limitaciones son metodológicas (etiqueta de suelo pendiente, modelo sin
validación independiente, códigos sin diccionario oficial, vigencia no
acreditada) y **no impiden entregar el prototipo**: impiden afirmar que el
modelo está científicamente validado o que emite avalúos. Esta decisión no
equivale a aprobación académica del trabajo, que corresponde al director.

## 13. Plan de cierre

**A. Correcciones obligatorias antes de entrega:** ninguna de código
detectada en esta auditoría.

**B. Correcciones recomendadas (no bloqueantes):**
1. Documentar en el manual de ejecución cómo activar localmente la
   demostración (`EXPERIMENTAL_ZHG_ENABLED=true`) y cómo desactivarla.
2. Incluir las capturas de `docs/capturas/` en la evidencia de entrega.

**C. Mejoras futuras fuera del alcance actual:**
- Obtener diccionario oficial de códigos (pendiente #2).
- Obtener etiqueta verificada de valor exclusivo del suelo (pendiente #1)
  para reabrir, con autorización, la predicción oficial.
- Evaluación con datos nuevos (territorios/zonas adicionales) antes de
  cualquier reivindicación de generalización.
- Docker/VPS (Fase 7 del plan original, diferida).

## 14. Evidencia visual

- `docs/capturas/f8_home_desktop.png`, `f8_prediccion_desktop.png` y las
  series de fases 4.1–7E (`f4_*`, `f6b_*`, `f7b_*`, `f7d_*`, `f7e_*`).

## 15. Limitaciones y riesgos pendientes

1. Etiqueta de valor exclusivo del suelo: pendiente (bloquea la predicción
   oficial; por diseño en 503).
2. Modelo ML: experimental, monozona, sin generalización demostrada, sin
   evaluación independiente.
3. Referencia ZHG: sin vigencia acreditada (`reference_date: null`).
4. Códigos territoriales: sin decodificación oficial.
5. Despliegue remoto: no realizado (VPS diferido; Docker pendiente).

## 16. Confirmaciones

- Rama `dev`, árbol limpio tras commits; **sin push**.
- Datos originales, modelos, hiperparámetros y métricas históricas
  intactos.
- Demostración experimental desactivada por defecto; predicción oficial
  503.
