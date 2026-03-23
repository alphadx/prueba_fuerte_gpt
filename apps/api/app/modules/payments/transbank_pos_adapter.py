"""Transbank POS adapter para pagos presenciales con terminal Redcompra (canal: pos).

Ciclo de vida:
  authorize() → inicia la operación en el terminal POS y deja el pago en pending_confirmation.
  capture()   → confirma el resultado del terminal usando approval_code y response_code.
  parse_webhook() → normaliza el callback asíncrono si el middleware POS lo soporta.
  validate_signature() → verifica HMAC-SHA256 con TRANSBANK_POS_CALLBACK_SECRET.

En modo sandbox (TRANSBANK_ENV=integration) no se realizan llamadas reales al terminal.
El comportamiento de rechazo se controla con:
  - intent.metadata["force_reject"] = "true"   → fuerza rechazo en authorize.
  - TransbankPosConfirmRequest.response_code != "00" → fuerza rechazo en capture.

En producción, el bloque marcado como placeholder debe ser reemplazado por el cliente
real (Transbank POS REST API o SDK de integración serial/USB según el canal físico).
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

_POS_SANDBOX_BASE_URL = "https://simulator.transbank.cl/api/v1"
_POS_PRODUCTION_BASE_URL = "https://tbk-pos-gateway.transbank.cl/api/v1"

# Código de respuesta que Transbank define como aprobado en terminales POS.
_APPROVED_RESPONSE_CODE = "00"


@dataclass
class TransbankPosConfig:
    environment: str        # "integration" | "production"
    commerce_code: str
    api_key: str
    device_id: str
    terminal_id: str
    callback_secret: str
    callback_url: str

    @property
    def base_url(self) -> str:
        return (
            _POS_PRODUCTION_BASE_URL
            if self.environment == "production"
            else _POS_SANDBOX_BASE_URL
        )

    @classmethod
    def from_env(cls) -> "TransbankPosConfig":
        return cls(
            environment=os.environ.get("TRANSBANK_ENV", "integration"),
            commerce_code=os.environ.get("TRANSBANK_POS_COMMERCE_CODE", ""),
            api_key=os.environ.get("TRANSBANK_POS_API_KEY", ""),
            device_id=os.environ.get("TRANSBANK_POS_DEVICE_ID", ""),
            terminal_id=os.environ.get("TRANSBANK_POS_TERMINAL_ID", ""),
            callback_secret=os.environ.get("TRANSBANK_POS_CALLBACK_SECRET", ""),
            callback_url=os.environ.get("TRANSBANK_POS_CALLBACK_URL", ""),
        )


class TransbankPosGateway(PaymentGateway):
    """Adapter de Transbank POS / Redcompra para el canal presencial."""

    provider_name = "transbank_pos"

    def __init__(self, config: TransbankPosConfig | None = None) -> None:
        self._config = config or TransbankPosConfig.from_env()

    def _is_sandbox(self) -> bool:
        return self._config.environment != "production"

    def _misconfigured(self) -> bool:
        return not self._config.commerce_code

    def authorize(self, intent: PaymentIntent) -> PaymentResult:
        """Inicia una operación POS en el terminal.

        En sandbox el terminal se simula de forma determinista.
        raw_payload_ref registra la referencia de diagnóstico con buy_order y terminal_id.
        El pago queda en PENDING_CONFIRMATION hasta que capture() reciba la confirmación
        del terminal.
        """
        if self._misconfigured():
            return PaymentResult(
                provider=self.provider_name,
                provider_payment_id="",
                status=PaymentStatus.REJECTED,
                error_code=PaymentErrorCode.PROVIDER_UNAVAILABLE,
                error_message=(
                    "TRANSBANK_POS_COMMERCE_CODE no configurado. "
                    "Revisa las variables de entorno del servicio."
                ),
                raw_payload_ref=f"{self.provider_name}://error/misconfigured",
            )

        if intent.metadata.get("force_reject") == "true":
            return PaymentResult(
                provider=self.provider_name,
                provider_payment_id=f"{self.provider_name}-{intent.idempotency_key}",
                status=PaymentStatus.REJECTED,
                error_code=PaymentErrorCode.REJECTED,
                error_message="POS operation forced rejection (force_reject=true).",
                raw_payload_ref=(
                    f"{self.provider_name}://authorize/{intent.idempotency_key}/rejected"
                ),
            )

        terminal_id = (
            intent.metadata.get("terminal_id")
            or self._config.terminal_id
            or "TID-DEFAULT"
        )
        buy_order = intent.metadata.get("buy_order") or f"pos-{intent.idempotency_key[:16]}"
        pos_payment_id = f"pos-{uuid.uuid4().hex[:12]}"

        raw_ref = (
            f"{self.provider_name}://authorize"
            f"?buy_order={buy_order}&terminal_id={terminal_id}"
            f"&pos_payment_id={pos_payment_id}"
        )

        if self._is_sandbox():
            return PaymentResult(
                provider=self.provider_name,
                provider_payment_id=pos_payment_id,
                status=PaymentStatus.PENDING_CONFIRMATION,
                error_code=None,
                error_message=None,
                raw_payload_ref=raw_ref,
            )

        # Producción — reemplazar con llamada real al Transbank POS REST API:
        #   POST {base_url}/transactions
        #   Headers: Commerce-Code: {commerce_code}, Api-Key-Secret: {api_key}
        #   Body:    {buy_order, amount: int(intent.amount), terminal_id, device_id, currency: "CLP"}
        #   Respuesta esperada: {pos_payment_id, status: "PENDING", terminal_id}
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id="",
            status=PaymentStatus.REJECTED,
            error_code=PaymentErrorCode.PROVIDER_UNAVAILABLE,
            error_message=(
                "Integración real de producción Transbank POS no activada. "
                "Establece TRANSBANK_ENV=integration para usar sandbox."
            ),
            raw_payload_ref=f"{self.provider_name}://error/production-not-ready",
        )

    def capture(self, intent: PaymentIntent) -> PaymentResult:
        """Confirma el resultado del terminal POS.

        Requiere en intent.metadata:
          - 'approval_code'  : código de aprobación del terminal (str, requerido si aprobado).
          - 'response_code'  : código de respuesta Transbank ('00' = aprobado, otro = rechazado).
          - 'provider_payment_id': identificador devuelto por authorize().

        En sandbox: response_code '00' → APPROVED, cualquier otro → REJECTED.
        """
        response_code = intent.metadata.get("response_code", "")
        approval_code = intent.metadata.get("approval_code", "")
        pos_payment_id = (
            intent.metadata.get("provider_payment_id")
            or f"{self.provider_name}-{intent.idempotency_key}"
        )

        if not response_code:
            return PaymentResult(
                provider=self.provider_name,
                provider_payment_id=pos_payment_id,
                status=PaymentStatus.REJECTED,
                error_code=PaymentErrorCode.INVALID_REQUEST,
                error_message="response_code requerido en metadata para confirmar operación POS.",
                raw_payload_ref=f"{self.provider_name}://error/missing-response-code",
            )

        if self._is_sandbox():
            if response_code == _APPROVED_RESPONSE_CODE:
                return PaymentResult(
                    provider=self.provider_name,
                    provider_payment_id=pos_payment_id,
                    status=PaymentStatus.APPROVED,
                    error_code=None,
                    error_message=None,
                    raw_payload_ref=(
                        f"{self.provider_name}://capture/{pos_payment_id}"
                        f"?approval_code={approval_code}&response_code={response_code}"
                    ),
                )
            return PaymentResult(
                provider=self.provider_name,
                provider_payment_id=pos_payment_id,
                status=PaymentStatus.REJECTED,
                error_code=PaymentErrorCode.REJECTED,
                error_message=(
                    f"Terminal rechazó la transacción (response_code={response_code})."
                ),
                raw_payload_ref=(
                    f"{self.provider_name}://capture/{pos_payment_id}"
                    f"?response_code={response_code}"
                ),
            )

        # Producción — reemplazar con:
        #   PUT {base_url}/transactions/{pos_payment_id}
        #   Body: {approval_code, response_code, terminal_id}
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=pos_payment_id,
            status=PaymentStatus.REJECTED,
            error_code=PaymentErrorCode.PROVIDER_UNAVAILABLE,
            error_message="Integración real de producción Transbank POS no activada.",
            raw_payload_ref=f"{self.provider_name}://error/production-not-ready",
        )

    def parse_webhook(self, payload: dict[str, str], *, signature: str | None) -> WebhookEvent:
        """Normaliza un callback asíncrono desde el middleware POS o Transbank."""
        event_id = (
            payload.get("event_id")
            or payload.get("buy_order")
            or "tbk-pos-event"
        )
        idem = payload.get("idempotency_key") or payload.get("buy_order") or "unknown"
        pos_payment_id = payload.get("provider_payment_id") or payload.get("pos_payment_id") or "unknown"

        response_code = payload.get("response_code", "")
        if response_code == _APPROVED_RESPONSE_CODE:
            status = PaymentStatus.APPROVED
        elif response_code and response_code != _APPROVED_RESPONSE_CODE:
            status = PaymentStatus.REJECTED
        else:
            raw_status = payload.get("status", "").upper()
            if raw_status in ("APPROVED", "AUTHORIZED"):
                status = PaymentStatus.APPROVED
            elif raw_status in ("REJECTED", "FAILED", "REVERSED"):
                status = PaymentStatus.REJECTED
            else:
                status = PaymentStatus.PENDING_CONFIRMATION

        return WebhookEvent(
            provider=self.provider_name,
            event_id=event_id,
            idempotency_key=idem,
            provider_payment_id=pos_payment_id,
            status=status,
            signature=signature,
            payload=payload,
        )

    def validate_signature(self, payload: dict[str, str], *, signature: str | None) -> bool:
        """Valida firma HMAC-SHA256 del callback POS.

        Sandbox: acepta firma cuando comienza con 'transbank_pos:' o si no hay secreto.
        Producción: verifica digest sobre pares clave=valor ordenados del payload.
        """
        secret = self._config.callback_secret

        if not secret:
            return self._is_sandbox()

        if signature is None:
            return False

        if self._is_sandbox() and signature.startswith("transbank_pos:"):
            return True

        try:
            body = "&".join(f"{k}={v}" for k, v in sorted(payload.items()))
            expected = hmac.new(
                secret.encode(), body.encode(), hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception:
            return False


transbank_pos_gateway = TransbankPosGateway()
