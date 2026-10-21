import os
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "India Leads Platform"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super_secret_temporary_key_for_development_32chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Initial Admin Setup (Read from backend/.env; used ONLY for initial bootstrap if no admin exists or explicit CLI reset)
    ADMIN_EMAIL: str = "admin@indialeads.internal"
    ADMIN_INITIAL_PASSWORD: Optional[str] = None
    ADMIN_FULL_NAME: str = "Principal Lead Admin"

    # Database
    DATABASE_URL: str = "sqlite:///./india_leads.db"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = True  # Default True for seamless local zero-dependency testing

    # Sourcing & Modes
    DEMO_MODE: bool = False
    DISCOVERY_PROVIDER: str = "overpass"
    OVERPASS_API_URL: str = "https://overpass.openstreetmap.fr/api/interpreter"
    OVERPASS_FALLBACK_URLS: List[str] = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter"
    ]
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    GOOGLE_SEARCH_API_KEY: Optional[str] = None
    GOOGLE_SEARCH_CX: Optional[str] = None

    # Server Host & Port
    HOST: str = "127.0.0.1"
    PORT: int = 8001

    # Crawler & Enrichment Safeguards
    ENRICHMENT_MAX_PAGES_PER_DOMAIN: int = 4
    ENRICHMENT_REQUEST_TIMEOUT_SECONDS: int = 10
    ENRICHMENT_RATE_LIMIT_DELAY: float = 1.0
    ENRICHMENT_USER_AGENT: str = "IndiaLeadsBot/1.0 (+https://indialeads.internal/bot; compliant verification)"
    SSRF_ALLOWED_PORTS: Union[List[int], str] = [80, 443]

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    @field_validator("DATABASE_URL", mode="before")
    def assemble_database_url(cls, v: str) -> str:
        if v and v.startswith("sqlite:///."):
            from pathlib import Path
            root = Path(__file__).resolve().parents[3]
            filename = v.replace("sqlite:///./", "").replace("sqlite:///", "")
            abs_path = (root / filename).resolve()
            return f"sqlite:///{abs_path.as_posix()}"
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("SSRF_ALLOWED_PORTS", mode="before")
    def assemble_ssrf_ports(cls, v: Union[str, List[int]]) -> List[int]:
        if isinstance(v, str):
            return [int(i.strip()) for i in v.split(",") if i.strip()]
        return v

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.startswith("postgresql")


settings = Settings()

