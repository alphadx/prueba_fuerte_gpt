# ERP Barrio Chile - Monorepo base

Este repositorio implementa el **paso 2 del plan** y la **base técnica del paso 3**: arquitectura base ejecutable + soporte Docker Compose con cola Redis.

## Estructura

- `apps/api`: API FastAPI y contrato OpenAPI.
- `apps/web`: frontend Next.js (esqueleto).
- `workers/alerts`: worker asíncrono para alertas.
- `infra`: utilidades de infraestructura y seeds.
- `tests`: pruebas unitarias e integración iniciales.

## Requisitos

- Python 3.11+
- Node.js 20+ (para `apps/web`)
- GNU Make
- Docker + Docker Compose

## Comandos principales

```bash
make up
make test
make seed
make compose-up
make compose-up-full
make compose-down
make compose-smoke
make architecture-review
```

### Qué hace cada comando

- `make up`: instala dependencias de API y levanta FastAPI localmente en `http://127.0.0.1:8000`.
- `make test`: ejecuta los tests base de API.
- `make seed`: genera datos semilla iniciales en `infra/seeds/dev_seed.json`.
- `make compose-up`: levanta perfil `core` (`postgres`, `redis`, `api`, `worker`, `web`).
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
- Revisión de mitigaciones del paso 2: `docs/step2_mitigations.md`.


## Política operativa de sesión (Docker)

- En cada sesión técnica se debe validar Docker al inicio con `make doctor-docker`.
- Si Docker no está instalado/disponible, **primero se debe instalar/habilitar** antes de ejecutar pruebas reales con Compose.
- Para pruebas integradas de servicios usar `make compose-up` (o `make compose-up-full`).


## Control de usuarios y SSO

- Se adopta estrategia de identidad con **Keycloak** (OIDC/OAuth2).
- Diseño y consideraciones: `docs/auth_strategy.md`.
- En perfil `full`, Keycloak queda disponible para preparar el paso 5 (auth/permisos).


## Revisión final de arquitectura

Para alinear pasos 9-12 con los requisitos críticos (correo IMAP, experiencia web+móvil y QR P2P), revisar `docs/final_infra_architecture_review.md`.
