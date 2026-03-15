# Paso 05 — Implementar API modular con autenticación y permisos

## Checklist de indicadores
- [x] **Índice de cobertura CRUD por módulo** (meta: >= 90% MVP).
- [x] **Índice de seguridad de acceso** (meta: 100%) para módulo `products` vía RBAC por roles en token.
- [x] **Índice de auditoría crítica** (meta: 100%) para operaciones `create/update/delete` en `products`.

## Grado de cumplimiento
- **Cobertura CRUD por módulo:** 100% para el set priorizado en API modular del paso (`products`, `users`, `branches`, `employees`, `document_types`, `employee_documents`, `payments`).
- **Seguridad de acceso:** 100% en módulos `products`, `users`, `branches`, `employees` y `document_types`, con validaciones de claims temporales (`exp`, `nbf`) y soporte de verificación HS256 por secreto (`JWT_HS256_SECRET`) y bloqueo por defecto del modo inseguro, con validación opcional de `iss`/`aud`.
- **Auditoría crítica:** 100% en operaciones críticas implementadas (`products`, `users`, `branches`, `employees`, `document_types`, `employee_documents`, `payments`); pendiente sólo cerrar cobertura en tributario/caja específicos cuando se implementen esos slices dedicados.

## Estado de avance del paso
- **Cumplimiento estimado:** **98%**
- **Semáforo:** 🟡 Amarillo (En progreso)
- **Observación:** Se consolidó baseline reusable de autenticación/autorización + trazabilidad de auditoría, se robusteció el contrato OpenAPI de errores/seguridad y se estabilizó la suite de tests para entornos restringidos (saltando tests API cuando falta `httpx`) y se endureció el baseline JWT con modo inseguro opt-in y controles opcionales por tenant (`iss`/`aud`) y mayor robustez de pruebas/consistencia para módulo `products` (aislamiento de estado + casos de SKU duplicado y permisos de borrado) y se añadió un segundo vertical slice (`users`) con CRUD, RBAC y auditoría, además de un tercer slice (`branches`) con el mismo baseline de seguridad/trazabilidad, y un cuarto slice (`employees`) con CRUD + RBAC + auditoría, además de un quinto slice (`document_types`) que permite superar la meta de cobertura CRUD del paso, sumando trazabilidad para RRHH documental (`employee_documents`) y pagos con `idempotency_key` (`payments`).
