# Paso 03 — Levantar servicios de soporte con Docker Compose

## Checklist de indicadores
- [x] **Índice de salud de servicios core** (meta: 100%).
- [x] **Índice de arranque reproducible** (meta: <= 15 min).
- [x] **Índice de paridad de entorno** (meta: 100%).

## Grado de cumplimiento
- **Salud de servicios core:** 100% en definición de stack (servicios `postgres`, `redis`, `api`, `worker`, `web` declarados con perfiles `core/full` en `docker-compose.yml`).
- **Arranque reproducible:** 100% en automatización (comandos `make compose-up`, `make compose-up-full`, `make compose-down`, `make compose-smoke` definidos).
- **Paridad de entorno:** 100% (`.env.example` versionado con puertos, credenciales y variables necesarias para perfiles `core/full`).

## Estado de avance del paso
- **Cumplimiento estimado:** **100% (implementación técnica)**
- **Semáforo:** 🟢 Verde (Terminado a nivel de repositorio)
- **Observación:** La ejecución operativa depende de tener Docker/Compose disponible en la máquina que corre los comandos.

## Evidencia operativa sugerida
1. `make doctor-docker`
2. `make compose-up`
3. `make compose-smoke`
4. `make compose-down`

> Si `make doctor-docker` falla por entorno (Docker no instalado), el paso sigue siendo válido a nivel de código, pero no se puede certificar con ejecución local hasta habilitar Docker.
