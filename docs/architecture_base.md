# Paso 2 completado: arquitectura base y repositorio ejecutable

## Monorepo inicial

- `apps/api`: servicio FastAPI con endpoint de healthcheck y encolado de alertas.
- `apps/web`: esqueleto de frontend Next.js.
- `workers/alerts`: worker para consumir cola Redis.
- `infra`: scripts y datos semilla.
- `tests`: pruebas iniciales de API.

## OpenAPI como fuente de verdad

El contrato inicial está definido en `apps/api/openapi.yaml` e incluye `GET /health` y `POST /alerts/dispatch`.

## Scripts de ejecución

- `make up`
- `make test`
- `make seed`
- `make compose-up`
- `make compose-up-full`
- `make compose-down`

Estos comandos permiten levantar, validar y preparar un estado base de desarrollo para continuar con el paso 3 (Docker Compose).

## Reforzamiento para siguientes contribuciones

- Aplicar la guía de estándares en `docs/development_standards.md`.
- Mantener enfoque API-first: actualizar OpenAPI antes de implementar endpoints.
- En PRs, reportar comandos exactos de validación y limitaciones de entorno (si existen).
