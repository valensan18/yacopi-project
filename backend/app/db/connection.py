"""Conexión a SQLite (solo lectura para consultas; escrituras son offline)."""

import sqlite3
from pathlib import Path


def get_connection(database_path: Path) -> sqlite3.Connection:
    if not database_path.exists():
        raise FileNotFoundError(
            f"Base de datos no encontrada: {database_path}. "
            "Ejecute `python scripts/build_db.py` primero."
        )
    conn = sqlite3.connect(
        f"file:{database_path}?mode=ro", uri=True, check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn
