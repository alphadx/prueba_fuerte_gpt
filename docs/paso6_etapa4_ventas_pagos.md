# Paso 6 — Etapa 4: Confirmación de venta y estados de pago

## Objetivo
Asegurar que la confirmación de venta aplique una máquina de estados de pago determinística por medio de pago y que se mantengan validaciones críticas de sesión/sucursal.

## Reglas implementadas
1. **Mapa determinístico método→estado**
   - `cash` → `payment_status=approved`, `sale.status=paid`
   - `card_stub` → `payment_status=pending`, `sale.status=confirmed`
   - `wallet_stub` → `payment_status=pending`, `sale.status=confirmed`
2. **Métodos no soportados** rechazan la confirmación (`ValueError` → 409 en API).
3. Se mantiene validación de sesión de caja:
   - caja debe estar `open`,
   - sucursal de caja y venta debe coincidir.

## Ajustes de implementación
- Se reemplazó lógica condicional ad-hoc por un diccionario `PAYMENT_STATE_BY_METHOD` en el servicio de ventas.
- Se simplificó la emisión de evento de facturación para eliminar rama redundante y mantener retorno consistente del agregado `Sale`.

## Evidencia de validación
- Se agregan pruebas API para:
  - venta con `card_stub` que deja estado de venta `confirmed` y pago `pending`,
  - rechazo por mismatch de sucursal entre venta y caja.
- Se ejecuta suite de regresión de POS+caja para validar compatibilidad de reglas previas.

## Salida formal de Etapa 4
Confirmación de venta y estados de pago implementados con comportamiento determinístico y cobertura de escenarios principales y de conflicto.
