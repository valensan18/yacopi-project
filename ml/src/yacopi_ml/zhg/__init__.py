"""Experimento ZHG (Fase 5): objetivo de referencia zonal, modo research."""

from .dataset import TARGET_DOMINANTE, TARGET_PONDERADO, build_zhg_dataset
from .splits import make_zhg_splits
from .train import load_zhg_blocked, run

__all__ = [
    "TARGET_DOMINANTE",
    "TARGET_PONDERADO",
    "build_zhg_dataset",
    "make_zhg_splits",
    "load_zhg_blocked",
    "run",
]
