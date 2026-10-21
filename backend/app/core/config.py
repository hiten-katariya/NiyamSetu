import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "NiyamSetu API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "insecure-default-development-secret-key-change-in-env"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # PostgreSQL database connection URL (points strictly to niyamsetu_dev)
    DATABASE_URL: str = "postgresql+psycopg2://niyamsetu_user:dev_password@localhost:5432/niyamsetu_dev"

    # CORS Allowed Origins
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # File storage
    STORAGE_LOCAL_DIR: str = "./uploads"

    # Seed passwords (for local development seeding only)
    SEED_ADMIN_PASSWORD: str = "ChangeMeDev123!"
    SEED_DEFAULT_USER_PASSWORD: str = "ChangeMeDev123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+psycopg2://", 1)
            elif v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg2://", 1)
        return v


settings = Settings()
