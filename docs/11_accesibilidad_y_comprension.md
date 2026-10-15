# Fase 7E — Accesibilidad, comprensión e interpretación de resultados

Fecha: 2026-10-15 · Rama dev · Sin cambios en datos, modelos, métricas ni
contratos de inferencia. Predicción oficial sigue en 503.

## 1. Objetivo

Convertir Atlas Vivo en una aplicación comprensible para personas sin
formación en catastro, estadística, geografía o IA, conservando el rigor:
cada resultado importante responde «¿Qué significa esto para el predio que
estoy consultando?» con los datos reales de la pantalla.

## 2. Conceptos explicados

- **Glosario central:** 56 términos en 3 categorías (Catastro y territorio:
  27; Estadística y aprendizaje automático: 20; Calidad de la información:
  9), cada uno con definición y, cuando aplica, «Cómo interpretarlo» y
  «Limitaciones». Búsqueda por texto + filtro por categoría.
- **Ayudas contextuales (HelpTip):** en ficha (identificación, superficies,
  ubicación, atributos territoriales, alertas), catálogo (identificador
  público, columna calidad), mapa (puntos y colores), análisis (4 gráficas),
  modelos (MAE/RMSE/R²) y predicción (estado del dominio).
- **Interpretaciones contextuales:** tarjeta «¿Qué significa esto para este
  predio?» en la ficha y en la tarjeta ZHG; «Qué significan estas alertas
  para este predio»; «¿Qué significa este resultado para el predio?» en la
  demostración ML.

## 3. Fuentes de las definiciones

Todas las definiciones se basan en la documentación del repositorio
(`docs/02_diccionario_datos.md`, `docs/04_metodologia_ml.md`,
`docs/06_fase5…`, guía maestra) y en las fuentes catastrales citadas en el
anteproyecto. **Términos no definibles documentalmente:** el significado
puntual de los códigos numéricos ZHF/AHT/VUS/UPS/CLC y de los valores de
`ZHG_VALOR_`/`ZHG_VALOR1` (vigencia y procedencia oficial no acreditadas).
En todos esos casos la UI lo declara: «su decodificación oficial no está
disponible» — no se inventan equivalencias.

## 4. Componentes implementados

- `src/components/HelpTip.tsx`: botón (?) accesible (mouse, clic, teclado,
  tacto; `aria-expanded`, cierre con Escape y clic fuera; panel que no se
  corta en móvil).
- `src/components/InterpretationCard.tsx`: bloque de interpretación con
  variante normal y de advertencia.
- `src/lib/interpretation.ts`: generación determinística de explicaciones
  (no es un modelo de IA; solo reglas verificables sobre los datos reales).
- `src/lib/glossary.ts`: datos del glosario.
- `src/pages/Glossary.tsx`: página con búsqueda y categorías; enlace
  «Glosario» en la navegación principal.

## 5. «¿Qué significa esto para este predio?»

Construida con los datos reales del predio consultado:

- **General:** destino económico, área catastral, presencia de construcción
  («por eso ningún valor total puede leerse como valor exclusivo del
  suelo») y disponibilidad de coordenadas.
- **Referencia ZHG:** monozona → «El terreno se encuentra asociado a la
  zona geoeconómica X, cuyo valor unitario de referencia registrado es de
  aproximadamente $… por hectárea. Este dato describe una referencia
  territorial y no significa que el predio completo tenga ese precio…»;
  multizona → advertencia de que no es adecuado un único valor; cobertura
  no apta → explica por qué no se muestra consolidación.
- **Alertas:** una frase de interpretación por bandera real.
- **Demostración ML:** advertencias prioritarias (participó en el ajuste /
  no es evaluación independiente / no es avalúo) + complemento con los
  valores reales de referencia, estimación y diferencia.

Si las condiciones del predio cambian, la explicación cambia (se verificó
con pruebas unitarias por caso).

## 6. Correcciones obligatorias en Predicción (A/B/C)

- **A. Unidad:** la diferencia se muestra en **COP/ha** (ej. «6.578 COP/ha
  (1,44 %)») usando formato es-CO.
- **B. Estado del dominio:** `in_domain` se traduce a «Los datos del predio
  están dentro de los rangos y categorías admitidos por la demostración
  experimental. Esto no significa precisión garantizada ni validación
  independiente.» El código técnico se conserva en el contrato de la API.
- **C. Orden de advertencias:** destacadas primero (ajuste → no evaluación
  independiente → no avalúo) y el resto en «Ver todas las limitaciones»
  (desplegable), sin duplicaciones.

## 7. Cambios por ruta

- `/predios`: HelpTips en búsqueda y columna de calidad.
- `/predios/:id`: tarjeta de interpretación general, interpretación de
  alertas, HelpTips por sección; la tarjeta ZHG incluye su interpretación.
- `/mapa`: nota y ayuda sobre puntos/colores en el panel de visualización.
- `/exploracion`: ayuda de interpretación en las 4 gráficas (unidades,
  ejes, lectura).
- `/modelos`: ayuda de MAE/RMSE/R² + sección que distingue experimentos
  históricos de Fase 5, artefacto actual, referencia ZHG y predicción
  oficial deshabilitada.
- `/prediccion`: correcciones A/B/C + interpretación del resultado.
- `/glosario` (nueva): búsqueda + categorías.
- Navegación: enlace «Glosario».

## 8. Revisión heurística (sin usuarios reales)

Ejercicio simulado con tres perfiles (ciudadano, estudiante, persona sin
conocimientos de ML) recorriendo cada ruta. Resultado: en todas las rutas
existe ahora una explicación de qué se ve, unidades legibles, distinción
dato/estimación y limitaciones visibles; los tres perfiles pueden
interpretar la ficha y la demostración sin ayuda de un ingeniero.
**No se realizaron entrevistas ni pruebas con usuarios humanos** (se
documenta como revisión heurística).

## 9. Pruebas ejecutadas

- vitest: **28/28** (9 nuevas: interpretaciones monozona/multizona/
  cobertura/banderas/demo, traducción de dominio, glosario con búsqueda y
  categorías, HelpTip por teclado con aria-expanded y Escape; correcciones
  A/B/C verificadas en el test de la demo).
- pytest: **94/94** (backend intacto). ruff/oxlint limpios; build TS+Vite OK.
- Playwright (escritorio 1440×900 y móvil 390×844, servidores reales):
  glosario con búsqueda, interpretación contextual con dato real, HelpTip
  operable por teclado, **0 errores de consola**. Capturas:
  `docs/capturas/f7e_comprension_{desktop,movil}.png`.

## 10. Limitaciones pendientes

- Significado puntual de códigos territoriales: requiere diccionario
  oficial de las fuentes (pendiente #2).
- Vigencia de la referencia ZHG: no acreditada (se muestra «no disponible»).
- La demostración ML sigue siendo experimental, monozona y sin evaluación
  independiente (Fase 7C).
