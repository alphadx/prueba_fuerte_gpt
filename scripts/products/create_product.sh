#!/usr/bin/env bash
set -euo pipefail

KEYCLOAK_HOST="${KEYCLOAK_HOST:-http://localhost:8081}"
API_HOST="${API_HOST:-http://localhost:8000}"
REALM="${KEYCLOAK_REALM:-erp-barrio}"
CLIENT_ID="${KEYCLOAK_CLIENT_ID:-erp-web}"

USERNAME="${USERNAME:-}"
PASSWORD="${PASSWORD:-}"
SKU="${SKU:-COMP-001}"
NAME="${NAME:-Computadoras}"
PRICE="${PRICE:-599990}"

usage() {
  echo "Uso: USERNAME=<user> PASSWORD=<pass> [SKU=.. NAME=.. PRICE=..] bash scripts/products/create_product.sh"
  exit 1
}

if [[ -z "$USERNAME" || -z "$PASSWORD" ]]; then
  usage
fi

TOKEN_RESPONSE="$(curl -s -X POST "$KEYCLOAK_HOST/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=$CLIENT_ID&username=$USERNAME&password=$PASSWORD")"

AUTH_TOKEN="$(echo "$TOKEN_RESPONSE" | jq -r '.access_token // empty')"

if [[ -z "$AUTH_TOKEN" ]]; then
  echo "ERROR: no se pudo obtener token de $USERNAME" >&2
  echo "$TOKEN_RESPONSE" | jq . >&2
  exit 1
fi

echo "[INFO] Consultando sucursales"
BRANCHES_RESPONSE="$(curl -s -X GET "$API_HOST/branches" -H "Authorization: Bearer $AUTH_TOKEN")"
echo "$BRANCHES_RESPONSE" | jq .

echo "[INFO] Creando producto"
PRODUCT_RESPONSE="$(curl -s -X POST "$API_HOST/products" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"sku\":\"$SKU\",\"name\":\"$NAME\",\"price\":$PRICE}")"

PRODUCT_ID="$(echo "$PRODUCT_RESPONSE" | jq -r '.id // empty')"
if [[ -z "$PRODUCT_ID" ]]; then
  echo "ERROR: no se pudo crear producto" >&2
  echo "$PRODUCT_RESPONSE" | jq . >&2
  exit 1
fi

echo "$PRODUCT_RESPONSE" | jq .

echo "[INFO] Verificando producto $PRODUCT_ID"
VERIFY_RESPONSE="$(curl -s -X GET "$API_HOST/products/$PRODUCT_ID" -H "Authorization: Bearer $AUTH_TOKEN")"
echo "$VERIFY_RESPONSE" | jq .

echo "OK PRODUCT_ID=$PRODUCT_ID SKU=$SKU NAME=$NAME PRICE=$PRICE"
