from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),
    )

    app_name: str = "Scalable AI Inference Platform"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
    )

    redis_url: str = "redis://redis:6379/0"
    redis_rate_limit_db: int = 1
    redis_cache_ttl_seconds: int = 300

    jwt_secret_key: str = Field(default="change-me")
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60
    service_api_keys: list[str] = Field(default_factory=lambda: ["dev-api-key"])

    prometheus_enabled: bool = True
    log_level: str = "INFO"
    request_timeout_seconds: float = 30.0
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    ray_serve_app_name: str = "ai-inference-platform"
    ray_dashboard_url: str = "http://ray:8265"
    model_registry_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
        / "configs"
        / "model_registry.json"
    )

    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    monitoring_docs_url: HttpUrl | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
