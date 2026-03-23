#!/usr/bin/env bash
set -euo pipefail

# Wrapper de compatibilidad: delega a scripts/products/create_product.sh
USERNAME="${TEST_USER:-${USERNAME:-bodega1}}"
PASSWORD="${TEST_PASSWORD:-${PASSWORD:-pass123}}"
SKU="${PRODUCT_SKU:-${SKU:-COMP-001}}"
NAME="${PRODUCT_NAME:-${NAME:-Computadoras}}"
PRICE="${PRODUCT_PRICE:-${PRICE:-599990}}"

USERNAME="$USERNAME" PASSWORD="$PASSWORD" SKU="$SKU" NAME="$NAME" PRICE="$PRICE" \
  bash scripts/products/create_product.sh
