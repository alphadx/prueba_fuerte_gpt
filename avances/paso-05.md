# Paso 05 — Implementar API modular con autenticación y permisos

## Checklist de indicadores
- [ ] **Índice de cobertura CRUD por módulo** (meta: >= 90% MVP).
- [x] **Índice de seguridad de acceso** (meta: 100%) para módulo `products` vía RBAC por roles en token.
- [x] **Índice de auditoría crítica** (meta: 100%) para operaciones `create/update/delete` en `products`.

## Grado de cumplimiento
- **Cobertura CRUD por módulo:** 20% (CRUD completo habilitado para módulo inicial `products`).
- **Seguridad de acceso:** 100% en módulo `products`; pendiente replicar en módulos restantes.
- **Auditoría crítica:** 100% en `products`; pendiente extender a caja/pagos/documentos tributarios/RRHH.

## Estado de avance del paso
- **Cumplimiento estimado:** **35%**
- **Semáforo:** 🟡 Amarillo (En progreso)
- **Observación:** Se implementó baseline reusable de autenticación (`Bearer/JWT claims`) + autorización RBAC + trazabilidad de auditoría para continuar con más vertical slices.
