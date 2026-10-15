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

SPLITS_BASE = Path(__file__).resolve().parents[4] / "data" / "splits" / "zhg"
SEED = 42
TEST_SIZE = 0.2
N_CLUSTERS = 25

SCENARIO_FILES = {
    "filas": ("train_filas", "test_filas"),
    "predio": ("train_predio", "test_predio"),
    "espacial": ("train_espacial", "test_espacial"),
    "zona": ("train_zona", "test_zona"),
}


def splits_dir_for(target_name: str, n_rows: int) -> Path:
    """Directorio versionado por firma del dataset (inmutable por diseño):
    cada combinación objetivo+tamaño conserva sus propias particiones."""
    return SPLITS_BASE / f"{target_name}_n{n_rows}"


def _hash_ids(ids: list[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(ids)).encode()).hexdigest()


def _write(splits_dir: Path, name: str, ids: list[str]) -> dict:
    path = splits_dir / f"{name}.json"
    payload = {"seed": SEED, "n": len(ids), "ids": ids, "sha256": _hash_ids(ids)}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {"n": len(ids), "sha256": payload["sha256"]}


def make_zhg_splits(
    df: pd.DataFrame, splits_dir: Path
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


def get_or_create_zhg_splits(
    df: pd.DataFrame, target_name: str, splits_dir: Path | None = None
) -> dict:
    """Carga particiones versionadas si existen; si no, las genera UNA vez.

    Con esto ningún experimento ni prueba sobrescribe particiones ajenas:
    cada firma (objetivo + tamaño) tiene su directorio inmutable."""
    directory = splits_dir or splits_dir_for(target_name, len(df))
    required = [f"{name}.json" for pair in SCENARIO_FILES.values() for name in pair]
    if directory.exists() and all((directory / name).exists() for name in required):
        return load_zhg_splits(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for stale in directory.glob("*.json"):
        stale.unlink()
    return make_zhg_splits(df, splits_dir=directory)


def load_zhg_splits(directory: Path) -> dict:
    """Lee las particiones congeladas de un directorio versionado."""
    out: dict = {}
    manifest: dict = {"directorio": str(directory)}
    for scenario, (train_key, test_key) in SCENARIO_FILES.items():
        train = json.loads(
            (directory / f"{train_key}.json").read_text(encoding="utf-8")
        )
        test = json.loads(
            (directory / f"{test_key}.json").read_text(encoding="utf-8")
        )
        out[scenario] = (train["ids"], test["ids"])
        manifest[f"{train_key}_n"] = train["n"]
        manifest[f"{train_key}_sha256"] = train["sha256"]
        manifest[f"{test_key}_n"] = test["n"]
        manifest[f"{test_key}_sha256"] = test["sha256"]
    out["manifest"] = manifest
    return out
