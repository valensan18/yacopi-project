"""Esquemas de estado del sistema."""

from pydantic import BaseModel


class SystemStatus(BaseModel):
    data_status: str
    dataset_version: str | None
    model_status: str
    model_ready: bool
    target_unit: str
    experimental_model: dict
    experimental_zhg: dict = {}
    valor_v1: dict = {}
    reason: str
    public_notice: str


class HealthStatus(BaseModel):
    status: str
    model_ready: bool
