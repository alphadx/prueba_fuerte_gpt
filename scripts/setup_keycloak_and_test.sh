#!/usr/bin/env bash
set -euo pipefail

USERNAME="${USERNAME:-bodega1}"
PASSWORD="${PASSWORD:-pass123}"
ROLE="${ROLE:-bodega}"
SKU="${SKU:-COMP-001}"
NAME="${NAME:-Computadoras}"
PRICE="${PRICE:-599990}"

echo "[1/3] Crear/actualizar usuario"
USERNAME="$USERNAME" PASSWORD="$PASSWORD" EMAIL="${USERNAME}@erp.local" \
  bash scripts/keycloak/create_user.sh

echo "[2/3] Asignar rol"
USERNAME="$USERNAME" ROLE="$ROLE" bash scripts/keycloak/assign_role.sh

echo "[3/3] Crear producto"
USERNAME="$USERNAME" PASSWORD="$PASSWORD" SKU="$SKU" NAME="$NAME" PRICE="$PRICE" \
  bash scripts/products/create_product.sh
