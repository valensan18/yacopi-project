"""Pruebas de integridad y calidad de datos (Fase 1).

Requieren los datos generados localmente (data/raw y data/processed); se
omiten automáticamente en CI sin datos. No presentan métricas científicas:
solo verifican reproducibilidad e integridad.
"""

import csv
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
REFERENCE = ROOT / "tests" / "fixtures" / "reference_diagnostico.json"

HAS_PROCESSED = (PROCESSED / "03_predios_consolidados.csv").exists()
HAS_RAW = (RAW / "interseccion_terrenos_zhg_r1_yacopi.csv").exists()

pytestmark = pytest.mark.skipif(
    not HAS_PROCESSED, reason="datos procesados no presentes (solo ejecución local)"
)

REFERENCE_KEYS = [
    "rows_intersections", "rows_zhf", "unique_parcels_intersections",
    "unique_parcels_zhf", "parcel_matches", "parcels_only_intersections",
    "parcels_only_zhf", "parcels_with_multiple_zone_intersections",
    "parcels_with_zhf_area_difference_above_5pct",
    "parcels_geometric_area_match_within_1pct",
    "parcels_geometric_area_difference_above_5pct",
    "parcels_zhg_dominant_zone_disagrees_with_zhf",
    "parcels_with_construction", "parcels_percentages_not_100",
]


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_diagnostico_reproduce_referencia():
    generated = json.loads(
        (PROCESSED / "06_resumen_diagnostico.json").read_text(encoding="utf-8")
    )
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    for key in REFERENCE_KEYS:
        assert generated[key] == reference[key], f"{key} difiere de la referencia"


def test_predios_consolidados_unicos_y_cantidad():
    rows = read_rows(PROCESSED / "03_predios_consolidados.csv")
    assert len(rows) == 7709
    ids = [r["numero_predial"] for r in rows]
    assert len(ids) == len(set(ids))


def test_porcentajes_zonas_suman_100():
    rows = read_rows(PROCESSED / "03_predios_consolidados.csv")
    for row in rows:
        value = float(row["suma_porcentaje_intersecciones"])
        assert abs(value - 100.0) <= 0.1, row["numero_predial"]


def test_banderas_una_fila_por_predio():
    rows = read_rows(PROCESSED / "03_predios_consolidados.csv")
    flags = read_rows(PROCESSED / "05_banderas_calidad.csv")
    assert len(flags) == len(rows)
    assert {f["numero_predial"] for f in flags} == {r["numero_predial"] for r in rows}


def test_coordenadas_en_rango_colombia():
    rows = read_rows(PROCESSED / "03_predios_consolidados.csv")
    valid = 0
    for row in rows:
        if not row["tr_latitud"] or not row["tr_longitud"]:
            continue
        lat, lon = float(row["tr_latitud"]), float(row["tr_longitud"])
        assert -6.0 <= lat <= 13.0, row["numero_predial"]
        assert -80.0 <= lon <= -66.0, row["numero_predial"]
        valid += 1
    assert valid == 7694


def test_srids_detectados():
    generated = json.loads(
        (PROCESSED / "06_resumen_diagnostico.json").read_text(encoding="utf-8")
    )
    assert generated["estimated_srid_intersections"] == 9377
    assert generated["estimated_srid_geometry_parcel"] == 9377
    assert generated["estimated_srid_zhf_geom"] == 3116


def test_solo_zhf_preservados():
    rows = read_rows(PROCESSED / "04_predios_solo_zhf.csv")
    assert len(rows) == 227


def test_sin_etiqueta_validada_en_consolidado():
    generated = json.loads(
        (PROCESSED / "06_resumen_diagnostico.json").read_text(encoding="utf-8")
    )
    assert "NO se ha confirmado" in generated["label_availability"]


class TestBuildDb:
    def test_build_db_esquema_y_conteos(self, tmp_path):
        from build_db import build

        db_path = tmp_path / "test.db"
        stats = build(db_path, PROCESSED, "test-version")
        assert stats["parcels"] == 7709
        assert stats["parcel_features"] == 7709
        assert stats["quality_flags"] == 15489
        assert stats["zhf_only_parcels"] == 227
        assert stats["model_targets"] == 0

        conn = sqlite3.connect(db_path)
        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {
            "parcels", "parcel_features", "parcel_value_references",
            "quality_flags", "model_targets", "zhf_only_parcels",
            "dataset_meta",
        } <= tables

        n_dupes = conn.execute(
            "SELECT COUNT(*) FROM (SELECT public_id FROM parcels GROUP BY "
            "public_id HAVING COUNT(*) > 1)"
        ).fetchone()[0]
        assert n_dupes == 0

        n_orphan = conn.execute(
            """SELECT COUNT(*) FROM parcel_features pf
               LEFT JOIN parcels p ON p.public_id = pf.public_id
               WHERE p.public_id IS NULL"""
        ).fetchone()[0]
        assert n_orphan == 0

        n_validated = conn.execute(
            "SELECT COUNT(*) FROM parcel_value_references "
            "WHERE es_etiqueta_validada = 1"
        ).fetchone()[0]
        assert n_validated == 0
        conn.close()

    def test_build_db_es_reproducible(self, tmp_path):
        from build_db import build

        stats_a = build(tmp_path / "a.db", PROCESSED, "v1")
        stats_b = build(tmp_path / "b.db", PROCESSED, "v1")
        assert stats_a == stats_b


class TestBuildMaps:
    def test_maps_crs_y_conteos(self, tmp_path):
        from build_maps import build

        resumen = build(tmp_path, PROCESSED)
        assert resumen["crs_audit"]["srids_zhf_geom"] == {3116: 7968}
        assert resumen["crs_audit"]["srids_intersections_sample"] == {9377: 100}
        assert resumen["puntos"]["features"] == 7694
        assert resumen["puntos"]["fuera_de_rango"] == 0
        assert resumen["poligonos"]["features"] == 7968
        assert resumen["poligonos"]["invalidos_descartados"] == 0

        points = json.loads(
            (tmp_path / "predios_puntos.geojson").read_text(encoding="utf-8")
        )
        assert points["type"] == "FeatureCollection"
        polygons = json.loads(
            (tmp_path / "predios_poligonos.geojson").read_text(encoding="utf-8")
        )
        assert polygons["type"] == "FeatureCollection"
        first = polygons["features"][0]["geometry"]
        assert first["type"] in ("Polygon", "MultiPolygon")


@pytest.mark.skipif(not HAS_RAW, reason="CSV originales no presentes")
class TestReproducibilidadYEntradas:
    def test_preparar_dos_veces_mismo_resultado(self, tmp_path):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "preparar_datos", ROOT / "scripts" / "preparar_datos.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        out_a, out_b = tmp_path / "a", tmp_path / "b"
        module.main(
            str(RAW / "interseccion_terrenos_zhg_r1_yacopi.csv"),
            str(RAW / "zhf_yacopi.csv"), str(out_a),
        )
        module.main(
            str(RAW / "interseccion_terrenos_zhg_r1_yacopi.csv"),
            str(RAW / "zhf_yacopi.csv"), str(out_b),
        )
        summary_a = json.loads(
            (out_a / "06_resumen_diagnostico.json").read_text(encoding="utf-8")
        )
        summary_b = json.loads(
            (out_b / "06_resumen_diagnostico.json").read_text(encoding="utf-8")
        )
        assert summary_a == summary_b

    def test_verify_inputs_ok(self):
        from verify_inputs import verify

        errors = verify(RAW / "data_manifest.json")
        assert errors == []
