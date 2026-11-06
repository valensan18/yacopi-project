"""Configuración del backend (pydantic-settings).

Variables de entorno disponibles (ver .env.example):
  APP_ENV, LOG_LEVEL, DATABASE_PATH, MODEL_DIR,
  EXPERIMENTAL_INFERENCE_ENABLED, CORS_ORIGINS, MAX_PAGE_LIMIT, MAX_MAP_POINTS
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    database_path: Path = REPO_ROOT / "data" / "parcels.db"
    model_dir: Path = REPO_ROOT / "ml" / "artifacts"
    experimental_inference_enabled: bool = False
    experimental_zhg_enabled: bool = False
    valor_v1_enabled: bool = False
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_page_limit: int = 100
    max_map_points: int = 8000
    default_page_limit: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()
