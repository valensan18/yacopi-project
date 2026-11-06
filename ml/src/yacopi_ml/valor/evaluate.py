"""Desgloses del experimento VALOR_TERRENO_Ha (experimental).

- Correlacion feature-objetivo (auditoria de fuga).
- Desempeno CatBoost por zona geoeconomica, rango de area y destino economico.
- Analisis de sensibilidad a valores extremos (> 50 M COP/ha).
"""

from __future__ import annotations

import json
from pathlib import Path

from catboost import CatBoostRegressor

from yacopi_ml.valor.dataset import CATEGORICAS, construir_dataset, seleccionar_features
from yacopi_ml.valor.modelos import SEED, metricas
from yacopi_ml.valor.splits import dividir_espacial, dividir_predios

ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = ROOT / "ml" / "artifacts" / "exp-valor-terreno-001"
UMBRAL_EXTREMO = 50_000_000.0


def rango_area(m2: float) -> str:
    if m2 < 2_000:
        return "< 0.2 ha"
    if m2 < 20_000:
        return "0.2 - 2 ha"
    if m2 < 100_000:
        return "2 - 10 ha"
    return ">= 10 ha"


def evaluar_escenario(esc: str) -> dict:
    ds = construir_dataset(esc)
    X, y, meta, _ = seleccionar_features(ds)
    ds = ds.assign(**{c: X[c] for c in X.columns})
    tr, te = dividir_predios(ds)

    # Correlacion feature-objetivo (SIN variables zonales/avalúo)
    corr = {}
    for c in X.columns:
        if X[c].dtype.kind in "biufc":
            corr[c] = float(ds[[c, "valor_terreno_ha"]].corr(numeric_only=True).iloc[0, 1])
    corr_ord = sorted(corr.items(), key=lambda t: -abs(t[1]))

    cat_idx = [X.columns.get_loc(c) for c in CATEGORICAS if c in X.columns]
    cat = CatBoostRegressor(
        iterations=1000, depth=6, learning_rate=0.05, loss_function="RMSE",
        random_seed=SEED, cat_features=cat_idx, verbose=False,
    )
    cat.fit(tr[X.columns], tr["valor_terreno_ha"].to_numpy())
    te = te.copy()
    te["pred"] = cat.predict(te[X.columns])

    out: dict = {"correlaciones_top": corr_ord[:12]}

    # Por zona
    zonas = {}
    for zona, g in te.groupby("codigo_zona_dominante"):
        zonas[str(zona)] = metricas(g["valor_terreno_ha"], g["pred"])
    out["por_zona"] = zonas

    # Por rango de area
    te["rango_area"] = te["area_terreno_m2"].apply(rango_area)
    rangos = {}
    for rango, g in te.groupby("rango_area"):
        rangos[rango] = metricas(g["valor_terreno_ha"], g["pred"])
    out["por_rango_area"] = rangos

    # Por destino economico
    destinos = {}
    for destino, g in te.groupby("destino_economico"):
        if len(g) >= 10:
            destinos[str(destino)] = metricas(g["valor_terreno_ha"], g["pred"])
    out["por_destino"] = destinos

    # Sensibilidad: sin valores extremos
    out["extremos"] = {
        "n_test": int(len(te)),
        "n_extremos_gt_50M": int((te["valor_terreno_ha"] > UMBRAL_EXTREMO).sum()),
        "max_valor_ha_test": float(te["valor_terreno_ha"].max()),
        "metricas_sin_extremos": metricas(
            te.loc[te["valor_terreno_ha"] <= UMBRAL_EXTREMO, "valor_terreno_ha"],
            te.loc[te["valor_terreno_ha"] <= UMBRAL_EXTREMO, "pred"],
        ),
    }

    # Caracterizacion de los dos tests (predio vs espacial)
    _, te_esp = dividir_espacial(ds)
    out["test_espacial_max_valor_ha"] = float(te_esp["valor_terreno_ha"].max())
    out["test_predio_max_valor_ha"] = float(te["valor_terreno_ha"].max())

    # Leave-one-zone-out (LOZO): el modelo nunca ve la zona evaluada.
    # Se evaluan TODAS las zonas (sin umbral de tamano) para que la suma de
    # registros coincida con el total del escenario.
    lozo = {}
    for zona, g in ds.groupby("codigo_zona_dominante"):
        tr_z = ds[ds["codigo_zona_dominante"] != zona]
        assert not set(tr_z["numero_predial"]) & set(g["numero_predial"])
        cat_z = CatBoostRegressor(
            iterations=1000, depth=6, learning_rate=0.05, loss_function="RMSE",
            random_seed=SEED, cat_features=cat_idx, verbose=False,
        )
        cat_z.fit(tr_z[X.columns], tr_z["valor_terreno_ha"].to_numpy())
        g = g.copy()
        g["pred"] = cat_z.predict(g[X.columns])
        lozo[str(zona)] = metricas(g["valor_terreno_ha"], g["pred"])
    out["lozo_por_zona"] = lozo
    out["lozo_suma_n"] = int(sum(v["n"] for v in lozo.values()))

    (ARTIFACTS / f"desgloses_esc_{esc}.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out


def main() -> None:
    todo = {}
    for esc in ["A", "B"]:
        r = evaluar_escenario(esc)
        todo[esc] = r
        print(f"=== {esc}: extremos={r['extremos']['n_extremos_gt_50M']} "
              f"max_test={r['extremos']['max_valor_ha_test']:.0f} "
              f"sin_extremos MAE={r['extremos']['metricas_sin_extremos']['mae_cop_ha']:.0f} "
              f"R2={r['extremos']['metricas_sin_extremos']['r2']:.3f}")
        print("  por_zona:", {k: round(v["mae_cop_ha"]) for k, v in r["por_zona"].items()})
        print("  por_rango:", {k: round(v["mae_cop_ha"]) for k, v in r["por_rango_area"].items()})
        print("  corr top:", [(k, round(v, 2)) for k, v in r["correlaciones_top"][:6]])
        if "lozo_por_zona" in r:
            print(
                "  LOZO por zona MAE:",
                {k: round(v["mae_cop_ha"]) for k, v in r["lozo_por_zona"].items()},
            )
    (ARTIFACTS / "desgloses.json").write_text(
        json.dumps(todo, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
