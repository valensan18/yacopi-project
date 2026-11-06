"""Particiones reproducibles del experimento VALOR_TERRENO_Ha (experimental)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[4]
SPLITS_DIR = ROOT / "data" / "splits" / "valor"

SEED = 20261023
TEST_SIZE = 0.2


def dividir_predios(
    ds: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Particion aleatoria por predio (un predio jamas en train y test)."""
    idx = ds.index.to_numpy()
    train_idx, test_idx = train_test_split(
        idx, test_size=TEST_SIZE, random_state=SEED, shuffle=True
    )
    return ds.loc[train_idx], ds.loc[test_idx]


def dividir_espacial(ds: pd.DataFrame, seed: int = SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Particion espacial por bloques geograficos (generalizacion real).

    Los predios sin coordenadas quedan en train (no se evaluan espacialmente).
    """
    lat = ds["tr_latitud"].to_numpy()
    lon = ds["tr_longitud"].to_numpy()
    valido = ~(np.isnan(lat) | np.isnan(lon))
    n_bins = 6
    lat_bin = pd.cut(lat[valido], bins=n_bins, labels=False)
    lon_bin = pd.cut(lon[valido], bins=n_bins, labels=False)
    bloques = pd.Series(list(zip(lat_bin, lon_bin, strict=False)), index=ds.index[valido])
    rng = np.random.default_rng(seed)
    bloques_orden = rng.permutation(bloques.unique())
    n_test = max(1, int(round(len(bloques_orden) * TEST_SIZE)))
    test_bloques = set(map(tuple, bloques_orden[:n_test]))
    es_test = bloques.isin(test_bloques)
    test_idx = es_test[es_test].index
    train_idx = ds.index.difference(test_idx)
    return ds.loc[train_idx], ds.loc[test_idx]


def guardar_particiones(escenario: str, ds: pd.DataFrame) -> dict:
    """Guarda particiones versionadas y devuelve rutas."""
    carpeta = SPLITS_DIR / f"valor_terreno_ha_{escenario}_n{len(ds)}"
    carpeta.mkdir(parents=True, exist_ok=True)

    salida = {}
    for nombre, (tr, te) in {
        "predio": dividir_predios(ds),
        "espacial": dividir_espacial(ds),
    }.items():
        for sub, d in (("train", tr), ("test", te)):
            ruta = carpeta / f"{sub}_{nombre}.json"
            ruta.write_text(
                json.dumps(
                    {
                        "seed": SEED,
                        "escenario": escenario,
                        "tamano_train": len(d),
                        "ids": d["numero_predial"].tolist(),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            salida[f"{sub}_{nombre}"] = ruta.relative_to(ROOT).as_posix()
    return salida
