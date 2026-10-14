# Diccionario de datos — Yacopí Predictor (v1, Fase 1)

Fecha: 2026-10-14 · Fuente: CSV originales auditados · Origen de conteos:
`scripts/preparar_datos.py` reproducido (diferencias vs referencia: ninguna).

## 1. Fuentes

| Fuente | Filas | Columnas | Rol |
|---|---|---|---|
| `interseccion_terrenos_zhg_r1_yacopi.csv` | 9.447 | 17 | Avalúos, superficies, destino y zonas geoeconómicas (varias filas por predio) |
| `zhf_yacopi.csv` | 7.968 | 28 | Zonas homogéneas físicas, uso, cobertura, puntos y geometrías |

- Llave de unión: `numero_predial` = `CODPRED` (texto, se preservan ceros).
- Granularidad analítica: **1 predio = 1 fila** (7.709 predios únicos de la
  primera fuente; 227 predios adicionales solo-ZHF conservados aparte).
- CRS verificado (Fase 1): `geometria`/`geometria_interseccion` → **SRID 9377**
  (MAGNA-SIRGAS Origen-Nacional); `geom` ZHF → **SRID 3116** (MAGNA-SIRGAS
  Bogotá). Mapas exportados en EPSG:4326.

## 2. Roles permitidos de cada columna

Cada columna se clasifica como: **id** (identificador), **X** (posible
predictora), **referencia económica** (excluida de X por riesgo de fuga),
**resultado**, **auditoría** o **metadato**. La lista explícita de X vive en
`ml/config/features.yaml` (allowlist) y las excluidas en su sección `blocked`.

## 3. Tabla consolidada (`03_predios_consolidados.csv`, 7.709 filas, 49 columnas)

### 3.1 Identificadores y metadatos (rol id/metadato — NUNCA predictores)

| Columna | Tipo | Descripción | Uso |
|---|---|---|---|
| `numero_predial` | texto | Identificador predial oficial (llave de cruce) | join/búsqueda interna |
| `numero_predial_anterior` | texto | Identificador anterior | trazabilidad |
| `departamento` | texto | Código departamento (25) | metadato |
| `municipio` | texto | Código municipio (885) | metadato |
| `codigo_orip` | texto | Código ORIP (normalizado sin `.0`) | id |
| `matricula_inmobiliaria` | texto | Matrícula | id |
| `codigo_lote` | texto | Código de lote | id |

### 3.2 Numéricas (rol X candidatas o referencia)

| Columna | Tipo | Unidad | Nulos | Rol | Notas |
|---|---|---|---|---|---|
| `area_terreno_catastral_m2` | float | m² | 0 | X (auditar efecto mecánico) | Superficie catastral; 0 no positivas |
| `area_zhf_m2` | float | m² | 15 (solo-ZHF intersecciones) | X | `AREA_TERRE`; definición por validar; difiere >5 % de la catastral en 4.924 predios |
| `area_construida_m2` | float | m² | 0 | X (cautela) | 3.033 predios con valor > 0 |
| `tr_latitud` / `tr_longitud` | float | grados | 15 cada una | X (espacial) | 7.694 válidas, 0 fuera de rango Colombia |
| `tr_este` / `tr_norte` | float | proyectado | 15 cada una | bloqueada | Coordenadas proyectadas; no al modelo |
| `suma_area_intersecciones_m2` | float | m² | 0 | bloqueada | Derivada de intersecciones |
| `razon_area_intersecciones_catastral` | float | adimensional | 0 | bloqueada | Derivada de área |
| `razon_area_zhf_catastral` | float | adimensional | 15 | bloqueada | Derivada de área |
| `razon_area_geo_zhg_zhf` | float | adimensional | 15 | bloqueada | Derivada de área |

### 3.3 Categóricas (rol X candidatas)

| Columna | N categorías | Nulos | Notas |
|---|---|---|---|
| `destino_economico` | 10 | 0 | Agropecuario 6.746; Religioso 627; Habitacional 225; Institucional 88; Comercial 10; Educativo 7; Minería hidrocarburos 2; Recreacional 2; Lote urbanizado no construido 1; Cultural 1 |
| `zhf_codigo` | 16 | 15 | Top: 14 (1.858), 08 (1.609), 05 (1.080), 13 (835), 04 (806) |
| `zhf_dispon` | 4 | 15 | 4 (4.541), 3 (3.112), 2 (41) |
| `zhf_influe` | 4 | 15 | 5 (4.656), 3 (2.049), 8 (989) |
| `zhf_uso_ac` | 3 | 15 | 16 (7.474), 12 (220) |
| `aht_vpoten` | 16 | 40 | Top: 23 (2.494), 30 (2.028), 38 (965), 17 (951), 44 (704) |
| `fa_element` | 2 | 471 | "Frontera agrícola nacional" (7.238); resto vacío |
| `vus_vocaci` | 9 | 18 | FPP (3.996), ASPp (3.165), CPSm (348), CA (72), CTIc (46)… |
| `ups` | 4 | 19 | Desarrollo agropecuario sin restricciones (4.838); Protección recursos naturales (1.663); Desarrollo forestal (1.189) |
| `clc_nivel1` | 7 | 18 | Territorios Agrícolas (5.757), Bosques y Áreas Seminaturales (1.262)…; `N/A` se conserva como categoría |
| `clc_nivel2` | 13 | 18 | Pastos (5.130), Bosques (641)… |
| `clc_nivel3` | 30 | 18 | Pastos limpios (4.339)… |
| `clc_nivel4` | 28 | 18 | Mayoría `N/A` (6.100) |
| `clc_nivel5` | 11 | 18 | Mayoría `N/A` (7.430) |
| `clc_nivel6` | 4 | 18 | Mayoría `N/A` (7.510) |

Los nulos en columnas ZHF/CLC se concentran en los 15 predios sin
coincidencia ZHF; `fa_element` (471) y `aht_vpoten` (40) tienen vacíos
adicionales propios de la fuente. `N/A` es categoría original, no nulo.

### 3.4 Referencias económicas (rol referencia — EXCLUIDAS de X)

| Columna | Unidad | Notas |
|---|---|---|
| `valor_avaluo_total_cop` | COP | Avalúo total aparente; **no validado** como suelo exclusivo (3.033 predios con construcción) |
| `referencia_avaluo_total_por_ha_cop` | COP/ha | Avalúo total / área catastral × 10.000; solo referencia |
| `valor_hectarea_agropecuario` | COP/ha | Precio de zona preasignado (fuga) |
| `ZHG_VALOR_`, `ZHG_VALOR1` | COP/ha | Precios zonales geoeconómicos (fuga) |
| `referencia_zhg_valor_predominante_cop_ha`, `referencia_zhg_valor_ponderado_cop_ha`, `referencia_zhg_valor_zhf_cop_ha`, `referencia_zhg_valor1_zhf_cop_ha` | COP/ha | Derivadas de precios zonales (fuga) |
| `zhg_codigo_predominante`, `zhg_codigo_zhf`, `zhg_porcentaje_predominante`, `zhg_subzona` | — | Códigos/contexto geoeconómico: evaluación estratificada, no X |

### 3.5 Resultados de auditoría

| Columna | Rol | Significado |
|---|---|---|
| `coincide_zhf` | auditoría | 1 si el predio está en ambas fuentes (7.694 sí, 15 no) |
| `cantidad_intersecciones` / `cantidad_zonas_zhg` | auditoría | 1.601 predios con varias intersecciones |
| `registros_zhf_mismo_predio` / `id_zhf_primera_fila` | auditoría | Control de duplicados ZHF (42 predios afectados) |
| `suma_porcentaje_intersecciones` | auditoría | Suma 100 % en todos los predios (0 anomalías) |

### 3.6 Geometrías (no entran al modelo)

`geometria`, `geometria_interseccion` (EWKB SRID 9377) y `geom` (EWKB SRID
3116) se procesan offline para mapas; nunca se pasan al estimador.

## 4. Fuente ZHF — columnas restantes

| Columna | Tipo | Uso |
|---|---|---|
| `id` | numérico | fila de origen |
| `AREA_TERRE` | float, m² | ver `area_zhf_m2` |
| `SINAP_NOMB`, `SINAP_CATE` | texto | áreas SINAP (no usadas aún; evaluar) |

## 5. Esquema SQLite (`data/parcels.db`, no versionado)

| Tabla | Filas | Contenido |
|---|---|---|
| `parcels` | 7.709 | predios: `public_id` (opaco, PK), `parcel_source_id` (privado), áreas, destino, lat/lon, subzona, alertas |
| `parcel_features` | 7.709 | 14 categóricas ZHF/UPS/CLC |
| `parcel_value_references` | 46.224 | 6 tipos de referencia económica por predio (`es_etiqueta_validada=0`) |
| `quality_flags` | 15.489 | banderas activas (11 códigos); 6.492 predios con ≥1 alerta |
| `model_targets` | 0 | etiquetas validadas (vacía; `label_status=pending_verification`) |
| `zhf_only_parcels` | 227 | predios solo-ZHF preservados |
| `dataset_meta` | 9 | versión, conteos, estado de etiqueta |

`public_id` = `p_` + SHA-256(`numero_predial`)[:16] (determinista y opaco).

## 6. Banderas de calidad (conteos reales)

| Código | Predios |
|---|---:|
| `suma_area_intersecciones_difiere_mas_5pct_area_catastral` | 4.924 |
| `area_zhf_difiere_mas_5pct_area_catastral` | 4.924 |
| `contiene_construccion` | 3.033 |
| `multiples_intersecciones_zhg` | 1.601 |
| `zona_zhg_zhf_diferente_de_zhg_dominante` | 843 |
| `area_geometrica_zhg_difiere_mas_5pct_zhf` | 106 |
| `zhf_codpred_repetido` | 42 |
| `sin_coincidencia_zhf` | 15 |
| `interseccion_filas_exactamente_duplicadas` | 1 |
| `porcentajes_zhg_no_suman_100` | 0 |
| `area_catastral_no_positiva` | 0 |

Ninguna bandera elimina registros; se muestran como alertas (guía §6.3).

## 7. Estado de la variable objetivo

`valor_terreno_cop_ha` (COP/ha) **pendiente de validación**: los CSV no traen
un valor exclusivo de terreno por predio (con método, fecha y superficie).
Hasta validarlo: `model_targets` vacía, `POST /predictions` → 503 y
experimentos Ruta B segregados con el proxy `avaluo_total/ha`.
