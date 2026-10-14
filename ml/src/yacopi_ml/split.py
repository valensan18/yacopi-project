"""Particiones reproducibles: aleatoria por predio y espacial por grupos.

- Partición ALEATORIA: 85/15 por predio (seed fija).
- Partición ESPACIAL: agrupación KMeans sobre coordenadas (construida SIN
  mirar la etiqueta) + GroupShuffleSplit 85/15 sobre grupos, de modo que
  ningún grupo de predios vecinos quede partido entre train y test.

Los IDs de cada partición se congelan en `data/splits/` (gitignored) con
hash SHA-256 para trazabilidad.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupShuffleSplit, train_test_split

SPLITS_DIR = Path(__file__).resolve().parents[3] / "data" / "splits"
SEED = 42
TEST_SIZE = 0.15
N_CLUSTERS = 25


def _hash_ids(ids: list[str]) -> str:
    payload = json.dumps(sorted(ids)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _write(splits_dir: Path, name: str, ids: list[str]) -> dict:
    path = splits_dir / f"{name}.json"
    payload = {
        "seed": SEED,
        "n": len(ids),
        "ids": ids,
        "sha256": _hash_ids(ids),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {"archivo": str(path), "n": len(ids), "sha256": payload["sha256"]}


def spatial_groups(coords: pd.DataFrame) -> np.ndarray:
    """Clusters KMeans sobre coordenadas (sin usar la etiqueta)."""
    X = coords[["tr_longitud", "tr_latitud"]].to_numpy(dtype=float)
    kmeans = KMeans(
        n_clusters=N_CLUSTERS, random_state=SEED, n_init=10
    ).fit(X)
    return kmeans.labels_


def make_splits(ids: list[str], coords: pd.DataFrame, splits_dir: Path = SPLITS_DIR):
    """Genera y congela las particiones aleatoria y espacial.

    Devuelve un diccionario con los cuatro conjuntos de IDs.
    """
    splits_dir.mkdir(parents=True, exist_ok=True)
    ids_arr = np.asarray(ids, dtype=object)

    # --- Aleatoria por predio ---
    train_rnd, test_rnd = train_test_split(
        ids_arr, test_size=TEST_SIZE, random_state=SEED, shuffle=True
    )

    # --- Espacial por grupos ---
    groups = spatial_groups(coords)
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=TEST_SIZE, random_state=SEED
    )
    train_idx, test_idx = next(splitter.split(ids_arr, groups=groups))
    train_spa = ids_arr[train_idx]
    test_spa = ids_arr[test_idx]

    # Verificación de integridad de las particiones
    assert len(set(ids)) == len(ids), "IDs duplicados antes de particionar"
    assert not set(train_rnd) & set(test_rnd), "solape en partición aleatoria"
    assert not set(train_spa) & set(test_spa), "solape en partición espacial"
    train_groups = set(groups[train_idx])
    test_groups = set(groups[test_idx])
    assert not train_groups & test_groups, "grupos espaciales cruzados"

    manifest = {
        "train_random": _write(splits_dir, "train_random", list(train_rnd)),
        "test_random": _write(splits_dir, "test_random", list(test_rnd)),
        "train_spatial": _write(splits_dir, "train_spatial", list(train_spa)),
        "test_spatial": _write(splits_dir, "test_spatial", list(test_spa)),
        "n_clusters": N_CLUSTERS,
        "n_grupos_train_espacial": len(train_groups),
        "n_grupos_test_espacial": len(test_groups),
    }
    return {
        "train_random": list(train_rnd),
        "test_random": list(test_rnd),
        "train_spatial": list(train_spa),
        "test_spatial": list(test_spa),
        "manifest": manifest,
    }


def load_splits(splits_dir: Path = SPLITS_DIR) -> dict:
    """Carga particiones previamente congeladas."""
    out = {}
    for name in ("train_random", "test_random", "train_spatial", "test_spatial"):
        out[name] = json.loads(
            (splits_dir / f"{name}.json").read_text(encoding="utf-8")
        )["ids"]
    return out
