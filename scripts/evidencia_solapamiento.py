"""Evidencia del solapamiento en la validacion espacial original.

En la version original, los modelos se entrenaban con tr_predio y se
evaluaban sobre te_esp: se calcula el solapamiento real de IDs para A y B.
"""

from __future__ import annotations

import json
from pathlib import Path

from yacopi_ml.valor.dataset import construir_dataset
from yacopi_ml.valor.splits import dividir_espacial, dividir_predios

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ml" / "artifacts" / "exp-valor-terreno-001" / "historial_no_independiente_v1"


def reporte_esc(esc: str) -> dict:
    ds = construir_dataset(esc)
    tr_predio, te_predio = dividir_predios(ds)
    tr_esp, te_esp = dividir_espacial(ds)

    set_tr = set(tr_predio["numero_predial"])
    set_te_esp = set(te_esp["numero_predial"])
    set_te_predio = set(te_predio["numero_predial"])
    set_tr_esp = set(tr_esp["numero_predial"])

    solape = set_tr & set_te_esp
    solape_te_predio_esp = set_te_predio & set_te_esp
    solape_tr_esp_te_esp = set_tr_esp & set_te_esp

    reporte = {
        "escenario": esc,
        "n_tr_predio": len(set_tr),
        "n_te_esp": len(set_te_esp),
        "solape_tr_predio_y_te_esp": {
            "n_ids": len(solape),
            "pct_de_te_esp": round(100 * len(solape) / len(set_te_esp), 2),
            "pct_de_tr_predio": round(100 * len(solape) / len(set_tr), 2),
        },
        "solape_te_predio_y_te_esp": len(solape_te_predio_esp),
        "solape_tr_esp_y_te_esp": len(solape_tr_esp_te_esp),
        "ejemplos_ids": sorted(solape)[:5],
    }
    return reporte


def main() -> None:
    out = [reporte_esc("A"), reporte_esc("B")]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "evidencia_solapamiento.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
