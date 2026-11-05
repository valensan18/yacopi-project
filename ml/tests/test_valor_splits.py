"""Pruebas de separacion de conjuntos del experimento VALOR_TERRENO_Ha.

Evitan reintroducir la contaminacion de la validacion espacial: cada
protocolo debe entrenar y evaluar sobre conjuntos disjuntos de predios.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from yacopi_ml.valor.dataset import construir_dataset
from yacopi_ml.valor.splits import dividir_espacial, dividir_predios


@pytest.mark.parametrize("esc", ["A", "B"])
def test_predio_train_test_disjuntos(esc: str) -> None:
    ds = construir_dataset(esc)
    tr, te = dividir_predios(ds)
    assert not set(tr["numero_predial"]) & set(te["numero_predial"])
    assert len(tr) + len(te) == len(ds)


@pytest.mark.parametrize("esc", ["A", "B"])
def test_espacial_train_test_disjuntos(esc: str) -> None:
    ds = construir_dataset(esc)
    tr, te = dividir_espacial(ds)
    assert not set(tr["numero_predial"]) & set(te["numero_predial"])


@pytest.mark.parametrize("esc", ["A", "B"])
def test_espacial_bloques_disjuntos(esc: str) -> None:
    ds = construir_dataset(esc)
    tr, te = dividir_espacial(ds)
    lat = ds["tr_latitud"].to_numpy()
    lon = ds["tr_longitud"].to_numpy()
    valido = ~(np.isnan(lat) | np.isnan(lon))
    lat_bin = pd.cut(lat[valido], bins=6, labels=False)
    lon_bin = pd.cut(lon[valido], bins=6, labels=False)
    bloques_full = pd.Series(
        list(zip(lat_bin, lon_bin, strict=False)), index=ds.index[valido]
    )
    bloques_tr = set(bloques_full.reindex(tr.index).dropna())
    bloques_te = set(bloques_full.reindex(te.index).dropna())
    assert not bloques_tr & bloques_te


def test_protocolo_rechaza_solapamiento() -> None:
    from yacopi_ml.valor.train import validar_protocolo

    ds = construir_dataset("A")
    tr = ds.iloc[:100]
    te = ds.iloc[50:150]  # comparte 50 predios
    X = ds[["area_terreno_m2"]]
    with pytest.raises(AssertionError):
        validar_protocolo(ds, tr, te, X)


def test_escenarios_sin_crossover() -> None:
    a = set(construir_dataset("A")["numero_predial"])
    b = set(construir_dataset("B")["numero_predial"])
    assert not a & b


