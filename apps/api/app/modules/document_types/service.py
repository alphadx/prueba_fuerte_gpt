"""In-memory service layer for document types module."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any


class DocumentSchemaValidationError(Exception):
    """Raised when an instance does not satisfy document metadata schema."""


ALLOWED_SCHEMA_TYPES = {"string", "number", "integer", "boolean", "object", "array", "null"}


@dataclass
class DocumentType:
    id: str
    code: str
    name: str
    requires_expiry: bool
    is_active: bool
    schema_version: int
    metadata_schema: dict[str, Any]


class DocumentTypeService:
    def __init__(self) -> None:
        self._by_id: dict[str, DocumentType] = {}
        self._ids_by_code: dict[str, str] = {}
        self._seq = 0
        self._lock = RLock()

    def list_document_types(self) -> list[DocumentType]:
        with self._lock:
            return [DocumentType(**vars(item)) for item in self._by_id.values()]

    def create_document_type(
        self,
        *,
        code: str,
        name: str,
        requires_expiry: bool,
        is_active: bool,
        schema_version: int,
        metadata_schema: dict[str, Any],
    ) -> DocumentType:
        with self._lock:
            if code in self._ids_by_code:
                raise ValueError("document type code already exists")
            _validate_schema_structure(metadata_schema)
            self._seq += 1
            document_type_id = f"dt-{self._seq:04d}"
            document_type = DocumentType(
                id=document_type_id,
                code=code,
                name=name,
                requires_expiry=requires_expiry,
                is_active=is_active,
                schema_version=schema_version,
                metadata_schema=metadata_schema,
            )
            self._by_id[document_type_id] = document_type
            self._ids_by_code[code] = document_type_id
            return DocumentType(**vars(document_type))

    def get_document_type(self, document_type_id: str) -> DocumentType:
        with self._lock:
            if document_type_id not in self._by_id:
                raise KeyError("document type not found")
            return DocumentType(**vars(self._by_id[document_type_id]))

    def get_document_type_by_code(self, code: str) -> DocumentType:
        with self._lock:
            document_type_id = self._ids_by_code.get(code)
            if document_type_id is None:
                raise KeyError("document type not found")
            return DocumentType(**vars(self._by_id[document_type_id]))

    def update_document_type(
        self,
        document_type_id: str,
        *,
        name: str | None,
        requires_expiry: bool | None,
        is_active: bool | None,
        schema_version: int | None,
        metadata_schema: dict[str, Any] | None,
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
            if metadata_schema is not None:
                _validate_schema_structure(metadata_schema)
                document_type.metadata_schema = metadata_schema
            if schema_version is not None:
                if schema_version < document_type.schema_version:
                    raise ValueError("schema_version cannot decrease")
                document_type.schema_version = schema_version
            return DocumentType(**vars(document_type))

    def validate_metadata(self, *, document_type_code: str, metadata: dict[str, Any]) -> None:
        document_type = self.get_document_type_by_code(document_type_code)
        _validate_instance(document_type.metadata_schema, metadata, path="metadata")

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


def _schema_type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "null":
        return value is None
    return False


def _validate_schema_structure(schema: dict[str, Any]) -> None:
    if schema.get("type") != "object":
        raise ValueError("metadata_schema must declare type=object")
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("metadata_schema.properties must be an object")

    required = schema.get("required", [])
    if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
        raise ValueError("metadata_schema.required must be a list of strings")

    for key, prop_schema in properties.items():
        if not isinstance(prop_schema, dict):
            raise ValueError(f"metadata_schema.properties.{key} must be an object")
        prop_type = prop_schema.get("type")
        if prop_type not in ALLOWED_SCHEMA_TYPES:
            raise ValueError(f"metadata_schema.properties.{key}.type is not supported")


def _validate_instance(schema: dict[str, Any], instance: Any, *, path: str) -> None:
    expected_type = schema.get("type")
    if expected_type and not _schema_type_matches(instance, expected_type):
        raise DocumentSchemaValidationError(f"{path} must be of type {expected_type}")

    if expected_type == "object":
        assert isinstance(instance, dict)
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                raise DocumentSchemaValidationError(f"{path}.{key} is required")

        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                _validate_instance(properties[key], value, path=f"{path}.{key}")

    if expected_type == "array":
        assert isinstance(instance, list)
        item_schema = schema.get("items")
        if item_schema is None:
            return
        if not isinstance(item_schema, dict):
            raise DocumentSchemaValidationError(f"{path}.items must be an object schema")
        for idx, value in enumerate(instance):
            _validate_instance(item_schema, value, path=f"{path}[{idx}]")


document_type_service = DocumentTypeService()
