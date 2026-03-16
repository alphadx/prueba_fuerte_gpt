# Paso 6 — Etapa 3: Reglas de caja y arqueo mínimo operable

## Objetivo
Implementar y validar invariantes operacionales de caja para que apertura, actualización y cierre sean consistentes y auditables.

## Reglas implementadas
1. **Inicio válido de sesión:** una caja sólo puede crearse con `status = open`.
2. **Unicidad operativa:** un mismo operador no puede tener dos sesiones abiertas en la misma sucursal.
3. **Mutabilidad restringida:** sólo sesiones `open` pueden recibir actualizaciones (`cash_delta`, `closing_amount`, `status`).
4. **Cierre válido:** para cambiar a `closed` se exige `closing_amount`.
5. **Estados admitidos:** `open` y `closed`.

## Cálculo de arqueo
- `expected_amount` inicia en `opening_amount` y se ajusta con `cash_delta`.
- `difference_amount = closing_amount - expected_amount` al cierre.

## Evidencia de validación
- Pruebas unitarias de servicio para:
  - prevención de doble caja abierta por operador/sucursal,
  - rechazo de actualización sobre caja cerrada.
- Pruebas API para:
  - conflicto 409 en creación duplicada,
  - conflicto 409 al intentar actualizar una caja ya cerrada.

## Salida formal de Etapa 3
Reglas de caja y arqueo mínimo operable implementadas con validación automatizada local.
