# Paso 2 completado: arquitectura base y repositorio ejecutable

## Monorepo inicial

- `apps/api`: servicio FastAPI con endpoint de healthcheck.
- `apps/web`: esqueleto de frontend Next.js.
- `workers/alerts`: esqueleto de worker para alertas.
- `infra`: scripts y datos semilla.
- `tests`: pruebas iniciales de API.

## OpenAPI como fuente de verdad

El contrato inicial está definido en `apps/api/openapi.yaml` e incluye el endpoint `GET /health`.

## Scripts de ejecución

- `make up`
- `make test`
- `make seed`

Estos comandos permiten levantar, validar y preparar un estado base de desarrollo para continuar con el paso 3 (Docker Compose).
