# Registro de avance del plan ERP (12 pasos)

## Estado general

- Fecha de actualización: 2026-03-14
- Estado global: **Paso 2 consolidado / Paso 3 completado (base técnica)**

## Avances ejecutados (inicio por paso 2)

### ✅ Paso 2 — Crear arquitectura base y repositorio ejecutable

**Resultado:** completado y reforzado con estándares.

**Evidencia en repositorio:**
- Estructura base de monorepo creada (`apps/api`, `apps/web`, `workers/alerts`, `infra`, `tests`).
- API FastAPI base y contrato OpenAPI.
- Scripts de trabajo en `Makefile`: `make up`, `make test`, `make seed`.
- Script seed inicial y dataset base (`infra/scripts/seed.py`, `infra/seeds/dev_seed.json`).
- Guías para colaboración y estándares (`docs/architecture_base.md`, `docs/development_standards.md`).

## Avance actual

### ✅ Paso 3 — Levantar servicios de soporte con Docker Compose

**Estado:** completado a nivel de repositorio (pendiente validación en entorno con Docker disponible).

**Implementado:**
- `docker-compose.yml` con perfiles `core` y `full`.
- `Makefile` extendido con `make compose-smoke` para validar readiness de API.
- Servicios `core`: `postgres`, `redis`, `api`, `worker`, `web`.
- Servicios `full`: `mailhog`, `greenmail` (SMTP+IMAP), `minio`, `keycloak`, `keycloak-db`.
- `.env.example` con variables base del entorno.
- Dockerfiles para `apps/api` y `workers/alerts`.
- API extendida con `POST /alerts/dispatch` para encolar eventos.
- Worker de alertas con consumo Redis (`BLPOP`).

**Pendiente de ejecución en este entorno:**
- Correr smoke end-to-end con daemon Docker habilitado (`make compose-up` + `make compose-smoke`).
- Capturar evidencia de logs API/worker durante despacho real de alerta.

## Tablero resumido del plan

- [x] Paso 1 — Alcance MVP y criterios de aceptación.
- [x] Paso 2 — Arquitectura base y repositorio ejecutable.
- [x] Paso 3 — Docker Compose + `.env.example` (base técnica).
- [ ] Paso 4 — Modelo de datos y migraciones.
- [ ] Paso 5 — API modular + auth/permisos.
- [ ] Paso 6 — POS y flujo de caja.
- [ ] Paso 7 — Boleta electrónica sandbox.
- [ ] Paso 8 — Adaptadores de pago.
- [ ] Paso 9 — E-commerce retiro en tienda.
- [ ] Paso 10 — RRHH documental + alertas.
- [ ] Paso 11 — Estado inicial de pruebas completo.
- [ ] Paso 12 — Validación final y checklist de salida.

## Forma de uso del registro

Cada avance debe añadir:
1. qué se hizo,
2. evidencia en archivos/comandos,
3. qué falta,
4. criterio de cierre del paso actual.


## Mitigaciones de revisión

- Se documentaron mitigaciones específicas del paso 2 en `docs/step2_mitigations.md`.
- Se incorporaron mejoras técnicas: endpoint `GET /ready`, control de fallback de cola y contrato OpenAPI actualizado.

- Mitigación operativa: se añadió `make doctor-docker` para forzar chequeo explícito de Docker al inicio de sesión.

- Se incorporó decisión de SSO con Keycloak y se agregó base de infraestructura en perfil `full`.


## Hardening de arquitectura (última ventana de cambios)

- Se agregó revisión formal en `docs/final_infra_architecture_review.md` para alinear pasos 9-12 con:
  - correo de pruebas verificable vía IMAP,
  - experiencia UI web/móvil,
  - validación QR para transacciones entre pares (P2P).
- Se reforzó infraestructura `compose full` con servicio GreenMail (SMTP + IMAP) para pruebas de notificaciones extremo a extremo.

