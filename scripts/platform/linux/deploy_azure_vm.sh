#!/usr/bin/env bash
# Azure VM deployment script.
# - Remote mode: run from local machine with AZURE_VM_HOST + AZURE_VM_USER.
# - VM mode: run on VM (used by GitHub Actions) with DEPLOY_MODE=vm.

set -euo pipefail

log() {
    echo "[deploy] $*"
}

fail() {
    echo "[deploy] ERROR: $*" >&2
    exit 1
}

require_env() {
    local key="$1"
    if [[ -z "${!key:-}" ]]; then
        fail "Required environment variable '${key}' is not set"
    fi
}

require_command() {
    local cmd="$1"
    command -v "$cmd" >/dev/null 2>&1 || fail "Command '${cmd}' is required but was not found"
}

select_compose_cmd() {
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD=(docker compose)
        return
    fi
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD=(docker-compose)
        return
    fi
    fail "Neither 'docker compose' nor 'docker-compose' is available on this host"
}

run_env_validation() {
    local app_dir="$1"
    local env_file="$2"
    local strict_flag=()

    if [[ "${DEPLOY_STRICT_VALIDATION:-false}" == "true" ]]; then
        strict_flag+=(--strict-warnings)
    fi

    log "Validating production environment configuration"
    docker run --rm \
        --env-file "${env_file}" \
        -v "${app_dir}:/app" \
        -w /app \
        python:3.11-slim \
        python scripts/deployment/validate_environment.py "${strict_flag[@]}"
}

write_env_file() {
    local env_file="$1"
    local db_auth db_user db_password

    # Keep POSTGRES_* aligned with PROD_DATABASE_URL for config validators that
    # may reconstruct DATABASE_URL in production.
    db_auth="${PROD_DATABASE_URL#*://}"
    db_auth="${db_auth%%@*}"
    db_user="${db_auth%%:*}"
    db_password="${db_auth#*:}"

    if [[ -z "${db_user}" || -z "${db_password}" || "${db_auth}" == "${PROD_DATABASE_URL}" ]]; then
        db_user="${POSTGRES_USER:-lms}"
        db_password="${POSTGRES_PASSWORD:-lms}"
    fi

    cat > "$env_file" <<EOF
PROJECT_NAME=LMS Backend
ENVIRONMENT=production
API_V1_PREFIX=/api/v1
DEBUG=false
ENABLE_API_DOCS=false
STRICT_ROUTER_IMPORTS=true
METRICS_ENABLED=true
METRICS_PATH=${METRICS_PATH:-/metrics}
API_RESPONSE_ENVELOPE_ENABLED=true
API_RESPONSE_SUCCESS_MESSAGE=${API_RESPONSE_SUCCESS_MESSAGE:-Success}
API_RESPONSE_ENVELOPE_EXCLUDED_PATHS=${API_RESPONSE_ENVELOPE_EXCLUDED_PATHS:-/docs,/redoc,/openapi.json,/metrics,/api/v1/health,/api/v1/ready,/api/v1/auth/token}
SENTRY_DSN=${SENTRY_DSN:-}
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=${SENTRY_RELEASE:-}
SENTRY_TRACES_SAMPLE_RATE=${SENTRY_TRACES_SAMPLE_RATE:-0.1}
SENTRY_PROFILES_SAMPLE_RATE=${SENTRY_PROFILES_SAMPLE_RATE:-0.0}
SENTRY_SEND_PII=${SENTRY_SEND_PII:-false}
SENTRY_ENABLE_FOR_CELERY=${SENTRY_ENABLE_FOR_CELERY:-true}
WEBHOOKS_ENABLED=${WEBHOOKS_ENABLED:-false}
WEBHOOK_TARGET_URLS=${WEBHOOK_TARGET_URLS:-}
WEBHOOK_SIGNING_SECRET=${WEBHOOK_SIGNING_SECRET:-}
WEBHOOK_TIMEOUT_SECONDS=${WEBHOOK_TIMEOUT_SECONDS:-5.0}
DATABASE_URL=${PROD_DATABASE_URL}
PROD_DATABASE_URL=${PROD_DATABASE_URL}
SQLALCHEMY_ECHO=${SQLALCHEMY_ECHO:-false}
DB_POOL_SIZE=${DB_POOL_SIZE:-20}
DB_MAX_OVERFLOW=${DB_MAX_OVERFLOW:-40}
POSTGRES_USER=${POSTGRES_USER:-${db_user}}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-${db_password}}
POSTGRES_DB=${POSTGRES_DB:-lms}
SECRET_KEY=${SECRET_KEY}
ALGORITHM=${ALGORITHM:-HS256}
ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES:-15}
REFRESH_TOKEN_EXPIRE_DAYS=${REFRESH_TOKEN_EXPIRE_DAYS:-30}
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=${PASSWORD_RESET_TOKEN_EXPIRE_MINUTES:-30}
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES=${EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES:-1440}
REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN=${REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN:-false}
MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES=${MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES:-10}
MFA_LOGIN_CODE_EXPIRE_MINUTES=${MFA_LOGIN_CODE_EXPIRE_MINUTES:-10}
MFA_LOGIN_CODE_LENGTH=${MFA_LOGIN_CODE_LENGTH:-6}
ACCESS_TOKEN_BLACKLIST_ENABLED=${ACCESS_TOKEN_BLACKLIST_ENABLED:-true}
ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED=${ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED:-true}
FRONTEND_BASE_URL=${FRONTEND_BASE_URL:-https://${APP_DOMAIN}}
EMAIL_FROM=${EMAIL_FROM:-no-reply@${APP_DOMAIN}}
SMTP_HOST=${SMTP_HOST:-}
SMTP_PORT=${SMTP_PORT:-587}
SMTP_USERNAME=${SMTP_USERNAME:-}
SMTP_PASSWORD=${SMTP_PASSWORD:-}
SMTP_USE_TLS=${SMTP_USE_TLS:-true}
SMTP_USE_SSL=${SMTP_USE_SSL:-false}
APP_DOMAIN=${APP_DOMAIN}
LETSENCRYPT_EMAIL=${LETSENCRYPT_EMAIL}
CORS_ORIGINS=${CORS_ORIGINS:-https://${APP_DOMAIN}}
TRUSTED_HOSTS=${TRUSTED_HOSTS:-${APP_DOMAIN},localhost,127.0.0.1}
REDIS_URL=${PROD_REDIS_URL:-redis://redis:6379/0}
CELERY_BROKER_URL=${PROD_CELERY_BROKER_URL:-redis://redis:6379/1}
CELERY_RESULT_BACKEND=${PROD_CELERY_RESULT_BACKEND:-redis://redis:6379/2}
PROD_REDIS_URL=${PROD_REDIS_URL:-redis://redis:6379/0}
PROD_CELERY_BROKER_URL=${PROD_CELERY_BROKER_URL:-redis://redis:6379/1}
PROD_CELERY_RESULT_BACKEND=${PROD_CELERY_RESULT_BACKEND:-redis://redis:6379/2}
TASKS_FORCE_INLINE=false
RATE_LIMIT_USE_REDIS=${RATE_LIMIT_USE_REDIS:-true}
RATE_LIMIT_REQUESTS_PER_MINUTE=${RATE_LIMIT_REQUESTS_PER_MINUTE:-100}
RATE_LIMIT_WINDOW_SECONDS=${RATE_LIMIT_WINDOW_SECONDS:-60}
RATE_LIMIT_REDIS_PREFIX=${RATE_LIMIT_REDIS_PREFIX:-ratelimit}
RATE_LIMIT_EXCLUDED_PATHS=${RATE_LIMIT_EXCLUDED_PATHS:-/,/docs,/redoc,/openapi.json,/api/v1/health,/api/v1/ready,/metrics}
AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE=${AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE:-5}
AUTH_RATE_LIMIT_WINDOW_SECONDS=${AUTH_RATE_LIMIT_WINDOW_SECONDS:-60}
AUTH_RATE_LIMIT_PATHS=${AUTH_RATE_LIMIT_PATHS:-/api/v1/auth/login,/api/v1/auth/token,/api/v1/auth/login/mfa}
FILE_UPLOAD_RATE_LIMIT_REQUESTS_PER_HOUR=${FILE_UPLOAD_RATE_LIMIT_REQUESTS_PER_HOUR:-10}
FILE_UPLOAD_RATE_LIMIT_WINDOW_SECONDS=${FILE_UPLOAD_RATE_LIMIT_WINDOW_SECONDS:-3600}
FILE_UPLOAD_RATE_LIMIT_PATHS=${FILE_UPLOAD_RATE_LIMIT_PATHS:-/api/v1/files/upload}
UPLOAD_DIR=${UPLOAD_DIR:-uploads}
CERTIFICATES_DIR=${CERTIFICATES_DIR:-certificates}
MAX_UPLOAD_MB=${MAX_UPLOAD_MB:-100}
ALLOWED_UPLOAD_EXTENSIONS=${ALLOWED_UPLOAD_EXTENSIONS:-mp4,avi,mov,pdf,doc,docx,jpg,jpeg,png}
FILE_STORAGE_PROVIDER=${FILE_STORAGE_PROVIDER:-azure}
FILE_DOWNLOAD_URL_EXPIRE_SECONDS=${FILE_DOWNLOAD_URL_EXPIRE_SECONDS:-900}
AZURE_KEYVAULT_URL=${AZURE_KEYVAULT_URL:-}
AZURE_CLIENT_ID=${AZURE_CLIENT_ID:-}
AZURE_TENANT_ID=${AZURE_TENANT_ID:-}
AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET:-}
AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION_STRING:-}
AZURE_STORAGE_ACCOUNT_NAME=${AZURE_STORAGE_ACCOUNT_NAME:-}
AZURE_STORAGE_ACCOUNT_KEY=${AZURE_STORAGE_ACCOUNT_KEY:-}
AZURE_STORAGE_ACCOUNT_URL=${AZURE_STORAGE_ACCOUNT_URL:-}
AZURE_STORAGE_CONTAINER_NAME=${AZURE_STORAGE_CONTAINER_NAME:-}
AZURE_STORAGE_CONTAINER_URL=${AZURE_STORAGE_CONTAINER_URL:-}
EOF
}

run_vm_deploy() {
    local app_dir="${APP_DIR:-/opt/lms_backend}"
    local env_file="${app_dir}/.env"
    local compose_file="${app_dir}/docker-compose.prod.yml"
    local ready_url="http://127.0.0.1/api/v1/ready"
    local compose_ps_output

    require_env "PROD_DATABASE_URL"
    require_env "SECRET_KEY"
    require_env "APP_DOMAIN"
    require_env "LETSENCRYPT_EMAIL"

    if [[ "${#SECRET_KEY}" -lt 32 ]]; then
        fail "SECRET_KEY must be at least 32 characters for production"
    fi

    require_command "docker"
    require_command "curl"
    select_compose_cmd

    mkdir -p "${app_dir}"
    cd "${app_dir}"

    if [[ ! -f "${compose_file}" ]]; then
        fail "Compose file not found: ${compose_file}"
    fi

    write_env_file "${env_file}"
    chmod 600 "${env_file}"
    run_env_validation "${app_dir}" "${env_file}"

    log "Running migrations"
    "${COMPOSE_CMD[@]}" -f "${compose_file}" run --build --rm migrate

    log "Starting production services"
    "${COMPOSE_CMD[@]}" -f "${compose_file}" up -d --build --remove-orphans redis api celery-worker celery-beat caddy

    log "Waiting for API readiness via Caddy"
    for _ in $(seq 1 30); do
        if curl -fsS -H "Host: ${APP_DOMAIN}" "${ready_url}" >/dev/null; then
            log "Deployment succeeded: https://${APP_DOMAIN}/api/v1/ready"
            return
        fi
        sleep 5
    done

    compose_ps_output="$("${COMPOSE_CMD[@]}" -f "${compose_file}" ps || true)"
    echo "${compose_ps_output}"
    "${COMPOSE_CMD[@]}" -f "${compose_file}" logs --tail=120 api caddy celery-worker celery-beat || true
    fail "Deployment finished but readiness probe did not pass"
}

run_remote_deploy() {
    local vm_host="${AZURE_VM_HOST:-}"
    local vm_user="${AZURE_VM_USER:-}"
    local app_dir="${APP_DIR:-/opt/lms_backend}"
    local ssh_port="${AZURE_VM_SSH_PORT:-22}"
    local ssh_opts=(-p "${ssh_port}" -o StrictHostKeyChecking=no)
    local temp_root archive_file env_file remote_archive remote_env

    require_env "AZURE_VM_HOST"
    require_env "AZURE_VM_USER"
    require_env "PROD_DATABASE_URL"
    require_env "SECRET_KEY"
    require_env "APP_DOMAIN"
    require_env "LETSENCRYPT_EMAIL"

    require_command "git"
    require_command "ssh"
    require_command "scp"

    temp_root="$(mktemp -d)"
    archive_file="${temp_root}/release.tar.gz"
    env_file="${temp_root}/deploy.env"
    remote_archive="/tmp/lms_backend_release.tar.gz"
    remote_env="/tmp/lms_backend_deploy.env"

    trap 'rm -rf "${temp_root}"' EXIT

    git archive --format=tar.gz -o "${archive_file}" HEAD

    cat > "${env_file}" <<EOF
APP_DIR=${app_dir}
PROD_DATABASE_URL=${PROD_DATABASE_URL}
SECRET_KEY=${SECRET_KEY}
APP_DOMAIN=${APP_DOMAIN}
LETSENCRYPT_EMAIL=${LETSENCRYPT_EMAIL}
FRONTEND_BASE_URL=${FRONTEND_BASE_URL:-}
CORS_ORIGINS=${CORS_ORIGINS:-}
TRUSTED_HOSTS=${TRUSTED_HOSTS:-}
SMTP_HOST=${SMTP_HOST:-}
SMTP_PORT=${SMTP_PORT:-}
SMTP_USERNAME=${SMTP_USERNAME:-}
SMTP_PASSWORD=${SMTP_PASSWORD:-}
EMAIL_FROM=${EMAIL_FROM:-}
SMTP_USE_TLS=${SMTP_USE_TLS:-}
SMTP_USE_SSL=${SMTP_USE_SSL:-}
SENTRY_DSN=${SENTRY_DSN:-}
SENTRY_RELEASE=${SENTRY_RELEASE:-}
AZURE_KEYVAULT_URL=${AZURE_KEYVAULT_URL:-}
AZURE_CLIENT_ID=${AZURE_CLIENT_ID:-}
AZURE_TENANT_ID=${AZURE_TENANT_ID:-}
AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET:-}
FILE_STORAGE_PROVIDER=${FILE_STORAGE_PROVIDER:-}
AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION_STRING:-}
AZURE_STORAGE_ACCOUNT_NAME=${AZURE_STORAGE_ACCOUNT_NAME:-}
AZURE_STORAGE_ACCOUNT_KEY=${AZURE_STORAGE_ACCOUNT_KEY:-}
AZURE_STORAGE_ACCOUNT_URL=${AZURE_STORAGE_ACCOUNT_URL:-}
AZURE_STORAGE_CONTAINER_NAME=${AZURE_STORAGE_CONTAINER_NAME:-}
AZURE_STORAGE_CONTAINER_URL=${AZURE_STORAGE_CONTAINER_URL:-}
EOF
    chmod 600 "${env_file}"

    log "Uploading release archive to ${vm_user}@${vm_host}"
    scp "${ssh_opts[@]}" "${archive_file}" "${vm_user}@${vm_host}:${remote_archive}"
    scp "${ssh_opts[@]}" "${env_file}" "${vm_user}@${vm_host}:${remote_env}"

    log "Executing deployment on VM"
    ssh "${ssh_opts[@]}" "${vm_user}@${vm_host}" <<'EOF'
set -euo pipefail
set -a
source /tmp/lms_backend_deploy.env
set +a
mkdir -p "${APP_DIR}"
find "${APP_DIR}" -mindepth 1 -maxdepth 1 ! -name ".env" -exec rm -rf {} +
tar -xzf /tmp/lms_backend_release.tar.gz -C "${APP_DIR}"
cd "${APP_DIR}"
    chmod +x scripts/platform/linux/deploy_azure_vm.sh
    DEPLOY_MODE=vm ./scripts/platform/linux/deploy_azure_vm.sh
rm -f /tmp/lms_backend_release.tar.gz /tmp/lms_backend_deploy.env
EOF
}

if [[ "${DEPLOY_MODE:-}" == "vm" ]]; then
    log "Starting VM-local deployment mode"
    run_vm_deploy
elif [[ -n "${AZURE_VM_HOST:-}" || -n "${AZURE_VM_USER:-}" ]]; then
    log "Starting remote deployment mode"
    run_remote_deploy
else
    log "Starting VM-local deployment mode"
    run_vm_deploy
fi
