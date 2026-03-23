#!/usr/bin/env bash
# =============================================================================
# bootstrap.sh — Arranque completo del stack ERP Barrio Chile
#
# Uso:
#   ./scripts/bootstrap.sh [--profile core|full] [--skip-tests] [--down]
#
# Opciones:
#   --profile  core|full   Perfil de Compose a levantar (default: full)
#   --skip-tests           Omite la ejecución de pytest
#   --down                 Baja el stack al finalizar (útil para CI)
#
# Genera: docs/bootstrap_run_YYYY-MM-DD_HH-MM-SS.txt con resultados.
# =============================================================================
set -euo pipefail

# ── Configuración ─────────────────────────────────────────────────────────────
PROFILE="full"
SKIP_TESTS=false
BRING_DOWN=false
ENV_FILE=".env"
REPORT_DIR="docs"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
REPORT="${REPORT_DIR}/bootstrap_run_${TIMESTAMP}.txt"

# ── Argumentos ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    --skip-tests) SKIP_TESTS=true; shift ;;
    --down) BRING_DOWN=true; shift ;;
    *) echo "Argumento desconocido: $1"; exit 1 ;;
  esac
done

# ── Utilidades ────────────────────────────────────────────────────────────────
PASS="[PASS]"
FAIL="[FAIL]"
INFO="[INFO]"
SKIP="[SKIP]"

mkdir -p "$REPORT_DIR"

log() { echo "$1" | tee -a "$REPORT"; }
step() { log ""; log "════════════════════════════════════════"; log "  $1"; log "════════════════════════════════════════"; }
result() {
  local label="$1" status="$2" detail="${3:-}"
  local mark
  [[ "$status" == "ok" ]] && mark="$PASS" || mark="$FAIL"
  log "  ${mark} ${label}${detail:+  →  ${detail}}"
}

# ── Detección de GitHub Codespaces ───────────────────────────────────────────
# En Codespaces los puertos se exponen como:
#   https://${CODESPACE_NAME}-${PORT}.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}
# Las conexiones curl desde el terminal SÍ funcionan con 127.0.0.1 porque
# Docker mapea los puertos al loopback del host de Codespaces.
IN_CODESPACES=false
CS_BASE_URL=""
if [[ -n "${CODESPACE_NAME:-}" ]]; then
  IN_CODESPACES=true
  CS_DOMAIN="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
  CS_BASE_URL="https://${CODESPACE_NAME}-PORT.${CS_DOMAIN}"
fi

# Construye la URL de acceso según entorno
service_url() {
  local port="$1"
  if [[ "$IN_CODESPACES" == "true" ]]; then
    echo "https://${CODESPACE_NAME}-${port}.${CS_DOMAIN}"
  else
    echo "http://127.0.0.1:${port}"
  fi
}

# ── Encabezado del reporte ────────────────────────────────────────────────────
{
  echo "ERP Barrio Chile — Bootstrap Report"
  echo "Fecha     : $(date)"
  echo "Perfil    : ${PROFILE}"
  echo "Entorno   : ${ENV_FILE}"
  echo "Host      : $(hostname)"
  echo "Git ref   : $(git rev-parse --short HEAD 2>/dev/null || echo 'n/a')"
  if [[ "$IN_CODESPACES" == "true" ]]; then
    echo "Codespace : ${CODESPACE_NAME}"
    echo "URL base  : ${CS_BASE_URL}"
  fi
} | tee "$REPORT"

GLOBAL_STATUS=0

# ── PASO 1: Docker disponible ─────────────────────────────────────────────────
step "1/7  Doctor Docker"
if command -v docker &>/dev/null; then
  DOCKER_VER=$(docker --version 2>&1)
  COMPOSE_VER=$(docker compose version 2>&1 || echo "n/a")
  result "Docker Engine"  "ok" "$DOCKER_VER"
  result "Docker Compose" "ok" "$COMPOSE_VER"
else
  result "Docker Engine" "fail" "no encontrado — instalar antes de continuar"
  log "  $FAIL Abortando: Docker no disponible."
  exit 1
fi

# ── PASO 2: Levantar stack ────────────────────────────────────────────────────
step "2/7  Compose up --profile ${PROFILE}"
if docker compose --env-file "$ENV_FILE" --profile "$PROFILE" up -d --build 2>&1 | tee -a "$REPORT"; then
  result "compose up" "ok"
else
  result "compose up" "fail"
  GLOBAL_STATUS=1
fi

# Espera breve para que servicios estén listos
log "  ${INFO} Esperando 5 s a que los servicios estén listos..."
sleep 5

# ── PASO 3: Migraciones ───────────────────────────────────────────────────────
step "3/7  Migraciones SQL"
if docker compose --env-file "$ENV_FILE" run --rm tooling \
    python infra/scripts/migrate.py up 2>&1 | tee -a "$REPORT"; then
  result "migrate-up" "ok"
else
  result "migrate-up" "fail"
  GLOBAL_STATUS=1
fi

# ── PASO 4: Tests ─────────────────────────────────────────────────────────────
step "4/7  Suite de tests"
if [[ "$SKIP_TESTS" == "true" ]]; then
  log "  ${SKIP} Tests omitidos (--skip-tests)"
else
  if docker compose --env-file "$ENV_FILE" run --rm tooling \
      pytest -q 2>&1 | tee -a "$REPORT"; then
    result "pytest" "ok"
  else
    result "pytest" "fail"
    GLOBAL_STATUS=1
  fi
fi

# ── PASO 5: Health checks de endpoints ───────────────────────────────────────
step "5/7  Health checks API"

API_PORT=$(grep -E '^API_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]')
API_PORT="${API_PORT:-8000}"
API_URL=$(service_url "$API_PORT")

for ENDPOINT in health ready; do
  HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}" "http://127.0.0.1:${API_PORT}/${ENDPOINT}" || echo "000")
  BODY=$(curl -fsS "http://127.0.0.1:${API_PORT}/${ENDPOINT}" 2>/dev/null || echo "error")
  if [[ "$HTTP_CODE" == "200" ]]; then
    result "GET /${ENDPOINT}" "ok" "HTTP ${HTTP_CODE} — ${BODY}  [${API_URL}/${ENDPOINT}]"
  else
    result "GET /${ENDPOINT}" "fail" "HTTP ${HTTP_CODE}"
    GLOBAL_STATUS=1
  fi
done

# ── PASO 6: Health checks de servicios auxiliares ────────────────────────────
step "6/7  Health checks servicios auxiliares"

declare -A SERVICE_PORTS=(
  ["mailhog_ui"]="$(grep -E '^MAILHOG_UI_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]')"
  ["minio_console"]="$(grep -E '^MINIO_CONSOLE_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]')"
  ["keycloak"]="$(grep -E '^KEYCLOAK_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]')"
  ["greenmail_web"]="$(grep -E '^GREENMAIL_WEB_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]')"
)
SERVICE_PORTS["mailhog_ui"]="${SERVICE_PORTS["mailhog_ui"]:-8025}"
SERVICE_PORTS["minio_console"]="${SERVICE_PORTS["minio_console"]:-9001}"
SERVICE_PORTS["keycloak"]="${SERVICE_PORTS["keycloak"]:-8081}"
SERVICE_PORTS["greenmail_web"]="${SERVICE_PORTS["greenmail_web"]:-8082}"

for SVC in mailhog_ui minio_console keycloak greenmail_web; do
  PORT="${SERVICE_PORTS[$SVC]}"
  # Solo verifica si el perfil full está activo
  if [[ "$PROFILE" == "core" ]] && [[ "$SVC" != "mailhog_ui" ]]; then
    log "  ${SKIP} ${SVC}:${PORT} (solo en perfil full)"
    continue
  fi
  SVC_URL=$(service_url "$PORT")
  HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}" "http://127.0.0.1:${PORT}" || echo "000")
  if [[ "$HTTP_CODE" =~ ^(200|301|302|303|401|403)$ ]]; then
    result "${SVC}:${PORT}" "ok" "HTTP ${HTTP_CODE}  [${SVC_URL}]"
  else
    result "${SVC}:${PORT}" "fail" "HTTP ${HTTP_CODE}"
    [[ "$PROFILE" == "full" ]] && GLOBAL_STATUS=1
  fi
done

# ── PASO 7: compose down opcional ────────────────────────────────────────────
step "7/7  Teardown"
if [[ "$BRING_DOWN" == "true" ]]; then
  docker compose --env-file "$ENV_FILE" down 2>&1 | tee -a "$REPORT"
  result "compose down" "ok"
else
  log "  ${INFO} Stack dejado corriendo. Usa 'make compose-down' para detenerlo."
fi

# ── Tabla de URLs de acceso ───────────────────────────────────────────────────
step "URLs de acceso a servicios"
API_PORT=$(grep -E '^API_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]'); API_PORT="${API_PORT:-8000}"
WEB_PORT=$(grep -E '^WEB_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]');  WEB_PORT="${WEB_PORT:-3000}"
MH_UI_PORT=$(grep -E '^MAILHOG_UI_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]'); MH_UI_PORT="${MH_UI_PORT:-8025}"
MINIO_CP=$(grep -E '^MINIO_CONSOLE_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]'); MINIO_CP="${MINIO_CP:-9001}"
KC_PORT=$(grep -E '^KEYCLOAK_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]'); KC_PORT="${KC_PORT:-8081}"
GM_WEB=$(grep -E '^GREENMAIL_WEB_PORT=' "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]'); GM_WEB="${GM_WEB:-8082}"

log "  Servicio          Puerto  URL de acceso"
log "  ─────────────────────────────────────────────────────────────────"
log "  API /health        ${API_PORT}    $(service_url $API_PORT)/health"
log "  API /ready         ${API_PORT}    $(service_url $API_PORT)/ready"
log "  API /docs          ${API_PORT}    $(service_url $API_PORT)/docs"
log "  Web UI             ${WEB_PORT}    $(service_url $WEB_PORT)"
log "  Mailhog UI         ${MH_UI_PORT}   $(service_url $MH_UI_PORT)"
log "  MinIO Console      ${MINIO_CP}   $(service_url $MINIO_CP)"
log "  Keycloak           ${KC_PORT}   $(service_url $KC_PORT)"
log "  GreenMail Web      ${GM_WEB}   $(service_url $GM_WEB)"
if [[ "$IN_CODESPACES" == "true" ]]; then
  log ""
  log "  ℹ Los puertos de Codespaces son PRIVATE por defecto."
  log "  Para acceder desde el navegador abre la pestaña 'Ports' en VS Code"
  log "  y marca como Public los que necesites compartir."
fi

# ── Resumen final ─────────────────────────────────────────────────────────────
log ""
log "════════════════════════════════════════"
if [[ "$GLOBAL_STATUS" -eq 0 ]]; then
  log "  ✅  RESULTADO FINAL: PASS"
else
  log "  ❌  RESULTADO FINAL: FAIL — revisa los [FAIL] arriba"
fi
log "  Reporte completo: ${REPORT}"
log "════════════════════════════════════════"
log ""

exit "$GLOBAL_STATUS"
