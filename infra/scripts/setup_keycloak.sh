#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

KEYCLOAK_HOST="${KEYCLOAK_HOST:-http://localhost:8081}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
REALM="${KEYCLOAK_REALM:-erp-barrio}"

echo -e "${YELLOW}=== Keycloak Setup ===${NC}"
echo "Host: $KEYCLOAK_HOST"
echo "Realm: $REALM"
echo ""

# Check if Keycloak is reachable
if ! curl -s -f "$KEYCLOAK_HOST/health" > /dev/null 2>&1; then
  echo -e "${RED}ERROR: Keycloak not reachable at $KEYCLOAK_HOST${NC}"
  echo "Make sure Keycloak is running: make compose-up-full"
  exit 1
fi

echo -e "${GREEN}✓ Keycloak is reachable${NC}"
echo ""

# Get admin token
echo -e "${YELLOW}Obtaining admin token...${NC}"
ADMIN_TOKEN=$(curl -s -X POST "$KEYCLOAK_HOST/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=admin-cli" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASS" \
  -d "grant_type=password" | jq -r '.access_token // empty')

if [ -z "$ADMIN_TOKEN" ]; then
  echo -e "${RED}ERROR: Could not obtain admin token. Check credentials.${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Admin token obtained${NC}"
echo ""

# Create realm
echo -e "${YELLOW}Creating realm '$REALM'...${NC}"
curl -s -X POST "$KEYCLOAK_HOST/admin/realms" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"realm\":\"$REALM\",\"enabled\":true}" > /dev/null 2>&1 || true
echo -e "${GREEN}✓ Realm created or already exists${NC}"
echo ""

# Create roles
echo -e "${YELLOW}Creating roles...${NC}"
for ROLE in admin cajero bodega rrhh; do
  curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/roles" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$ROLE\"}" > /dev/null 2>&1 || true
  echo -e "${GREEN}✓ Role '$ROLE' created or already exists${NC}"
done
echo ""

# Create clients
echo -e "${YELLOW}Creating client 'erp-web' (public)...${NC}"
curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId":"erp-web",
    "publicClient":true,
    "directAccessGrantsEnabled":true,
    "redirectUris":["http://localhost:3000/*"]
  }' > /dev/null 2>&1 || true
echo -e "${GREEN}✓ Client 'erp-web' created or already exists${NC}"

echo -e "${YELLOW}Creating client 'erp-api' (confidential)...${NC}"
curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId":"erp-api",
    "publicClient":false,
    "serviceAccountsEnabled":true
  }' > /dev/null 2>&1 || true
echo -e "${GREEN}✓ Client 'erp-api' created or already exists${NC}"
echo ""

# Create test user
echo -e "${YELLOW}Creating test user 'cajero1'...${NC}"
curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username":"cajero1",
    "email":"cajero1@erp.local",
    "enabled":true
  }' > /dev/null 2>&1 || true
echo -e "${GREEN}✓ User 'cajero1' created or already exists${NC}"

# Get user ID and set password
echo -e "${YELLOW}Setting password for 'cajero1'...${NC}"
USER_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "$KEYCLOAK_HOST/admin/realms/$REALM/users?username=cajero1" | jq -r '.[0].id // empty')

if [ -n "$USER_ID" ]; then
  curl -s -X PUT "$KEYCLOAK_HOST/admin/realms/$REALM/users/$USER_ID/reset-password" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "type":"password",
      "value":"pass123",
      "temporary":false
    }' > /dev/null 2>&1 || true
  echo -e "${GREEN}✓ Password set${NC}"

  # Assign cajero role
  echo -e "${YELLOW}Assigning role 'cajero' to user...${NC}"
  ROLE_JSON=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$KEYCLOAK_HOST/admin/realms/$REALM/roles/cajero")
  
  curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/users/$USER_ID/role-mappings/realm" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "[$ROLE_JSON]" > /dev/null 2>&1 || true
  echo -e "${GREEN}✓ Role assigned${NC}"
fi
echo ""

echo -e "${GREEN}=== ✓ Setup completed ===${NC}"
echo ""
echo -e "${YELLOW}Test credentials:${NC}"
echo "  Username: cajero1"
echo "  Password: pass123"
echo "  Role: cajero"
echo ""
echo -e "${YELLOW}Get a token:${NC}"
echo "  TOKEN=\$(curl -s -X POST \"$KEYCLOAK_HOST/realms/$REALM/protocol/openid-connect/token\" \\"
echo "    -H \"Content-Type: application/x-www-form-urlencoded\" \\"
echo "    -d \"grant_type=password&client_id=erp-web&username=cajero1&password=pass123\" | jq -r .access_token)"
echo ""
echo -e "${YELLOW}Use it against the API:${NC}"
echo "  curl -H \"Authorization: Bearer \\\$TOKEN\" http://localhost:8000/health"
echo ""
