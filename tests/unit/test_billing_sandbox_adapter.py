from app.modules.billing.provider import BillingEmissionRequest
from app.modules.billing.sandbox_adapter import SandboxBillingProvider


def _request() -> BillingEmissionRequest:
    return BillingEmissionRequest(
        company_id="company-001",
        branch_id="br-001",
        sale_id="sale-100",
        document_type="boleta",
        totals=1234,
        idempotency_key="sale-100:boleta",
    )


def test_sandbox_adapter_fail_first_n_then_success(monkeypatch):
    monkeypatch.setenv("BILLING_SANDBOX_FAIL_FIRST_N", "1")
    monkeypatch.delenv("BILLING_SANDBOX_FORCE_ERROR", raising=False)
    provider = SandboxBillingProvider()

    try:
        provider.emit(_request())
        assert False, "expected RuntimeError on first attempt"
    except RuntimeError:
        pass

    emitted = provider.emit(_request())
    assert emitted.status == "accepted"
    assert emitted.track_id.startswith("track-")


def test_sandbox_adapter_progressive_status(monkeypatch):
    monkeypatch.setenv("BILLING_SANDBOX_EMIT_STATUS", "processing")
    monkeypatch.setenv("BILLING_SANDBOX_STATUS_MODE", "progressive")
    provider = SandboxBillingProvider()

    emitted = provider.emit(_request())

    first = provider.get_status(track_id=emitted.track_id)
    second = provider.get_status(track_id=emitted.track_id)

    assert first == "processing"
    assert second == "accepted"


def test_sandbox_adapter_rejected_status(monkeypatch):
    monkeypatch.setenv("BILLING_SANDBOX_EMIT_STATUS", "rejected")
    provider = SandboxBillingProvider()

    emitted = provider.emit(_request())

    assert emitted.status == "rejected"
    assert provider.get_status(track_id=emitted.track_id) == "rejected"
    assert "company-001/br-001" in emitted.raw_payload_ref
