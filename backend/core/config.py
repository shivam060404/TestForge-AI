from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://qa_user:qa_pass@localhost:5432/qa_agent"
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "qa-artifacts"
    minio_use_ssl: bool = False
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_origins: List[str] = ["http://localhost:3000"]
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_temperature: float = 0.1
    groq_max_tokens: int = 4096
    llm_timeout_seconds: float = 45.0
    llm_max_retries: int = 2
    llm_cost_per_1k_input_tokens: float = 0.0
    llm_cost_per_1k_output_tokens: float = 0.0
    ai_max_intent_length: int = 5000
    environment: str = "development"
    artifacts_dir: str = "./artifacts"

    @field_validator("database_url")
    @classmethod
    def require_postgres(cls, value: str) -> str:
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use PostgreSQL with the asyncpg driver")
        return value


settings = Settings()
