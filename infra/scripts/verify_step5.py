"""Static verification for step 5 API modularization assets.

Checks:
- Core auth/permissions/audit files exist.
- Expected module slices exist with router/service/schemas.
- OpenAPI contains expected paths for each slice.
- API tests and unit tests for each slice exist.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CORE_FILES = (
    "apps/api/app/core/auth.py",
    "apps/api/app/core/permissions.py",
    "apps/api/app/core/audit.py",
)

MODULES = (
    "products",
    "users",
    "branches",
    "employees",
    "document_types",
    "employee_documents",
    "payments",
    "cash_sessions",
)

OPENAPI_PATH_MARKERS = (
    "/products:",
    "/users:",
    "/branches:",
    "/employees:",
    "/document-types:",
    "/employee-documents:",
    "/payments:",
    "/cash-sessions:",
)

API_TEST_FILES = (
    "tests/api/test_products.py",
    "tests/api/test_users.py",
    "tests/api/test_branches.py",
    "tests/api/test_employees.py",
    "tests/api/test_document_types.py",
    "tests/api/test_employee_documents.py",
    "tests/api/test_payments.py",
    "tests/api/test_cash_sessions.py",
)

UNIT_TEST_FILES = (
    "tests/unit/test_user_service.py",
    "tests/unit/test_branch_service.py",
    "tests/unit/test_employee_service.py",
    "tests/unit/test_document_type_service.py",
    "tests/unit/test_employee_document_service.py",
    "tests/unit/test_payment_service.py",
    "tests/unit/test_cash_session_service.py",
)


def assert_exists(relative_path: str) -> None:
    path = ROOT / relative_path
    if not path.exists():
        raise AssertionError(f"Missing required file: {relative_path}")


def main() -> None:
    for file_path in CORE_FILES:
        assert_exists(file_path)

    for module_name in MODULES:
        for file_name in ("router.py", "service.py", "schemas.py"):
            assert_exists(f"apps/api/app/modules/{module_name}/{file_name}")

    openapi_content = (ROOT / "apps/api/openapi.yaml").read_text(encoding="utf-8")
    for marker in OPENAPI_PATH_MARKERS:
        if marker not in openapi_content:
            raise AssertionError(f"Missing OpenAPI path marker: {marker}")

    for file_path in API_TEST_FILES:
        assert_exists(file_path)

    for file_path in UNIT_TEST_FILES:
        assert_exists(file_path)

    print("[ok] Validación estática del paso 5 completada")


if __name__ == "__main__":
    main()
