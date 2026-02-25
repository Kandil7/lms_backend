import os
from functools import lru_cache
import logging
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from .secrets import get_secret, initialize_secrets_manager

logger = logging.getLogger(__name__)

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
    ALLOW_INITIAL_ADMIN_CREATION: bool = False  # Must be explicitly enabled for bootstrap
    API_V1_PREFIX: str = "/api/v1"
    ENABLE_API_DOCS: bool = True
    STRICT_ROUTER_IMPORTS: bool = False
    METRICS_ENABLED: bool = True
    METRICS_PATH: str = "/metrics"
    API_RESPONSE_ENVELOPE_ENABLED: bool = False
    API_RESPONSE_SUCCESS_MESSAGE: str = "Success"
    API_RESPONSE_ENVELOPE_EXCLUDED_PATHS: CsvList = Field(
        default_factory=lambda: [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
            "/api/v1/health",
            "/api/v1/ready",
            "/api/v1/auth/token",
        ]
    )
    SENTRY_DSN: str | None = None
    SENTRY_ENVIRONMENT: str | None = None
    SENTRY_RELEASE: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.0, ge=0.0, le=1.0)
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(default=0.0, ge=0.0, le=1.0)
    SENTRY_SEND_PII: bool = False
    SENTRY_ENABLE_FOR_CELERY: bool = True
    SECRETS_MANAGER_SOURCE: Literal["auto", "env_var", "vault", "azure_key_vault"] = "auto"
    WEBHOOKS_ENABLED: bool = False
    WEBHOOK_TARGET_URLS: CsvList = Field(default_factory=list)
    WEBHOOK_SIGNING_SECRET: str | None = None
    WEBHOOK_TIMEOUT_SECONDS: float = Field(default=5.0, ge=1.0, le=30.0)

    DATABASE_URL: str = "postgresql+psycopg2://lms:lms@localhost:5432/lms"
    SQLALCHEMY_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30  # Connection pool timeout in seconds
    DB_POOL_RECYCLE: int = 1800  # Recycle connections after 30 minutes

    # Security secrets - will be loaded from secrets manager in production
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 1440
    ALLOW_PUBLIC_ROLE_REGISTRATION: bool = False
    REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN: bool = False
    MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES: int = 10
    MFA_LOGIN_CODE_EXPIRE_MINUTES: int = 10
    MFA_LOGIN_CODE_LENGTH: int = 6
    ACCESS_TOKEN_BLACKLIST_ENABLED: bool = True
    ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED: bool = True  # Must be true in production for security
    ACCESS_TOKEN_BLACKLIST_PREFIX: str = "auth:blacklist:access"
    SECURITY_HEADERS_ENABLED: bool = True
    CSRF_ENABLED: bool = False  # Enable in production with HTTPS

    # Trusted proxy configuration for X-Forwarded-For handling
    TRUSTED_PROXY_IPS: CsvList = Field(default_factory=lambda: [])  # Empty = trust all proxies

    FRONTEND_BASE_URL: str = "http://localhost:3000"
    APP_DOMAIN: str | None = None
    EMAIL_FROM: str = "no-reply@lms.local"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    # Firebase Configuration
    FIREBASE_ENABLED: bool = False
    FIREBASE_PROJECT_ID: str | None = None
    FIREBASE_PRIVATE_KEY: str | None = None
    FIREBASE_CLIENT_EMAIL: str | None = None
    FIREBASE_AUTH_EMULATOR_HOST: str | None = None

    # Firebase Cloud Functions email endpoint (optional alternative to direct SMTP)
    FIREBASE_FUNCTIONS_URL: str | None = None
    FIREBASE_FUNCTIONS_API_KEY: str | None = None

    # Database credentials - must be overridden in production
    # WARNING: Default values are for local development only
    POSTGRES_USER: str = "lms"
    POSTGRES_PASSWORD: str = "lms"  # Override in production!
    POSTGRES_DB: str = "lms"

    # Azure Blob Storage configuration - can be loaded from secrets manager in production
    AZURE_STORAGE_CONNECTION_STRING: str | None = None
    AZURE_STORAGE_ACCOUNT_NAME: str | None = None
    AZURE_STORAGE_ACCOUNT_KEY: str | None = None
    AZURE_STORAGE_ACCOUNT_URL: str | None = None
    AZURE_STORAGE_CONTAINER_NAME: str | None = None
    AZURE_STORAGE_CONTAINER_URL: str | None = None

    CACHE_ENABLED: bool = True
    CACHE_KEY_PREFIX: str = "app:cache"
    CACHE_DEFAULT_TTL_SECONDS: int = 120
    COURSE_CACHE_TTL_SECONDS: int = 120
    LESSON_CACHE_TTL_SECONDS: int = 120
    QUIZ_CACHE_TTL_SECONDS: int = 120
    QUIZ_QUESTION_CACHE_TTL_SECONDS: int = 120

    CORS_ORIGINS: CsvList = Field(default_factory=lambda: ["http://localhost:3000"])
    TRUSTED_HOSTS: CsvList = Field(default_factory=lambda: ["localhost", "127.0.0.1", "testserver"])

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    TASKS_FORCE_INLINE: bool = False  # Changed from True - run tasks asynchronously in background
    RATE_LIMIT_USE_REDIS: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_REDIS_PREFIX: str = "ratelimit"
    RATE_LIMIT_EXCLUDED_PATHS: CsvList = Field(
        default_factory=lambda: [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/ready",
        ]
    )
    AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 60
    AUTH_RATE_LIMIT_PATHS: CsvList = Field(
        default_factory=lambda: [
            "/api/v1/auth/login",
            "/api/v1/auth/token",
            "/api/v1/auth/login/mfa",
        ]
    )
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_SECONDS: int = 900  # 15 minutes
    FILE_UPLOAD_RATE_LIMIT_REQUESTS_PER_HOUR: int = 100
    FILE_UPLOAD_RATE_LIMIT_WINDOW_SECONDS: int = 3600
    FILE_UPLOAD_RATE_LIMIT_PATHS: CsvList = Field(default_factory=lambda: ["/api/v1/files/upload"])

    ASSIGNMENT_RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    ASSIGNMENT_RATE_LIMIT_WINDOW_SECONDS: int = 60
    ASSIGNMENT_RATE_LIMIT_PATHS: CsvList = Field(
        default_factory=lambda: [
            "/api/v1/assignments",
            "/api/v1/assignments/submit",
            "/api/v1/assignments/submissions",
        ]
    )

    UPLOAD_DIR: str = "uploads"
    CERTIFICATES_DIR: str = "certificates"
    MAX_UPLOAD_MB: int = 100
    ALLOWED_UPLOAD_EXTENSIONS: CsvList = Field(
        default_factory=lambda: [
            "mp4",
            "avi",
            "mov",
            "pdf",
            "doc",
            "docx",
            "jpg",
            "jpeg",
            "png",
        ]
    )
    FILE_STORAGE_PROVIDER: Literal["local", "azure"] = "azure"
    FILE_DOWNLOAD_URL_EXPIRE_SECONDS: int = 900
    WEBSOCKET_CONNECTION_TTL_SECONDS: int = 3600

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

    @field_validator(
        "RATE_LIMIT_EXCLUDED_PATHS",
        "API_RESPONSE_ENVELOPE_EXCLUDED_PATHS",
        "WEBHOOK_TARGET_URLS",
        "AUTH_RATE_LIMIT_PATHS",
        "FILE_UPLOAD_RATE_LIMIT_PATHS",
        mode="before",
    )
    @classmethod
    def parse_csv_lists(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator(
        "RATE_LIMIT_EXCLUDED_PATHS",
        "API_RESPONSE_ENVELOPE_EXCLUDED_PATHS",
        "AUTH_RATE_LIMIT_PATHS",
        "FILE_UPLOAD_RATE_LIMIT_PATHS",
        mode="after",
    )
    @classmethod
    def normalize_path_lists(cls, value: list[str]) -> list[str]:
        normalized_paths: list[str] = []
        for item in value:
            cleaned = item.strip()
            if not cleaned:
                continue
            if not cleaned.startswith("/"):
                cleaned = f"/{cleaned}"
            if cleaned != "/" and cleaned.endswith("/"):
                cleaned = cleaned.rstrip("/")
            normalized_paths.append(cleaned)
        return normalized_paths

    @field_validator("METRICS_PATH", mode="before")
    @classmethod
    def normalize_metrics_path(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            return "/metrics"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        return normalized

    @property
    def MAX_UPLOAD_BYTES(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def API_DOCS_EFFECTIVE_ENABLED(self) -> bool:
        if self.ENVIRONMENT == "production":
            return False
        return self.ENABLE_API_DOCS

    @property
    def STRICT_ROUTER_IMPORTS_EFFECTIVE(self) -> bool:
        if self.ENVIRONMENT == "production":
            return True
        return self.STRICT_ROUTER_IMPORTS

    @property
    def SENTRY_ENVIRONMENT_EFFECTIVE(self) -> str:
        return self.SENTRY_ENVIRONMENT or self.ENVIRONMENT

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.ENVIRONMENT != "production":
            return self

        if self.DEBUG:
            raise ValueError("DEBUG must be false when ENVIRONMENT=production")

        # In production, load sensitive values from secrets manager
        if self.ENVIRONMENT == "production":
            # Initialize secrets manager for production.
            # "auto": try configured providers, then fall back to env_var.
            # explicit provider: require successful initialization.
            secrets_manager_source = "env_var"
            requested_source = (self.SECRETS_MANAGER_SOURCE or "auto").lower()
            keyvault_url = os.getenv("AZURE_KEYVAULT_URL") or os.getenv("AZURE_KEYVAULT_ENDPOINT")
            vault_addr = os.getenv("VAULT_ADDR")

            try:
                if requested_source == "env_var":
                    initialize_secrets_manager("env_var")
                    secrets_manager_source = "env_var"
                elif requested_source == "azure_key_vault":
                    success = initialize_secrets_manager("azure_key_vault", vault_url=keyvault_url)
                    if not success:
                        raise ValueError(
                            "SECRETS_MANAGER_SOURCE=azure_key_vault but initialization failed. "
                            "Verify AZURE_KEYVAULT_URL and Azure credentials."
                        )
                    secrets_manager_source = "azure_key_vault"
                elif requested_source == "vault":
                    success = initialize_secrets_manager(
                        "vault",
                        vault_url=vault_addr,
                        vault_token=os.getenv("VAULT_TOKEN"),
                        vault_namespace=os.getenv("VAULT_NAMESPACE"),
                    )
                    if not success:
                        raise ValueError(
                            "SECRETS_MANAGER_SOURCE=vault but initialization failed. "
                            "Verify VAULT_ADDR and Vault credentials."
                        )
                    secrets_manager_source = "vault"
                else:
                    success = False
                    if keyvault_url:
                        success = initialize_secrets_manager(
                            "azure_key_vault",
                            vault_url=keyvault_url,
                        )
                        if success:
                            secrets_manager_source = "azure_key_vault"
                    if not success and vault_addr:
                        success = initialize_secrets_manager(
                            "vault",
                            vault_url=vault_addr,
                            vault_token=os.getenv("VAULT_TOKEN"),
                            vault_namespace=os.getenv("VAULT_NAMESPACE"),
                        )
                        if success:
                            secrets_manager_source = "vault"
                    if not success:
                        initialize_secrets_manager("env_var")
                        secrets_manager_source = "env_var"
            except Exception as e:
                logger.error(f"Failed to initialize secrets manager: {e}")
                raise ValueError(
                    f"Failed to initialize secrets manager in production: {e}. "
                    "Ensure secrets provider configuration is correct."
                ) from e

            logger.info(f"Secrets manager initialized with source: {secrets_manager_source}")

            # Override sensitive values from secrets manager
            if (
                self.SECRET_KEY
                in {
                    "change-me",
                    "change-this-in-production-with-64-random-chars-minimum",
                }
                or len(self.SECRET_KEY) < 32
                or self.SECRET_KEY == ""  # Empty string is not allowed
            ):
                secret_key = get_secret("SECRET_KEY", default=self.SECRET_KEY)
                if secret_key and len(secret_key) >= 32:
                    self.SECRET_KEY = secret_key
                else:
                    raise ValueError(
                        "SECRET_KEY must be a strong random value (32+ chars) in production"
                    )

            # Load database credentials from secrets
            if self.POSTGRES_PASSWORD == "lms":
                db_password = get_secret(
                    "DATABASE_PASSWORD",
                    default=None,  # Don't fall back to default!
                )
                if db_password and db_password != "lms":
                    self.POSTGRES_PASSWORD = db_password
                    # Reconstruct DATABASE_URL
                    self.DATABASE_URL = f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DATABASE_URL.split('@')[1]}"
                elif not db_password:
                    raise ValueError(
                        "POSTGRES_PASSWORD must be set from secrets manager in production. "
                        "Set DATABASE_PASSWORD secret in Azure Key Vault or Vault."
                    )

            # Load SMTP credentials from secrets
            if self.SMTP_PASSWORD is None or self.SMTP_PASSWORD == "":
                smtp_password = get_secret("SMTP_PASSWORD", default=self.SMTP_PASSWORD)
                if smtp_password:
                    self.SMTP_PASSWORD = smtp_password

            # Load Sentry DSN from secrets
            if self.SENTRY_DSN is None:
                sentry_dsn = get_secret("SENTRY_DSN", default=self.SENTRY_DSN)
                if sentry_dsn:
                    self.SENTRY_DSN = sentry_dsn

            # Load Azure storage credentials from secrets
            if not (self.AZURE_STORAGE_CONNECTION_STRING or "").strip():
                azure_connection_string = get_secret(
                    "AZURE_STORAGE_CONNECTION_STRING",
                    default=self.AZURE_STORAGE_CONNECTION_STRING,
                )
                if azure_connection_string:
                    self.AZURE_STORAGE_CONNECTION_STRING = azure_connection_string
            if not (self.AZURE_STORAGE_ACCOUNT_NAME or "").strip():
                azure_account_name = get_secret(
                    "AZURE_STORAGE_ACCOUNT_NAME",
                    default=self.AZURE_STORAGE_ACCOUNT_NAME,
                )
                if azure_account_name:
                    self.AZURE_STORAGE_ACCOUNT_NAME = azure_account_name
            if not (self.AZURE_STORAGE_ACCOUNT_KEY or "").strip():
                azure_account_key = get_secret(
                    "AZURE_STORAGE_ACCOUNT_KEY", default=self.AZURE_STORAGE_ACCOUNT_KEY
                )
                if azure_account_key:
                    self.AZURE_STORAGE_ACCOUNT_KEY = azure_account_key
            if not (self.AZURE_STORAGE_ACCOUNT_URL or "").strip():
                azure_account_url = get_secret(
                    "AZURE_STORAGE_ACCOUNT_URL",
                    default=self.AZURE_STORAGE_ACCOUNT_URL,
                )
                if azure_account_url:
                    self.AZURE_STORAGE_ACCOUNT_URL = azure_account_url
            if not (self.AZURE_STORAGE_CONTAINER_NAME or "").strip():
                azure_container_name = get_secret(
                    "AZURE_STORAGE_CONTAINER_NAME",
                    default=self.AZURE_STORAGE_CONTAINER_NAME,
                )
                if azure_container_name:
                    self.AZURE_STORAGE_CONTAINER_NAME = azure_container_name
            if not (self.AZURE_STORAGE_CONTAINER_URL or "").strip():
                azure_container_url = get_secret(
                    "AZURE_STORAGE_CONTAINER_URL",
                    default=self.AZURE_STORAGE_CONTAINER_URL,
                )
                if azure_container_url:
                    self.AZURE_STORAGE_CONTAINER_URL = azure_container_url

        # Validate required production settings
        insecure_values = {
            "change-me",
            "change-this-in-production-with-64-random-chars-minimum",
        }
        if self.SECRET_KEY in insecure_values or len(self.SECRET_KEY) < 32 or self.SECRET_KEY == "":
            raise ValueError("SECRET_KEY must be a strong random value (32+ chars) in production")

        if self.ACCESS_TOKEN_BLACKLIST_ENABLED and not self.ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED:
            raise ValueError("ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED must be true in production")

        if self.TASKS_FORCE_INLINE:
            raise ValueError("TASKS_FORCE_INLINE must be false when ENVIRONMENT=production")

        if self.FILE_STORAGE_PROVIDER == "azure":
            has_container = bool((self.AZURE_STORAGE_CONTAINER_NAME or "").strip())
            has_connection_string = bool((self.AZURE_STORAGE_CONNECTION_STRING or "").strip())
            has_account_url = bool((self.AZURE_STORAGE_ACCOUNT_URL or "").strip())

            if not has_container:
                raise ValueError(
                    "AZURE_STORAGE_CONTAINER_NAME is required when FILE_STORAGE_PROVIDER=azure in production"
                )
            if not has_connection_string and not has_account_url:
                raise ValueError(
                    "Either AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_URL is required when FILE_STORAGE_PROVIDER=azure in production"
                )

        return self

    @model_validator(mode="after")
    def validate_firebase_settings(self):
        # Validate Firebase configuration when enabled
        if self.FIREBASE_ENABLED:
            # When Firebase is enabled, either FIREBASE_PROJECT_ID or FIREBASE_FUNCTIONS_URL must be set
            if not self.FIREBASE_PROJECT_ID and not self.FIREBASE_FUNCTIONS_URL:
                raise ValueError(
                    "When FIREBASE_ENABLED=True, either FIREBASE_PROJECT_ID or FIREBASE_FUNCTIONS_URL must be set"
                )

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
