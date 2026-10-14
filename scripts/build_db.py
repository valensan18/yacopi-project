"""Construcción reproducible de la base SQLite de consulta (Fase 1).

Uso:
  python scripts/build_db.py [--output data/parcels.db]
                             [--processed data/processed] [--version dataset-v1]

Estructura (ver docs/02_diccionario_datos.md):
  parcels                    una fila por predio (7.709) con identificador opaco
  parcel_features            atributos físicos/territoriales categóricos
  parcel_value_references    referencias económicas NO validadas como etiqueta
  quality_flags              banderas de calidad activas por predio
  model_targets              etiquetas validadas (vacía hasta aprobación)
  zhf_only_parcels           los 227 predios presentes solo en ZHF
  dataset_meta               versiones, hashes y conteos

El identificador `public_id` es opaco y determinista (SHA-256 truncado del
numero_predial). Los identificadores oficiales quedan solo en esta base, que
NO se versiona en Git.
"""

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "parcels.db"
DEFAULT_PROCESSED = ROOT / "data" / "processed"
DEFAULT_VERSION = "dataset-v1"

VALUE_REFERENCES = [
    # (nombre_columna_consolidado, reference_type, unit)
    ("valor_avaluo_total_cop", "avaluo_total", "COP"),
    ("referencia_avaluo_total_por_ha_cop", "avaluo_total_ha", "COP/ha"),
    ("referencia_zhg_valor_ponderado_cop_ha", "zhg_valor_ponderado_ha", "COP/ha"),
    ("referencia_zhg_valor_predominante_cop_ha", "zhg_valor_predominante_ha", "COP/ha"),
    ("referencia_zhg_valor_zhf_cop_ha", "zhg_valor_zhf", "COP/ha"),
    ("referencia_zhg_valor1_zhf_cop_ha", "zhg_valor1_zhf", "COP/ha"),
]

FEATURE_COLUMNS = [
    "zhf_codigo", "zhf_dispon", "zhf_influe", "zhf_uso_ac",
    "aht_vpoten", "fa_element", "vus_vocaci", "ups",
    "clc_nivel1", "clc_nivel2", "clc_nivel3", "clc_nivel4",
    "clc_nivel5", "clc_nivel6",
]

FLAG_CODES = [
    "sin_coincidencia_zhf",
    "multiples_intersecciones_zhg",
    "interseccion_filas_exactamente_duplicadas",
    "porcentajes_zhg_no_suman_100",
    "suma_area_intersecciones_difiere_mas_5pct_area_catastral",
    "area_zhf_difiere_mas_5pct_area_catastral",
    "area_geometrica_zhg_difiere_mas_5pct_zhf",
    "zona_zhg_zhf_diferente_de_zhg_dominante",
    "zhf_codpred_repetido",
    "area_catastral_no_positiva",
    "contiene_construccion",
]

SCHEMA = """
CREATE TABLE parcels (
  public_id TEXT PRIMARY KEY,
  parcel_source_id TEXT NOT NULL UNIQUE,
  dataset_version TEXT NOT NULL,
  destino_economico TEXT,
  area_terreno_catastral_m2 REAL,
  area_zhf_m2 REAL,
  area_construida_m2 REAL,
  latitud REAL,
  longitud REAL,
  subzona TEXT,
  coincide_zhf INTEGER NOT NULL,
  cantidad_intersecciones INTEGER,
  cantidad_zonas_zhg INTEGER,
  tiene_alertas_calidad INTEGER NOT NULL DEFAULT 0,
  n_alertas_calidad INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_parcels_destino ON parcels(destino_economico);
CREATE INDEX idx_parcels_subzona ON parcels(subzona);
CREATE INDEX idx_parcels_coords ON parcels(latitud, longitud);
CREATE INDEX idx_parcels_version ON parcels(dataset_version);

CREATE TABLE parcel_features (
  public_id TEXT PRIMARY KEY REFERENCES parcels(public_id),
  zhf_codigo TEXT, zhf_dispon TEXT, zhf_influe TEXT, zhf_uso_ac TEXT,
  aht_vpoten TEXT, fa_element TEXT, vus_vocaci TEXT, ups TEXT,
  clc_nivel1 TEXT, clc_nivel2 TEXT, clc_nivel3 TEXT, clc_nivel4 TEXT,
  clc_nivel5 TEXT, clc_nivel6 TEXT
);

CREATE TABLE parcel_value_references (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  public_id TEXT NOT NULL REFERENCES parcels(public_id),
  reference_type TEXT NOT NULL,
  value_cop REAL,
  unit TEXT NOT NULL,
  source_column TEXT NOT NULL,
  source_file TEXT NOT NULL,
  valuation_date TEXT,
  es_etiqueta_validada INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_value_refs_parcel ON parcel_value_references(public_id);
CREATE INDEX idx_value_refs_type ON parcel_value_references(reference_type);

CREATE TABLE quality_flags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  public_id TEXT NOT NULL REFERENCES parcels(public_id),
  code TEXT NOT NULL,
  source_version TEXT NOT NULL
);
CREATE INDEX idx_flags_parcel ON quality_flags(public_id);
CREATE INDEX idx_flags_code ON quality_flags(code);

CREATE TABLE model_targets (
  public_id TEXT PRIMARY KEY REFERENCES parcels(public_id),
  target_cop_ha REAL NOT NULL,
  source_kind TEXT NOT NULL,
  source_document TEXT,
  valuation_date TEXT,
  area_definition TEXT,
  approval_status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE zhf_only_parcels (
  parcel_source_id TEXT PRIMARY KEY,
  dataset_version TEXT NOT NULL,
  area_zhf_m2 REAL,
  latitud REAL,
  longitud REAL,
  zhf_codigo TEXT,
  zhg_codigo TEXT
);

CREATE TABLE dataset_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""


def public_id_for(parcel_source_id: str) -> str:
    return "p_" + hashlib.sha256(parcel_source_id.encode("utf-8")).hexdigest()[:16]


def fnum(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        ans = float(value)
    except ValueError:
        return None
    return ans if ans == ans and ans not in (float("inf"), float("-inf")) else None


def read_rows(path: Path) -> list[dict]:
    import csv

    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def build(db_path: Path, processed: Path, dataset_version: str) -> dict:
    consolidated = read_rows(processed / "03_predios_consolidados.csv")
    flags = read_rows(processed / "05_banderas_calidad.csv")
    solo_zhf = read_rows(processed / "04_predios_solo_zhf.csv")
    flags_by_id = {r["numero_predial"]: r for r in flags}

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)

    n_flags_total = 0
    with conn:
        for row in consolidated:
            public_id = public_id_for(row["numero_predial"])
            flag_row = flags_by_id.get(row["numero_predial"], {})
            active = [
                code for code in FLAG_CODES if flag_row.get(code, "0") == "1"
            ]
            lat, lon = fnum(row["tr_latitud"]), fnum(row["tr_longitud"])
            conn.execute(
                """INSERT INTO parcels (
                       public_id, parcel_source_id, dataset_version,
                       destino_economico, area_terreno_catastral_m2,
                       area_zhf_m2, area_construida_m2, latitud, longitud,
                       subzona, coincide_zhf, cantidad_intersecciones,
                       cantidad_zonas_zhg, tiene_alertas_calidad,
                       n_alertas_calidad)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    public_id, row["numero_predial"], dataset_version,
                    row["destino_economico"] or None,
                    fnum(row["area_terreno_catastral_m2"]),
                    fnum(row["area_zhf_m2"]),
                    fnum(row["area_construida_m2"]),
                    lat, lon,
                    row["zhg_subzona"] or None,
                    int(row["coincide_zhf"]),
                    int(row["cantidad_intersecciones"] or 0),
                    int(row["cantidad_zonas_zhg"] or 0),
                    int(bool(active)),
                    len(active),
                ),
            )
            conn.execute(
                "INSERT INTO parcel_features (public_id, "
                + ", ".join(FEATURE_COLUMNS)
                + ") VALUES ("
                + ", ".join("?" for _ in range(1 + len(FEATURE_COLUMNS)))
                + ")",
                [public_id] + [row[c] or None for c in FEATURE_COLUMNS],
            )
            for col, ref_type, unit in VALUE_REFERENCES:
                value = fnum(row[col])
                if value is not None:
                    conn.execute(
                        """INSERT INTO parcel_value_references
                               (public_id, reference_type, value_cop, unit,
                                source_column, source_file)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (public_id, ref_type, value, unit, col,
                         "03_predios_consolidados.csv"),
                    )
            for code in active:
                n_flags_total += 1
                conn.execute(
                    """INSERT INTO quality_flags (public_id, code, source_version)
                       VALUES (?, ?, ?)""",
                    (public_id, code, dataset_version),
                )

        for row in solo_zhf:
            conn.execute(
                """INSERT INTO zhf_only_parcels
                       (parcel_source_id, dataset_version, area_zhf_m2,
                        latitud, longitud, zhf_codigo, zhg_codigo)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["CODPRED"], dataset_version, fnum(row["AREA_TERRE"]),
                    fnum(row["TR_LATITUD"]), fnum(row["TR_LONGITU"]),
                    row["ZHF_CODIGO"] or None, row["ZHG_CODIGO"] or None,
                ),
            )

        meta = {
            "dataset_version": dataset_version,
            "generated_at": "ver manifest local",
            "parcels": len(consolidated),
            "zhf_only": len(solo_zhf),
            "quality_flag_rows": n_flags_total,
            "label_status": "pending_verification",
            "model_targets_rows": 0,
        }
        for key, value in meta.items():
            conn.execute(
                "INSERT INTO dataset_meta (key, value) VALUES (?, ?)",
                (key, str(value)),
            )

    stats = {
        "parcels": conn.execute("SELECT COUNT(*) FROM parcels").fetchone()[0],
        "parcel_features": conn.execute(
            "SELECT COUNT(*) FROM parcel_features"
        ).fetchone()[0],
        "value_references": conn.execute(
            "SELECT COUNT(*) FROM parcel_value_references"
        ).fetchone()[0],
        "quality_flags": conn.execute(
            "SELECT COUNT(*) FROM quality_flags"
        ).fetchone()[0],
        "zhf_only_parcels": conn.execute(
            "SELECT COUNT(*) FROM zhf_only_parcels"
        ).fetchone()[0],
        "model_targets": conn.execute(
            "SELECT COUNT(*) FROM model_targets"
        ).fetchone()[0],
        "parcels_con_alertas": conn.execute(
            "SELECT COUNT(*) FROM parcels WHERE tiene_alertas_calidad = 1"
        ).fetchone()[0],
    }
    conn.close()
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_DB))
    parser.add_argument("--processed", default=str(DEFAULT_PROCESSED))
    parser.add_argument("--version", default=DEFAULT_VERSION)
    args = parser.parse_args()
    stats = build(Path(args.output), Path(args.processed), args.version)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
