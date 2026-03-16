from app.modules.employee_documents.file_storage import employee_document_file_storage_service


def setup_function() -> None:
    employee_document_file_storage_service.reset_state()


def test_file_storage_create_and_list_by_document() -> None:
    created = employee_document_file_storage_service.create_file(
        employee_document_id="edoc-0001",
        file_name="licencia.pdf",
        content_type="application/pdf",
        storage_uri="minio://hr/edoc-0001/licencia.pdf",
        uploaded_at="2026-01-10T10:00:00Z",
    )

    assert created.id.startswith("efile-")
    files = employee_document_file_storage_service.list_files(employee_document_id="edoc-0001")
    assert len(files) == 1
    assert files[0].storage_uri == "minio://hr/edoc-0001/licencia.pdf"
