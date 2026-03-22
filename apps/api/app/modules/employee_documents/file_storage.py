"""In-memory file storage metadata service for employee documents."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass
class EmployeeDocumentFile:
    id: str
    employee_document_id: str
    file_name: str
    content_type: str
    storage_uri: str
    uploaded_at: str


class EmployeeDocumentFileStorageService:
    def __init__(self) -> None:
        self._by_id: dict[str, EmployeeDocumentFile] = {}
        self._by_document_id: dict[str, list[str]] = {}
        self._seq = 0
        self._lock = RLock()

    def create_file(
        self,
        *,
        employee_document_id: str,
        file_name: str,
        content_type: str,
        storage_uri: str,
        uploaded_at: str,
    ) -> EmployeeDocumentFile:
        with self._lock:
            self._seq += 1
            file_id = f"efile-{self._seq:04d}"
            file_item = EmployeeDocumentFile(
                id=file_id,
                employee_document_id=employee_document_id,
                file_name=file_name,
                content_type=content_type,
                storage_uri=storage_uri,
                uploaded_at=uploaded_at,
            )
            self._by_id[file_id] = file_item
            self._by_document_id.setdefault(employee_document_id, []).append(file_id)
            return EmployeeDocumentFile(**vars(file_item))

    def list_files(self, *, employee_document_id: str) -> list[EmployeeDocumentFile]:
        with self._lock:
            ids = self._by_document_id.get(employee_document_id, [])
            return [EmployeeDocumentFile(**vars(self._by_id[item_id])) for item_id in ids]

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._by_document_id.clear()
            self._seq = 0


employee_document_file_storage_service = EmployeeDocumentFileStorageService()
