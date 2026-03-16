"""In-memory service layer for employee documents module."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any


@dataclass
class EmployeeDocument:
    id: str
    employee_id: str
    document_type_code: str
    expires_on: str
    status: str
    metadata: dict[str, Any]


class EmployeeDocumentService:
    def __init__(self) -> None:
        self._by_id: dict[str, EmployeeDocument] = {}
        self._ids_by_key: dict[tuple[str, str], str] = {}
        self._seq = 0
        self._lock = RLock()

    def list_documents(self) -> list[EmployeeDocument]:
        with self._lock:
            return [EmployeeDocument(**vars(item)) for item in self._by_id.values()]

    def create_document(
        self,
        *,
        employee_id: str,
        document_type_code: str,
        expires_on: str,
        status: str,
        metadata: dict[str, Any],
    ) -> EmployeeDocument:
        with self._lock:
            unique_key = (employee_id, document_type_code)
            if unique_key in self._ids_by_key:
                raise ValueError("employee document already exists")
            self._seq += 1
            document_id = f"edoc-{self._seq:04d}"
            document = EmployeeDocument(
                id=document_id,
                employee_id=employee_id,
                document_type_code=document_type_code,
                expires_on=expires_on,
                status=status,
                metadata=metadata,
            )
            self._by_id[document_id] = document
            self._ids_by_key[unique_key] = document_id
            return EmployeeDocument(**vars(document))

    def get_document(self, document_id: str) -> EmployeeDocument:
        with self._lock:
            if document_id not in self._by_id:
                raise KeyError("employee document not found")
            return EmployeeDocument(**vars(self._by_id[document_id]))

    def update_document(
        self,
        document_id: str,
        *,
        expires_on: str | None,
        status: str | None,
        metadata: dict[str, Any] | None,
    ) -> EmployeeDocument:
        with self._lock:
            if document_id not in self._by_id:
                raise KeyError("employee document not found")
            document = self._by_id[document_id]
            if expires_on is not None:
                document.expires_on = expires_on
            if status is not None:
                document.status = status
            if metadata is not None:
                document.metadata = metadata
            return EmployeeDocument(**vars(document))

    def delete_document(self, document_id: str) -> None:
        with self._lock:
            document = self.get_document(document_id)
            del self._by_id[document_id]
            del self._ids_by_key[(document.employee_id, document.document_type_code)]

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._ids_by_key.clear()
            self._seq = 0


employee_document_service = EmployeeDocumentService()
