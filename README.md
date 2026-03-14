# ERP Barrio Chile - Monorepo base

Este repositorio implementa el **paso 2 del plan**: arquitectura base y repositorio ejecutable para un MVP ERP en Chile.

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

## Comandos principales

```bash
make up
make test
make seed
```

### Qué hace cada comando

- `make up`: instala dependencias de API y levanta FastAPI localmente en `http://127.0.0.1:8000`.
- `make test`: ejecuta los tests base de API.
- `make seed`: genera datos semilla iniciales en `infra/seeds/dev_seed.json`.

## Contrato OpenAPI como fuente de verdad

El contrato vive en `apps/api/openapi.yaml`. Cualquier endpoint nuevo debe declararse primero ahí.
