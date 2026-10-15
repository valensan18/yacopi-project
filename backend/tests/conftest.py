"""Fixtures del backend: base SQLite mínima para pruebas (sin datos reales)."""

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "backend"))

from build_db import SCHEMA, public_id_for  # noqa: E402


def build_minimal_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    parcels = [
        ("A", "Agropecuario", 50000.0, 51000.0, 0.0, 5.53, -74.32, "05"),
        ("B", "Habitacional", 2500.0, 2400.0, 120.0, 5.55, -74.35, "08"),
        ("C", "Agropecuario", 300000.0, 310000.0, 0.0, 5.60, -74.40, "14"),
        ("D", "Religioso", 12000.0, None, 40.0, 5.57, -74.38, "17"),
        ("E", "Agropecuario", 80000.0, 80000.0, 0.0, 5.51, -74.30, "05"),
    ]
    with conn:
        for source_id, destino, area, area_zhf, built, lat, lon, subzona in parcels:
            public_id = public_id_for(source_id)
            conn.execute(
                """INSERT INTO parcels (public_id, parcel_source_id,
                       dataset_version, destino_economico,
                       area_terreno_catastral_m2, area_zhf_m2,
                       area_construida_m2, latitud, longitud, subzona,
                       coincide_zhf, cantidad_intersecciones,
                       cantidad_zonas_zhg, tiene_alertas_calidad,
                       n_alertas_calidad)
                   VALUES (?, ?, 'test-v1', ?, ?, ?, ?, ?, ?, ?, 1, 1, 1, ?, ?)""",
                (public_id, source_id, destino, area, area_zhf, built,
                 lat, lon, subzona, int(built > 0), int(built > 0)),
            )
            conn.execute(
                """INSERT INTO parcel_features (public_id, zhf_codigo,
                       zhf_dispon, zhf_influe, zhf_uso_ac, aht_vpoten,
                       fa_element, vus_vocaci, ups, clc_nivel1, clc_nivel2,
                       clc_nivel3, clc_nivel4, clc_nivel5, clc_nivel6)
                   VALUES (?, '05', '4', '3', '16', '23', 'Frontera agrícola nacional',
                           'ASPp', 'Zonas de desarrollo agropecuario sin restricciones',
                           '2. Territorios Agrícolas', '2.3. Pastos',
                           '2.3.1. Pastos limpios', 'N/A', 'N/A', 'N/A')""",
                (public_id,),
            )
            if built > 0:
                conn.execute(
                    """INSERT INTO quality_flags (public_id, code, source_version)
                       VALUES (?, 'contiene_construccion', 'test-v1')""",
                    (public_id,),
                )
        conn.execute(
            "INSERT INTO dataset_meta (key, value) VALUES ('dataset_version', 'test-v1')"
        )
        # Referencias ZHG de prueba (Fase 6B)
        conn.execute(
            """INSERT INTO zhg_zones (zone_code, value_cop_ha, source_column, source_file)
               VALUES ('03', 1368119.6, 'valor_hectarea_agropecuario', 'test'),
                      ('06', 547247.2, 'valor_hectarea_agropecuario', 'test')"""
        )
        zhg_fixture = [
            # (source_id, zone, value, area, share, coverage)
            ("A", "03", 1368119.6, 50000.0, 100.0, "consistente"),
            ("B", "03", 1368119.6, 1200.0, 50.0, "dudosa"),
            ("B", "06", 547247.2, 1200.0, 50.0, "dudosa"),
            ("C", "03", 1368119.6, 100000.0, 66.6, "no_apta"),
            ("C", "06", 547247.2, 50000.0, 33.3, "no_apta"),
            ("E", "06", 547247.2, 80000.0, 100.0, "consistente"),
        ]
        for source_id, zone, value, area, share, coverage in zhg_fixture:
            conn.execute(
                """INSERT INTO parcel_zhg_references
                       (public_id, zone_code, value_cop_ha, area_intersection_m2,
                        share_pct, coverage_status, source_file, dataset_version)
                   VALUES (?, ?, ?, ?, ?, ?, 'test', 'test-v1')""",
                (public_id_for(source_id), zone, value, area, share, coverage),
            )
    conn.close()


@pytest.fixture
def mini_db(tmp_path):
    path = tmp_path / "mini.db"
    build_minimal_db(path)
    return path


def build_mini_zhg_demo(model_dir: Path, entries: dict[str, dict]) -> Path:
    """Artefacto de demostración ZHG mínimo para pruebas (Fase 7B)."""
    import json

    import joblib
    import pandas as pd
    from sklearn.dummy import DummyRegressor

    art = model_dir / "exp-zhg-001-demo"
    art.mkdir(parents=True, exist_ok=True)

    schema = {
        "orden": ["area_terreno_catastral_m2", "tr_latitud", "destino_economico"],
        "numericas": ["area_terreno_catastral_m2", "tr_latitud"],
        "categoricas": ["destino_economico"],
        "unidades": {"area_terreno_catastral_m2": "m2", "tr_latitud": "grados"},
    }
    (art / "feature_schema.json").write_text(
        json.dumps(schema), encoding="utf-8"
    )
    stats = {
        "numeric": {
            "area_terreno_catastral_m2": {"min": 1000.0, "max": 900_000.0},
            "tr_latitud": {"min": 5.3, "max": 5.9},
        },
        "categorical": {"destino_economico": ["Agropecuario", "SIN_DATO"]},
    }
    (art / "training_stats.json").write_text(
        json.dumps(stats), encoding="utf-8"
    )
    (art / "features.json").write_text(
        json.dumps(entries, ensure_ascii=False), encoding="utf-8"
    )
    (art / "split_membership.json").write_text(
        json.dumps({pid: {"predio": "train"} for pid in entries}),
        encoding="utf-8",
    )
    (art / "manifest.json").write_text(
        json.dumps({
            "model_id": "exp-zhg-001-demo",
            "status": "experimental",
            "target_description": "valor unitario de referencia ZHG del suelo rural (COP/ha)",
        }),
        encoding="utf-8",
    )
    model = DummyRegressor(strategy="mean")
    frame = pd.DataFrame([{
        "area_terreno_catastral_m2": 50000.0,
        "tr_latitud": 5.5,
        "destino_economico": "Agropecuario",
    }])
    model.fit(frame, [500_000.0])
    joblib.dump(model, art / "model.joblib")
    return art
