"""Registro centralizado de todos los gateways de pago disponibles.

Estructura:
  - stubs   : transbank_stub, mercadopago_stub  (sandbox / testing)
  - real    : cash, transbank_web, transbank_pos (producción / integración)

El service consume GATEWAY_REGISTRY como fuente única de providers.
Para agregar un nuevo proveedor basta con instanciarlo e incluirlo aquí;
el resto del módulo (service, router, flags) lo absorbe sin cambios.

Separación de canales:
  - transbank_web  → channel: web
  - transbank_pos  → channel: pos
  - cash           → channel: pos  (efectivo, sin restricción de canal)
  - stubs          → cualquier canal (solo para tests)
"""

from __future__ import annotations

from app.modules.payments.cash_adapter import cash_payment_gateway
from app.modules.payments.gateway import PaymentGateway
from app.modules.payments.stub_adapters import mercadopago_stub_gateway, transbank_stub_gateway
from app.modules.payments.transbank_pos_adapter import transbank_pos_gateway
from app.modules.payments.transbank_web_adapter import transbank_web_gateway

# Mapa completo de providers: nombre → instancia de gateway.
# La clave es el valor que se usa como `method` en PaymentIntent
# y como `provider` en Payment/PaymentResult.
GATEWAY_REGISTRY: dict[str, PaymentGateway] = {
    # ── Efectivo ──────────────────────────────────────────────────────────────
    cash_payment_gateway.provider_name: cash_payment_gateway,

    # ── Transbank real ────────────────────────────────────────────────────────
    transbank_web_gateway.provider_name: transbank_web_gateway,   # "transbank_web"
    transbank_pos_gateway.provider_name: transbank_pos_gateway,   # "transbank_pos"

    # ── Stubs de testing ──────────────────────────────────────────────────────
    transbank_stub_gateway.provider_name: transbank_stub_gateway,         # "transbank_stub"
    mercadopago_stub_gateway.provider_name: mercadopago_stub_gateway,     # "mercadopago_stub"
}

# Restricción de canal por proveedor.
# El service valida que el canal del intento coincida antes de ejecutar.
# None = sin restricción.
PROVIDER_CHANNEL_CONSTRAINT: dict[str, str | None] = {
    "cash":              None,            # acepta pos y web
    "transbank_web":     "web",
    "transbank_pos":     "pos",
    "transbank_stub":    None,
    "mercadopago_stub":  None,
}
