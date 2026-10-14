#!/usr/bin/env python3
"""Auditoría y preparación conservadora de los CSV de Yacopí.

Uso:
  python preparar_datos.py interseccion_terrenos_zhg_r1_yacopi.csv 'zhf_yacopi (1).csv' --output carpeta

No elimina observaciones ni fabrica etiquetas de precio de terreno.
Consolida intersecciones por numero_predial para evitar duplicaciones.
"""
import argparse
import collections
import csv
import json
import math
from pathlib import Path
from statistics import median


def read_csv(path):
    with Path(path).open('r', encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames
        rows = [{k:(v.strip() if v is not None else '') for k,v in row.items()} for row in reader]
    return headers, rows


def write_csv(path, keys, rows):
    with Path(path).open('w', encoding='utf-8', newline='') as fh:
        w=csv.DictWriter(fh, fieldnames=keys, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def fnumber(value):
    if value in ('', 'NA', 'N/A', None):
        return None
    try:
        ans=float(value)
    except (ValueError, TypeError):
        return None
    return ans if math.isfinite(ans) else None


def numstr(v, places=5):
    return '' if v is None else f'{v:.{places}f}'.rstrip('0').rstrip('.')


def norm_code(value):
    return str(value).zfill(2) if value != '' else ''


def srid_of_hex(wkb):
    # Extended WKB starts with byte order (1), geometry type including SRID bit and SRID.
    try:
        if len(wkb)>=18:
            prefix = bytes.fromhex(wkb[:18])
            order = 'little' if prefix[0] == 1 else 'big'
            gtype = int.from_bytes(prefix[1:5],order)
            if gtype & 0x20000000:
                return int.from_bytes(prefix[5:9],order)
    except Exception:
        pass
    return None


def main(source_inter, source_zhf, output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    cols_i, irows = read_csv(source_inter)
    cols_z, zrows = read_csv(source_zhf)
    # Normalize categorical zone codes. Preserve raw geometry in both copies.
    norm_i=[]
    for source_row,x in enumerate(irows,2):
        r=x.copy()
        r['codigo_zona_geoeconomica']=norm_code(r['codigo_zona_geoeconomica'])
        if r['codigo_orip'].endswith('.0') and r['codigo_orip'][:-2].isdigit():
            r['codigo_orip']=r['codigo_orip'][:-2]
        r['fila_origen']=str(source_row)
        norm_i.append(r)
    norm_z=[]
    for source_row,x in enumerate(zrows,2):
        r=x.copy()
        r['ZHG_CODIGO']=norm_code(r['ZHG_CODIGO'])
        r['fila_origen']=str(source_row)
        norm_z.append(r)
    write_csv(out/'01_intersecciones_normalizadas.csv',['fila_origen']+cols_i,norm_i)
    write_csv(out/'02_zhf_normalizadas.csv',['fila_origen']+cols_z,norm_z)

    groups_i=collections.defaultdict(list)
    groups_z=collections.defaultdict(list)
    for x in norm_i:groups_i[x['numero_predial']].append(x)
    for x in norm_z:groups_z[x['CODPRED']].append(x)

    full_duplicates_i=sum(c-1 for c in collections.Counter(tuple(x[c] for c in cols_i) for x in norm_i).values() if c>1)
    duplicate_z_keys=sum(len(v)-1 for v in groups_z.values())
    differing_z_duplicates=[]
    for code,records in groups_z.items():
        if len(records)>1:
            attributes=[c for c in cols_z if c not in ('id','geom')]
            if any(len(set(r[c] for r in records))>1 for c in attributes):
                differing_z_duplicates.append(code)

    master=[]
    issues=[]
    mismatched_geo=0
    areas_diff=0
    geo_area_consistent_1pct=0
    geo_area_discrepant_5pct=0
    nonpositive_area=0
    duplicate_affected=[]
    for pred, parts in groups_i.items():
        first=parts[0]
        area=fnumber(first['area_terreno_m2'])
        avaluo=fnumber(first['valor_avaluo'])
        built=fnumber(first['area_construida_m2'])
        shares_by_zone=collections.defaultdict(float)
        prices_by_zone={}
        for part in parts:
            code=part['codigo_zona_geoeconomica']
            shares_by_zone[code]+=fnumber(part['porcentaje_en_zonageo_respecto_suma']) or 0.0
            prices_by_zone[code]=fnumber(part['valor_hectarea_agropecuario'])
        dominant=max(shares_by_zone, key=shares_by_zone.get)
        weighted=sum(s * (prices_by_zone[code] or 0) for code,s in shares_by_zone.items())/100
        sharesum=sum(shares_by_zone.values())
        area_inter=sum(fnumber(p['area_en_zonageoeconomica_m2']) or 0 for p in parts)
        orig_dup=(len(parts)!=len({tuple(part[c] for c in cols_i) for part in parts}))
        if orig_dup:duplicate_affected.append(pred)
        zr=groups_z.get(pred,[])
        # The 47 excess rows in ZHF have identical non-geometry attributes for a CODPRED.
        # Use first only for parcel-level attributes, preserving every row in normalized source.
        z=zr[0] if zr else None
        zarea=fnumber(z['AREA_TERRE']) if z else None
        area_ratio=(zarea/area) if zarea is not None and area is not None and area>0 else None
        area_join_flag=bool(area_ratio is not None and abs(area_ratio-1)>0.05)
        geo_area_ratio=(area_inter/zarea) if zarea is not None and zarea>0 else None
        geo_area_flag=bool(geo_area_ratio is not None and abs(geo_area_ratio-1)>0.05)
        if geo_area_ratio is not None and abs(geo_area_ratio-1)<=0.01:geo_area_consistent_1pct+=1
        if geo_area_flag:geo_area_discrepant_5pct+=1
        if area_join_flag:areas_diff+=1
        zone_mismatch=bool(z and dominant!=z['ZHG_CODIGO'])
        if zone_mismatch:mismatched_geo+=1
        if not area or area<=0:nonpositive_area+=1
        avaluo_per_ha=(avaluo/area*10000) if avaluo is not None and area and area>0 else None
        inter_ratio=(area_inter/area) if area and area>0 else None
        flag_inter_ratio=bool(inter_ratio is not None and abs(inter_ratio-1)>0.05)
        issue={
            'numero_predial':pred,
            'sin_coincidencia_zhf':int(z is None),
            'multiples_intersecciones_zhg':int(len(parts)>1),
            'interseccion_filas_exactamente_duplicadas':int(orig_dup),
            'porcentajes_zhg_no_suman_100':int(abs(sharesum-100)>0.1),
            'suma_area_intersecciones_difiere_mas_5pct_area_catastral':int(flag_inter_ratio),
            'area_zhf_difiere_mas_5pct_area_catastral':int(area_join_flag),
            'area_geometrica_zhg_difiere_mas_5pct_zhf':int(geo_area_flag),
            'zona_zhg_zhf_diferente_de_zhg_dominante':int(zone_mismatch),
            'zhf_codpred_repetido':int(len(zr)>1),
            'area_catastral_no_positiva':int(not area or area<=0),
            'contiene_construccion':int(bool(built and built>0))
        }
        issues.append(issue)
        result={
            'numero_predial':pred,
            'numero_predial_anterior':first['numero_predial_anterior'],
            'departamento':first['departamento'],
            'municipio':first['municipio'],
            'codigo_orip':first['codigo_orip'],
            'matricula_inmobiliaria':first['matricula_inmobiliaria'],
            'codigo_lote':first['codigo_lote'],
            'destino_economico':first['destino_economico'],
            'valor_avaluo_total_cop':numstr(avaluo,2),
            'area_terreno_catastral_m2':numstr(area,4),
            'area_construida_m2':numstr(built,3),
            'referencia_avaluo_total_por_ha_cop':numstr(avaluo_per_ha,2),
            'cantidad_intersecciones':len(parts),
            'cantidad_zonas_zhg':len(shares_by_zone),
            'zhg_codigo_predominante':dominant,
            'zhg_porcentaje_predominante':numstr(shares_by_zone[dominant],6),
            'referencia_zhg_valor_predominante_cop_ha':numstr(prices_by_zone[dominant],2),
            'referencia_zhg_valor_ponderado_cop_ha':numstr(weighted,2),
            'suma_porcentaje_intersecciones':numstr(sharesum,6),
            'suma_area_intersecciones_m2':numstr(area_inter,4),
            'razon_area_intersecciones_catastral':numstr(inter_ratio,6),
            'coincide_zhf':int(z is not None),
            'registros_zhf_mismo_predio':len(zr),
            'id_zhf_primera_fila':z['id'] if z else '',
            'area_zhf_m2':z['AREA_TERRE'] if z else '',
            'razon_area_zhf_catastral':numstr(area_ratio,6),
            'razon_area_geo_zhg_zhf':numstr(geo_area_ratio,6),
            'tr_latitud':z['TR_LATITUD'] if z else '',
            'tr_longitud':z['TR_LONGITU'] if z else '',
            'tr_este':z['TR_ESTE'] if z else '',
            'tr_norte':z['TR_NORTE'] if z else '',
            'zhf_codigo':z['ZHF_CODIGO'] if z else '',
            'zhf_dispon':z['ZHF_DISPON'] if z else '',
            'zhf_influe':z['ZHF_INFLUE'] if z else '',
            'zhf_uso_ac':z['ZHF_USO_AC'] if z else '',
            'aht_vpoten':z['AHT_VPOTEN'] if z else '',
            'fa_element':z['FA_ELEMENT'] if z else '',
            'vus_vocaci':z['VUS_VOCACI'] if z else '',
            'ups':z['UPS'] if z else '',
            'zhg_codigo_zhf':z['ZHG_CODIGO'] if z else '',
            'referencia_zhg_valor_zhf_cop_ha':z['ZHG_VALOR_'] if z else '',
            'referencia_zhg_valor1_zhf_cop_ha':z['ZHG_VALOR1'] if z else '',
            'zhg_subzona':z['ZHG_SUBZON'] if z else '',
        }
        for k in ['CLC_NIVEL1','CLC_NIVEL2','CLC_NIVEL3','CLC_NIVEL4','CLC_NIVEL5','CLC_NIVEL6']:
            result[k.lower()]=z[k] if z else ''
        master.append(result)

    # All 227 ZHF-only parcel identifiers preserved in a separate diagnostics file.
    extra_zhf=[zr[0] for pred,zr in groups_z.items() if pred not in groups_i]
    write_csv(out/'03_predios_consolidados.csv',list(master[0]),master)
    write_csv(out/'04_predios_solo_zhf.csv',cols_z,extra_zhf)
    write_csv(out/'05_banderas_calidad.csv',list(issues[0]),issues)

    # Categorical summary and derived-value audit (the latter is NOT a verified terrain label).
    destinations=collections.Counter(x['destino_economico'] for x in master)
    zhf_subzones=collections.Counter(x['zhg_subzona'] for x in master if x['zhg_subzona'])
    summary={
        'rows_intersections':len(irows), 'rows_zhf':len(zrows),
        'unique_parcels_intersections':len(groups_i), 'unique_parcels_zhf':len(groups_z),
        'parcel_matches':len(groups_i.keys() & groups_z.keys()),
        'parcels_only_intersections':len(groups_i.keys()-groups_z.keys()),
        'parcels_only_zhf':len(groups_z.keys()-groups_i.keys()),
        'duplicates_intersection_exact_rows':full_duplicates_i,
        'duplicate_zhf_excess_rows':duplicate_z_keys,
        'duplicate_zhf_with_different_attributes':len(differing_z_duplicates),
        'parcels_with_repeated_identical_intersections':len(duplicate_affected),
        'parcels_with_multiple_zone_intersections':sum(x['cantidad_intersecciones']>1 for x in master),
        'parcels_with_zhf_area_difference_above_5pct':areas_diff,
        'parcels_geometric_area_match_within_1pct':geo_area_consistent_1pct,
        'parcels_geometric_area_difference_above_5pct':geo_area_discrepant_5pct,
        'parcels_with_intersection_area_difference_above_5pct':sum(x['suma_area_intersecciones_difiere_mas_5pct_area_catastral'] for x in issues),
        'parcels_zhg_dominant_zone_disagrees_with_zhf':mismatched_geo,
        'parcels_with_construction':sum(x['contiene_construccion'] for x in issues),
        'parcels_percentages_not_100':sum(x['porcentajes_zhg_no_suman_100'] for x in issues),
        'estimated_srid_intersections':srid_of_hex(norm_i[0]['geometria_interseccion']),
        'estimated_srid_geometry_parcel':srid_of_hex(norm_i[0]['geometria']),
        'estimated_srid_zhf_geom':srid_of_hex(norm_z[0]['geom']),
        'destinations':dict(destinations.most_common()),
        'zhg_subzone_counts_matched':dict(zhf_subzones.most_common()),
        'label_availability':'NO se ha confirmado que valor_avaluo_total_cop sea un avalúo exclusivo del terreno',
    }
    (out/'06_resumen_diagnostico.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')

    with (out/'07_informe_calidad.md').open('w',encoding='utf-8') as fh:
        fh.write(f'''# Auditoría inicial de datos — valoración rural en Yacopí

## Estado

Diagnóstico realizado exclusivamente con los dos CSV suministrados. No se han modificado los archivos originales ni eliminado observaciones de sus copias normalizadas.

| Indicador | Resultado |
|---|---:|
| Filas de intersecciones geoeconómicas | {len(irows):,} |
| Filas de características ZHF | {len(zrows):,} |
| Predios únicos en intersecciones | {len(groups_i):,} |
| Predios únicos en ZHF | {len(groups_z):,} |
| Predios coincidentes por ID | {summary['parcel_matches']:,} |
| Predios solo en intersecciones | {summary['parcels_only_intersections']:,} |
| Predios solo en ZHF | {summary['parcels_only_zhf']:,} |
| Filas idénticas sobrantes en intersecciones | {full_duplicates_i:,} |
| Filas excedentes en ZHF por CODPRED | {duplicate_z_keys:,} |
| Predios con varias intersecciones | {summary['parcels_with_multiple_zone_intersections']:,} |
| Predios con construcción positiva | {summary['parcels_with_construction']:,} |
| Discrepancia de áreas ZHF/catastral superior a 5 % | {areas_diff:,} |
| Intersecciones geográficas y área ZHF coinciden dentro del 1 % | {geo_area_consistent_1pct:,} |
| Discrepancia de área entre dos fuentes geográficas superior a 5 % | {geo_area_discrepant_5pct:,} |
| Discrepancia de áreas de intersección/catastral superior a 5 % | {summary['parcels_with_intersection_area_difference_above_5pct']:,} |
| Zona dominante distinta de la ZHG declarada en ZHF | {mismatched_geo:,} |

Los porcentajes de participación de zonas geoeconómicas **suman 100 % por predio** en el CSV de intersecciones, pero la suma de áreas de la intersección no coincide en muchos casos con `area_terreno_m2`. Las diferencias de área son **alertas para verificar el significado/fecha de cada campo**, no prueba automática de error de captura. En cambio, las áreas de las dos fuentes geométricas concuerdan en {geo_area_consistent_1pct:,} de {summary['parcel_matches']:,} predios dentro del 1 %, lo que indica consistencia espacial relativa entre ellas, sin probar que el área catastral esté equivocada.

## Puntos críticos para el desarrollo de IA

1. **La variable objetivo sigue pendiente de validación.** `valor_avaluo` representa aparentemente el avalúo catastral total; dividirlo por el área calcula `referencia_avaluo_total_por_ha_cop`, pero eso **no demuestra** que sea valor del terreno sin construcciones. {summary['parcels_with_construction']:,} predios presentan `area_construida_m2 > 0`. No presentaremos ese cociente como etiqueta confirmada para el proyecto.
2. **Evitar fuga de información.** Las columnas `valor_hectarea_agropecuario`, `ZHG_VALOR_`, `ZHG_VALOR1` y las referencias ZHG calculadas contienen valores de zona ya asignados. No deben usarse como entradas para predecir ese mismo valor; y la disponibilidad del avalúo no autoriza automáticamente su empleo como etiqueta de valor de terreno.
3. **Granularidad.** `interseccion_terrenos_zhg_r1_yacopi.csv` contiene varias filas para un mismo `numero_predial`, mientras `zhf_yacopi (1).csv` tiene 47 filas adicionales por identificadores `CODPRED` repetidos (sin contradicciones en atributos tabulares). El conjunto consolidado mantiene **una fila por predio** para evitar un producto cartesiano en el cruce.
4. **Geometría y sistemas de referencia.** Los encabezados WKB indican SRID {summary['estimated_srid_intersections']} en `geometria_interseccion` / `geometria` y SRID {summary['estimated_srid_zhf_geom']} en `geom`. No combinar coordenadas proyectadas ni superponer capas sin revisar y transformar CRS con software GIS.
5. **Diferencias de zonas.** La zona geoeconómica predominante de la tabla de intersecciones no coincide con `ZHG_CODIGO` en el archivo ZHF para {mismatched_geo:,} predios enlazados. Puede reflejar distintas reglas de asignación; se recomienda verificar con la fuente.
6. **Etiquetas.** No hay información temporal documentada ni diccionario oficial de los códigos. `N/A` en coberturas CLC se conserva como categoría original y los identificadores se mantienen como texto (incluidos ceros iniciales).

## Qué se hizo, sin alterar fuentes

- Trim de espacios, codificación UTF-8, códigos ZHG de longitud dos (`01`…`11`) y ORIP como texto sin `.0` espurio en la copia normalizada.
- Se **conservaron todas las filas y geometrías** en `01_intersecciones_normalizadas.csv` y `02_zhf_normalizadas.csv`, con su número de fila de origen.
- Se creó `03_predios_consolidados.csv` agrupando intersecciones por `numero_predial`, tomando la zona predominante según **porcentaje acumulado** y calculando un **precio ZHG ponderado de referencia**, no una etiqueta validada de valor comercial.
- El enlace con ZHF se hizo por identificador; ante coincidencias repetidas con atributos iguales, se tomó la primera fila **solo en la tabla consolidada**.
- Se preservaron los {summary['parcels_only_zhf']:,} predios presentes solo en ZHF en `04_predios_solo_zhf.csv`.
- Las advertencias se registraron, por predio, en `05_banderas_calidad.csv`.

## Diccionario resumido de la tabla consolidada

| Campo | Uso / interpretación |
|---|---|
| `numero_predial` | Identificador (texto, llave del cruce) |
| `valor_avaluo_total_cop` | Avalúo disponible en la fuente; **no debe tratarse automáticamente como valor exclusivo del suelo** |
| `area_terreno_catastral_m2` | Área declarada en primera fuente, m² |
| `area_zhf_m2` | `AREA_TERRE` declarado en segunda fuente, definición exacta por validar |
| `area_construida_m2` | Construcción declarada en primera fuente, m² |
| `referencia_avaluo_total_por_ha_cop` | Avalúo total / área catastral × 10.000; solo referencia, no etiqueta confirmada |
| `zhg_codigo_predominante` | Zona con mayor suma de porcentaje por predio |
| `referencia_zhg_valor_ponderado_cop_ha` | Promedio de valores ZHG, ponderado por porcentaje de intersección; variable derivada, no etiqueta independiente |
| `zhf_codigo`, `zhf_dispon`, `zhf_influe`, `zhf_uso_ac` | Variables codificadas de zonas homogéneas físicas |
| `ups`, `vus_vocaci`, `clc_nivel1`…`clc_nivel6` | Vocación, uso y coberturas del suelo; categorías sin recodificación semántica |
| `tr_latitud`, `tr_longitud` | Coordenadas geográficas referenciales del archivo ZHF |
| `coincide_zhf` | Indicador de presencia de predio en las dos fuentes |

## Antes de entrenar modelos comparables

1. Solicitar el **diccionario técnico** de ambos archivos, incluyendo fechas, método de valoración y definición de `AREA_TERRE`, `ZHG_VALOR_` y `ZHG_VALOR1`.
2. Aclarar si existe una columna/archivo de **valor exclusivo de terreno por predio**, separado del valor de construcciones, con fecha de referencia.
3. Validar geométricamente los predios fuera de tolerancia y las zonas discordantes.
4. Definir una división de entrenamiento/prueba **por predio y preferentemente espacial** para evitar resultados inflados por vecindad.
5. Entrenar baselines y modelos candidatos, registrar MAE, RMSE, MdAPE, R², error por subzona y análisis de interpretación. Reentrenar sólo cuando exista una etiqueta defendible.

> Nota: un modelo que predice exactamente el valor ZHG a partir de su código geoeconómico no constituye un logro predictivo independiente. Los datos del trabajo de Jesús son un antecedente, no una garantía de precisión de los nuevos CSV.
''')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Auditar dos CSV catastrales de Yacopí sin destruir datos')
    p.add_argument('intersecciones')
    p.add_argument('zhf')
    p.add_argument('--output',default='salida_yacopi')
    args=p.parse_args()
    main(args.intersecciones,args.zhf,args.output)
