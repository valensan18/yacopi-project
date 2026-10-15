# Corrección global de coherencia de textos (Fase 9)

Fecha: 2026-10-15 · Rama dev · Solo textos de interfaz; sin cambios en
datos, modelos, métricas ni contratos.

## 1. Descripciones desactualizadas detectadas y corregidas

| # | Ubicación | Texto anterior (incorrecto) | Corrección |
|---|---|---|---|
| 1 | Footer global (`AppShell`) | "El modelo predictivo es experimental y estima un proxy de avalúo catastral total por hectárea" | Descripción centralizada actual (referencias ZHG + demostración ML; sin avalúos ni precios comerciales) |
| 2 | Inicio · aviso metodológico | "El único modelo disponible es experimental: predice un proxy…" | Referencia ZHG + demostración Random Forest + oficial deshabilitada + enlace a Predicción |
| 3 | Análisis · disclaimer | Remitía ML solo a Modelos | Aclara: gráficas ≠ predicciones; históricos en Modelos; demostración en Predicción (con enlaces) |
| 4 | Modelos · lede | "solo hay un experimento con un proxy" | Describe referencia ZHG, demostración actual e históricos |
| 5 | Modelos · título sección proxy | "Experimento proxy (Ruta B)" | "Experimento proxy (histórico, Fase 2)" |
| 6 | Acerca de · arquitectura | "Entrenamiento offline (experimento proxy)" | "Referencias zonales ZHG (dato) + artefacto experimental verificado" |
| 7 | Acerca de · limitaciones | "El modelo es experimental y estima un proxy…" | Descripción extendida centralizada + limitaciones del modelo actual |
| 8 | Metodología · paso 4 | Solo mencionaba el proxy | Incluye Fase 2 (histórico) y Fase 5 (ZHG vigente) |
| 9 | Metodología · sección proxy | "Limitaciones del proxy catastral" | "Experimentos históricos: limitaciones del proxy catastral" con contextualización |
| 10 | Banner de estado | Solo mencionaba el proxy al activarse | Distingue proxy histórico y demostración ZHG |

## 2. Textos históricos conservados (sin alterar)

- Modelos: métricas reales de `exp-proxy-001` (tablas espacial/aleatoria) y
  explicación "Avalúo total por hectárea vs. valor del suelo".
- Predicción: bloque del proxy solo visible si su flag local se activa
  (etiquetado como proxy).
- Metodología: limitaciones del proxy como experimento histórico.
- Glosario: nuevo término "Experimento histórico (proxy)".
- Documentos `docs/02–10`: intactos (trazabilidad).

## 3. Fuente única de contenido

`frontend/src/lib/appContent.ts`:
`APP_NAME`, `APP_DESCRIPTION_CORTA`, `APP_DESCRIPTION_EXTENDIDA`,
`REFERENCIA_ZHG_DESCRIPCION`, `MODELO_EXPERIMENTAL_DESCRIPCION`,
`DIFERENCIA_REFERENCIA_VS_ESTIMACION`, `EXPERIMENTOS_HISTORICOS_DESCRIPCION`,
`ESTADO_PREDICCION_OFICIAL`, `NO_AVALUOS`, `LIMITACIONES_GENERALES`.

Componentes que la usan: `AppShell` (footer), `About` (limitaciones),
`SystemStatusBanner` (textos de estado), y los tests de regresión.
Centraliza solo los conceptos que deben mantenerse consistentes; no es un
CMS.

## 4. Prevención de regresiones

`frontend/src/test/content.test.tsx` (5 pruebas): footer usa la descripción
centralizada y no contiene la frase del proxy; portada describe la
demostración actual con enlace a Predicción y sin el proxy como modelo
actual; Análisis diferencia gráficas/predicción con enlaces; Acerca de usa
la descripción extendida; las constantes centrales distinguen los conceptos
clave. Si una modificación futura reintroduce afirmaciones desactualizadas,
estas pruebas fallan.

## 5. Evidencia

- vitest: **33/33** · ruff/oxlint limpios · build OK (backend intacto:
  96 pytest de la fase anterior siguen válidos; sin cambios de backend).
- Playwright (escritorio 1440×900 y móvil 390×844, contenido renderizado):
  **14/14 comprobaciones** (footer actual y sin proxy; inicio con
  demostración actual y enlace; análisis diferenciado con enlaces; modelos
  con histórico y ZHG; metodología contextualizada; acerca con descripción
  extendida; glosario con el término histórico; predicción sin bloque proxy
  visible) con **0 errores de consola**.
- Capturas: `docs/capturas/f9_home_{desktop,movil}.png` y
  `f9_prediccion_{desktop,movil}.png`.

## 6. Limitaciones pendientes

Ninguna nueva. Persisten las documentadas: códigos territoriales sin
diccionario oficial, vigencia ZHG no acreditada, modelo sin evaluación
independiente y predicción oficial en 503.
