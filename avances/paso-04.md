# Paso 04 — Diseñar modelo de datos inicial y migraciones

## Checklist de indicadores
- [x] **Índice de cobertura de entidades MVP** (meta: 100%).
- [x] **Índice de migraciones idempotentes** (meta: 100% para la cadena inicial 0001).
- [x] **Índice de consistencia relacional** (meta: 0 críticos en constraints base).

## Grado de cumplimiento
- **Cobertura de entidades MVP:** 100% (20/20 entidades del alcance inicial en migración 0001).
- **Migraciones idempotentes:** 100% a nivel de assets SQL (`IF NOT EXISTS` + rollback versionado).
- **Consistencia relacional:** 0 críticos detectados en revisión estática de FK/UNIQUE/CHECK.

## Estado de avance del paso
- **Cumplimiento estimado:** **100%**
- **Semáforo:** 🟢 Verde (Terminado)
- **Observación:** se creó esquema inicial completo con guía de ejecución y script para aplicar/rollback.

## Evidencia
- Migraciones: `infra/migrations/0001_initial_schema.up.sql`, `infra/migrations/0001_initial_schema.down.sql`.
- Runner: `infra/scripts/migrate.py` + comandos `make migrate-up|migrate-down|migrate-status`.
- Diagrama ER base y cobertura: `infra/migrations/README.md`.
