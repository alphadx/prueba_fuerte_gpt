"""In-memory service layer for document types module."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass
class DocumentType:
    id: str
    code: str
    name: str
    requires_expiry: bool
    is_active: bool


class DocumentTypeService:
    def __init__(self) -> None:
        self._by_id: dict[str, DocumentType] = {}
        self._ids_by_code: dict[str, str] = {}
        self._seq = 0
        self._lock = RLock()

    def list_document_types(self) -> list[DocumentType]:
        with self._lock:
            return [DocumentType(**vars(item)) for item in self._by_id.values()]

    def create_document_type(self, *, code: str, name: str, requires_expiry: bool, is_active: bool) -> DocumentType:
        with self._lock:
            if code in self._ids_by_code:
                raise ValueError("document type code already exists")
            self._seq += 1
            document_type_id = f"dt-{self._seq:04d}"
            document_type = DocumentType(
                id=document_type_id,
                code=code,
                name=name,
                requires_expiry=requires_expiry,
                is_active=is_active,
            )
            self._by_id[document_type_id] = document_type
            self._ids_by_code[code] = document_type_id
            return DocumentType(**vars(document_type))

    def get_document_type(self, document_type_id: str) -> DocumentType:
        with self._lock:
            if document_type_id not in self._by_id:
                raise KeyError("document type not found")
            return DocumentType(**vars(self._by_id[document_type_id]))

    def update_document_type(
        self,
        document_type_id: str,
        *,
        name: str | None,
        requires_expiry: bool | None,
        is_active: bool | None,
    ) -> DocumentType:
        with self._lock:
            if document_type_id not in self._by_id:
                raise KeyError("document type not found")
            document_type = self._by_id[document_type_id]
            if name is not None:
                document_type.name = name
            if requires_expiry is not None:
                document_type.requires_expiry = requires_expiry
            if is_active is not None:
                document_type.is_active = is_active
            return DocumentType(**vars(document_type))

    def delete_document_type(self, document_type_id: str) -> None:
        with self._lock:
            document_type = self.get_document_type(document_type_id)
            del self._by_id[document_type_id]
            del self._ids_by_code[document_type.code]

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._ids_by_code.clear()
            self._seq = 0


document_type_service = DocumentTypeService()
