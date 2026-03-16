# Paso 6 — Etapa 7: Hardening y cierre

## Objetivo
Cerrar el paso 6 con mejoras de hardening en trazabilidad operativa y checklist final de cumplimiento.

## Hardening aplicado
1. **Auditoría de rechazos de dominio** en endpoints críticos:
   - `POST /sales/complete` ahora registra `sales.complete.rejected` antes de devolver `409`.
   - `POST /cash-sessions` registra `cash_sessions.create.rejected` en conflictos de creación.
   - `PATCH /cash-sessions/{id}` registra `cash_sessions.update.rejected` en conflictos de actualización.
2. **Cobertura de auditoría de rechazo**:
   - prueba API para rechazo en ventas por mismatch de sucursal,
   - prueba API para rechazo de caja duplicada.

## Checklist final del paso 6
- [x] Apertura/cierre de caja con invariantes operativos.
- [x] Confirmación de venta con estados de pago determinísticos.
- [x] Descuento de stock + kardex por venta confirmada.
- [x] Rollback completo en fallos (incluyendo limpieza de movimientos kardex).
- [x] Auditoría de operaciones exitosas y rechazadas en endpoints críticos.
- [x] Suite automatizada de unidad/API en verde.

## Salida formal de Etapa 7
Paso 6 cerrado con criterios funcionales, técnicos y de trazabilidad cumplidos para el flujo POS y caja mínimo operable.
