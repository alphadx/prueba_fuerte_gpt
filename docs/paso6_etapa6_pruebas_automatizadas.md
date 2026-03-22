# Paso 6 — Etapa 6: Pruebas automatizadas por etapas

## Objetivo
Consolidar cobertura automatizada del flujo POS+caja+stock con foco en reglas de dominio críticas y escenarios de error.

## Cobertura incorporada en esta etapa
1. **Pruebas unitarias de `SaleService`** (`tests/unit/test_sales_service.py`):
   - mapeo determinístico de estados de pago por método (`cash` y `card_stub`),
   - rechazo por mismatch de sucursal entre venta y caja,
   - rollback completo ante falla parcial multi-línea (stock + kardex + no persistencia de venta).
2. **Regresión API existente** del flujo POS y caja:
   - `tests/api/test_sales_pos_flow.py`,
   - `tests/api/test_products.py`,
   - `tests/api/test_cash_sessions.py`,
   - `tests/unit/test_cash_session_service.py`.

## Resultado de validación local
Suite ejecutada en esta etapa:

```bash
PYTHONPATH=apps/api pytest -q \
  tests/unit/test_sales_service.py \
  tests/api/test_sales_pos_flow.py \
  tests/api/test_products.py \
  tests/api/test_cash_sessions.py \
  tests/unit/test_cash_session_service.py
```

Resultado esperado: pruebas en verde, incluyendo escenarios happy path y failure path del paso 6.

## Salida formal de Etapa 6
Cobertura automatizada reforzada y alineada con reglas de dominio de POS, caja, stock y rollback.
