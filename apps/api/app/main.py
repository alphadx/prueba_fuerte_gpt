"""Aplicación base de API para el MVP.

Notas para desarrolladores y agentes GPT:
- Mantener este archivo mínimo; la lógica de negocio debe vivir en módulos de dominio.
- Cualquier cambio de contrato HTTP debe reflejarse primero en `apps/api/openapi.yaml`.
"""

from fastapi import FastAPI

app = FastAPI(title="ERP Barrio API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Healthcheck simple para smoke tests y orquestación."""
    return {"status": "ok"}
