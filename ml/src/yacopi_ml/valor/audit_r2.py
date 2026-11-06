"""Auditoria de R2 del experimento VALOR_TERRENO_Ha (protocolo v2 independiente).

- Recalcula R2 en entrenamiento, test por predio y test espacial, cada uno
  entrenado con SU propio conjunto (sin contaminacion).
- Guarda predicciones alineadas (y_true, y_pred) por modelo y particion.
- Genera las 10 graficas obligatorias de la auditoria.
- Ejemplo didactico de R2 negativo con ENTRENAMIENTO y PRUEBA separados.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

from yacopi_ml.valor.dataset import construir_dataset, seleccionar_features
from yacopi_ml.valor.modelos import entrenar_modelos, metricas, predecir
from yacopi_ml.valor.splits import dividir_espacial, dividir_predios

ROOT = Path(__file__).resolve().parents[4]
FIG_DIR = ROOT / "entrega_docente" / "figuras"
AUDIT_DIR = ROOT / "ml" / "artifacts" / "exp-valor-terreno-001" / "audit_r2"

plt.rcParams.update({"font.size": 9, "figure.dpi": 130})


def evaluar_protocolo(ds: pd.DataFrame, tr: pd.DataFrame, te: pd.DataFrame,
                      X: pd.DataFrame, esc: str, etiqueta: str) -> list:
    ids_tr = set(tr["numero_predial"])
    ids_te = set(te["numero_predial"])
    assert not ids_tr & ids_te, f"solapamiento en {etiqueta}"

    X_tr = tr[X.columns]
    y_tr = tr["valor_terreno_ha"]
    X_te = te[X.columns]
    y_te = te["valor_terreno_ha"]

    modelos = entrenar_modelos(X_tr, y_tr)
    filas = []
    for nombre, m in modelos.items():
        pred_tr = predecir({nombre: m}, X_tr)[nombre]
        pred_te = predecir({nombre: m}, X_te)[nombre]
        filas.append({
            "escenario": esc,
            "modelo": nombre,
            "particion": etiqueta,
            "n": int(len(te)),
            **metricas(y_te, pred_te),
        })
        df2 = te[["numero_predial", "codigo_zona_dominante"]].copy()
        df2["y_true"] = y_te.to_numpy()
        df2["y_pred"] = pred_te
        df2["modelo"] = nombre
        df2["particion"] = etiqueta
        (AUDIT_DIR / f"preds_{esc}_{nombre}_{etiqueta}.csv").write_text(
            df2.to_csv(index=False), encoding="utf-8"
        )
        if etiqueta == "test_predio":
            filas.append({
                "escenario": esc,
                "modelo": nombre,
                "particion": "train",
                "n": int(len(tr)),
                **metricas(y_tr, pred_tr),
            })
    return filas


def auditoria_escenario(esc: str) -> pd.DataFrame:
    ds = construir_dataset(esc)
    X, y, _, _ = seleccionar_features(ds)
    ds = ds.assign(**{c: X[c] for c in X.columns})
    tr, te = dividir_predios(ds)
    tr_esp, te_esp = dividir_espacial(ds)

    assert not set(tr["numero_predial"]) & set(te["numero_predial"])
    assert not set(tr_esp["numero_predial"]) & set(te_esp["numero_predial"])

    filas = evaluar_protocolo(ds, tr, te, X, esc, "test_predio")
    filas += evaluar_protocolo(ds, tr_esp, te_esp, X, esc, "test_espacial")
    return pd.DataFrame(filas)


def figuras(tabla: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # 01: R2 comparativo por modelo y escenario (particiones independientes)
    for esc, g in tabla.groupby("escenario"):
        piv = g.pivot_table(index="modelo", columns="particion", values="r2")
        piv = piv.reindex(columns=["test_predio", "test_espacial"])
        piv.plot.bar(rot=20, figsize=(8, 4.5), title=f"R² por modelo y partición — escenario {esc}")
        plt.axhline(0, color="gray", lw=0.8)
        plt.tight_layout()
        plt.savefig(FIG_DIR / f"fig01_r2_comparativo_esc_{esc}.png")
        plt.close()

    # 02: train vs test predio
    for esc, g in tabla.groupby("escenario"):
        tr2 = g[g.particion == "train"].set_index("modelo")["r2"]
        te2 = g[g.particion == "test_predio"].set_index("modelo")["r2"]
        pd.DataFrame({"train": tr2, "test_predio": te2}).plot.bar(
            rot=20, figsize=(8, 4.5), title=f"R² entrenamiento vs prueba — escenario {esc}"
        )
        plt.axhline(0, color="gray", lw=0.8)
        plt.tight_layout()
        plt.savefig(FIG_DIR / f"fig02_train_vs_test_esc_{esc}.png")
        plt.close()

    # 03-05: reales vs predichos, residuos vs predichos, distribucion residuos (CatBoost)
    for esc in ["A", "B"]:
        for split in ["test_predio", "test_espacial"]:
            p = AUDIT_DIR / f"preds_{esc}_catboost_{split}.csv"
            if not p.exists():
                continue
            d = pd.read_csv(p)
            fig, axs = plt.subplots(1, 3, figsize=(13, 4))
            axs[0].scatter(d["y_true"], d["y_pred"], s=6, alpha=0.5)
            lim = [0, d[["y_true", "y_pred"]].max().max() * 1.02]
            axs[0].plot(lim, lim, "r--", lw=1)
            axs[0].set_xlim(lim)
            axs[0].set_ylim(lim)
            axs[0].set_xlabel("y real (COP/ha)")
            axs[0].set_ylabel("y predicho (COP/ha)")
            axs[0].set_title(f"Reales vs predichos — {esc} {split}")
            r = d["y_true"] - d["y_pred"]
            axs[1].scatter(d["y_pred"], r, s=6, alpha=0.5)
            axs[1].axhline(0, color="r", lw=1)
            axs[1].set_xlabel("y predicho")
            axs[1].set_ylabel("residuo")
            axs[1].set_title("Residuos vs predicciones")
            axs[2].hist(r, bins=40)
            axs[2].set_xlabel("residuo")
            axs[2].set_title("Distribución de residuos")
            plt.tight_layout()
            plt.savefig(FIG_DIR / f"fig03_05_reales_residuos_{esc}_{split}.png")
            plt.close()

    # 06: errores por zona, calculados desde las predicciones v2 de esta
    # auditoria (CatBoost, test por predio) con la zona dominante por area.
    for esc in ["A", "B"]:
        p = AUDIT_DIR / f"preds_{esc}_catboost_test_predio.csv"
        if not p.exists():
            continue
        d = pd.read_csv(p)
        zonas = d.groupby("codigo_zona_dominante")[["y_true", "y_pred"]].apply(
            lambda g: mean_absolute_error(g["y_true"], g["y_pred"])
        )
        plt.figure(figsize=(8, 4))
        plt.bar(zonas.index.astype(str), zonas.values)
        plt.title(f"MAE por zona dominante (CatBoost, test por predio v2) — escenario {esc}")
        plt.xlabel("Zona")
        plt.ylabel("MAE (COP/ha)")
        plt.tight_layout()
        plt.savefig(FIG_DIR / f"fig06_errores_por_zona_esc_{esc}.png")
        plt.close()

    # 07: distribucion del objetivo por escenario
    for esc in ["A", "B"]:
        ds = construir_dataset(esc)
        v = ds["valor_terreno_ha"]
        plt.figure(figsize=(8, 4))
        plt.hist(np.log10(v), bins=40)
        plt.title(f"Distribución de VALOR_TERRENO_Ha (log10) — escenario {esc} (n={len(v)})")
        plt.xlabel("log10(COP/ha)")
        plt.tight_layout()
        plt.savefig(FIG_DIR / f"fig07_distribucion_objetivo_esc_{esc}.png")
        plt.close()

    # 08: influencia de superficies pequenas
    plt.figure(figsize=(8, 4))
    ds = construir_dataset("A")
    peque = ds[ds["area_terreno_m2"] < 2000]
    grande = ds[ds["area_terreno_m2"] >= 2000]
    plt.boxplot(
        [peque["valor_terreno_ha"], grande["valor_terreno_ha"]],
        tick_labels=["< 0,2 ha", ">= 0,2 ha"],
    )
    plt.title("VALOR_TERRENO_Ha según tamaño del predio (escenario A)")
    plt.ylabel("COP/ha")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig08_influencia_areas_pequenas.png")
    plt.close()

    # 09: comparacion frente al baseline de la media
    for esc in ["A", "B"]:
        g = tabla[(tabla.escenario == esc) & (tabla.particion == "test_predio")]
        base = g[g.modelo == "dummy_media"]["r2"].iloc[0]
        g = g[g.modelo != "dummy_media"]
        plt.figure(figsize=(8, 4))
        plt.bar(g["modelo"], g["r2"])
        plt.axhline(base, color="gray", ls="--", label=f"R² dummy (media) = {base:.2f}")
        plt.axhline(0, color="red", lw=0.8)
        plt.title(f"R² en test por predio frente al baseline — escenario {esc}")
        plt.xticks(rotation=20)
        plt.legend()
        plt.tight_layout()
        plt.savefig(FIG_DIR / f"fig09_vs_baseline_esc_{esc}.png")
        plt.close()

    # 10: MAE y RMSE por escenario
    g = tabla[tabla.particion == "test_predio"]
    piv = g.pivot_table(index="modelo", columns="escenario", values=["mae_cop_ha", "rmse_cop_ha"])
    piv.plot.bar(rot=20, figsize=(9, 4.5), title="MAE y RMSE en test por predio, por escenario")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig10_mae_rmse_por_escenario.png")
    plt.close()


def ejemplo_didactico() -> None:
    """R2 negativo SIN error de programacion, con train y test separados.

    Ajusta una recta sobre la rama izquierda de una parabola y evalua sobre
    la rama derecha (fuera del rango de entrenamiento): la extrapolacion
    lineal falla y el R2 en prueba es claramente negativo.
    """
    rng = np.random.default_rng(7)
    x_tr = np.linspace(0, 2, 60)
    y_tr = (x_tr - 3) ** 2 + rng.normal(0, 0.2, size=60)
    x_te = np.linspace(6, 10, 60)
    y_te = (x_te - 3) ** 2 + rng.normal(0, 0.2, size=60)

    m = LinearRegression().fit(x_tr.reshape(-1, 1), y_tr)
    pred_te = m.predict(x_te.reshape(-1, 1))
    r2 = r2_score(y_te, pred_te)
    assert r2 < 0, f"el ejemplo debe producir R2 negativo, obtuvo {r2}"

    plt.figure(figsize=(7, 4))
    plt.scatter(x_tr, y_tr, s=10, label="entrenamiento (x ∈ [0, 2])")
    plt.scatter(x_te, y_te, s=10, label="prueba (x ∈ [6, 10])")
    xs = np.linspace(0, 10, 50)
    plt.plot(xs, m.predict(xs.reshape(-1, 1)), color="red",
             label=f"recta ajustada; R² prueba = {r2:.2f}")
    plt.title("Ejemplo didáctico: R² negativo con train/test separados")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig00_ejemplo_r2_negativo.png")
    plt.close()
    (AUDIT_DIR / "ejemplo_didactico.json").write_text(
        json.dumps(
            {
                "descripcion": "Regresion lineal ajustada en x en [0,2] y evaluada en "
                "x en [6,10] sobre una parabola: la extrapolacion es peor que la media "
                "de la prueba (R2 negativo) sin error de implementacion.",
                "n_train": int(len(x_tr)),
                "n_test": int(len(x_te)),
                "r2_test": float(r2),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    tabla_a = auditoria_escenario("A")
    tabla_b = auditoria_escenario("B")
    tabla = pd.concat([tabla_a, tabla_b], ignore_index=True)
    (AUDIT_DIR / "tabla_r2_completa.csv").write_text(
        tabla.to_csv(index=False), encoding="utf-8"
    )
    figuras(tabla)
    ejemplo_didactico()
    print(tabla.to_string(index=False))
    ejemplo = json.loads(
        (AUDIT_DIR / "ejemplo_didactico.json").read_text(encoding="utf-8")
    )
    print("ejemplo didactico R2 test =", ejemplo["r2_test"])


if __name__ == "__main__":
    main()
