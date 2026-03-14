# Estándares de desarrollo para el MVP ERP (humanos + GPTs)

Este documento define un marco común para que el repositorio sea consistente, revisable y fácil de escalar.

## 1) Principios base

1. **API-first**
   - El contrato OpenAPI es la fuente de verdad.
   - Todo endpoint nuevo o cambio de payload debe partir en `apps/api/openapi.yaml`.

2. **Vertical slices por dominio**
   - Evitar módulos “utilitarios genéricos” con lógica de negocio mezclada.
   - Cada capacidad (inventario, ventas, billing, órdenes, RRHH, alertas) debe evolucionar por módulo.

3. **Asíncrono para tareas no críticas de caja**
   - Facturación, reintentos y alertas deben ir a worker/cola.
   - El POS no debe bloquearse por integraciones externas.

4. **Idempotencia y trazabilidad**
   - Endpoints sensibles (pagos/webhooks/documentos tributarios) deben usar `idempotency_key`.
   - Registrar eventos de auditoría para operaciones críticas.

## 2) Convenciones de código

### Python (API/worker)
- Seguir PEP 8 + type hints obligatorios en funciones públicas.
- Documentar reglas de dominio con docstrings cortas y orientadas a negocio.
- Evitar lógica compleja en routers; moverla a servicios de aplicación/dominio.

### Nombres y estructura
- Carpetas en minúscula (`inventory`, `sales`, `billing`).
- Archivos descriptivos (`service.py`, `repository.py`, `schemas.py`, `router.py`).
- Tests espejan la estructura funcional (`tests/api/<modulo>/...`).

## 3) Contrato y versionamiento de API

- Definir primero en OpenAPI:
  - request/response,
  - códigos HTTP,
  - errores de negocio.
- Cambios breaking requieren:
  - incremento de versión de API,
  - nota de migración en PR.

## 4) Testing mínimo por feature

Cada feature debe incluir, como mínimo:
1. **Test unitario** de regla de negocio principal.
2. **Test de integración API** del caso feliz.
3. **Caso de error controlado** (validación o regla de dominio).

Comandos estándar del repo:
- `make test`
- `make seed`

Si el entorno bloquea instalación de dependencias, al menos ejecutar validaciones estáticas (ej. `py_compile`) y dejar evidencia.

## 5) Seguridad y datos

- No commitear secretos reales.
- Usar `.env.example` como contrato de variables.
- Logging sin PII sensible en texto plano.
- Auditoría obligatoria en: caja, pagos, documentos tributarios y RRHH documental.

## 6) Guía de PR (humanos y GPTs)

Todo PR debe incluir:
1. **Motivación** (qué problema resuelve).
2. **Resumen técnico** (qué cambió y por qué).
3. **Testing ejecutado** (comandos exactos + resultado).
4. **Riesgos/pendientes** (si aplica).

Formato sugerido de commit:
- `feat: ...`
- `fix: ...`
- `docs: ...`
- `refactor: ...`
- `test: ...`

## 7) Referencias recomendadas

- OpenAPI Specification 3.1: https://spec.openapis.org/oas/latest.html
- FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/
- OWASP ASVS (baseline seguridad): https://owasp.org/www-project-application-security-verification-standard/
- Conventional Commits: https://www.conventionalcommits.org/

## 8) Checklist rápido antes de merge

- [ ] OpenAPI actualizado si hubo cambios de contrato.
- [ ] Tests (o validaciones estáticas) ejecutados y reportados.
- [ ] Sin secretos ni credenciales en el diff.
- [ ] Documentación actualizada (README/docs del módulo).
- [ ] Riesgos y siguientes pasos explícitos en el PR.


## 9) Política de entorno para pruebas reales (Docker)

- Toda sesión que involucre servicios (`api`, `worker`, `postgres`, `redis`) debe iniciar con verificación de Docker.
- Comando base: `make doctor-docker`.
- Si Docker no está disponible, se considera bloqueo de entorno y se debe:
  1. registrar el intento de instalación/activación,
  2. documentar el bloqueo exacto,
  3. continuar con validaciones estáticas mientras se habilita Docker.
