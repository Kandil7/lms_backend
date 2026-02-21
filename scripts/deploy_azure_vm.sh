#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/lms_backend}"
ENV_FILE="$APP_DIR/.env"
COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"

if command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  DC="docker compose"
fi

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: $name" >&2
    exit 1
  fi
}

upsert_env() {
  local key="$1"
  local value="$2"
  local escaped
  escaped="$(printf '%s' "$value" | sed -e 's/[\/&]/\\&/g')"

  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${escaped}|" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

mkdir -p "$APP_DIR"
cd "$APP_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  cp .env.production.example "$ENV_FILE"
fi

require_env "PROD_DATABASE_URL"
require_env "SECRET_KEY"
require_env "APP_DOMAIN"
require_env "LETSENCRYPT_EMAIL"
require_env "FRONTEND_BASE_URL"
require_env "CORS_ORIGINS"
require_env "TRUSTED_HOSTS"
require_env "SMTP_HOST"
require_env "SMTP_PORT"
require_env "SMTP_USERNAME"
require_env "SMTP_PASSWORD"
require_env "EMAIL_FROM"

upsert_env "ENVIRONMENT" "production"
upsert_env "DEBUG" "false"
upsert_env "ENABLE_API_DOCS" "false"
upsert_env "STRICT_ROUTER_IMPORTS" "true"
upsert_env "TASKS_FORCE_INLINE" "false"
upsert_env "ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED" "true"

upsert_env "PROD_DATABASE_URL" "$PROD_DATABASE_URL"
upsert_env "DATABASE_URL" "$PROD_DATABASE_URL"
upsert_env "SECRET_KEY" "$SECRET_KEY"

upsert_env "APP_DOMAIN" "$APP_DOMAIN"
upsert_env "LETSENCRYPT_EMAIL" "$LETSENCRYPT_EMAIL"
upsert_env "FRONTEND_BASE_URL" "$FRONTEND_BASE_URL"
upsert_env "CORS_ORIGINS" "$CORS_ORIGINS"
upsert_env "TRUSTED_HOSTS" "$TRUSTED_HOSTS"

upsert_env "SMTP_HOST" "$SMTP_HOST"
upsert_env "SMTP_PORT" "$SMTP_PORT"
upsert_env "SMTP_USERNAME" "$SMTP_USERNAME"
upsert_env "SMTP_PASSWORD" "$SMTP_PASSWORD"
upsert_env "EMAIL_FROM" "$EMAIL_FROM"

if [[ -n "${SENTRY_DSN:-}" ]]; then
  upsert_env "SENTRY_DSN" "$SENTRY_DSN"
fi

if [[ -n "${SENTRY_RELEASE:-}" ]]; then
  upsert_env "SENTRY_RELEASE" "$SENTRY_RELEASE"
fi

if [[ -n "${WEBHOOK_TARGET_URLS:-}" ]]; then
  upsert_env "WEBHOOK_TARGET_URLS" "$WEBHOOK_TARGET_URLS"
fi

$DC -f "$COMPOSE_FILE" pull || true
$DC -f "$COMPOSE_FILE" down --remove-orphans
$DC -f "$COMPOSE_FILE" up -d --build
$DC -f "$COMPOSE_FILE" ps

$DC -f "$COMPOSE_FILE" exec -T api python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/v1/ready', timeout=10).status == 200 else 1)"
echo "Deployment completed successfully."
