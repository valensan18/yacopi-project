"""Verificación de CRS y exportación de GeoJSON EPSG:4326 para Leaflet.

Uso:
  python scripts/build_maps.py [--output data/maps]

Lee las geometrías EWKB de `data/processed/02_zhf_normalizadas.csv` (SRID
esperado 3116) y los puntos de `03_predios_consolidados.csv`. Reprojecta los
polígonos a EPSG:4326, los simplifica preservando topología y valida rangos.
También audita el SRID de las geometrías de intersección (esperado 9377).

Salidas:
  predios_puntos.geojson      puntos referenciales (TR_LATITUD/TR_LONGITUD)
  predios_poligonos.geojson   polígonos simplificados WGS84
  resumen_maps.json           conteos, CRS detectados y tamaños
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import shapely
import shapely.wkb
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

SRID_ESPERADO_ZHF = 3116  # MAGNA-SIRGAS / Colombia Bogotá
SRID_ESPERADO_INTERSECTIONS = 9377  # MAGNA-SIRGAS Origen-Nacional
TOLERANCIA_SIMPLIF_M = 15.0  # simplificación en metros (antes de reproyectar)

LAT_MIN, LAT_MAX = -6.0, 13.0
LON_MIN, LON_MAX = -80.0, -66.0


def srid_of_hex(wkb: str):
    try:
        if len(wkb) >= 18:
            prefix = bytes.fromhex(wkb[:18])
            order = "little" if prefix[0] == 1 else "big"
            gtype = int.from_bytes(prefix[1:5], order)
            if gtype & 0x20000000:
                return int.from_bytes(prefix[5:9], order)
    except Exception:
        pass
    return None


def load_geometry(wkb: str):
    if not wkb:
        return None
    try:
        return shapely.wkb.loads(bytes.fromhex(wkb))
    except Exception:
        return None


def build(output_dir: Path, processed: Path = PROCESSED) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Auditoría de SRID en las dos fuentes normalizadas ---
    srids_zhf: dict = {}
    srids_inter: dict = {}
    with (processed / "02_zhf_normalizadas.csv").open(
        encoding="utf-8", newline=""
    ) as fh:
        for row in csv.DictReader(fh):
            srid = srid_of_hex(row["geom"])
            srids_zhf[srid] = srids_zhf.get(srid, 0) + 1
    with (processed / "01_intersecciones_normalizadas.csv").open(
        encoding="utf-8", newline=""
    ) as fh:
        reader = csv.DictReader(fh)
        for _ in range(50):  # muestra suficiente para confirmar el encabezado
            try:
                row = next(reader)
            except StopIteration:
                break
            for col in ("geometria", "geometria_interseccion"):
                srid = srid_of_hex(row[col])
                srids_inter[srid] = srids_inter.get(srid, 0) + 1

    # --- Puntos referenciales ---
    features = []
    valid = 0
    missing = 0
    out_of_range = 0
    with (processed / "03_predios_consolidados.csv").open(
        encoding="utf-8", newline=""
    ) as fh:
        for row in csv.DictReader(fh):
            lat_raw, lon_raw = row["tr_latitud"], row["tr_longitud"]
            if not lat_raw or not lon_raw:
                missing += 1
                continue
            try:
                lat, lon = float(lat_raw), float(lon_raw)
            except ValueError:
                missing += 1
                continue
            if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
                out_of_range += 1
                continue
            valid += 1
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "numero_predial": row["numero_predial"],
                    "destino_economico": row["destino_economico"],
                    "zhg_subzona": row["zhg_subzona"],
                },
            })
    points_fc = {"type": "FeatureCollection", "features": features}
    points_path = output_dir / "predios_puntos.geojson"
    points_path.write_text(json.dumps(points_fc, ensure_ascii=False), encoding="utf-8")

    # --- Polígonos ZHF (SRID 3116 -> 4326, simplificados) ---
    transformer = Transformer.from_crs(SRID_ESPERADO_ZHF, 4326, always_xy=True)
    to_wgs84 = lambda geom: shapely.transform(  # noqa: E731
        geom, transformer.transform, interleaved=False
    )

    poly_features = []
    n_poly = 0
    invalid_repaired = 0
    invalid_dropped = 0
    load_failures = 0
    wrong_srid = 0
    with (processed / "02_zhf_normalizadas.csv").open(
        encoding="utf-8", newline=""
    ) as fh:
        for row in csv.DictReader(fh):
            srid = srid_of_hex(row["geom"])
            if srid != SRID_ESPERADO_ZHF:
                wrong_srid += 1
                continue
            geom = load_geometry(row["geom"])
            if geom is None or geom.is_empty:
                load_failures += 1
                continue
            if not geom.is_valid:
                repaired = shapely.make_valid(geom)
                if repaired.is_valid:
                    invalid_repaired += 1
                    geom = repaired
                else:
                    invalid_dropped += 1
                    continue
            simplified = geom.simplify(TOLERANCIA_SIMPLIF_M, preserve_topology=True)
            wgs = to_wgs84(simplified)
            n_poly += 1
            poly_features.append({
                "type": "Feature",
                "geometry": json.loads(shapely.to_geojson(wgs)),
                "properties": {
                    "id_zhf": row["id"],
                    "CODPRED": row["CODPRED"],
                    "ZHF_CODIGO": row["ZHF_CODIGO"],
                    "ZHG_CODIGO": row["ZHG_CODIGO"],
                },
            })
    poly_fc = {"type": "FeatureCollection", "features": poly_features}
    poly_path = output_dir / "predios_poligonos.geojson"
    poly_path.write_text(json.dumps(poly_fc, ensure_ascii=False), encoding="utf-8")

    resumen = {
        "crs_audit": {
            "srids_zhf_geom": srids_zhf,
            "srids_intersections_sample": srids_inter,
            "srid_esperado_zhf": SRID_ESPERADO_ZHF,
            "srid_esperado_intersections": SRID_ESPERADO_INTERSECTIONS,
        },
        "puntos": {
            "features": len(features),
            "validos": valid,
            "faltantes": missing,
            "fuera_de_rango": out_of_range,
            "archivo": str(points_path),
            "tamano_mb": round(points_path.stat().st_size / 1e6, 2),
        },
        "poligonos": {
            "features": n_poly,
            "invalidos_reparados": invalid_repaired,
            "invalidos_descartados": invalid_dropped,
            "fallos_de_carga": load_failures,
            "srid_distinto": wrong_srid,
            "tolerancia_simplificacion_m": TOLERANCIA_SIMPLIF_M,
            "archivo": str(poly_path),
            "tamano_mb": round(poly_path.stat().st_size / 1e6, 2),
        },
    }
    (output_dir / "resumen_maps.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return resumen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(ROOT / "data" / "maps"))
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    resumen = build(output)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
