"""Verificacion de integridad del artefacto exp-valor-v1 (auditoria preproduccion).

Comprueba:
- Pertenencia: todos los public_id de features.json estan en la cohorte del
  ajuste final (los mismos 4.676 predios del escenario A).
- Integridad: hashes sha256 de cada archivo del artefacto.
- Correspondencia artefacto-manifiesto-backend: campos que exige el servicio
  (rol, status, model_id, version, schema orden).
- Privacidad: ausencia de numero_predial, valor_avaluo y coordenadas fuera
  de las features permitidas... (las coordenadas son feature legitima; se
  verifica que NO exista numero_predial ni valor_avaluo en features.json).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))
sys.path.insert(0, str(ROOT / "backend"))

ART = ROOT / "deploy-model" / "exp-valor-v1"

EXCLUIDAS = [
    "numero_predial", "parcel_source_id", "valor_avaluo",
    "valor_avaluo_total_cop", "matricula_inmobiliaria", "codigo_orip",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verificar() -> dict:
    out: dict = {}
    manifest = json.loads((ART / "manifest.json").read_text(encoding="utf-8"))
    schema = json.loads((ART / "feature_schema.json").read_text(encoding="utf-8"))
    features = json.loads((ART / "features.json").read_text(encoding="utf-8"))

    # 1) pertenencia al ajuste final
    from yacopi_ml.valor.dataset import construir_dataset

    ds = construir_dataset("A")
    import hashlib as _h

    def pid(source: str) -> str:
        return "p_" + _h.sha256(source.encode("utf-8")).hexdigest()[:16]

    ids_ajuste = {pid(s) for s in ds["numero_predial"]}
    ids_features = set(features.keys())
    out["pertenencia_ajuste"] = {
        "n_features": len(features),
        "n_ajuste": len(ds),
        "n_manifest": manifest.get("n_fit"),
        "ids_no_ajustables": sorted(ids_features - ids_ajuste)[:10],
        "ids_del_ajuste_sin_feature": sorted(ids_ajuste - ids_features)[:10],
        "coincidencia_total": ids_features == ids_ajuste,
    }

    # 2) hashes
    out["hashes_sha256"] = {
        p.name: sha(p)
        for p in sorted(ART.iterdir())
        if p.is_file() and p.name != "MODEL_CARD.md"
    }

    # 3) correspondencia manifiesto-backend
    out["manifiesto_backend"] = {
        "model_id": manifest.get("model_id"),
        "model_version": manifest.get("model_version"),
        "rol_esperado": "demostracion_academica",
        "rol": manifest.get("rol"),
        "status_esperado": "experimental_demo",
        "status": manifest.get("status"),
        "target": manifest.get("target"),
        "n_fit": manifest.get("n_fit"),
        "orden_schema": schema.get("orden"),
        "numericas": schema.get("numericas"),
        "categoricas": schema.get("categoricas"),
        "seed": manifest.get("seed"),
        "hiperparametros": manifest.get("hiperparametros"),
    }

    # 4) privacidad: los valores de features son solo las columnas del schema
    claves_extra = set()
    campos_sensibles = []
    for _pid, entry in features.items():
        fila = entry.get("features", {})
        claves_extra |= set(fila.keys()) - set(schema["orden"])
        for campo in EXCLUIDAS:
            if campo in fila or campo in entry:
                campos_sensibles.append(campo)
    out["privacidad_features"] = {
        "claves_extra_fuera_del_schema": sorted(claves_extra),
        "campos_sensibles_encontrados": sorted(set(campos_sensibles)),
        "ids_solo_public_id": all(
            k.startswith("p_") and len(k) == 18 for k in features
        ),
        "tamano_mb": round((ART / "features.json").stat().st_size / 1e6, 2),
    }
    return out


if __name__ == "__main__":
    resultado = verificar()
    print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))
