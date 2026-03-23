#!/usr/bin/env bash
set -euo pipefail

KEYCLOAK_HOST="${KEYCLOAK_HOST:-http://localhost:8081}"
REALM="${KEYCLOAK_REALM:-erp-barrio}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"

USERNAME="${USERNAME:-}"
ROLE="${ROLE:-}"

usage() {
  echo "Uso: USERNAME=<user> ROLE=<admin|bodega|cajero|rrhh> bash scripts/keycloak/assign_role.sh"
  exit 1
}

if [[ -z "$USERNAME" || -z "$ROLE" ]]; then
  usage
fi

ADMIN_TOKEN="$(curl -s -X POST "$KEYCLOAK_HOST/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=admin-cli&username=$ADMIN_USER&password=$ADMIN_PASS" | jq -r '.access_token // empty')"

if [[ -z "$ADMIN_TOKEN" ]]; then
  echo "ERROR: no se pudo obtener token admin" >&2
  exit 1
fi

USER_ID="$(curl -s -X GET "$KEYCLOAK_HOST/admin/realms/$REALM/users?username=$USERNAME" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id // empty')"

if [[ -z "$USER_ID" ]]; then
  echo "ERROR: usuario no existe: $USERNAME" >&2
  exit 1
fi

ROLE_REP="$(curl -s -X GET "$KEYCLOAK_HOST/admin/realms/$REALM/roles/$ROLE" \
  -H "Authorization: Bearer $ADMIN_TOKEN")"
ROLE_ID="$(echo "$ROLE_REP" | jq -r '.id // empty')"

if [[ -z "$ROLE_ID" ]]; then
  echo "ERROR: rol no existe: $ROLE" >&2
  exit 1
fi

curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/users/$USER_ID/role-mappings/realm" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "[{\"id\":\"$ROLE_ID\",\"name\":\"$ROLE\"}]" \
  > /dev/null

echo "OK USERNAME=$USERNAME ROLE=$ROLE"
