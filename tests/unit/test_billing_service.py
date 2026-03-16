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

    for _ in range(20):
        billing_service.process_pending(limit=10)

    final = billing_service.get_by_sale_id("sale-02")
    assert final.status == "failed"
    assert final.dead_lettered is True
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


def test_billing_service_event_queue_drains_then_processes(monkeypatch):
    monkeypatch.delenv("BILLING_SANDBOX_FORCE_ERROR", raising=False)
    billing_service.reset_state()

    billing_service.enqueue_sale_emission_event(sale_id="sale-04", branch_id="br-1", total=1200)

    queued = billing_service.get_by_sale_id("sale-04")
    assert queued.status == "queued"
    assert queued.attempts == 0

    enqueued, processed, succeeded, failed, dead_lettered = billing_service.process_worker_batch(limit=10)
    assert (enqueued, processed, succeeded, failed, dead_lettered) == (1, 1, 1, 0, 0)

    final = billing_service.get_by_sale_id("sale-04")
    assert final.status == "accepted"
    assert final.track_id is not None


def test_billing_service_backoff_and_dead_letter_tracking(monkeypatch):
    monkeypatch.setenv("BILLING_SANDBOX_FORCE_ERROR", "true")
    billing_service.reset_state()
    billing_service.enqueue_sale_document(sale_id="sale-05", branch_id="br-1", total=1200)

    processed, succeeded, failed = billing_service.process_pending(limit=10)
    assert (processed, succeeded, failed) == (1, 0, 1)

    retrying = billing_service.get_by_sale_id("sale-05")
    assert retrying.status == "retryable_error"
    assert retrying.retry_after_batches > 0
    assert retrying.dead_lettered is False

    for _ in range(20):
        billing_service.process_pending(limit=10)

    failed_doc = billing_service.get_by_sale_id("sale-05")
    assert failed_doc.status == "failed"
    assert failed_doc.dead_lettered is True
    assert billing_service.dead_letter_count() == 1
