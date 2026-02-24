#!/usr/bin/env bash
# Azure VM deployment script for demo environment.
# - Remote mode: run from local machine with AZURE_VM_HOST + AZURE_VM_USER.
# - VM mode: run on VM with DEPLOY_MODE=vm.

set -euo pipefail

log() {
    echo "[demo-deploy] $*"
}

fail() {
    echo "[demo-deploy] ERROR: $*" >&2
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

write_env_file() {
    local env_file="$1"
    local app_domain frontend_base_url cors_origins trusted_hosts
    local postgres_user postgres_password postgres_db demo_database_url

    app_domain="${APP_DOMAIN}"
    frontend_base_url="${FRONTEND_BASE_URL:-https://${app_domain}}"
    cors_origins="${CORS_ORIGINS:-https://${app_domain}}"
    trusted_hosts="${TRUSTED_HOSTS:-${app_domain},localhost,127.0.0.1}"

    postgres_user="${POSTGRES_USER:-lms_demo}"
    postgres_password="${POSTGRES_PASSWORD:-lms_demo}"
    postgres_db="${POSTGRES_DB:-lms_demo}"

    demo_database_url="${DEMO_DATABASE_URL:-postgresql+psycopg2://${postgres_user}:${postgres_password}@db:5432/${postgres_db}}"

    cat > "${env_file}" <<EOF
PROJECT_NAME=LMS Backend Demo Azure
VERSION=1.0.0
ENVIRONMENT=staging
API_V1_PREFIX=/api/v1
DEBUG=false
ENABLE_API_DOCS=${ENABLE_API_DOCS:-true}
STRICT_ROUTER_IMPORTS=${STRICT_ROUTER_IMPORTS:-false}
METRICS_ENABLED=${METRICS_ENABLED:-true}
METRICS_PATH=${METRICS_PATH:-/metrics}
API_RESPONSE_ENVELOPE_ENABLED=${API_RESPONSE_ENVELOPE_ENABLED:-false}
API_RESPONSE_SUCCESS_MESSAGE=${API_RESPONSE_SUCCESS_MESSAGE:-Success}
API_RESPONSE_ENVELOPE_EXCLUDED_PATHS=${API_RESPONSE_ENVELOPE_EXCLUDED_PATHS:-/docs,/redoc,/openapi.json,/metrics,/api/v1/health,/api/v1/ready,/api/v1/auth/token}
SENTRY_DSN=${SENTRY_DSN:-}
SENTRY_ENVIRONMENT=${SENTRY_ENVIRONMENT:-demo-azure}
SENTRY_RELEASE=${SENTRY_RELEASE:-}
SENTRY_TRACES_SAMPLE_RATE=${SENTRY_TRACES_SAMPLE_RATE:-0.0}
SENTRY_PROFILES_SAMPLE_RATE=${SENTRY_PROFILES_SAMPLE_RATE:-0.0}
SENTRY_SEND_PII=${SENTRY_SEND_PII:-false}
SENTRY_ENABLE_FOR_CELERY=${SENTRY_ENABLE_FOR_CELERY:-false}
WEBHOOKS_ENABLED=${WEBHOOKS_ENABLED:-false}
WEBHOOK_TARGET_URLS=${WEBHOOK_TARGET_URLS:-}
WEBHOOK_SIGNING_SECRET=${WEBHOOK_SIGNING_SECRET:-}
WEBHOOK_TIMEOUT_SECONDS=${WEBHOOK_TIMEOUT_SECONDS:-5.0}
APP_DOMAIN=${app_domain}
LETSENCRYPT_EMAIL=${LETSENCRYPT_EMAIL}
POSTGRES_USER=${postgres_user}
POSTGRES_PASSWORD=${postgres_password}
POSTGRES_DB=${postgres_db}
DATABASE_URL=${demo_database_url}
DEMO_DATABASE_URL=${demo_database_url}
SQLALCHEMY_ECHO=${SQLALCHEMY_ECHO:-false}
DB_POOL_SIZE=${DB_POOL_SIZE:-20}
DB_MAX_OVERFLOW=${DB_MAX_OVERFLOW:-40}
SECRET_KEY=${SECRET_KEY}
ALGORITHM=${ALGORITHM:-HS256}
ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES:-15}
REFRESH_TOKEN_EXPIRE_DAYS=${REFRESH_TOKEN_EXPIRE_DAYS:-30}
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=${PASSWORD_RESET_TOKEN_EXPIRE_MINUTES:-30}
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES=${EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES:-1440}
ALLOW_PUBLIC_ROLE_REGISTRATION=${ALLOW_PUBLIC_ROLE_REGISTRATION:-true}
REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN=${REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN:-false}
MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES=${MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES:-10}
MFA_LOGIN_CODE_EXPIRE_MINUTES=${MFA_LOGIN_CODE_EXPIRE_MINUTES:-10}
MFA_LOGIN_CODE_LENGTH=${MFA_LOGIN_CODE_LENGTH:-6}
ACCESS_TOKEN_BLACKLIST_ENABLED=${ACCESS_TOKEN_BLACKLIST_ENABLED:-true}
ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED=${ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED:-false}
ACCESS_TOKEN_BLACKLIST_PREFIX=${ACCESS_TOKEN_BLACKLIST_PREFIX:-auth:blacklist:access}
SECURITY_HEADERS_ENABLED=${SECURITY_HEADERS_ENABLED:-true}
FRONTEND_BASE_URL=${frontend_base_url}
EMAIL_FROM=${EMAIL_FROM:-no-reply@${app_domain}}
SMTP_HOST=${SMTP_HOST:-}
SMTP_PORT=${SMTP_PORT:-587}
SMTP_USERNAME=${SMTP_USERNAME:-}
SMTP_PASSWORD=${SMTP_PASSWORD:-}
SMTP_USE_TLS=${SMTP_USE_TLS:-true}
SMTP_USE_SSL=${SMTP_USE_SSL:-false}
CORS_ORIGINS=${cors_origins}
TRUSTED_HOSTS=${trusted_hosts}
REDIS_URL=${DEMO_REDIS_URL:-redis://redis:6379/0}
CELERY_BROKER_URL=${DEMO_CELERY_BROKER_URL:-redis://redis:6379/1}
CELERY_RESULT_BACKEND=${DEMO_CELERY_RESULT_BACKEND:-redis://redis:6379/2}
DEMO_REDIS_URL=${DEMO_REDIS_URL:-redis://redis:6379/0}
DEMO_CELERY_BROKER_URL=${DEMO_CELERY_BROKER_URL:-redis://redis:6379/1}
DEMO_CELERY_RESULT_BACKEND=${DEMO_CELERY_RESULT_BACKEND:-redis://redis:6379/2}
TASKS_FORCE_INLINE=${TASKS_FORCE_INLINE:-true}
RATE_LIMIT_USE_REDIS=${RATE_LIMIT_USE_REDIS:-true}
RATE_LIMIT_REQUESTS_PER_MINUTE=${RATE_LIMIT_REQUESTS_PER_MINUTE:-200}
RATE_LIMIT_WINDOW_SECONDS=${RATE_LIMIT_WINDOW_SECONDS:-60}
RATE_LIMIT_REDIS_PREFIX=${RATE_LIMIT_REDIS_PREFIX:-ratelimit}
RATE_LIMIT_EXCLUDED_PATHS=${RATE_LIMIT_EXCLUDED_PATHS:-/,/docs,/redoc,/openapi.json,/api/v1/health,/api/v1/ready,/metrics}
AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE=${AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE:-120}
AUTH_RATE_LIMIT_WINDOW_SECONDS=${AUTH_RATE_LIMIT_WINDOW_SECONDS:-60}
AUTH_RATE_LIMIT_PATHS=${AUTH_RATE_LIMIT_PATHS:-/api/v1/auth/login,/api/v1/auth/token,/api/v1/auth/login/mfa}
MAX_FAILED_LOGIN_ATTEMPTS=${MAX_FAILED_LOGIN_ATTEMPTS:-10}
FILE_UPLOAD_RATE_LIMIT_REQUESTS_PER_HOUR=${FILE_UPLOAD_RATE_LIMIT_REQUESTS_PER_HOUR:-200}
FILE_UPLOAD_RATE_LIMIT_WINDOW_SECONDS=${FILE_UPLOAD_RATE_LIMIT_WINDOW_SECONDS:-3600}
FILE_UPLOAD_RATE_LIMIT_PATHS=${FILE_UPLOAD_RATE_LIMIT_PATHS:-/api/v1/files/upload}
CACHE_ENABLED=${CACHE_ENABLED:-true}
CACHE_KEY_PREFIX=${CACHE_KEY_PREFIX:-demo:cache}
CACHE_DEFAULT_TTL_SECONDS=${CACHE_DEFAULT_TTL_SECONDS:-120}
COURSE_CACHE_TTL_SECONDS=${COURSE_CACHE_TTL_SECONDS:-120}
LESSON_CACHE_TTL_SECONDS=${LESSON_CACHE_TTL_SECONDS:-120}
QUIZ_CACHE_TTL_SECONDS=${QUIZ_CACHE_TTL_SECONDS:-120}
QUIZ_QUESTION_CACHE_TTL_SECONDS=${QUIZ_QUESTION_CACHE_TTL_SECONDS:-120}
UPLOAD_DIR=${UPLOAD_DIR:-uploads}
CERTIFICATES_DIR=${CERTIFICATES_DIR:-certificates}
MAX_UPLOAD_MB=${MAX_UPLOAD_MB:-100}
ALLOWED_UPLOAD_EXTENSIONS=${ALLOWED_UPLOAD_EXTENSIONS:-mp4,avi,mov,pdf,doc,docx,jpg,jpeg,png}
FILE_STORAGE_PROVIDER=${FILE_STORAGE_PROVIDER:-local}
FILE_DOWNLOAD_URL_EXPIRE_SECONDS=${FILE_DOWNLOAD_URL_EXPIRE_SECONDS:-900}
AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION_STRING:-}
AZURE_STORAGE_ACCOUNT_NAME=${AZURE_STORAGE_ACCOUNT_NAME:-}
AZURE_STORAGE_ACCOUNT_KEY=${AZURE_STORAGE_ACCOUNT_KEY:-}
AZURE_STORAGE_ACCOUNT_URL=${AZURE_STORAGE_ACCOUNT_URL:-}
AZURE_STORAGE_CONTAINER_NAME=${AZURE_STORAGE_CONTAINER_NAME:-}
AZURE_STORAGE_CONTAINER_URL=${AZURE_STORAGE_CONTAINER_URL:-}
UVICORN_WORKERS=${UVICORN_WORKERS:-1}
SEED_DEMO_DATA=${SEED_DEMO_DATA:-true}
DEMO_SKIP_ATTEMPT=${DEMO_SKIP_ATTEMPT:-true}
EOF
}

seed_demo_data() {
    local compose_file="$1"
    local env_file="$2"
    local skip_attempt="${DEMO_SKIP_ATTEMPT:-true}"
    local seed_enabled="${SEED_DEMO_DATA:-true}"

    if [[ "${seed_enabled}" != "true" ]]; then
        log "Skipping demo seed (SEED_DEMO_DATA=${seed_enabled})"
        return
    fi

    local seed_args=(
        scripts/database/seed_demo_data.py
        --reset-passwords
        --json-output
        postman/demo_seed_snapshot.azure.json
    )

    if [[ "${skip_attempt}" == "true" ]]; then
        seed_args+=(--skip-attempt)
    fi

    log "Seeding demo data"
    "${COMPOSE_CMD[@]}" --env-file "${env_file}" -f "${compose_file}" exec -T api python "${seed_args[@]}"
}

run_vm_deploy() {
    local app_dir="${APP_DIR:-/opt/lms_backend_demo}"
    local env_file="${app_dir}/.env.demo.azure"
    local compose_file="${app_dir}/docker-compose.demo.azure.yml"
    local ready_url="http://127.0.0.1/api/v1/ready"

    require_env "APP_DOMAIN"
    require_env "LETSENCRYPT_EMAIL"
    require_env "SECRET_KEY"

    if [[ "${#SECRET_KEY}" -lt 32 ]]; then
        fail "SECRET_KEY must be at least 32 characters"
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

    log "Running demo migrations"
    "${COMPOSE_CMD[@]}" --env-file "${env_file}" -f "${compose_file}" run --build --rm migrate

    log "Starting demo services"
    "${COMPOSE_CMD[@]}" --env-file "${env_file}" -f "${compose_file}" up -d --build --remove-orphans db redis api caddy

    log "Waiting for demo readiness via Caddy"
    for _ in $(seq 1 36); do
        if curl -fsS -H "Host: ${APP_DOMAIN}" "${ready_url}" >/dev/null; then
            seed_demo_data "${compose_file}" "${env_file}"
            log "Demo deployment succeeded: https://${APP_DOMAIN}/api/v1/ready"
            return
        fi
        sleep 5
    done

    "${COMPOSE_CMD[@]}" --env-file "${env_file}" -f "${compose_file}" ps || true
    "${COMPOSE_CMD[@]}" --env-file "${env_file}" -f "${compose_file}" logs --tail=120 api caddy db redis || true
    fail "Demo deployment finished but readiness probe did not pass"
}

run_remote_deploy() {
    local vm_host="${AZURE_VM_HOST:-}"
    local vm_user="${AZURE_VM_USER:-}"
    local app_dir="${APP_DIR:-/opt/lms_backend_demo}"
    local ssh_port="${AZURE_VM_SSH_PORT:-22}"
    local ssh_opts=(-p "${ssh_port}" -o StrictHostKeyChecking=no)
    local temp_root archive_file env_file
    local remote_archive="/tmp/lms_backend_demo_release.tar.gz"
    local remote_env="/tmp/lms_backend_demo_deploy.env"

    require_env "AZURE_VM_HOST"
    require_env "AZURE_VM_USER"
    require_env "APP_DOMAIN"
    require_env "LETSENCRYPT_EMAIL"
    require_env "SECRET_KEY"

    require_command "git"
    require_command "ssh"
    require_command "scp"

    temp_root="$(mktemp -d)"
    archive_file="${temp_root}/release.tar.gz"
    env_file="${temp_root}/deploy.env"

    trap 'rm -rf "${temp_root}"' EXIT

    git archive --format=tar.gz -o "${archive_file}" HEAD

    cat > "${env_file}" <<EOF
APP_DIR=${app_dir}
APP_DOMAIN=${APP_DOMAIN}
LETSENCRYPT_EMAIL=${LETSENCRYPT_EMAIL}
SECRET_KEY=${SECRET_KEY}
FRONTEND_BASE_URL=${FRONTEND_BASE_URL:-}
CORS_ORIGINS=${CORS_ORIGINS:-}
TRUSTED_HOSTS=${TRUSTED_HOSTS:-}
POSTGRES_USER=${POSTGRES_USER:-}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-}
POSTGRES_DB=${POSTGRES_DB:-}
DEMO_DATABASE_URL=${DEMO_DATABASE_URL:-}
DEMO_REDIS_URL=${DEMO_REDIS_URL:-}
DEMO_CELERY_BROKER_URL=${DEMO_CELERY_BROKER_URL:-}
DEMO_CELERY_RESULT_BACKEND=${DEMO_CELERY_RESULT_BACKEND:-}
FILE_STORAGE_PROVIDER=${FILE_STORAGE_PROVIDER:-}
AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION_STRING:-}
AZURE_STORAGE_ACCOUNT_NAME=${AZURE_STORAGE_ACCOUNT_NAME:-}
AZURE_STORAGE_ACCOUNT_KEY=${AZURE_STORAGE_ACCOUNT_KEY:-}
AZURE_STORAGE_ACCOUNT_URL=${AZURE_STORAGE_ACCOUNT_URL:-}
AZURE_STORAGE_CONTAINER_NAME=${AZURE_STORAGE_CONTAINER_NAME:-}
AZURE_STORAGE_CONTAINER_URL=${AZURE_STORAGE_CONTAINER_URL:-}
SMTP_HOST=${SMTP_HOST:-}
SMTP_PORT=${SMTP_PORT:-}
SMTP_USERNAME=${SMTP_USERNAME:-}
SMTP_PASSWORD=${SMTP_PASSWORD:-}
EMAIL_FROM=${EMAIL_FROM:-}
SENTRY_DSN=${SENTRY_DSN:-}
SENTRY_RELEASE=${SENTRY_RELEASE:-}
SEED_DEMO_DATA=${SEED_DEMO_DATA:-true}
DEMO_SKIP_ATTEMPT=${DEMO_SKIP_ATTEMPT:-true}
ENABLE_API_DOCS=${ENABLE_API_DOCS:-true}
UVICORN_WORKERS=${UVICORN_WORKERS:-1}
EOF
    chmod 600 "${env_file}"

    log "Uploading demo release archive to ${vm_user}@${vm_host}"
    scp "${ssh_opts[@]}" "${archive_file}" "${vm_user}@${vm_host}:${remote_archive}"
    scp "${ssh_opts[@]}" "${env_file}" "${vm_user}@${vm_host}:${remote_env}"

    log "Executing demo deployment on VM"
    ssh "${ssh_opts[@]}" "${vm_user}@${vm_host}" <<'EOF'
set -euo pipefail
set -a
source /tmp/lms_backend_demo_deploy.env
set +a
mkdir -p "${APP_DIR}"
find "${APP_DIR}" -mindepth 1 -maxdepth 1 ! -name ".env" ! -name ".env.demo.azure" -exec rm -rf {} +
tar -xzf /tmp/lms_backend_demo_release.tar.gz -C "${APP_DIR}"
cd "${APP_DIR}"
    chmod +x scripts/platform/linux/deploy_azure_demo_vm.sh
    DEPLOY_MODE=vm ./scripts/platform/linux/deploy_azure_demo_vm.sh
rm -f /tmp/lms_backend_demo_release.tar.gz /tmp/lms_backend_demo_deploy.env
EOF
}

if [[ "${DEPLOY_MODE:-}" == "vm" ]]; then
    log "Starting VM-local demo deployment mode"
    run_vm_deploy
elif [[ -n "${AZURE_VM_HOST:-}" || -n "${AZURE_VM_USER:-}" ]]; then
    log "Starting remote demo deployment mode"
    run_remote_deploy
else
    log "Starting VM-local demo deployment mode"
    run_vm_deploy
fi
