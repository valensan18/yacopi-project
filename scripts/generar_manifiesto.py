"""Genera el manifiesto de reproducibilidad de la entrega docente."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from catboost import CatBoostRegressor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "entrega_docente" / "manifiesto_reproducibilidad.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT
    ).stdout.strip()
    branch = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, cwd=ROOT
    ).stdout.strip()

    entradas = {
        "interseccion_terrenos_zhg_r1_yacopi.csv": sha(
            ROOT / "data" / "raw" / "interseccion_terrenos_zhg_r1_yacopi.csv"
        ),
        "zhf_yacopi.csv": sha(ROOT / "data" / "raw" / "zhf_yacopi.csv"),
    }

    splits_valor = {}
    for p in sorted((ROOT / "data" / "splits" / "valor").glob("*/*.json")):
        splits_valor[p.relative_to(ROOT).as_posix()] = sha(p)

    resultados = {}
    for esc in ["A", "B"]:
        r = json.loads(
            (ROOT / "ml" / "artifacts" / "exp-valor-terreno-001" / f"resultados_esc_{esc}.json")
            .read_text(encoding="utf-8")
        )
        resultados[f"valor_terreno_{esc}"] = {
            "protocolo": r.get("version_protocolo"),
            "n_predios": r["n_predios"],
            "protocolo_predio": {
                "n_train": r["protocolos"]["predio"]["n_train"],
                "n_test": r["protocolos"]["predio"]["n_test"],
                "metricas": {
                    k: {m: v.get(m) for m in ("mae_cop_ha", "r2")}
                    for k, v in r["protocolos"]["predio"]["resultados"].items()
                    if not k.startswith("_")
                },
            },
            "protocolo_espacial": {
                "n_train": r["protocolos"]["espacial"]["n_train"],
                "n_test": r["protocolos"]["espacial"]["n_test"],
                "metricas": {
                    k: {m: v.get(m) for m in ("mae_cop_ha", "r2")}
                    for k, v in r["protocolos"]["espacial"]["resultados"].items()
                    if not k.startswith("_")
                },
            },
        }

    zhg = json.loads(
        (ROOT / "ml" / "artifacts" / "exp-zhg-001" / "metrics.json").read_text(encoding="utf-8")
    )
    resultados["zhg_fase5"] = {
        "target": zhg["target"],
        "n_predios": zhg["n_predios"],
        "criterio_aceptacion": zhg["criterio_aceptacion"],
        "r2_zona_fuera": {
            k: round(v["zona"]["r2"], 4) for k, v in zhg["scenarios"].items()
        },
        "nota_integridad": "verificado por reentrenamiento completo (exp-zhg-rerun): "
        "las particiones congeladas actuales reproducen EXACTAMENTE las metricas "
        "historicas de Fase 5 (R2 zona fuera incluidos). La variante ponderada no "
        "se reentreno en esta entrega.",
    }

    manifiesto = {
        "proyecto": "Atlas Vivo — entrega docente de reproducibilidad",
        "generado_el": datetime.now(UTC).isoformat(),
        "commit": commit,
        "rama": branch,
        "entradas": entradas,
        "entornos": {
            "python": platform.python_version(),
            "sistema": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "catboost": CatBoostRegressor.get_version()
            if hasattr(CatBoostRegressor, "get_version")
            else "n/d",
        },
        "semillas": {
            "proxy_fase2": 42,
            "zhg_fase5": 42,
            "valor_terreno_rama_experimental": 20261023,
        },
        "particiones": {
            "proxy": "data/splits/{train,test}_{random,spatial}.json",
            "zhg": "data/splits/zhg/<objetivo>_n<size>/",
            "valor": "data/splits/valor/valor_terreno_ha_{A|B}_n<size>/",
            "valor_hashes": splits_valor,
        },
        "resultados_clave": resultados,
        "pruebas": {
            "pytest_backend_ml": "96 tests (ultima corrida documentada)",
            "vitest_frontend": "33 tests (ultima corrida documentada)",
        },
        "limitaciones": [
            "CSV originales no incluidos en el paquete (privados).",
            "Variante ZHG ponderada no reentrenada en esta entrega (metricas de su metrics.json).",
            "La demo RF no tiene evaluacion independiente por diseno.",
        ],
    }
    OUT.write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifiesto, indent=2, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    main()
