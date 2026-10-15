"""Particiones del experimento ZHG (Fase 5, escenarios 1–4).

- Escenario 1: aleatoria por filas (solo referencia comparativa).
- Escenario 2: agrupada por PREDIO (nunca el mismo predio en train/test).
- Escenario 3: espacial por bloques geográficos (KMeans sobre coordenadas
  reales de predio).
- Escenario 4: dejando ZONAS geoeconómicas completas fuera (grupos = zona
  dominante; con 11 zonas se reporta variabilidad alta).

Todos los escenarios se congelan con seed 42 y se validan: sin solapes de
predio ni de zona entre entrenamiento y prueba.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupShuffleSplit, train_test_split

SPLITS_DIR = Path(__file__).resolve().parents[4] / "data" / "splits" / "zhg"
SEED = 42
TEST_SIZE = 0.2
N_CLUSTERS = 25


def _hash_ids(ids: list[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(ids)).encode()).hexdigest()


def _write(splits_dir: Path, name: str, ids: list[str]) -> dict:
    path = splits_dir / f"{name}.json"
    payload = {"seed": SEED, "n": len(ids), "ids": ids, "sha256": _hash_ids(ids)}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {"n": len(ids), "sha256": payload["sha256"]}


def make_zhg_splits(
    df: pd.DataFrame, splits_dir: Path = SPLITS_DIR
) -> dict:
    splits_dir.mkdir(parents=True, exist_ok=True)
    ids = df["public_id"].astype(str).tolist()
    ids_arr = np.asarray(ids, dtype=object)
    zona = df["zona_dominante"].astype(str).tolist()

    # Escenario 1: filas
    train_r, test_r = train_test_split(
        ids_arr, test_size=TEST_SIZE, random_state=SEED, shuffle=True
    )

    # Escenario 2: grupos por predio (el predio es único por fila aquí,
    # así que equivale a una partición por identificador)
    splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEED)
    train_idx, test_idx = next(splitter.split(ids_arr, groups=ids_arr))
    train_p, test_p = ids_arr[train_idx], ids_arr[test_idx]

    # Escenario 3: bloques espaciales (SOLO predios con coordenadas válidas;
    # los predios sin coordenadas quedan excluidos de este escenario)
    coords_raw = df[["tr_longitud", "tr_latitud"]].to_numpy(dtype=float)
    valid_coords = ~(np.isnan(coords_raw).any(axis=1))
    ids_spatial = ids_arr[valid_coords]
    coords = coords_raw[valid_coords]
    clusters = KMeans(n_clusters=N_CLUSTERS, random_state=SEED, n_init=10).fit(coords)
    spatial_splitter = GroupShuffleSplit(
        n_splits=1, test_size=TEST_SIZE, random_state=SEED
    )
    tr_idx, te_idx = next(spatial_splitter.split(ids_spatial, groups=clusters.labels_))
    train_s, test_s = ids_spatial[tr_idx], ids_spatial[te_idx]

    # Escenario 4: zonas completas fuera
    zona_arr = np.asarray(zona, dtype=object)
    zone_splitter = GroupShuffleSplit(
        n_splits=1, test_size=TEST_SIZE, random_state=SEED
    )
    tr_idx, te_idx = next(zone_splitter.split(ids_arr, groups=zona_arr))
    train_z, test_z = ids_arr[tr_idx], ids_arr[te_idx]

    # Integridad
    assert not set(train_r) & set(test_r)
    assert not set(train_p) & set(test_p)
    assert not set(train_s) & set(test_s)
    assert not set(train_z) & set(test_z)
    zonas_train = set(zona_arr[np.isin(ids_arr, train_z)])
    zonas_test = set(zona_arr[np.isin(ids_arr, test_z)])
    assert not zonas_train & zonas_test, "zonas cruzadas entre train y test"

    manifest = {
        "filas_train": _write(splits_dir, "train_filas", list(train_r)),
        "filas_test": _write(splits_dir, "test_filas", list(test_r)),
        "predio_train": _write(splits_dir, "train_predio", list(train_p)),
        "predio_test": _write(splits_dir, "test_predio", list(test_p)),
        "espacial_train": _write(splits_dir, "train_espacial", list(train_s)),
        "espacial_test": _write(splits_dir, "test_espacial", list(test_s)),
        "zona_train": _write(splits_dir, "train_zona", list(train_z)),
        "zona_test": _write(splits_dir, "test_zona", list(test_z)),
        "zonas_en_train": sorted(zonas_train),
        "zonas_en_test": sorted(zonas_test),
        "excluidos_espacial_sin_coordenadas": int((~valid_coords).sum()),
    }
    return {
        "filas": (list(train_r), list(test_r)),
        "predio": (list(train_p), list(test_p)),
        "espacial": (list(train_s), list(test_s)),
        "zona": (list(train_z), list(test_z)),
        "manifest": manifest,
    }
