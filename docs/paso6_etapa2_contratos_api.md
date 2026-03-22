# Paso 6 — Etapa 2: Contratos API POS + Caja

## 1) Objetivo
Definir contratos canónicos de request/response y errores para los endpoints del flujo POS y caja, alineados con las reglas de dominio de la Etapa 1.

## 2) Endpoints cubiertos
- Caja: `POST /cash-sessions`, `PATCH /cash-sessions/{id}`, `GET /cash-sessions`, `GET /cash-sessions/{id}`.
- Ventas POS: `POST /sales/complete`, `GET /sales`.
- Pagos (soporte de flujo): `POST /payments`, `PATCH /payments/{id}`.

## 3) Contratos de request/response (canónicos)

### 3.1 `POST /cash-sessions`
**Request mínimo**
```json
{
  "branch_id": "branch-1",
  "opened_by": "user-cajero",
  "opening_amount": 10000,
  "status": "open"
}
```

**Response 201**
```json
{
  "id": "cs_123",
  "branch_id": "branch-1",
  "opened_by": "user-cajero",
  "opening_amount": 10000,
  "closing_amount": null,
  "expected_amount": 10000,
  "difference_amount": null,
  "status": "open"
}
```

### 3.2 `PATCH /cash-sessions/{id}` (cierre / arqueo)
**Request mínimo de cierre**
```json
{
  "closing_amount": 14500,
  "cash_delta": 4500,
  "status": "closed"
}
```

**Response 200**
```json
{
  "id": "cs_123",
  "branch_id": "branch-1",
  "opened_by": "user-cajero",
  "opening_amount": 10000,
  "closing_amount": 14500,
  "expected_amount": 14500,
  "difference_amount": 0,
  "status": "closed"
}
```

### 3.3 `POST /sales/complete`
**Request mínimo**
```json
{
  "branch_id": "branch-1",
  "cash_session_id": "cs_123",
  "sold_by": "user-cajero",
  "payment_method": "cash",
  "lines": [
    {
      "product_id": "prod-1",
      "quantity": 2
    }
  ]
}
```

**Response 201**
```json
{
  "id": "sale_123",
  "branch_id": "branch-1",
  "cash_session_id": "cs_123",
  "sold_by": "user-cajero",
  "status": "confirmed",
  "subtotal": 2000,
  "taxes": 380,
  "total": 2380,
  "payment_method": "cash",
  "payment_status": "approved",
  "billing_event_emitted": true,
  "lines": [
    {
      "product_id": "prod-1",
      "quantity": 2,
      "unit_price": 1000,
      "line_subtotal": 2000,
      "line_tax": 380,
      "line_total": 2380
    }
  ]
}
```

### 3.4 `GET /sales`
**Response 200**
```json
{
  "items": [
    {
      "id": "sale_123",
      "branch_id": "branch-1",
      "cash_session_id": "cs_123",
      "sold_by": "user-cajero",
      "status": "confirmed",
      "subtotal": 2000,
      "taxes": 380,
      "total": 2380,
      "payment_method": "cash",
      "payment_status": "approved",
      "billing_event_emitted": true,
      "lines": [
        {
          "product_id": "prod-1",
          "quantity": 2,
          "unit_price": 1000,
          "line_subtotal": 2000,
          "line_tax": 380,
          "line_total": 2380
        }
      ]
    }
  ]
}
```

### 3.5 `POST /payments` (flujo auxiliar)
**Request mínimo**
```json
{
  "sale_id": "sale_123",
  "amount": 2380,
  "method": "cash",
  "status": "approved",
  "idempotency_key": "pay-sale_123-cash"
}
```

## 4) Tabla de errores canónicos

| Endpoint | Código | Regla de negocio | `detail` esperado (ejemplo) |
|---|---:|---|---|
| `POST /sales/complete` | 409 | caja inexistente/cerrada | `Cash session must be open` |
| `POST /sales/complete` | 409 | sucursal inconsistente | `Cash session branch mismatch` |
| `POST /sales/complete` | 409 | stock insuficiente | `Insufficient stock for product ...` |
| `PATCH /cash-sessions/{id}` | 409 | cierre inválido por estado | `Only open cash sessions can be closed` |
| `PATCH /cash-sessions/{id}` | 404 | sesión no existe | `Cash session not found` |
| `POST /payments` | 409 | idempotency key duplicada | `Payment already exists for idempotency key` |

> Nota: Los textos exactos de `detail` pueden variar por implementación, pero el código HTTP y tipo de conflicto deben mantenerse estables para consumidores del API.

## 5) Reglas de consistencia de contrato
1. Todos los endpoints del flujo POS/caja deben devolver errores de dominio con `4xx` + `detail` legible.
2. `POST /sales/complete` debe mantener determinismo de montos (`subtotal + taxes = total`).
3. Cierre de caja debe conservar consistencia de arqueo:
   - `expected_amount = opening_amount + cash_delta`
   - `difference_amount = closing_amount - expected_amount`
4. El contrato de venta confirmada debe incluir `payment_status` y `billing_event_emitted` para trazabilidad operacional.

## 6) Checklist de validación de etapa
- [x] Endpoints clave identificados y documentados.
- [x] Payload mínimo por endpoint documentado.
- [x] Respuestas esperadas (success) documentadas.
- [x] Mapa de errores canónicos por regla de dominio documentado.
- [x] Reglas de consistencia de contrato documentadas.

## 7) Salida formal de Etapa 2
Contratos API POS + caja definidos y listos para guiar la implementación/ajustes de la **Etapa 3 (reglas de caja y arqueo mínimo operable)**.
