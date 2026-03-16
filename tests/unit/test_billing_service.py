from app.modules.billing.service import billing_service


def test_billing_service_idempotent_enqueue_and_successful_processing(monkeypatch):
    monkeypatch.delenv("BILLING_SANDBOX_FORCE_ERROR", raising=False)
    billing_service.reset_state()

    first = billing_service.enqueue_sale_document(sale_id="sale-01", branch_id="br-1", total=1200)
    second = billing_service.enqueue_sale_document(sale_id="sale-01", branch_id="br-1", total=1200)

    assert first.idempotency_key == second.idempotency_key

    processed, succeeded, failed = billing_service.process_pending(limit=10)
    assert (processed, succeeded, failed) == (1, 1, 0)

    final = billing_service.get_by_sale_id("sale-01")
    assert final.status == "accepted"
    assert final.track_id is not None
    assert final.folio is not None
    assert final.xml_url is not None
    assert final.pdf_url is not None
    assert final.sii_status == "accepted"


def test_billing_service_transitions_to_failed_after_max_attempts(monkeypatch):
    monkeypatch.setenv("BILLING_SANDBOX_FORCE_ERROR", "true")
    billing_service.reset_state()
    billing_service.enqueue_sale_document(sale_id="sale-02", branch_id="br-1", total=1200)

    for _ in range(3):
        billing_service.process_pending(limit=10)

    final = billing_service.get_by_sale_id("sale-02")
    assert final.status == "failed"
    assert final.attempts == final.max_attempts
    assert "temporary error" in (final.last_error or "")


def test_billing_service_supports_multiple_document_types_for_same_sale(monkeypatch):
    monkeypatch.delenv("BILLING_SANDBOX_FORCE_ERROR", raising=False)
    billing_service.reset_state()

    boleta = billing_service.enqueue_sale_document(sale_id="sale-03", branch_id="br-1", total=1200, document_type="boleta")
    factura = billing_service.enqueue_sale_document(sale_id="sale-03", branch_id="br-1", total=1200, document_type="factura")

    assert boleta.document_type == "boleta"
    assert factura.document_type == "factura"

    processed, succeeded, failed = billing_service.process_pending(limit=10)
    assert (processed, succeeded, failed) == (2, 2, 0)

    assert billing_service.get_by_sale_id("sale-03", document_type="boleta").status == "accepted"
    assert billing_service.get_by_sale_id("sale-03", document_type="factura").status == "accepted"
