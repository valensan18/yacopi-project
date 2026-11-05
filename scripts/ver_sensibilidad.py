import json
from pathlib import Path

ruta = Path(
    "ml/artifacts/exp-valor-terreno-001/sensibilidad/sensibilidad_area_terreno.json"
)
r = json.loads(ruta.read_text(encoding="utf-8"))
print("SENSIBILIDAD area_terreno_m2 (escenario A, protocolo v2)")
for variante, modelos in r.items():
    if variante in ("escenario", "protocolo"):
        continue
    print(" ", variante)
    for m, protos in modelos.items():
        print(
            f"    {m:14s} predio R2={protos['predio']['r2']:+.3f} "
            f"MAE={protos['predio']['mae_cop_ha']:>10,.0f} | espacial "
            f"R2={protos['espacial']['r2']:+.3f} MAE={protos['espacial']['mae_cop_ha']:>10,.0f}"
        )
