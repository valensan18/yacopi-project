"""Verificación de entradas: hashes, esquema y conteos de los CSV originales.

Uso:
  python scripts/verify_inputs.py [--manifest data/raw/data_manifest.json]

Compara los archivos de data/raw/ contra el manifiesto generado en la Fase 0.
No modifica los CSV originales. Termina con código de salida != 0 si alguna
verificación falla.
"""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DEFAULT = ROOT / "data" / "raw" / "data_manifest.json"

EXPECTED_HEADERS = {
    "interseccion_terrenos_zhg_r1_yacopi.csv": [
        "departamento", "municipio", "numero_predial_anterior", "numero_predial",
        "codigo_orip", "matricula_inmobiliaria", "codigo_lote", "destino_economico",
        "valor_avaluo", "area_terreno_m2", "area_en_zonageoeconomica_m2",
        "porcentaje_en_zonageo_respecto_suma", "area_construida_m2",
        "codigo_zona_geoeconomica", "valor_hectarea_agropecuario",
        "geometria_interseccion", "geometria",
    ],
    "zhf_yacopi.csv": [
        "id", "geom", "CODPRED", "AREA_TERRE", "TR_LATITUD", "TR_LONGITU",
        "TR_ESTE", "TR_NORTE", "ZHF_CODIGO", "ZHF_DISPON", "ZHF_INFLUE",
        "ZHF_USO_AC", "SINAP_NOMB", "SINAP_CATE", "AHT_VPOTEN", "FA_ELEMENT",
        "VUS_VOCACI", "UPS", "ZHG_CODIGO", "ZHG_VALOR_", "ZHG_VALOR1",
        "ZHG_SUBZON", "CLC_NIVEL1", "CLC_NIVEL2", "CLC_NIVEL3", "CLC_NIVEL4",
        "CLC_NIVEL5", "CLC_NIVEL6",
    ],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def count_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return sum(1 for _ in fh) - 1


def verify(manifest_path: Path) -> list[str]:
    errors: list[str] = []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent

    for entry in manifest["files"]:
        path = base / entry["name"]
        if not path.exists():
            errors.append(f"Falta {path}")
            continue
        actual_hash = sha256(path)
        if actual_hash != entry["sha256"]:
            errors.append(
                f"{entry['name']}: SHA-256 difiere (manifiesto {entry['sha256']}, "
                f"actual {actual_hash})"
            )
        size = path.stat().st_size
        if size != entry["size_bytes"]:
            errors.append(
                f"{entry['name']}: tamaño difiere (manifiesto {entry['size_bytes']}, "
                f"actual {size})"
            )
        expected_headers = EXPECTED_HEADERS.get(entry["name"])
        if expected_headers:
            with path.open("r", encoding="utf-8-sig", newline="") as fh:
                headers = next(csv.reader(fh))
            if headers != expected_headers:
                errors.append(
                    f"{entry['name']}: encabezados no coinciden\n"
                    f"  esperado: {expected_headers}\n  actual:   {headers}"
                )
        rows = count_rows(path)
        if rows != entry["rows_expected"]:
            errors.append(
                f"{entry['name']}: filas {rows}, esperadas {entry['rows_expected']}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(MANIFEST_DEFAULT))
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Manifiesto no encontrado: {manifest_path}")
        return 2

    errors = verify(manifest_path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: hashes, tamaños, encabezados y conteos de los CSV originales verificados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
