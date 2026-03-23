"""Transbank Webpay Plus adapter for web checkout flows (channel: web).

Ciclo de vida:
  authorize() → inicia la transacción y devuelve redirect_url en raw_payload_ref.
  capture()   → hace commit luego del retorno del usuario (requiere token_ws en metadata).
  parse_webhook() → normaliza el callback/notificación de Transbank.
  validate_signature() → verifica HMAC-SHA256 con TRANSBANK_WEBHOOK_SECRET_WEB.

En modo sandbox (TRANSBANK_ENV=integration) no se realizan llamadas HTTP reales;
se devuelven respuestas deterministas para pruebas locales y CI.
En producción, el método _call_transbank_api() debe ser reemplazado con el cliente HTTP real.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import uuid
from dataclasses import dataclass

from app.modules.payments.gateway import (
    PaymentErrorCode,
    PaymentGateway,
    PaymentIntent,
    PaymentResult,
    PaymentStatus,
    WebhookEvent,
)

_INTEGRATION_BASE_URL = "https://webpay3gint.transbank.cl"
_PRODUCTION_BASE_URL = "https://webpay3g.transbank.cl"
_TX_PATH = "/rswebpaytransaction/api/webpay/v1.2/transactions"


@dataclass
class TransbankWebConfig:
    environment: str        # "integration" | "production"
    commerce_code: str
    api_key: str
    return_url: str
    webhook_secret: str

    @property
    def base_url(self) -> str:
        return _PRODUCTION_BASE_URL if self.environment == "production" else _INTEGRATION_BASE_URL

    @classmethod
    def from_env(cls) -> "TransbankWebConfig":
        return cls(
            environment=os.environ.get("TRANSBANK_ENV", "integration"),
            commerce_code=os.environ.get("TRANSBANK_COMMERCE_CODE_WEB", ""),
            api_key=os.environ.get("TRANSBANK_API_KEY_WEB", ""),
            return_url=os.environ.get("TRANSBANK_RETURN_URL", ""),
            webhook_secret=os.environ.get("TRANSBANK_WEBHOOK_SECRET_WEB", ""),
        )


class TransbankWebGateway(PaymentGateway):
    """Adapter de Transbank Webpay Plus para el canal web."""

    provider_name = "transbank_web"

    def __init__(self, config: TransbankWebConfig | None = None) -> None:
        self._config = config or TransbankWebConfig.from_env()

    def _is_sandbox(self) -> bool:
        return self._config.environment != "production"

    def _misconfigured(self) -> bool:
        return not self._config.commerce_code or not self._config.return_url

    def authorize(self, intent: PaymentIntent) -> PaymentResult:
        """Inicia transacción Webpay Plus.

        En sandbox devuelve un token determinista basado en idempotency_key.
        raw_payload_ref contiene la redirect_url que el servicio expondrá al cliente.
        """
        if self._misconfigured():
            return PaymentResult(
                provider=self.provider_name,
                provider_payment_id="",
                status=PaymentStatus.REJECTED,
                error_code=PaymentErrorCode.PROVIDER_UNAVAILABLE,
                error_message=(
                    "TRANSBANK_COMMERCE_CODE_WEB o TRANSBANK_RETURN_URL no configurados. "
                    "Revisa las variables de entorno del servicio."
                ),
                raw_payload_ref=f"{self.provider_name}://error/misconfigured",
            )

        buy_order = intent.metadata.get("buy_order") or f"ord-{intent.idempotency_key[:16]}"
        session_id = intent.metadata.get("session_id") or str(uuid.uuid4())
        return_url = intent.metadata.get("return_url") or self._config.return_url

        if self._is_sandbox():
            token = f"sandbox-token-{intent.idempotency_key}"
            redirect_url = (
                f"{self._config.base_url}/webpayserver/initTransaction?token_ws={token}"
            )
            return PaymentResult(
                provider=self.provider_name,
                provider_payment_id=token,
                status=PaymentStatus.PENDING_CONFIRMATION,
                error_code=None,
                error_message=None,
                # raw_payload_ref transporta redirect_url; el service lo extrae para la respuesta.
                raw_payload_ref=redirect_url,
            )

        # Producción — bloque intencional: requiere credenciales reales y cliente HTTP.
        # Para activar, reemplazar este bloque con la llamada real:
        #   POST {base_url}{_TX_PATH}
        #   Headers: Tbk-Api-Key-Id: {commerce_code}, Tbk-Api-Key-Secret: {api_key}
        #   Body:    {buy_order, session_id, amount: int(intent.amount), return_url, currency: "CLP"}
        #   Respuesta esperada: {token, url}
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id="",
            status=PaymentStatus.REJECTED,
            error_code=PaymentErrorCode.PROVIDER_UNAVAILABLE,
            error_message=(
                "Integración real de producción Transbank no activada. "
                "Establece TRANSBANK_ENV=integration para usar sandbox."
            ),
            raw_payload_ref=f"{self.provider_name}://error/production-not-ready",
        )

    def capture(self, intent: PaymentIntent) -> PaymentResult:
        """Commit de la transacción Webpay luego del retorno del usuario.

        Requiere intent.metadata['token_ws'] con el token devuelto por Transbank.
        En sandbox: tokens con prefijo 'sandbox-reject-' son forzadamente rechazados.
        """
        token = intent.metadata.get("token_ws")
        if not token:
            return PaymentResult(
                provider=self.provider_name,
                provider_payment_id="",
                status=PaymentStatus.REJECTED,
                error_code=PaymentErrorCode.INVALID_REQUEST,
                error_message="token_ws requerido en metadata para el capture Webpay.",
                raw_payload_ref=f"{self.provider_name}://error/missing-token",
            )

        if self._is_sandbox():
            if token.startswith("sandbox-reject-"):
                return PaymentResult(
                    provider=self.provider_name,
                    provider_payment_id=token,
                    status=PaymentStatus.REJECTED,
                    error_code=PaymentErrorCode.REJECTED,
                    error_message="Transbank rechazó la transacción (sandbox forced reject).",
                    raw_payload_ref=f"{self.provider_name}://capture/{token}/rejected",
                )
            return PaymentResult(
                provider=self.provider_name,
                provider_payment_id=token,
                status=PaymentStatus.APPROVED,
                error_code=None,
                error_message=None,
                raw_payload_ref=f"{self.provider_name}://capture/{token}/approved",
            )

        # Producción — reemplazar con:
        #   PUT {base_url}{_TX_PATH}/{token}
        #   Headers: Tbk-Api-Key-Id, Tbk-Api-Key-Secret
        #   Respuesta: {vci, buy_order, session_id, card_detail, accounting_date,
        #               transaction_date, authorization_code, payment_type_code,
        #               response_code, installments_number, amount, status}
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=token,
            status=PaymentStatus.REJECTED,
            error_code=PaymentErrorCode.PROVIDER_UNAVAILABLE,
            error_message="Integración real de producción Transbank no activada.",
            raw_payload_ref=f"{self.provider_name}://error/production-not-ready",
        )

    def parse_webhook(self, payload: dict[str, str], *, signature: str | None) -> WebhookEvent:
        """Normaliza un callback o notificación entrante de Transbank Webpay."""
        event_id = (
            payload.get("event_id")
            or payload.get("buy_order")
            or "tbk-web-event"
        )
        idem = payload.get("idempotency_key") or payload.get("session_id") or "unknown"
        token = payload.get("token_ws") or payload.get("provider_payment_id") or "unknown"

        raw_status = payload.get("status", "").upper()
        if raw_status in ("AUTHORIZED", "APPROVED"):
            status = PaymentStatus.APPROVED
        elif raw_status in ("FAILED", "NULLIFIED", "REJECTED"):
            status = PaymentStatus.REJECTED
        else:
            status = PaymentStatus.PENDING_CONFIRMATION

        return WebhookEvent(
            provider=self.provider_name,
            event_id=event_id,
            idempotency_key=idem,
            provider_payment_id=token,
            status=status,
            signature=signature,
            payload=payload,
        )

    def validate_signature(self, payload: dict[str, str], *, signature: str | None) -> bool:
        """Valida firma HMAC-SHA256 del webhook.

        Producción: verifica digest sobre los pares clave=valor ordenados del payload.
        Sandbox: acepta firmas que comiencen con 'transbank_web:' o si no hay secreto configurado.
        """
        secret = self._config.webhook_secret

        if not secret:
            return self._is_sandbox()

        if signature is None:
            return False

        if self._is_sandbox() and signature.startswith("transbank_web:"):
            return True

        try:
            body = "&".join(f"{k}={v}" for k, v in sorted(payload.items()))
            expected = hmac.new(
                secret.encode(), body.encode(), hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception:
            return False


transbank_web_gateway = TransbankWebGateway()
