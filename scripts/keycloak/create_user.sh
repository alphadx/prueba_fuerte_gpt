#!/usr/bin/env bash
set -euo pipefail

KEYCLOAK_HOST="${KEYCLOAK_HOST:-http://localhost:8081}"
REALM="${KEYCLOAK_REALM:-erp-barrio}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"

USERNAME="${USERNAME:-}"
PASSWORD="${PASSWORD:-}"
EMAIL="${EMAIL:-}"
FIRST_NAME="${FIRST_NAME:-}"
LAST_NAME="${LAST_NAME:-}"

usage() {
  echo "Uso: USERNAME=<user> PASSWORD=<pass> [EMAIL=.. FIRST_NAME=.. LAST_NAME=..] bash scripts/keycloak/create_user.sh"
  exit 1
}

if [[ -z "$USERNAME" || -z "$PASSWORD" ]]; then
  usage
fi

if [[ -z "$EMAIL" ]]; then
  EMAIL="${USERNAME}@erp.local"
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
  curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/users" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USERNAME\",\"email\":\"$EMAIL\",\"firstName\":\"$FIRST_NAME\",\"lastName\":\"$LAST_NAME\",\"enabled\":true,\"emailVerified\":true}" \
    > /dev/null

  USER_ID="$(curl -s -X GET "$KEYCLOAK_HOST/admin/realms/$REALM/users?username=$USERNAME" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id // empty')"
fi

if [[ -z "$USER_ID" ]]; then
  echo "ERROR: no se pudo obtener USER_ID de $USERNAME" >&2
  exit 1
fi

curl -s -X PUT "$KEYCLOAK_HOST/admin/realms/$REALM/users/$USER_ID/reset-password" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"type\":\"password\",\"value\":\"$PASSWORD\",\"temporary\":false}" \
  > /dev/null

# Dejar usuario listo para direct grant
curl -s -X PUT "$KEYCLOAK_HOST/admin/realms/$REALM/users/$USER_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"id\":\"$USER_ID\",\"username\":\"$USERNAME\",\"email\":\"$EMAIL\",\"enabled\":true,\"emailVerified\":true,\"requiredActions\":[],\"attributes\":{}}" \
  > /dev/null

echo "OK USER_ID=$USER_ID USERNAME=$USERNAME"
