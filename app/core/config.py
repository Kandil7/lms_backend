from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

CsvList = Annotated[list[str], NoDecode]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "LMS Backend"
    VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+psycopg2://lms:lms@localhost:5432/lms"
    SQLALCHEMY_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40

    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    CORS_ORIGINS: CsvList = Field(default_factory=lambda: ["http://localhost:3000"])
    TRUSTED_HOSTS: CsvList = Field(default_factory=lambda: ["localhost", "127.0.0.1", "testserver"])

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    TASKS_FORCE_INLINE: bool = True
    RATE_LIMIT_USE_REDIS: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_REDIS_PREFIX: str = "ratelimit"
    RATE_LIMIT_EXCLUDED_PATHS: CsvList = Field(
        default_factory=lambda: ["/", "/docs", "/redoc", "/openapi.json", "/api/v1/health", "/api/v1/ready"]
    )

    UPLOAD_DIR: str = "uploads"
    CERTIFICATES_DIR: str = "certificates"
    MAX_UPLOAD_MB: int = 100
    ALLOWED_UPLOAD_EXTENSIONS: CsvList = Field(
        default_factory=lambda: ["mp4", "avi", "mov", "pdf", "doc", "docx", "jpg", "jpeg", "png"]
    )
    FILE_STORAGE_PROVIDER: Literal["local", "s3"] = "local"
    FILE_DOWNLOAD_URL_EXPIRE_SECONDS: int = 900

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None
    AWS_S3_BUCKET: str | None = None
    AWS_S3_BUCKET_URL: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("TRUSTED_HOSTS", mode="before")
    @classmethod
    def parse_hosts(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("ALLOWED_UPLOAD_EXTENSIONS", mode="before")
    @classmethod
    def parse_extensions(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return [item.lower() for item in value]

    @field_validator("RATE_LIMIT_EXCLUDED_PATHS", mode="before")
    @classmethod
    def parse_rate_limit_excluded_paths(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def MAX_UPLOAD_BYTES(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.ENVIRONMENT != "production":
            return self

        if self.DEBUG:
            raise ValueError("DEBUG must be false when ENVIRONMENT=production")

        insecure_values = {"change-me", "change-this-in-production-with-64-random-chars-minimum"}
        if self.SECRET_KEY in insecure_values or len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be a strong random value (32+ chars) in production")

        if self.TASKS_FORCE_INLINE:
            raise ValueError("TASKS_FORCE_INLINE must be false when ENVIRONMENT=production")

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
