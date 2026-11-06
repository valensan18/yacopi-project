import json
from pathlib import Path

r = json.loads(Path("ml/artifacts/exp-valor-terreno-001/resumen.json").read_text(encoding="utf-8"))
print("PROTOCOLO V2 (independiente)")
for esc, datos in r.items():
    print(f"\n=== ESCENARIO {esc} (n={datos['n_predios']}) ===")
    for proto in ["predio", "espacial"]:
        p = datos["protocolos"][proto]
        print(f"  -- {proto}: train {p['n_train']} / test {p['n_test']}")
        for nombre, m in p["resultados"].items():
            if isinstance(m, list):
                continue
            print(
                f"     {nombre:34s} n={m['n']:>4d} MAE={m['mae_cop_ha']:>12,.0f} "
                f"R2={m['r2']:+.4f} MdAPE={m['mdape']:.3f}"
            )
