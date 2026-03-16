# Paso 09 — Construir e-commerce básico con retiro en tienda

## Estado operativo
- **Ejecución:** iterativa en 7 etapas (según `plan.md`).
- **Etapa actual:** ✅ **Etapa 4 completada** (backend de creación de pedido + descuento stock + idempotencia).
- **Regla de control:** no se inicia la etapa siguiente sin autorización explícita del usuario.

## Checklist de indicadores del paso
- [ ] **Índice de éxito checkout retiro** (meta: >= 95%).
- [ ] **Índice de consistencia stock web/tienda** (meta: >= 99% sin quiebres por desalineación).
- [ ] **Índice de transición válida de estados de pedido** (meta: 100%).

## Grado de cumplimiento (al cierre de etapa 4)
- **Éxito checkout retiro:** 60% (checkout backend implementado con respuesta canónica).
- **Consistencia stock web/tienda:** 55% (descuento stock en confirmación + rollback ante falla).
- **Transición de estados de pedido:** 25% (estado inicial `recibido` persistido, faltan transiciones etapa 5).

---

## Etapa 1 — Análisis funcional/técnico y criterios de aceptación (cerrada)
- Alcance funcional validado: catálogo por sucursal, carrito, checkout con `PickupSlot`, creación de pedido y ciclo de retiro.
- Reglas de dominio base: estado inicial `recibido`, transiciones forward-only y validación de stock al confirmar checkout.
- Riesgos priorizados: sobreventa, desfase de stock, saltos de estado y acoplamiento UI/dominio.

## Etapa 2 — Diseño modular + contratos API (cerrada)
- Diseño modular documentado para `catalog`, `cart`, `pickup_slots`, `checkout`, `orders`, `inventory`.
- Contratos API v1 y catálogo de errores normalizados definidos.
- Invariantes técnicos establecidos: consistencia de sucursal, idempotencia y máquina de estados forward-only.

---

## Etapa 3 — Frontend MVP (completada)

### 1) Objetivo de la etapa
Entregar una experiencia web mínima funcional para retiro en tienda con:
- catálogo por sucursal,
- carrito,
- checkout con selección de `PickupSlot`,
- validaciones básicas UX responsive en desktop y móvil.

### 2) Implementación realizada
Se creó un frontend MVP estático en `apps/web`:
- `index.html`: estructura de layout, selector de sucursal, catálogo, carrito y formulario de checkout.
- `styles.css`: estilos base, panel de carrito, tarjetas de producto y comportamiento responsive (`@media` <= 900px).
- `app.js`: lógica cliente para:
  - cargar productos por sucursal,
  - mostrar stock por sucursal,
  - agregar productos al carrito,
  - calcular subtotal,
  - seleccionar y renderizar `PickupSlot` por sucursal,
  - validar checkout y confirmar pedido simulado en estado `recibido`.

### 3) Reglas UX aplicadas
- Producto sin stock aparece deshabilitado para evitar agregar ítems no disponibles.
- Cambio de sucursal reinicia carrito para evitar mezcla de stock entre sucursales.
- Checkout impide confirmar carrito vacío.
- Formulario valida nombre, email y teléfono antes de confirmar.

### 4) Resultado funcional de la etapa
- Se dispone de una maqueta operable de flujo:
  1. seleccionar sucursal,
  2. navegar catálogo con stock visible,
  3. agregar productos al carrito,
  4. seleccionar `PickupSlot`,
  5. confirmar retiro y obtener mensaje de pedido creado (estado inicial `recibido`).

### 5) Pendientes para etapa 4
- Conectar checkout real a backend y persistencia de orden.
- Reemplazar confirmación simulada por creación real con idempotencia.
- Integrar reglas de reserva/descuento de stock por sucursal.

### 6) DoD de etapa 3 (cumplido)
- [x] Catálogo por sucursal visible en frontend.
- [x] Carrito funcional con subtotal.
- [x] Checkout con selección de `PickupSlot`.
- [x] Validaciones básicas de formulario y carrito.
- [x] Layout responsive base para móvil/desktop.


## Etapa 4 — Backend checkout + stock + idempotencia (completada)

### Implementación realizada
- Nuevo módulo `orders` en API con servicio y router.
- Endpoint `POST /checkout/pickup/confirm` con header `Idempotency-Key` para evitar doble descuento por reintentos.
- Creación de pedido pickup en estado inicial `recibido`.
- Descuento de stock por línea al confirmar checkout.
- Rollback de movimientos de stock cuando ocurre falla de confirmación (ej.: stock insuficiente).
- Endpoint `GET /orders/{order_id}` para consulta del pedido creado.
- Endpoints de soporte para frontend:
  - `GET /catalog/products?branch_id=...`
  - `GET /pickup-slots?branch_id=...&date=...`

### Validaciones y reglas de etapa 4
- Confirmación exige al menos una línea de pedido.
- Cantidades deben ser positivas.
- Reintento con la misma `Idempotency-Key` retorna el mismo `order_id` (operación idempotente).
- Error por stock insuficiente retorna `INSUFFICIENT_STOCK_AT_CONFIRMATION`.

### DoD etapa 4 (cumplido)
- [x] Backend de creación de pedido pickup implementado.
- [x] Descuento de stock aplicado al confirmar checkout.
- [x] Rollback de stock en fallas de confirmación.
- [x] Idempotencia operativa por `Idempotency-Key`.
- [x] Cobertura de pruebas unitarias y API para el flujo principal.

## Estado de avance del paso
- **Cumplimiento estimado total del paso 9:** **62%** (análisis + contratos + frontend + backend checkout).
- **Semáforo:** 🟡 Amarillo (backend base listo, falta máquina de estados de transición).
- **Próximo hito:** etapa 5 (máquina de estados y transiciones auditables de pedido).

## Solicitud de control de avance
**Etapa 4 finalizada.** Indica explícitamente si autorizas avanzar a la **Etapa 5**.
