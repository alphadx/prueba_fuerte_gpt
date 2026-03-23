# Paso 8 — Hardening y checklist de cierre (capa de pagos por adaptadores)

## Objetivo
Cerrar el paso 8 con verificación final de confiabilidad, trazabilidad y control operativo sobre `cash`, `transbank_stub` y `mercadopago_stub`.

## Alcance validado
- Contrato canónico `PaymentGateway` y estados monotónicos.
- Adaptadores `cash` + stubs con autorización/captura simulada.
- Webhook unificado con validación de firma e idempotencia por evento.
- Feature flags por `branch_id + channel + method`.
- Conciliación básica de caja por sucursal.

## Checklist de hardening (Etapa 7)
- [x] **Contrato canónico estable** (`PaymentIntent`, `PaymentResult`, `WebhookEvent`, `PaymentStatus`).
- [x] **Drivers MVP implementados** (`cash`, `transbank_stub`, `mercadopago_stub`).
- [x] **Webhook unificado** con validación de firma por proveedor.
- [x] **Idempotencia de webhook** por clave de evento (`provider:event_id`).
- [x] **Transición monotónica de estados** para descartar callbacks stale.
- [x] **Feature flags por sucursal/canal** con bloqueo efectivo (`403`) cuando un medio está deshabilitado.
- [x] **Conciliación básica de cash** disponible por sucursal.
- [x] **Auditoría operativa** en endpoints críticos (create payment, flags, webhooks, reconciliation).
- [x] **Cobertura de pruebas integrales** (happy path, duplicados, rechazo, timeout, firma inválida).

## Comandos de validación ejecutados
- `pytest -q tests/unit/test_payment_feature_flags.py tests/unit/test_payment_webhook_idempotency.py tests/unit/test_stub_payment_adapters.py tests/unit/test_cash_payment_adapter.py tests/unit/test_payment_gateway_contract.py tests/unit/test_payment_service.py tests/api/test_payments.py`

## Resultado de cierre
- Paso 8 queda **cerrado a nivel prototipo iterativo (7/7)** con controles mínimos de confiabilidad y operación.
- Siguiente foco recomendado: consolidar métricas operativas (ratio de rechazo/timeout por proveedor) y persistencia duradera para eventos de webhook.
