"""Estado del sistema: datos, modelo oficial y modelo experimental."""

import sqlite3

from fastapi import APIRouter, Request

from ..db.connection import get_connection
from ..schemas.system import SystemStatus

router = APIRouter(tags=["system"])

PUBLIC_NOTICE = (
    "Información académica de apoyo. No constituye avalúo oficial ni "
    "sustituye la valoración catastral."
)


@router.get("/system/status", response_model=SystemStatus)
def system_status(request: Request) -> SystemStatus:
    settings = request.app.state.settings
    dataset_version = None
    try:
        conn = get_connection(settings.database_path)
        try:
            row = conn.execute(
                "SELECT value FROM dataset_meta WHERE key = 'dataset_version'"
            ).fetchone()
            dataset_version = row["value"] if row else None
        finally:
            conn.close()
    except (FileNotFoundError, sqlite3.Error):
        dataset_version = None

    experimental = request.app.state.experimental_predictor.info()
    experimental["habilitado"] = settings.experimental_inference_enabled

    experimental_zhg = request.app.state.experimental_zhg.info()
    experimental_zhg["habilitado"] = settings.experimental_zhg_enabled

    return SystemStatus(
        data_status="audited_and_curated" if dataset_version else "unavailable",
        dataset_version=dataset_version,
        model_status="label_pending",
        model_ready=False,
        target_unit="COP/ha",
        experimental_model=experimental,
        experimental_zhg=experimental_zhg,
        reason=(
            "Valor exclusivo de terreno por predio no validado; el endpoint "
            "oficial de predicción permanece bloqueado"
        ),
        public_notice=PUBLIC_NOTICE,
    )
