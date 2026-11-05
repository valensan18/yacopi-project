import sys

sys.path.insert(0, "ml/src")
from yacopi_ml.valor.dataset import cargar_zhf

zhf = cargar_zhf()
cols = [
    "zhf_codigo", "zhf_dispon", "zhf_influe", "zhf_uso_ac", "aht_vpoten",
    "fa_element", "vus_vocaci", "ups", "clc_nivel1", "clc_nivel2", "clc_nivel3",
    "clc_nivel4", "clc_nivel5", "clc_nivel6", "tr_latitud", "tr_longitu",
]
z = zhf.copy()
z["_area"] = z["area_terre"].fillna(0)
z_sorted = z.sort_values("_area", ascending=False)
antes = z_sorted.groupby("codpred").first()  # skipna=True (mezcla filas)
despues = z_sorted.groupby("codpred").first(skipna=False)  # fila real
cambios = {}
for c in cols:
    a = antes[c].fillna("__NA__")
    d = despues[c].fillna("__NA__")
    n = int((a != d).sum())
    cambios[c] = n
print("predios cuyo valor cambia con skipna=False (mezcla previa):")
for c, n in cambios.items():
    if n:
        print(f"  {c:15s} {n}")
total = int(
    (antes[cols].fillna("__NA__").values != despues[cols].fillna("__NA__").values)
    .any(axis=1)
    .sum()
)
print("predios afectados en >=1 columna:", total)
