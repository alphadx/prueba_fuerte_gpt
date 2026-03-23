# Guía de Keycloak: Setup y obtención de tokens

## Resumen rápido

Esta guía explica cómo **configurar Keycloak** (crear realm, usuarios, clientes) y obtener **tokens JWT válidos** para pruebas contra la API en local o Codespaces.

## Requisitos previos

1. Stack levantado con perfil `full`:
   ```bash
   make compose-up-full
   ```
   o
   ```bash
   docker compose up -d keycloak keycloak-db
   ```

2. Acceso a Keycloak en:
   - **Local**: http://127.0.0.1:8081
   - **Codespaces**: https://<CODESPACE_NAME>-8081.app.github.dev

3. Credenciales admin por defecto (desde `.env`):
   - Username: `admin`
   - Password: `admin`

## Puertos y rutas

| Componente | Host | Interno | Ruta |
|---|---|---|---|
| **Keycloak UI/API** | `8081` | `8080` | http://localhost:8081 |
| **Token endpoint** | `8081` | `8080` | http://localhost:8081/realms/{realm}/protocol/openid-connect/token |
| **Admin API** | `8081` | `8080` | http://localhost:8081/admin/realms |

> **Nota crítica**: Keycloak escucha internamente en `8080` pero Docker lo expone en `8081` (host). Usa siempre `8081` en URLs locales.

## Opción A: Setup vía consola web (manual, recomendado para explorar)

### 1. Acceder a Keycloak Admin Console

Abre http://127.0.0.1:8081/ y entra como `admin:admin`.

### 2. Crear el realm `erp-barrio`

- Lado izquierdo: haz clic en el selector de realm (arriba) → **Create realm**.
- Nombre: `erp-barrio`
- Estado: **On**
- Clic **Create**.

### 3. Crear roles

En el realm `erp-barrio`:
- Menú: **Realm roles** (lado izquierdo, bajo "Configure")
- Clic **Create role**
- Repite para cada rol:
  - `admin`
  - `cajero`
  - `bodega`
  - `rrhh`

### 4. Crear clients

#### Client `erp-web` (público, para testing password grant)

- Menú: **Clients** → **Create client**
- Client ID: `erp-web`
- **Next**
- Capabilidad: marca **Direct access grants enabled** (permite password flow para testing)
- **Next → Save**
- En la pestaña **Access settings**, Redirect URIs: `http://localhost:3000/*`
- Guarda.

#### Client `erp-api` (confidential, para backend/service accounts)

- Menú: **Clients** → **Create client**
- Client ID: `erp-api`
- Client authentication: **On** (confidential client)
- **Next**
- Capabilidades: marca **Service accounts enabled** (permite client credentials flow)
- **Next → Save**
- Guarda y copia el **Client secret** de la pestaña **Credentials** (lo necesitarás luego).

### 5. Crear usuario para testing

- Menú: **Users** → **Add user**
- Username: `cajero1`
- Email: `cajero1@erp.local`
- First name: `Juan`
- Last name: `Cajero`
- Enabled: **On**
- **Create**

En la pestaña **Credentials**:
- Clic **Set password**
- Password: `pass123`
- Confirm password: `pass123`
- Temporary: **Off** (para evitar reset en primer login)
- **Set password**

En la pestaña **Role mappings**:
- Clic **Assign role**
- Selecciona `cajero` (realm role)
- **Assign**

## Opción B: Setup vía admin API (automatizado, ideal para CI/CD)

Ejecuta el script automático:

```bash
./infra/scripts/setup_keycloak.sh
```

O si prefieres hacerlo manualmente línea por línea:

```bash
#!/bin/bash
set -e

KEYCLOAK_HOST="http://localhost:8081"
ADMIN_USER="admin"
ADMIN_PASS="admin"
REALM="erp-barrio"

echo "=== Obtener token admin ==="
ADMIN_TOKEN=$(curl -s -X POST "$KEYCLOAK_HOST/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=admin-cli" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASS" \
  -d "grant_type=password" | jq -r .access_token)

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
  echo "ERROR: No se pudo obtener token admin. Verifica Keycloak está levantado."
  exit 1
fi
echo "✓ Token admin obtenido"

echo "=== Crear realm $REALM ==="
curl -s -X POST "$KEYCLOAK_HOST/admin/realms" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"realm\":\"$REALM\",\"enabled\":true}" | jq . || echo "✓ Realm creado o ya existe"

echo "=== Crear roles ==="
for ROLE in admin cajero bodega rrhh; do
  curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/roles" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$ROLE\"}" | jq . || echo "✓ Rol $ROLE creado o ya existe"
done

echo "=== Crear client erp-web (público) ==="
curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId":"erp-web",
    "publicClient":true,
    "directAccessGrantsEnabled":true,
    "redirectUris":["http://localhost:3000/*"]
  }' | jq . || echo "✓ Client erp-web creado o ya existe"

echo "=== Crear client erp-api (confidential) ==="
curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId":"erp-api",
    "publicClient":false,
    "serviceAccountsEnabled":true
  }' | jq . || echo "✓ Client erp-api creado o ya existe"

echo "=== Crear usuario cajero1 ==="
curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username":"cajero1",
    "email":"cajero1@erp.local",
    "enabled":true
  }' | jq . || echo "✓ Usuario cajero1 creado o ya existe"

echo "=== Establecer contraseña para cajero1 ==="
USER_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "$KEYCLOAK_HOST/admin/realms/$REALM/users?username=cajero1" | jq -r '.[0].id')

curl -s -X PUT "$KEYCLOAK_HOST/admin/realms/$REALM/users/$USER_ID/reset-password" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type":"password",
    "value":"pass123",
    "temporary":false
  }' | jq . || echo "✓ Contraseña establecida"

echo "=== Asignar rol 'cajero' a cajero1 ==="
ROLE_JSON=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "$KEYCLOAK_HOST/admin/realms/$REALM/roles/cajero")

curl -s -X POST "$KEYCLOAK_HOST/admin/realms/$REALM/users/$USER_ID/role-mappings/realm" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "[$ROLE_JSON]" | jq . || echo "✓ Rol asignado"

echo ""
echo "=== ✓ Setup completado ==="
echo "Usuario: cajero1"
echo "Contraseña: pass123"
echo "Rol: cajero"
echo ""
```

## Obtener tokens (para testing)

### 1. Password grant (usuario + contraseña, para testing)

```bash
TOKEN=$(curl -s -X POST "http://localhost:8081/realms/erp-barrio/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=erp-web" \
  -d "username=cajero1" \
  -d "password=pass123" | jq -r .access_token)

echo "$TOKEN"
```

### 2. Client credentials grant (backend a backend)

```bash
# Primero obtén el client secret de erp-api (desde admin console o API)
CLIENT_SECRET="<el_secreto_de_erp_api>"

TOKEN=$(curl -s -X POST "http://localhost:8081/realms/erp-barrio/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=erp-api" \
  -d "client_secret=$CLIENT_SECRET" | jq -r .access_token)

echo "$TOKEN"
```

## Decodificar y validar token

```bash
# Decodificar payload
echo -n "$TOKEN" | cut -d. -f2 | base64 --decode | jq .
```

Espera ver algo como:
```json
{
  "exp": 1774240400,
  "iat": 1774240100,
  "jti": "abc123...",
  "iss": "http://localhost:8081/realms/erp-barrio",
  "aud": ["erp-web"],
  "sub": "user-uuid-here",
  "typ": "Bearer",
  "azp": "erp-web",
  "session_state": "...",
  "realm_access": {
    "roles": ["cajero"]
  },
  "scope": "profile email"
}
```

## Usar token contra la API

```bash
# Asigna el token a una variable
TOKEN="eyJhbG..."

# Llama a un endpoint protegido
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/protected-endpoint
```

Ejemplo con un endpoint real (ej. crear un producto, si requiere admin):
```bash
curl -X POST http://localhost:8000/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sku":"TEST-001","name":"Test","price":100}'
```

La API validará:
- Firma del token (si `JWT_HS256_SECRET` está definido)
- Expiración (`exp`)
- Roles requeridos por el endpoint

## Variables de entorno para validación

En `apps/api`, puedes configurar:

```bash
# Verificación de firma (si está en .env)
JWT_HS256_SECRET=test-secret

# Permitir tokens sin firma (solo desarrollo local)
JWT_ALLOW_INSECURE_TOKENS=true

# Validación de emisor (opcional)
JWT_EXPECTED_ISS=http://localhost:8081/realms/erp-barrio

# Validación de audiencia (opcional)
JWT_EXPECTED_AUD=erp-web
```

> **Nota**: Por defecto la API **no valida firma** de tokens de Keycloak (porque Keycloak usa RS256 y la API espera HS256 o sin verificación). Si quieres validar la firma de Keycloak, necesitas obtener la clave pública en `http://localhost:8081/realms/erp-barrio/protocol/openid-connect/certs` y configurar validación RSA en la API.

## Troubleshooting

| Error | Causa | Solución |
|---|---|---|
| `"error": "Realm does not exist"` | El realm `erp-barrio` no se creó | Ejecuta setup (Opción A o B) |
| `"error": "HTTP 401 Unauthorized"` (admin API) | Token admin inválido o expirado | Regenera: `export ADMIN_TOKEN=$(curl ... grant_type=password ...)` |
| `null` en `jq -r .access_token` | El request de token falló | Verifica username/password/client_id en el curl |
| API devuelve 401 "Missing bearer token" | No incluiste el header Authorization | Añade `-H "Authorization: Bearer $TOKEN"` |
| API devuelve 401 "Invalid roles claim" | El token no tiene `roles` o `realm_access.roles` | Asigna un rol al usuario (step 5 Opción A, o verifica assignación en API) |

## Referencias

- [Documentación de autenticación (auth_strategy.md)](./auth_strategy.md)
- [Código de validación en API (auth.py)](../apps/api/app/core/auth.py)
- [Variables de entorno (.env)](../.env)
- [Documentos oficiales de Keycloak](https://www.keycloak.org/documentation)
