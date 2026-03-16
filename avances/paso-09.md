# Paso 09 — Construir e-commerce básico con retiro en tienda

## Estado operativo
- **Ejecución:** iterativa en 7 etapas (según `plan.md`).
- **Etapa actual:** ✅ **Etapa 2 completada** (diseño modular y contratos API).
- **Regla de control:** no se inicia la etapa siguiente sin autorización explícita del usuario.

## Checklist de indicadores del paso
- [ ] **Índice de éxito checkout retiro** (meta: >= 95%).
- [ ] **Índice de consistencia stock web/tienda** (meta: >= 99% sin quiebres por desalineación).
- [ ] **Índice de transición válida de estados de pedido** (meta: 100%).

## Grado de cumplimiento (al cierre de etapa 2)
- **Éxito checkout retiro:** 10% (contratos definidos, frontend/backend aún no implementados).
- **Consistencia stock web/tienda:** 10% (reglas y eventos definidos, sin ejecución real).
- **Transición de estados de pedido:** 15% (contrato de transición definido, falta enforcement en servicio).

---

## Etapa 1 — Análisis funcional/técnico y criterios de aceptación (cerrada)

### Objetivo
Definir el comportamiento esperado del canal web con retiro en tienda, sus fronteras técnicas y criterios de aceptación medibles.

### Salidas de etapa 1
- Alcance funcional validado: catálogo por sucursal, carrito, checkout con `PickupSlot`, creación de pedido y ciclo de retiro.
- Reglas de dominio base: estado inicial `recibido`, transiciones forward-only y validación de stock al confirmar checkout.
- Riesgos priorizados: sobreventa, desfase de stock, saltos de estado y acoplamiento UI/dominio.

---

## Etapa 2 — Diseño modular + contratos API (completada)

### 1) Objetivo de la etapa
Definir la arquitectura lógica del paso 9 y publicar contratos API canónicos (requests/responses/errores) para habilitar implementación incremental en etapas 3-6.

### 2) Diseño modular propuesto

#### 2.1 `catalog`
- **Responsabilidad:** exponer productos y disponibilidad por sucursal para navegación web.
- **Entradas clave:** `branch_id`, filtros (`query`, `category`, `page`, `limit`).
- **Salidas clave:** listado de productos con `available_stock`, `price`, `is_pickup_enabled`.

#### 2.2 `cart`
- **Responsabilidad:** mantener composición del carrito y validar cantidades.
- **Entradas clave:** `cart_id`, líneas (`product_id`, `qty`, `branch_id`).
- **Salidas clave:** subtotal, validaciones de stock preliminares, versión del carrito.

#### 2.3 `pickup_slots`
- **Responsabilidad:** gestionar disponibilidad de franjas de retiro por sucursal.
- **Entradas clave:** `branch_id`, fecha objetivo, capacidad por slot.
- **Salidas clave:** slots con estado (`available`, `low_capacity`, `full`).

#### 2.4 `checkout`
- **Responsabilidad:** confirmar compra de retiro de forma idempotente.
- **Entradas clave:** `cart_id`, `pickup_slot_id`, datos cliente mínimos, `idempotency_key`.
- **Salidas clave:** `order_id`, estado inicial `recibido`, resumen de confirmación.

#### 2.5 `orders`
- **Responsabilidad:** orquestar ciclo de vida del pedido pickup y su trazabilidad.
- **Entradas clave:** `order_id`, transición solicitada, actor (`web`, `staff`).
- **Salidas clave:** estado actual, historial de eventos, timestamps SLA.

#### 2.6 `inventory`
- **Responsabilidad:** reserva/descuento/liberación de stock por eventos de checkout/pedido.
- **Entradas clave:** eventos de orden y líneas de productos.
- **Salidas clave:** movimientos consistentes por sucursal y resultado de reserva.

### 3) Contratos API canónicos (v1)

> Prefijo sugerido: `/api/v1`

#### 3.1 Catálogo y stock por sucursal
- `GET /catalog/products?branch_id={id}&q={text}&page={n}&limit={n}`
  - **200**:
    ```json
    {
      "items": [
        {
          "product_id": "prod_001",
          "sku": "SKU-001",
          "name": "Arroz 1kg",
          "price": 1290,
          "currency": "CLP",
          "available_stock": 18,
          "branch_id": "br_01",
          "is_pickup_enabled": true
        }
      ],
      "page": 1,
      "limit": 20,
      "total": 1
    }
    ```
  - **400** `INVALID_BRANCH`

#### 3.2 Carrito
- `POST /carts`
  - **Request**:
    ```json
    { "branch_id": "br_01" }
    ```
  - **201**:
    ```json
    { "cart_id": "cart_123", "branch_id": "br_01", "version": 1 }
    ```

- `POST /carts/{cart_id}/items`
  - **Request**:
    ```json
    { "product_id": "prod_001", "qty": 2 }
    ```
  - **200**:
    ```json
    {
      "cart_id": "cart_123",
      "version": 2,
      "items": [{ "product_id": "prod_001", "qty": 2, "unit_price": 1290 }],
      "subtotal": 2580
    }
    ```
  - **409** `INSUFFICIENT_STOCK_PRECHECK`

#### 3.3 Pickup slots
- `GET /pickup-slots?branch_id={id}&date={YYYY-MM-DD}`
  - **200**:
    ```json
    {
      "branch_id": "br_01",
      "date": "2026-03-16",
      "slots": [
        {
          "pickup_slot_id": "slot_10_11",
          "start_at": "2026-03-16T10:00:00-03:00",
          "end_at": "2026-03-16T11:00:00-03:00",
          "status": "available",
          "remaining_capacity": 7
        }
      ]
    }
    ```
  - **404** `NO_SLOTS_CONFIGURED`

#### 3.4 Confirmación checkout pickup
- `POST /checkout/pickup/confirm`
  - **Headers:** `Idempotency-Key: <uuid>`
  - **Request**:
    ```json
    {
      "cart_id": "cart_123",
      "pickup_slot_id": "slot_10_11",
      "customer": {
        "name": "María Pérez",
        "email": "maria@example.com",
        "phone": "+56911112222"
      }
    }
    ```
  - **201**:
    ```json
    {
      "order_id": "ord_9001",
      "order_state": "recibido",
      "branch_id": "br_01",
      "pickup_slot_id": "slot_10_11",
      "totals": { "subtotal": 2580, "currency": "CLP" },
      "created_at": "2026-03-16T10:22:00-03:00"
    }
    ```
  - **409** `INSUFFICIENT_STOCK_AT_CONFIRMATION`
  - **409** `PICKUP_SLOT_UNAVAILABLE`
  - **422** `INVALID_CART_STATE`

#### 3.5 Gestión de estado de pedido
- `GET /orders/{order_id}`
  - **200**: estado actual + historial.

- `POST /orders/{order_id}/transitions`
  - **Request**:
    ```json
    {
      "target_state": "preparado",
      "actor": "staff",
      "reason": "pedido armado en bodega"
    }
    ```
  - **200**:
    ```json
    {
      "order_id": "ord_9001",
      "previous_state": "recibido",
      "current_state": "preparado",
      "transition_at": "2026-03-16T11:00:00-03:00"
    }
    ```
  - **409** `INVALID_ORDER_TRANSITION`
  - **409** `ORDER_ALREADY_IN_TARGET_STATE`

### 4) Errores normalizados
Formato común:
```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK_AT_CONFIRMATION",
    "message": "Stock insuficiente al confirmar checkout.",
    "details": { "product_id": "prod_001", "requested": 2, "available": 1 },
    "trace_id": "trc_abc123"
  }
}
```

Catálogo inicial de códigos:
- `INVALID_BRANCH`
- `INVALID_CART_STATE`
- `INSUFFICIENT_STOCK_PRECHECK`
- `INSUFFICIENT_STOCK_AT_CONFIRMATION`
- `PICKUP_SLOT_UNAVAILABLE`
- `INVALID_ORDER_TRANSITION`
- `ORDER_ALREADY_IN_TARGET_STATE`
- `ORDER_NOT_FOUND`

### 5) Invariantes técnicos acordados para implementación
- `branch_id` es obligatorio y consistente en catálogo/carrito/checkout/pedido.
- Confirmación de checkout debe ser idempotente mediante `Idempotency-Key`.
- Estado inicial obligatorio de orden confirmada: `recibido`.
- Transiciones permitidas exclusivamente: `recibido -> preparado -> listo_para_retiro -> entregado`.
- Ninguna transición depende del estado local de UI; el backend es fuente de verdad.

### 6) DoD de etapa 2 (cumplido)
- [x] Diseño modular documentado por responsabilidad.
- [x] Contratos API de catálogo/carrito/slots/checkout/orders definidos.
- [x] Errores normalizados publicados.
- [x] Invariantes de dominio y técnica establecidos.
- [x] Entrada lista para etapa 3 (frontend MVP).

## Estado de avance del paso
- **Cumplimiento estimado total del paso 9:** **30%** (análisis + diseño contractual cerrados).
- **Semáforo:** 🟡 Amarillo (base de implementación lista).
- **Próximo hito:** etapa 3 (frontend MVP catálogo/carrito/checkout con `PickupSlot`).

## Solicitud de control de avance
**Etapa 2 finalizada.** Indica explícitamente si autorizas avanzar a la **Etapa 3**.
