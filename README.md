# ERP Barrio Chile - Monorepo base

Este repositorio implementa los **pasos 2, 3 y 4 del plan**: arquitectura base ejecutable, soporte Docker Compose y migraciones iniciales del modelo de datos MVP.

## Estructura

- `apps/api`: API FastAPI y contrato OpenAPI.
- `apps/web`: frontend Next.js (esqueleto).
- `workers/alerts`: worker asíncrono para alertas.
- `infra`: utilidades de infraestructura y seeds.
- `tests`: pruebas unitarias e integración iniciales.

## Requisitos

- Docker Engine + Docker Compose v2
- GNU Make

> Nota: Python/Node locales quedan opcionales para flujos legacy. El flujo principal del repo se ejecuta con Docker.

## Arranque rápido (una sola línea)

```bash
make bootstrap          # levanta stack full + migra + testea + genera reporte
```

El reporte queda en `docs/bootstrap_run_YYYY-MM-DD_HH-MM-SS.txt`.

Opciones avanzadas del script directo:

```bash
./scripts/bootstrap.sh --profile core          # solo servicios core
./scripts/bootstrap.sh --profile full          # stack completo (default)
./scripts/bootstrap.sh --profile full --down   # levanta, valida y baja (CI)
./scripts/bootstrap.sh --skip-tests            # omite pytest
```

---

## Puertos expuestos

| Servicio | Puerto host | URL de acceso | Perfil |
|---|---|---|---|
| **API FastAPI** | `8000` | http://127.0.0.1:8000 | core / full |
| **API /health** | `8000` | http://127.0.0.1:8000/health | core / full |
| **API /ready** | `8000` | http://127.0.0.1:8000/ready | core / full |
| **PostgreSQL** | `5432` | `psql -h 127.0.0.1 -U erp_user -d erp_barrio` | core / full |
| **Redis** | `6379` | `redis-cli -h 127.0.0.1` | core / full |
| **Web estática** | `3000` | http://127.0.0.1:3000 | core / full |
| **Mailhog UI** | `8025` | http://127.0.0.1:8025 | full |
| **Mailhog SMTP** | `1025` | `smtp://127.0.0.1:1025` | full |
| **MinIO API** | `9000` | http://127.0.0.1:9000 | full |
| **MinIO Console** | `9001` | http://127.0.0.1:9001 | full |
| **Keycloak** | `8081` | http://127.0.0.1:8081 | full |
| **Keycloak DB** | `5433` | `psql -h 127.0.0.1 -p 5433 -U keycloak -d keycloak` | full |
| **GreenMail SMTP** | `3025` | `smtp://127.0.0.1:3025` | full |
| **GreenMail IMAP** | `3143` | `imap://127.0.0.1:3143` | full |
| **GreenMail Web** | `8082` | http://127.0.0.1:8082 | full |

> Los puertos pueden sobreescribirse en el archivo `.env` (ver `.env.example`).

---

## Acceso en GitHub Codespaces

En Codespaces los servicios Docker se exponen automáticamente con URLs públicas de la forma:

```
https://<CODESPACE_NAME>-<PUERTO>.app.github.dev
```

Para ver las URLs exactas de tu entorno (local **o** Codespaces) ejecuta:

```bash
make urls
```

Ejemplo de salida en Codespaces:

```
── Codespaces URLs ──────────────────────────────────────────────────────
API /health   : https://obscure-system-7wq7q7x94wcpgpj-8000.app.github.dev/health
API /docs     : https://obscure-system-7wq7q7x94wcpgpj-8000.app.github.dev/docs
Web UI        : https://obscure-system-7wq7q7x94wcpgpj-3000.app.github.dev
Mailhog UI    : https://obscure-system-7wq7q7x94wcpgpj-8025.app.github.dev
MinIO Console : https://obscure-system-7wq7q7x94wcpgpj-9001.app.github.dev
Keycloak      : https://obscure-system-7wq7q7x94wcpgpj-8081.app.github.dev
GreenMail Web : https://obscure-system-7wq7q7x94wcpgpj-8082.app.github.dev
─────────────────────────────────────────────────────────────────────────
ℹ  Puertos PRIVATE por defecto. Cambia visibilidad en la pestaña Ports de VS Code.
```

> **Nota sobre visibilidad**: por defecto todos los puertos están en modo `Private` (requieren autenticación con tu cuenta GitHub). Si necesitas compartir una URL, abre la pestaña **Ports** en VS Code y cambia la visibilidad a `Public`.

> **Nota sobre Keycloak**: las redirecciones OAuth2 de Keycloak usan `localhost` por defecto. En Codespaces hay que configurar el `frontendUrl` de Keycloak como `https://<CODESPACE_NAME>-8081.app.github.dev` para que los flujos SSO funcionen correctamente desde el navegador.

---

## Comandos principales

```bash
make bootstrap          # arranque completo automatizado (recomendado)
make urls               # imprime las URLs de acceso (local o Codespaces)
make up                 # levanta stack core
make test               # corre tests en contenedor tooling
make seed               # genera datos semilla
make migrate-up         # aplica migraciones pendientes
make migrate-status     # lista migraciones aplicadas
make verify-step4       # validaciones estáticas paso 4
make compose-up         # levanta perfil core
make compose-up-full    # levanta perfil full
make compose-down       # baja el stack
make compose-smoke      # smoke /health + /ready
make architecture-review
```

### Qué hace cada comando

- `make up`: levanta stack `core` con Docker Compose (`postgres`, `redis`, `api`, `worker`, `web`, `tooling`). El servicio `web` publica el frontend estático de `apps/web` en el puerto `3000`.
- `make test`: ejecuta tests en contenedor `tooling` (sin `venv` local).
- `make seed`: genera datos semilla iniciales en `infra/seeds/dev_seed.json` desde `tooling`.
- `make migrate-up`: aplica migraciones SQL versionadas desde `tooling` contra PostgreSQL de Compose.
- `make migrate-status`: lista versiones de migración aplicadas desde `tooling`.
- `make verify-step4`: ejecuta validaciones estáticas desde `tooling`.
- `make compose-up`: levanta perfil `core` (`postgres`, `redis`, `api`, `worker`, `web`, `tooling`).
- `make compose-up-full`: levanta perfil `full` (core + `mailhog`, `greenmail`, `minio`, `keycloak`, `keycloak-db`).
- `make compose-down`: baja servicios Docker Compose.
- `make compose-smoke`: valida endpoints `/health` y `/ready` de la API levantada por Compose.
- `make architecture-review`: revisa requisitos críticos de arquitectura (IMAP, UX web/móvil, QR P2P).

## Contrato OpenAPI como fuente de verdad

El contrato vive en `apps/api/openapi.yaml`. Cualquier endpoint nuevo debe declararse primero ahí.

## Endpoints iniciales

- `GET /health`: disponibilidad del servicio.
- `POST /alerts/dispatch`: encola alertas documentales hacia Redis/worker.

## Estándares y colaboración

- Estándares técnicos y guía de colaboración (humanos + GPTs): `docs/development_standards.md`.
- Guía específica del paso 2: `docs/architecture_base.md`.
- Registro de avance del plan: `docs/progress_log.md`.
- Migraciones y diagrama ER base (paso 4): `infra/migrations/README.md`.
- Revisión de mitigaciones del paso 2: `docs/step2_mitigations.md`.


## Política operativa de sesión (Docker)

- En cada sesión técnica se debe validar Docker al inicio con `make doctor-docker`.
- Si Docker no está instalado/disponible, **primero se debe instalar/habilitar** antes de ejecutar pruebas reales con Compose.
- Para pruebas integradas de servicios usar `make compose-up` (o `make compose-up-full`).
- Para ejecución de tests/scripts Python usar el servicio `tooling` vía targets `make`.


## Control de usuarios y SSO

- Se adopta estrategia de identidad con **Keycloak** (OIDC/OAuth2).
- Diseño y consideraciones: [docs/auth_strategy.md](docs/auth_strategy.md).
- En perfil `full`, Keycloak queda disponible inmediatamente.

### Setup rápido de Keycloak para testing

Para crear realm, usuarios, clientes y obtener tokens JWT en local:

1. **Levanta el stack con perfil full:**
   ```bash
   make compose-up-full
   ```

2. **Opción A - Setup vía consola web (exploración manual):**
   - Accede a http://127.0.0.1:8081 (credenciales: `admin`/`admin`)
   - Crea realm `erp-barrio`, usuarios, roles y clients manualmente
   - Detalles completos: [docs/keycloak_quickstart.md](docs/keycloak_quickstart.md)

3. **Opción B - Setup automatizado:**
   ```bash
   chmod +x ./infra/scripts/setup_keycloak.sh
   ./infra/scripts/setup_keycloak.sh
   ```
   Esto crea automáticamente:
   - Realm: `erp-barrio`
   - Roles: `admin`, `cajero`, `bodega`, `rrhh`
   - Clients: `erp-web` (público), `erp-api` (confidential)
   - Usuario test: `cajero1` / password: `pass123`

4. **Obtén un token para testing:**
   ```bash
   TOKEN=$(curl -s -X POST "http://localhost:8081/realms/erp-barrio/protocol/openid-connect/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=password&client_id=erp-web&username=cajero1&password=pass123" | jq -r .access_token)
   echo "$TOKEN"
   ```

5. **Valida el token contra la API:**
   ```bash
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/health
   ```

**Guía completa y troubleshooting:** [docs/keycloak_quickstart.md](docs/keycloak_quickstart.md)

**Información de puertos y arquitectura:** [docs/auth_strategy.md](docs/auth_strategy.md)


## Revisión final de arquitectura

Para alinear pasos 9-12 con los requisitos críticos (correo IMAP, experiencia web+móvil y QR P2P), revisar `docs/final_infra_architecture_review.md`.

## Registro documental de inspección (`docs/inspeccion`)

Se creó un paquete documental completo para la inspección por pasos, con reportes ejecutivos y anexos técnicos de evidencia:

- `docs/inspeccion/plan.md`: plan base de inspección y criterios de aprobación parcial (alcance operativo vigente en pasos 3–5).
- `docs/inspeccion/reporte_paso1.md` a `docs/inspeccion/reporte_paso5.md`: reportes por paso con estado, observaciones y porcentaje de aceptación.
- `docs/inspeccion/anexos/paso1_analisis.md` a `docs/inspeccion/anexos/paso5_analisis.md`: análisis técnico detallado por paso (hallazgos, patrones/anti-patrones, riesgos y recomendaciones).
- `docs/inspeccion/reporte.md`: consolidado ejecutivo con calificación agrupada por paso y nota general.
- `docs/inspeccion/anexos/conclusion_general.md`: criterio de consolidación, lectura ejecutiva del resultado global y acciones de gobernanza recomendadas.

En conjunto, este registro deja trazabilidad documental de la inspección realizada, separando el resumen de gestión (reportes) de la evidencia técnica ampliada (anexos).
