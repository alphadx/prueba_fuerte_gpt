# Paso 6 — Etapa 1: Análisis detallado y criterios de aceptación

## 1) Objetivo de la etapa
Definir de forma inequívoca las reglas funcionales y técnicas del flujo POS + caja para que las siguientes etapas implementen comportamiento verificable (sin ambigüedades de contrato ni de dominio).

## 2) Alcance del análisis
- Flujo de caja: apertura, operación, cierre y arqueo.
- Flujo de venta POS: creación/confirmación con impacto en pagos e inventario.
- Trazabilidad: auditoría mínima y eventos del dominio.
- Escenarios de falla: estado de caja inválido, stock insuficiente, pago en estado no final.

## 3) Reglas funcionales obligatorias (baseline)

### Caja
1. No se puede confirmar una venta si no existe sesión de caja abierta para la sucursal de la venta.
2. El cierre de caja sólo se permite para sesiones abiertas.
3. El arqueo debe exponer:
   - monto de apertura,
   - entradas/salidas en efectivo (`cash_delta`),
   - monto esperado (`expected_amount`),
   - monto contado (`closing_amount`),
   - diferencia (`difference_amount`).
4. `difference_amount = closing_amount - expected_amount`.

### Venta POS
1. Una venta confirmada debe contener al menos una línea de producto válida.
2. El total de venta debe ser determinístico: `subtotal + impuestos = total`.
3. La confirmación de venta debe validar coherencia de sucursal entre caja y venta.
4. El estado de pago debe mapear por medio:
   - `cash` → `approved`,
   - `card_stub` / `wallet_stub` → `pending`.

### Inventario/Kardex
1. Confirmar una venta debe descontar stock por línea.
2. Cada descuento debe registrar un movimiento kardex `outbound` con referencia a la venta.
3. Si falla el descuento de cualquier línea, el flujo debe revertir cambios parciales de stock (rollback).

## 4) Invariantes de dominio
- No existe venta “confirmada” con stock insuficiente.
- No existe cierre de caja con sesión en estado distinto de `open`.
- Toda venta confirmada genera trazabilidad de inventario.
- Toda operación crítica (apertura/cierre de caja, confirmación de venta) deja rastro auditable.

## 5) Matriz de escenarios críticos

| ID | Escenario | Precondición | Resultado esperado | Severidad |
|---|---|---|---|---|
| POS-01 | Venta cash happy path | Caja abierta + stock suficiente | Venta confirmada, pago `approved`, stock decrementado, kardex generado | Alta |
| POS-02 | Venta con stock insuficiente | Caja abierta + una línea sin stock | Rechazo de confirmación, sin decrementos netos de stock | Crítica |
| POS-03 | Venta sin caja abierta | Caja inexistente/cerrada | Rechazo por regla de dominio de caja | Crítica |
| POS-04 | Cierre de caja válido | Caja abierta | Cierre exitoso con `expected_amount` y `difference_amount` calculados | Alta |
| POS-05 | Cierre de caja duplicado | Caja ya cerrada | Rechazo con conflicto de estado | Alta |
| POS-06 | Pago no cash | Medio `card_stub`/`wallet_stub` | Venta confirmada con pago en `pending` | Media |

## 6) Criterios de aceptación medibles (Definition of Done de etapa)

### Venta
- CA-V1: 100% de ventas confirmadas en happy path con cálculo consistente de montos.
- CA-V2: 100% de rechazos por stock insuficiente mantienen inventario sin decremento neto.

### Caja
- CA-C1: 100% de cierres válidos calculan `difference_amount` correctamente.
- CA-C2: 100% de cierres inválidos (sesión no abierta) devuelven error de dominio consistente.

### Inventario
- CA-I1: 100% de ventas confirmadas generan movimiento kardex por línea.
- CA-I2: 0 ventas confirmadas con stock negativo.

## 7) Riesgos y mitigaciones para siguientes etapas
- Riesgo: divergencia entre contrato API y reglas de dominio.
  - Mitigación: cerrar etapa 2 con tabla de errores y payloads canónicos.
- Riesgo: rollback parcial defectuoso en ventas multi-línea.
  - Mitigación: pruebas de integración específicas en etapa 6.
- Riesgo: inconsistencia entre caja/sucursal/usuario.
  - Mitigación: validaciones explícitas de pertenencia en etapa 3 y 4.

## 8) Salida formal de Etapa 1
- Reglas de negocio mínimas establecidas.
- Matriz de escenarios críticos establecida.
- Criterios de aceptación cuantificables definidos.
- Etapa lista para pasar a **Etapa 2 (contratos API POS + caja)**.
