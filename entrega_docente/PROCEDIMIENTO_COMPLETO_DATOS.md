# Procedimiento completo sobre los datos

Trazabilidad de cada transformación aplicada desde los CSV originales hasta
los datasets de modelado. El código real vive en `scripts/preparar_datos.py`
(normalización, histórico, conservado byte-idéntico), `scripts/build_db.py`
(consolidación y SQLite), `scripts/audit_data.py` (auditoría) y
`scripts/verify_inputs.py` (verificación de entradas).

## 2.1 Fuentes

| CSV | Filas | Columnas | Rol |
|---|---|---|---|
| `data/raw/interseccion_terrenos_zhg_r1_yacopi.csv` | 9.447 | 17 | Intersecciones geoeconómicas ZHG por predio; trae `valor_avaluo`, `area_terreno_m2`, `area_construida_m2`, `valor_hectarea_agropecuario`, geometrías |
| `data/raw/zhf_yacopi.csv` | 7.968 | 28 | Zonas homogéneas físicas: CODPRED, AREA_TERRE, coordenadas, ZHF_*, CLC_*, ZHG_* |

- Hashes SHA-256 y procedencia en `data/raw/data_manifest.json`
  (generado 2026-10-14). Fecha y procedencia catastral de los valores: **no
  documentadas en los archivos** (pendiente con el profesor).
- SRID estimado en auditoría: intersecciones/geometría predial 9.377
  (MAGNA-SIRGAS / CTM12), ZHF 3.116 filas con el mismo SRID estimado.
- Identificador de predio: `numero_predial` (30 dígitos) en intersecciones;
  `CODPRED` en ZHF.

## 2.2 Limpieza y consolidación (tabla de trazabilidad)

| # | Operación | Qué se hizo | Por qué | Código | Antes | Después | Consecuencia estadística |
|---|---|---|---|---|---|---|---|
| 1 | Lectura cruda | Carga de ambos CSV | — | `scripts/preparar_datos.py` | — | 9.447 + 7.968 | Línea base |
| 2 | Normalización de nombres | Columnas a snake_case, `TR_LONGITU`→`tr_longitud` | Nombres consistentes | `preparar_datos.py` | 17/28 cols | 17/28 cols | Sin pérdida |
| 3 | Conversión numérica | `valor_avaluo`, áreas, coordenadas → float | Evitar strings numéricos | `preparar_datos.py` | 9.447 | 9.447 | 0 nulos en avalúo/áreas |
| 4 | Normalización de códigos | Zonas ZHG a 2 dígitos (`02`…`11`) | Unificar formato inter-fuente | `preparar_datos.py` | — | — | Permite el join zonal |
| 5 | Deduplicación exacta | 3 filas idénticas de intersecciones eliminadas; 47 filas sobrantes de ZHF con atributos idénticos descartadas | Filas repetidas inflarían conteos | `audit_data.py` / consolidación | 9.447 / 7.968 | 9.444 / 7.921 únicos | Evita pseudorréplicas |
| 6 | Unión por predio | `numero_predial` ↔ `CODPRED` | Enriquecer con ZHF/CLC | `build_db.py` | — | 7.694 predios con coincidencia; 15 solo intersección; 227 solo ZHF | 15 predios sin ZHF (imputados `SIN_DATO` en ML) |
| 7 | Consolidación 1 fila/predio | `03_predios_consolidados.csv` | Unidad de análisis predio | `build_db.py` | 9.444 | **7.709** | Evita que predios multizona cuenten varias veces |
| 8 | Intersecciones múltiples | 1.601 predios con varias zonas ZHG | Reconoce predios multizona | `audit_data.py` | — | 1.601 | El valor dominante/ponderado maneja la mezcla |
| 9 | Zona dominante y ponderado | `zhg_codigo_predominante`, valor dominante y `referencia_zhg_valor_ponderado_cop_ha` | Asignar la referencia zonal a cada predio | `build_db.py` | — | 7.709 | Crea el objetivo ZHG (11 valores) y su variante ponderada (651) |
| 10 | Áreas comparadas | `razon_area_zhf_catastral`, `razon_area_intersecciones_catastral`, área geométrica vs catastral | Detectar inconsistencias | `audit_data.py` | — | 4.924 predios con |ZHF−catastral|>5 %; 106 con geométrica−catastral>5 % | Señala ruido en el área como feature y denominador |
| 11 | Banderas de calidad | `05_banderas_calidad.csv` (multi-intersección, áreas, construcción, coincidencia ZHF) | Documentar en vez de borrar | `audit_data.py` | 7.709 | 7.709 (con banderas) | Nada se elimina silenciosamente |
| 12 | Identificador público | `public_id = "p_" + sha256(numero_predial)[:16]` | No exponer identificadores catastrales | `build_db.py` | — | 7.709 | Privacidad; no afecta métricas |
| 13 | Datasets ML | Selección de features (allowlist) y etiquetas por contrato | Control de fuga y trazabilidad | `ml/config/*.yaml`, `yacopi_ml/{labels,dataset,zhg,valor}` | 7.709 | cohorte proxy 7.694; ZHG 7.709; valor A 4.676 / B 986 | Define qué se predice y con qué |

### Exclusiones documentadas

- Proxy (Fase 2): cohorte 7.694/7.694, **0 excluidos** (proxy calculable en
  todos; se usó todo el consolidado).
- VALOR_TERRENO_Ha: excluidos 2.470 registros con construcción > 32 m² y los
  de construcción > 0 y ≤ 32 se separan en el escenario B. No se excluyó
  automáticamente ningún valor extremo; el análisis de sensibilidad se reporta
  por separado (ver `AUDITORIA_R2_ATLAS_VIVO.md`).
- ZHG (Fase 5): 4.924 predios marcados "no apta" (multi-zona/sin valor
  unívoco) quedaron fuera del objetivo dominante por definición de cobertura;
  el ponderado usa 2.785.

## 2.3 Calidad de datos (hallazgos)

| Aspecto | Hallazgo |
|---|---|
| Área ZHF vs catastral | Mediana ZHF = 103,2 % del terreno; 64,4 % de filas con ZHF > terreno (solapamiento de polígonos); 4.924 predios difieren >5 % |
| Predios multizona | 1.601 con varias intersecciones ZHG; 843 donde la zona ZHF difiere de la dominante |
| Construcción | 3.033 predios con `area_construida_m2 > 0`; máxima 2.016 m² |
| Coordenadas | 7.694 válidas; 15 faltantes; 0 fuera de rango |
| Valores económicos | avalúo 4.000 – 878.808.000 COP (mediana 2.818.000); sin nulos/negativos |
| Áreas mínimas | 46 filas con área ≤ 100 m² → cocientes hasta 1.354 M COP/ha (extremas) |
| Fechas | No documentadas en los CSV |
| Fuga potencial | Variables zonales (código/valor ZHG) se excluyen de X; área en denominador del proxy también es feature (relación mecánica parcial, señalada en `/modelos`) |
