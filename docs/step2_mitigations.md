# Revisión de mitigaciones pendientes para Paso 2 (arquitectura base)

Este documento resume consideraciones detectadas en la revisión y cómo quedaron mitigadas o pendientes.

## 1) Riesgo: contrato API y app se desalinean

**Mitigación implementada**
- OpenAPI actualizado a versión `0.2.1`.
- Se documentó `GET /ready` y respuesta de error `503` para `POST /alerts/dispatch` cuando cola no está disponible.

## 2) Riesgo: fallas de Redis quedan silenciosas

**Mitigación implementada**
- `queue.py` ahora registra warning con causa técnica.
- Se incorporó política explícita de fallback controlada por `ALLOW_MEMORY_QUEUE_FALLBACK`.
- Si fallback está deshabilitado y Redis falla, se retorna error controlado (`HTTP 503`).

## 3) Riesgo: falta readiness para operación en contenedores

**Mitigación implementada**
- Se agregó `GET /ready` para checks de disponibilidad operativa.

## 4) Riesgo: validaciones incompletas en el flujo asíncrono

**Mitigación implementada**
- Test adicional para payload inválido en `POST /alerts/dispatch` (espera `422`).

## 5) Riesgo: configuración no explícita para degradación local

**Mitigación implementada**
- `.env.example` incluye `ALLOW_MEMORY_QUEUE_FALLBACK=true`.

## Pendientes recomendados (siguiente iteración)

1. Definir `healthcheck` en `docker-compose.yml` para `api`, `worker`, `redis` y `postgres`.
2. Agregar test de integración API -> Redis -> worker en entorno con Docker disponible.
3. Incorporar métricas básicas del worker (conteo procesados/fallidos).
4. Establecer política de reintentos y dead-letter queue para eventos fallidos.
