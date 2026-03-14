# workers/alerts

Worker asíncrono para motor de alertas RRHH documental.

## Estado actual

- Implementado `worker.py` que consume eventos desde Redis (`BLPOP`).
- Cola por defecto: `alerts_queue`.
- Variables configurables: `REDIS_URL`, `ALERTS_QUEUE`, `WORKER_POLL_SECONDS`.

## Ejecución

- Local dockerizado: `make compose-up`.
- La API publica eventos con `POST /alerts/dispatch` y el worker los procesa en segundo plano.
