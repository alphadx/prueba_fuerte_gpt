# Paso 05 — Implementar API modular con autenticación y permisos

## Checklist de indicadores
- [ ] **Índice de cobertura CRUD por módulo** (meta: >= 90% MVP).
- [x] **Índice de seguridad de acceso** (meta: 100%) para módulo `products` vía RBAC por roles en token.
- [x] **Índice de auditoría crítica** (meta: 100%) para operaciones `create/update/delete` en `products`.

## Grado de cumplimiento
- **Cobertura CRUD por módulo:** 20% (CRUD completo habilitado para módulo inicial `products`).
- **Seguridad de acceso:** 100% en módulo `products`, con validaciones de claims temporales (`exp`, `nbf`) y soporte de verificación HS256 por secreto (`JWT_HS256_SECRET`) y bloqueo por defecto del modo inseguro.
- **Auditoría crítica:** 100% en `products`; pendiente extender a caja/pagos/documentos tributarios/RRHH.

## Estado de avance del paso
- **Cumplimiento estimado:** **50%**
- **Semáforo:** 🟡 Amarillo (En progreso)
- **Observación:** Se consolidó baseline reusable de autenticación/autorización + trazabilidad de auditoría, se robusteció el contrato OpenAPI de errores/seguridad y se estabilizó la suite de tests para entornos restringidos (saltando tests API cuando falta `httpx`) y se endureció el baseline JWT con modo inseguro opt-in.
