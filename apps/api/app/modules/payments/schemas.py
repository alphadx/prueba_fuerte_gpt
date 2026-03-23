"""Schemas for payments CRUD endpoints."""

from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    sale_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    method: str = Field(min_length=1)
    status: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)


class CashPaymentCreateRequest(BaseModel):
    sale_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = Field(default="CLP", min_length=3, max_length=3)
    idempotency_key: str = Field(min_length=1)


class StubPaymentCreateRequest(BaseModel):
    sale_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = Field(default="CLP", min_length=3, max_length=3)
    idempotency_key: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class PaymentWebhookRequest(BaseModel):
    payload: dict[str, str] = Field(default_factory=dict)
    signature: str | None = None


class PaymentWebhookResponse(BaseModel):
    provider: str
    event_id: str
    duplicated: bool
    payment_id: str | None
    previous_status: str | None
    current_status: str | None




class PaymentMethodFlagUpsertRequest(BaseModel):
    branch_id: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    method: str = Field(min_length=1)
    enabled: bool


class PaymentMethodFlagResponse(BaseModel):
    branch_id: str
    channel: str
    method: str
    enabled: bool


class PaymentMethodFlagListResponse(BaseModel):
    items: list[PaymentMethodFlagResponse]

class PaymentUpdateRequest(BaseModel):
    status: str | None = Field(default=None, min_length=1)


class PaymentResponse(BaseModel):
    id: str
    sale_id: str
    amount: float
    method: str
    status: str
    idempotency_key: str
    provider: str = "local"
    provider_payment_id: str | None = None
    branch_id: str | None = None
    channel: str | None = None
    currency: str = "CLP"


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]


class CashReconciliationResponse(BaseModel):
    branch_id: str
    payments_total: int
    approved_total: int
    pending_total: int
    amount_total: float
    amount_approved: float


class PaymentObservabilityResponse(BaseModel):
    payments_total: int
    approved_total: int
    rejected_total: int
    pending_total: int
    webhook_events_processed: int
    error_rate: float


# ── Transbank WEB ──────────────────────────────────────────────────────────────

class TransbankWebInitRequest(BaseModel):
    """Inicio de checkout Transbank Webpay (canal web)."""

    sale_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = Field(default="CLP", min_length=3, max_length=3)
    idempotency_key: str = Field(min_length=1)
    return_url: str | None = Field(
        default=None,
        description="URL a la que Transbank redirigirá al usuario tras autorizar. "
                    "Si se omite se usa TRANSBANK_RETURN_URL del entorno.",
    )
    metadata: dict[str, str] = Field(default_factory=dict)


class TransbankWebInitResponse(BaseModel):
    """Respuesta de inicio de checkout web: incluye URL de redirección."""

    payment_id: str
    provider: str
    provider_payment_id: str
    redirect_url: str
    status: str


class TransbankWebCommitRequest(BaseModel):
    """Confirmación del retorno del usuario desde Transbank."""

    token: str = Field(
        min_length=1,
        description="token_ws devuelto por Transbank en el retorno (query param).",
    )
    idempotency_key: str | None = Field(
        default=None,
        description="Clave de idempotencia del intento original, si el cliente desea re-validar.",
    )


# ── Transbank POS / Redcompra ──────────────────────────────────────────────────

class TransbankPosInitRequest(BaseModel):
    """Inicio de operación de pago en terminal POS Transbank (Redcompra)."""

    sale_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = Field(default="CLP", min_length=3, max_length=3)
    idempotency_key: str = Field(min_length=1)
    terminal_id: str = Field(min_length=1, description="Identificador del terminal POS.")
    cashier_id: str = Field(min_length=1, description="Identificador del cajero en turno.")
    device_id: str | None = Field(
        default=None,
        description="Identificador de dispositivo POS si el middleware lo requiere.",
    )
    metadata: dict[str, str] = Field(default_factory=dict)


class TransbankPosConfirmRequest(BaseModel):
    """Confirmación del resultado del terminal POS tras la operación."""

    provider_payment_id: str = Field(
        min_length=1,
        description="provider_payment_id devuelto por el init POS.",
    )
    approval_code: str = Field(
        min_length=1,
        description="Código de aprobación emitido por la red Transbank.",
    )
    response_code: str = Field(
        min_length=1,
        description="Código de respuesta del terminal (00=aprobado, otros=rechazado).",
    )
    terminal_id: str = Field(min_length=1)
    ticket_number: str | None = Field(default=None, description="Número de ticket impreso.")
    metadata: dict[str, str] = Field(default_factory=dict)


# ── Respuesta genérica de confirmación ────────────────────────────────────────

class ProviderConfirmationResponse(BaseModel):
    """Resultado de un commit/confirm de proveedor externo (WEB o POS)."""

    payment_id: str | None
    provider: str
    previous_status: str | None
    current_status: str | None
