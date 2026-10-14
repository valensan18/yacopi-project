# DESIGN SYSTEM — ATLAS VIVO · Observatorio Territorial de Yacopí

Dirección aprobada (Fase 4): **Propuesta A (ATLAS VIVO, cartografía
cinematográfica) con acentos de B** (densidad tabular e instrumentación en
Pantalla Predios) **y de C** (ritmo editorial y notas al margen en
Metodología). Este documento es la fuente de verdad visual del frontend.

> Nota de origen: las skills de diseño referenciadas en la solicitud
> (`ui-ux-pro-max`, `design`, `design-system`, `ui-styling`, `brand`) no
> existen en `.opencode/skills/` de este equipo (solo `effect` y
> `humanizer`). Este sistema se fundamenta en los mismos principios que esas
> skills representan, documentados aquí con trazabilidad.

---

## 1. Identidad y tono

- Voz: español (Colombia), académica y sobria, sin tecnicismo innecesario.
- Tratamiento: observatorio, no dashboard ni brochure.
- Regla de honestidad: todo número mostrado proviene de la API real;
  cualquier elemento ilustrativo se rotula explícitamente (p. ej. relieve
  3D ilustrativo; puntos = coordenadas referenciales reales).
- El modelo ML es experimental y predice un proxy (avalúo catastral total
  por ha). Nunca presentar como valor de suelo ni avalúo oficial.

## 2. Paleta

| Token | Hex | Uso |
|---|---|---|
| `--ink` | `#0B1613` | fondo principal (verde-pizarra profundo) |
| `--ink-2` | `#101F1A` | superficies elevadas |
| `--pine` | `#1E4D3B` | verde mineral primario |
| `--moss` | `#2F6B52` | verde secundario, estados |
| `--copper` | `#C97B4A` | acento mineral (CTA, énfasis, hitos) |
| `--amber-data` | `#E8B44F` | acento de datos (estilo GEO LAB) |
| `--chalk` | `#F4EFE6` | texto principal sobre oscuro |
| `--stone` | `#8FA39A` | texto secundario |
| `--paper` | `#F6F1E7` | fondo modo editorial (Metodología) |
| `--sepia` | `#2A2118` | texto sobre papel |
| `--grid` | `#1C2B25` | líneas de retícula cartográfica |

Accesibilidad: pares verificados WCAG AA — `chalk/ink` (≈12,6:1),
`stone/ink` (≈6,3:1), `sepia/paper` (≈12:1), `copper/ink` (≈5,9:1, uso
solo en gráficos/acentos grandes, no en texto pequeño).

## 3. Tipografía

| Rol | Familia | Fuente de carga |
|---|---|---|
| Display / titulares | Fraunces (variable, peso 400–700, optical size) | `@fontsource-variable/fraunces` |
| Texto / interfaz | Public Sans (variable) | `@fontsource-variable/public-sans` |
| Datos / códigos / unidades | JetBrains Mono (variable) | `@fontsource-variable/jetbrains-mono` |

Escala fluida (móvil → escritorio, `clamp`):

- `--fs-display`: `clamp(2.4rem, 1.2rem + 6vw, 5.5rem)`
- `--fs-h2`: `clamp(1.8rem, 1.2rem + 2.4vw, 3rem)`
- `--fs-h3`: `clamp(1.3rem, 1.05rem + 1vw, 1.8rem)`
- `--fs-body`: `1rem/1.0625rem`
- `--fs-data`: `clamp(1.4rem, 1.1rem + 1.4vw, 2.6rem)` (cifras grandes)
- `--fs-mono`: `0.8125rem` (coordenadas, códigos)

Números: `Intl.NumberFormat('es-CO')`; unidades siempre visibles (COP/ha,
ha, m²); los rangos de porcentaje se explican en tooltip/nota.

## 4. Espaciado, radios, sombras y retícula

- Espaciado base 8 px: `--s1..--s8` (8→96 px). Secciones con `--s8` de
  respiro vertical en escritorio, `--s6` en móvil.
- Radios: `--r-sm 6px` (botones/inputs), `--r-md 12px` (tarjetas),
  `--r-lg 20px` (paneles grandes).
- Sombras: solo para elevación funcional (`--shadow-card`, `--shadow-nav`);
  evitar sombras duras sobre fondos oscuros.
- Retícula cartográfica: líneas finas `--grid` a 6 % de opacidad como
  textura de fondo (hero y secciones de datos). 12 columnas en escritorio,
  4 en móvil.

## 5. Componentes base (nomenclatura)

`AppShell` (nav + banner de estado + footer), `SystemStatusBanner`,
`PageTitle`, `KpiCard`, `ParcelTable` (acento B: densidad, mono, zebra
sutil, sticky header), `ParcelFilters`, `ParcelDetailCard`,
`ModelStatusNotice`, `PredictionForm`, `PredictionResult`,
`ModelComparisonTable`, `MapExplorer` + `MapLegend`, `EmptyState`,
`ErrorState`, `LoadingSkeleton`, `DataQualityBadge`, `Disclaimer`,
`SectionNote` (acento C: notas al margen en Metodología).

## 6. Movimiento (jerarquía única de motores)

| Motor | Responsabilidad exclusiva | Reglas |
|---|---|---|
| Lenis | scroll inercial suave | desactivado con `prefers-reduced-motion`; `data-lenis-prevent` en contenedores de Leaflet y en overlays scrollables |
| GSAP + ScrollTrigger | animaciones de scroll (pin, parallax, reveals, contadores, cámara 3D) | sincronizado con Lenis (`lenis.on('scroll', ScrollTrigger.update)`); todas las animaciones con `matchMedia('(prefers-reduced-motion: reduce)')` → saltan al estado final |
| Motion | microinteracciones declarativas (hover de tarjetas, AnimatePresence de rutas, entradas de menú móvil) | no duplica responsabilidades de GSAP |
| R3F + Three + Drei | única escena 3D (héroe) | `React.lazy`, `dpr=[1,1.75]`, sin postprocesado, auto-rotación solo si no hay reduced-motion |

Duración/curvas: reveals 0,7 s `power3.out`; microinteracciones 0,2–0,3 s
`easeOut`; parallax ligero (8–14 % de desplazamiento); nunca animar
`width/height/top/left` de contenedores grandes (solo `transform/opacity`).

## 7. Escena 3D (narrativa, no decorativa)

- Composición: relieve ilustrativo (malla procedural, sin datos de
  elevación) + nube de 7.694 puntos = predios reales (lat/lon desde
  `GET /maps/points`, color por `destino_economico`).
- Narrativa: "el relieve del territorio es el relieve de su uso" → la
  cámara viaja de vista general a detalle con el scroll (GSAP ↔ ref 3D).
- Rótulo visible en la escena: "Relieve ilustrativo · Puntos: coordenadas
  referenciales de predios reales".
- Fallback sin WebGL: degradado + textura de puntos 2D + mismo titular
  (componente `Scene3DFallback`), detectado con prueba de contexto WebGL.
- Móvil: densidad de puntos reducida (muestreo), sin niebla dinámica,
  cámara estática si reduced-motion.

## 8. Cartografía y datos (Leaflet + Plotly)

- Leaflet: tema oscuro propio (tiles CartoDB Dark Matter con atribución),
  puntos por capa de destino, leyenda `MapLegend`, popup con `public_id`
  opaco. Lenis no interfiere (prevent). Plotly: tema oscuro con tokens,
  formato es-CO, leyendas y títulos; lazy-load por página.

## 9. Responsive y accesibilidad

- Breakpoints: móvil <640, tablet 640–1024, escritorio ≥1024.
- Foco visible (`:focus-visible` con `--copper`), labels vinculados,
  contraste AA, `aria-live` para estados de carga/error, alt descriptivo
  en gráficas (Plotly descarga accesible), tablas con `<caption>`.
- `prefers-reduced-motion`: desactiva Lenis, GSAP scroll y auto-rotación
  3D; la información nunca depende de la animación.
- Íconos: SVG inline (sin librería extra), stroke 1,5, 20 px base.

## 10. Medición de rendimiento (obligatoria, no declarativa)

- FPS real: contador rAF en devtools overlay (solo desarrollo) sobre el
  hero con la escena 3D activa; registrar p50/p95 en el informe.
- Bundle: `vite build` con reporte de tamaño por chunk; umbral de revisión:
  chunk 3D lazy ≥ 350 kB gzip → optimizar (no prometer 60 FPS sin medir).
- Memoria GPU: reutilizar geometría de puntos (un solo `BufferGeometry`
  con `vertexColors`), sin instancias redundantes.
