import json
from pathlib import Path

ruta = Path("ml/artifacts/exp-valor-terreno-001/estabilidad_rf_v1.json")
r = json.loads(ruta.read_text(encoding="utf-8"))
res = r["resumen"]
print(
    "RF gana MAE en", res["rf_gana_mae_en"], "de 5 pliegues; "
    "gana MdAPE en", res["rf_gana_mdape_en"], "de 5"
)
print("R2: rf", {k: round(v, 3) for k, v in res["r2"]["rf"].items()},
      "| zhg", {k: round(v, 3) for k, v in res["r2"]["zhg"].items()})
print()
print("pliegues:")
for p in r["pliegues"]:
    rf = p["rf"]
    zh = p["referencia_zhg"]
    print(
        f"  seed {p['seed']}: RF MAE={rf['mae_cop_ha']:>10,.0f} MdAPE={rf['mdape']:.3f} "
        f"RMSE={rf['rmse_cop_ha']:>11,.0f} R2={rf['r2']:+.3f} | "
        f"ZHG MAE={zh['mae_cop_ha']:>10,.0f} MdAPE={zh['mdape']:.3f} "
        f"RMSE={zh['rmse_cop_ha']:>11,.0f}"
    )
print()
print("desglose por zona (test sellado espacial v2, RF):")
for z, v in r["desglose_error_sellado"]["por_zona"].items():
    print(f"  zona {z}: n={v['n']} MAE={v['mae']:>10,.0f} MdAPE={v['mdape']:.3f}")
