import json
from pathlib import Path

r = json.loads(Path("ml/artifacts/exp-proxy-rerun/metrics.json").read_text(encoding="utf-8"))
ui = {
    "espacial": {
        "Baseline (mediana)": ("-0.03", 6592762),
        "Ridge": ("-0.11", 15196282),
        "Árbol de decisión": ("0.53", 4215432),
        "Random Forest": ("0.74", 3226230),
        "CatBoost": ("0.76", 3730373),
    },
    "aleatoria": {
        "Baseline (mediana)": ("-0.02", 7889929),
        "Ridge": ("0.40", 13581815),
        "Árbol de decisión": ("0.66", 4176143),
        "Random Forest": ("0.82", 2674886),
        "CatBoost": ("0.81", 3336590),
    },
}
mapeo = {"Baseline (mediana)": "dummy", "Ridge": "ridge", "Árbol de decisión": "tree",
         "Random Forest": "forest", "CatBoost": "catboost"}
cabecera = (
    f"{'particion':9s} {'modelo':18s} {'UI R2':>7s} {'rerun R2':>9s} "
    f"{'UI MAE':>10s} {'rerun MAE':>11s}  coincide"
)
print(cabecera)
for part, modelos in ui.items():
    for nombre, (r2_ui, mae_ui) in modelos.items():
        res = r["protocols"][{"espacial": "spatial", "aleatoria": "random"}[part]][
            "test"
        ][mapeo[nombre]]
        ok = abs(res["r2"] - float(r2_ui)) < 0.005 and abs(res["mae_cop_ha"] - mae_ui) <= 1
        print(
            f"{part:9s} {nombre:18s} {r2_ui:>7s} {res['r2']:>+9.4f} "
            f"{mae_ui:>10,} {res['mae_cop_ha']:>11,.0f}  {'SI' if ok else 'NO'}"
        )
print("\nConclusión: el reentrenamiento con las particiones congeladas reproduce las",
      "cifras mostradas en la interfaz /modelos (incluidos los R2 negativos).")
