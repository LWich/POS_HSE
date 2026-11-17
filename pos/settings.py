from pathlib import Path

from pydantic import Field, FiniteFloat
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POS_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    db_path: Path = Path("/data/pos.sqlite3")
    db_timeout: FiniteFloat = Field(default=10.0, ge=0)
    api_host: str = Field(default="127.0.0.1", min_length=1)
    api_port: int = Field(default=8000, ge=1, le=65535)
    health_request_timeout: FiniteFloat = Field(default=2.0, gt=0)
