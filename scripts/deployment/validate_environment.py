#!/usr/bin/env python3
"""
Environment validation for production deployment.

This script is intended to run before deployment and fail fast on unsafe
configuration. It validates values from process env and optionally from an
env-file (`KEY=VALUE` lines).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

LOGGER = logging.getLogger("env-validator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

INSECURE_PLACEHOLDERS = {
    "change-me",
    "change-this-in-production-with-64-random-chars-minimum",
    "placeholder-for-azure-key-vault",
}


def _as_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _normalize(value: str | None) -> str:
    return (value or "").strip()


def load_env_file(env_file: Path) -> None:
    if not env_file.exists():
        raise FileNotFoundError(f"env file not found: {env_file}")

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class EnvironmentValidator:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def _error(self, message: str) -> None:
        self.errors.append(message)

    def _warn(self, message: str) -> None:
        self.warnings.append(message)

    def _get(self, key: str) -> str:
        return _normalize(os.getenv(key))

    def validate_required_flags(self) -> None:
        expected = {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "ENABLE_API_DOCS": "false",
            "STRICT_ROUTER_IMPORTS": "true",
            "TASKS_FORCE_INLINE": "false",
            "ACCESS_TOKEN_BLACKLIST_ENABLED": "true",
            "ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED": "true",
        }
        for key, expected_value in expected.items():
            actual = self._get(key)
            if not actual:
                self._error(f"Missing required environment variable: {key}")
                continue
            if actual.lower() != expected_value:
                self._error(
                    f"Invalid value for {key}: expected '{expected_value}', got '{actual}'"
                )

    def validate_critical_presence(self) -> None:
        required = [
            "PROD_DATABASE_URL",
            "DATABASE_URL",
            "SECRET_KEY",
            "APP_DOMAIN",
            "LETSENCRYPT_EMAIL",
            "REDIS_URL",
            "CELERY_BROKER_URL",
            "CELERY_RESULT_BACKEND",
            "CORS_ORIGINS",
            "TRUSTED_HOSTS",
        ]
        for key in required:
            if not self._get(key):
                self._error(f"Missing required environment variable: {key}")

    def validate_secret_key(self) -> None:
        secret_key = self._get("SECRET_KEY")
        if not secret_key:
            return
        if len(secret_key) < 32:
            self._error("SECRET_KEY must be at least 32 characters")
        lower = secret_key.lower()
        if lower in INSECURE_PLACEHOLDERS or "change-this" in lower:
            self._error("SECRET_KEY contains insecure placeholder value")

    def validate_database_urls(self) -> None:
        database_url = self._get("DATABASE_URL")
        prod_database_url = self._get("PROD_DATABASE_URL")
        if not database_url or not prod_database_url:
            return

        if database_url != prod_database_url:
            self._warn("DATABASE_URL differs from PROD_DATABASE_URL")

        for name, url in (
            ("DATABASE_URL", database_url),
            ("PROD_DATABASE_URL", prod_database_url),
        ):
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            if not parsed.scheme or not host:
                self._error(f"{name} is not a valid database URL")
                continue
            if host in {"localhost", "127.0.0.1", "::1"}:
                self._error(f"{name} must not point to localhost in production")

        query = parse_qs(urlparse(prod_database_url).query)
        sslmode = (query.get("sslmode") or [""])[0].lower()
        if ".postgres.database.azure.com" in prod_database_url.lower() and sslmode != "require":
            self._error("PROD_DATABASE_URL must include sslmode=require for Azure PostgreSQL")

    def validate_runtime_urls(self) -> None:
        for key in ["REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"]:
            value = self._get(key)
            if not value:
                continue
            parsed = urlparse(value)
            host = (parsed.hostname or "").lower()
            if parsed.scheme not in {"redis", "rediss"}:
                self._error(f"{key} must use redis:// or rediss://")
            if host in {"localhost", "127.0.0.1", "::1"}:
                self._warn(f"{key} points to localhost; verify this is intentional")

    def validate_tls(self) -> None:
        app_domain = self._get("APP_DOMAIN")
        letsencrypt_email = self._get("LETSENCRYPT_EMAIL")
        if app_domain in {"localhost", "127.0.0.1"}:
            self._error("APP_DOMAIN must be a public DNS name in production")
        if "." not in app_domain:
            self._error("APP_DOMAIN must look like a valid DNS name")
        if "@" not in letsencrypt_email:
            self._error("LETSENCRYPT_EMAIL must be a valid email address")

    def validate_secret_manager(self) -> None:
        keyvault = self._get("AZURE_KEYVAULT_URL")
        vault = self._get("VAULT_ADDR")
        source = (self._get("SECRETS_MANAGER_SOURCE") or self._get("SECRETS_SOURCE")).lower()

        if source in {"env", "environment", "env_var"}:
            # Explicitly running with environment-based secrets.
            return

        if source == "azure_key_vault":
            if not keyvault:
                self._error(
                    "AZURE_KEYVAULT_URL is required when SECRETS_MANAGER_SOURCE=azure_key_vault"
                )
            return

        if source == "vault":
            if not vault:
                self._error("VAULT_ADDR is required when SECRETS_MANAGER_SOURCE=vault")
            return

        if source and source not in {"auto", "env", "environment", "env_var", "vault", "azure_key_vault"}:
            self._warn(f"Unknown SECRETS_MANAGER_SOURCE value: '{source}' (expected auto/env_var/vault/azure_key_vault)")

        if not keyvault and not vault:
            self._warn("No secret manager configured (AZURE_KEYVAULT_URL or VAULT_ADDR)")
        if keyvault and vault:
            self._warn(
                "Both AZURE_KEYVAULT_URL and VAULT_ADDR are set; ensure this is intentional"
            )

    def validate_cors_and_hosts(self) -> None:
        app_domain = self._get("APP_DOMAIN")
        cors_origins = self._get("CORS_ORIGINS")
        trusted_hosts = self._get("TRUSTED_HOSTS")

        if "*" in cors_origins:
            self._error("CORS_ORIGINS must not contain wildcard '*' in production")
        if app_domain and app_domain not in trusted_hosts:
            self._warn("TRUSTED_HOSTS does not contain APP_DOMAIN")

    def validate_file_storage(self) -> None:
        provider = self._get("FILE_STORAGE_PROVIDER").lower()
        if provider == "azure":
            container_name = self._get("AZURE_STORAGE_CONTAINER_NAME")
            connection_string = self._get("AZURE_STORAGE_CONNECTION_STRING")
            account_url = self._get("AZURE_STORAGE_ACCOUNT_URL")
            if not container_name:
                self._error(
                    "AZURE_STORAGE_CONTAINER_NAME is required when FILE_STORAGE_PROVIDER=azure"
                )
            if not connection_string and not account_url:
                self._error(
                    "Either AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_URL is required when FILE_STORAGE_PROVIDER=azure"
                )
            if any(token in (connection_string or "").lower() for token in INSECURE_PLACEHOLDERS):
                self._error("AZURE_STORAGE_CONNECTION_STRING contains placeholder value")

    def validate_observability(self) -> None:
        sentry_dsn = self._get("SENTRY_DSN")
        sentry_enabled = _as_bool(self._get("SENTRY_ENABLED"))
        if sentry_enabled is not False and not sentry_dsn:
            self._warn("SENTRY_DSN is empty; production error tracking is disabled")

        metrics_enabled = _as_bool(self._get("METRICS_ENABLED"))
        if metrics_enabled is False:
            self._warn("METRICS_ENABLED=false; production telemetry is reduced")

    def run(self) -> tuple[bool, list[str], list[str]]:
        LOGGER.info("Starting environment validation")
        self.validate_required_flags()
        self.validate_critical_presence()
        self.validate_secret_key()
        self.validate_database_urls()
        self.validate_runtime_urls()
        self.validate_tls()
        self.validate_secret_manager()
        self.validate_cors_and_hosts()
        self.validate_file_storage()
        self.validate_observability()

        LOGGER.info(
            "Validation completed: %s error(s), %s warning(s)",
            len(self.errors),
            len(self.warnings),
        )
        return len(self.errors) == 0, self.errors, self.warnings

    def print_report(self) -> None:
        print("\n" + "=" * 68)
        print("ENVIRONMENT VALIDATION REPORT")
        print("=" * 68)
        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for idx, message in enumerate(self.errors, 1):
                print(f"  {idx}. {message}")
        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for idx, message in enumerate(self.warnings, 1):
                print(f"  {idx}. {message}")
        if not self.errors and not self.warnings:
            print("\nNo issues detected.")
        print(f"\nSTATUS: {'PASS' if not self.errors else 'FAIL'}")
        print("=" * 68)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate production environment settings")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional env file to load before validation (KEY=VALUE format)",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Return non-zero when warnings are present",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        if args.env_file is not None:
            load_env_file(args.env_file)
        validator = EnvironmentValidator()
        success, _, warnings = validator.run()
        validator.print_report()
        if not success:
            return 1
        if warnings and args.strict_warnings:
            return 1
        return 0
    except Exception as exc:
        LOGGER.error("Validation failed with exception: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
