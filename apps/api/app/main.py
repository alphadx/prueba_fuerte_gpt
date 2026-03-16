"""Aplicación base de API para el MVP.

Notas para desarrolladores y agentes GPT:
- Mantener este archivo mínimo; la lógica de negocio debe vivir en módulos de dominio.
- Cualquier cambio de contrato HTTP debe reflejarse primero en `apps/api/openapi.yaml`.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.modules.branches.router import router as branches_router
from app.modules.cash_sessions.router import router as cash_sessions_router
from app.modules.document_types.router import router as document_types_router
from app.modules.employee_documents.router import router as employee_documents_router
from app.modules.payments.router import router as payments_router
from app.modules.employees.router import router as employees_router
from app.modules.products.router import router as products_router
from app.modules.sales.router import router as sales_router
from app.modules.users.router import router as users_router
from app.services.queue import queue_client

app = FastAPI(title="ERP Barrio API", version="0.3.8")


class AlertDispatchRequest(BaseModel):
    employee_id: str = Field(min_length=1)
    document_type: str = Field(min_length=1)
    days_to_expire: int = Field(ge=0)


@app.get("/health")
def health() -> dict[str, str]:
    """Healthcheck simple para smoke tests y orquestación."""
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Readiness endpoint for container orchestration checks."""
    return {"status": "ready"}


@app.post("/alerts/dispatch")
def dispatch_alert(payload: AlertDispatchRequest) -> dict[str, str]:
    """Encola un evento de alerta documental para procesamiento asíncrono."""
    try:
        backend = queue_client.enqueue_alert(payload.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"status": "queued", "backend": backend}


app.include_router(products_router)

app.include_router(users_router)

app.include_router(branches_router)

app.include_router(employees_router)

app.include_router(document_types_router)

app.include_router(employee_documents_router)

app.include_router(payments_router)

app.include_router(cash_sessions_router)

app.include_router(sales_router)
