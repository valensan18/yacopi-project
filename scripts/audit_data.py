"""Auditoría de datos de la Fase 1: reproducibilidad + validaciones ampliadas.

Uso:
  python scripts/audit_data.py [--output data/processed]

Ejecuta el pipeline heredado (preparar_datos.py) y lo compara contra el
diagnóstico de referencia (tests/fixtures/reference_diagnostico.json).
Además calcula validaciones adicionales sobre el consolidado: nulos por
columna, unicidad, rangos de coordenadas y resumen de banderas. Escribe
`08_validacion_fase1.json` en el directorio de salida.
"""

import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

from preparar_datos import main as run_preparar

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tests" / "fixtures" / "reference_diagnostico.json"
RAW_DIR = ROOT / "data" / "raw"
RAW_INTERSECTIONS = RAW_DIR / "interseccion_terrenos_zhg_r1_yacopi.csv"
RAW_ZHF = RAW_DIR / "zhf_yacopi.csv"

# Bounding box aproximada de Colombia continental (grados, WGS84)
LAT_MIN, LAT_MAX = -6.0, 13.0
LON_MIN, LON_MAX = -80.0, -66.0

COMPARED_KEYS = [
    "rows_intersections", "rows_zhf", "unique_parcels_intersections",
    "unique_parcels_zhf", "parcel_matches", "parcels_only_intersections",
    "parcels_only_zhf", "duplicates_intersection_exact_rows",
    "duplicate_zhf_excess_rows", "duplicate_zhf_with_different_attributes",
    "parcels_with_repeated_identical_intersections",
    "parcels_with_multiple_zone_intersections",
    "parcels_with_zhf_area_difference_above_5pct",
    "parcels_geometric_area_match_within_1pct",
    "parcels_geometric_area_difference_above_5pct",
    "parcels_with_intersection_area_difference_above_5pct",
    "parcels_zhg_dominant_zone_disagrees_with_zhf",
    "parcels_with_construction", "parcels_percentages_not_100",
    "estimated_srid_intersections", "estimated_srid_geometry_parcel",
    "estimated_srid_zhf_geom", "destinations", "zhg_subzone_counts_matched",
    "label_availability",
]


def fnum(value):
    try:
        ans = float(value)
    except (TypeError, ValueError):
        return None
    return ans if math.isfinite(ans) else None


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def column_nulls(rows: list[dict]) -> dict:
    return {
        col: sum(1 for r in rows if r.get(col, "").strip() == "")
        for col in rows[0]
    }


def coordinate_stats(rows: list[dict]) -> dict:
    stats = {"valid": 0, "invalid_out_of_range": 0, "missing": 0}
    for r in rows:
        lat, lon = fnum(r["tr_latitud"]), fnum(r["tr_longitud"])
        if lat is None or lon is None:
            stats["missing"] += 1
        elif not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            stats["invalid_out_of_range"] += 1
        else:
            stats["valid"] += 1
    return stats


def audit(output_dir: Path) -> int:
    errors: list[str] = []

    run_preparar(str(RAW_INTERSECTIONS), str(RAW_ZHF), str(output_dir))

    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    generated = json.loads(
        (output_dir / "06_resumen_diagnostico.json").read_text(encoding="utf-8")
    )
    diffs = {k: (reference.get(k), generated.get(k)) for k in COMPARED_KEYS
             if reference.get(k) != generated.get(k)}
    if diffs:
        for key, (expected, actual) in diffs.items():
            errors.append(f"{key}: esperado {expected}, obtenido {actual}")

    consolidated = read_rows(output_dir / "03_predios_consolidados.csv")
    flags = read_rows(output_dir / "05_banderas_calidad.csv")
    solo_zhf = read_rows(output_dir / "04_predios_solo_zhf.csv")

    ids = [r["numero_predial"] for r in consolidated]
    duplicates = [key for key, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append(f"numero_predial duplicado en consolidado: {duplicates[:5]}")

    if len(flags) != len(consolidated):
        errors.append(
            f"banderas ({len(flags)}) != consolidado ({len(consolidated)})"
        )

    nulls = column_nulls(consolidated)
    coords = coordinate_stats(consolidated)
    flag_totals = {
        col: sum(int(r.get(col, "0")) for r in flags)
        for col in flags[0] if col != "numero_predial"
    }

    report = {
        "reproducible": not bool(diffs),
        "compared_keys": len(COMPARED_KEYS),
        "differences": diffs,
        "parcels_consolidated": len(consolidated),
        "parcels_unique_ids": len(set(ids)),
        "duplicate_parcel_ids": duplicates,
        "parcels_only_zhf": len(solo_zhf),
        "nulls_by_column": nulls,
        "coordinates": coords,
        "quality_flag_totals": flag_totals,
        "reference_file": str(REFERENCE),
    }
    (output_dir / "08_validacion_fase1.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if errors:
        print("\n".join(f"ERROR: {e}" for e in errors))
        return 1
    print("AUDITORIA OK: pipeline reproducible, unicidad y rangos verificados")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(ROOT / "data" / "processed"))
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    return audit(output)


if __name__ == "__main__":
    sys.exit(main())
