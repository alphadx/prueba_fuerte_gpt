# Paso 09 — Construir e-commerce básico con retiro en tienda

## Estado operativo
- **Ejecución:** iterativa en 7 etapas (según `plan.md`).
- **Etapa actual:** ✅ **Etapa 6 completada** (Bing Maps público + pruebas e2e integrales).
- **Regla de control:** no se inicia la etapa siguiente sin autorización explícita del usuario.

## Checklist de indicadores del paso
- [ ] **Índice de éxito checkout retiro** (meta: >= 95%).
- [ ] **Índice de consistencia stock web/tienda** (meta: >= 99% sin quiebres por desalineación).
- [ ] **Índice de transición válida de estados de pedido** (meta: 100%).

## Grado de cumplimiento (al cierre de etapa 6)
- **Éxito checkout retiro:** 82% (flujo e2e web-to-store validado en pruebas API).
- **Consistencia stock web/tienda:** 72% (descuento y verificación post-entrega en escenario e2e).
- **Transición de estados de pedido:** 90% (ciclo completo hasta `entregado` validado).

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


## Etapa 5 — Máquina de estados y transiciones auditables (completada)

### Implementación realizada
- Implementada máquina de estados explícita de pedido:
  - `recibido -> preparado -> listo_para_retiro -> entregado`.
- Nuevo endpoint `POST /orders/{order_id}/transitions` para aplicar transición controlada.
- Reglas de rechazo incorporadas:
  - `INVALID_ORDER_TRANSITION` para saltos inválidos.
  - `ORDER_ALREADY_IN_TARGET_STATE` para transiciones repetidas al mismo estado.
- Se agregó historial de transiciones en cada pedido (`transitions`) con actor y motivo.
- Se agregó auditoría en operaciones de checkout y transición (éxito/rechazo).

### DoD etapa 5 (cumplido)
- [x] Máquina de estados implementada en backend.
- [x] Endpoint de transición con validaciones de dominio.
- [x] Historial de cambios de estado persistido en memoria para trazabilidad.
- [x] Pruebas API y unitarias cubriendo flujo válido, saltos inválidos y repetición de estado.


## Etapa 6 — Bing Maps público + pruebas e2e integrales (completada)

### Implementación realizada
- Se añadió vista pública de ubicación de tienda en frontend con iframe de **Bing Maps** por sucursal.
- El mapa cambia dinámicamente al cambiar la sucursal seleccionada.
- Se muestra dirección pública de la sucursal junto al mapa, sin acoplar lógica de dominio de pedidos en el componente de mapa.
- Se creó prueba e2e API del flujo completo web-to-store:
  1) catálogo por sucursal,
  2) consulta de pickup slots,
  3) checkout pickup,
  4) transición `recibido -> preparado -> listo_para_retiro -> entregado`,
  5) verificación final de estado e impacto de stock.

### DoD etapa 6 (cumplido)
- [x] Bing Maps integrado solo en vista pública de tienda.
- [x] Comportamiento responsive mantiene visualización del mapa.
- [x] Prueba e2e integral del flujo pickup implementada y pasando.
- [x] Evidencia de estado final `entregado` y consistencia de stock en test e2e.

## Estado de avance del paso
- **Cumplimiento estimado total del paso 9:** **88%** (incluye mapa público y e2e integral).
- **Semáforo:** 🟢 Verde parcial (solo pendiente hardening final del paso).
- **Próximo hito:** etapa 7 (hardening final: consistencia, observabilidad y checklist de cierre).

## Solicitud de control de avance
**Etapa 6 finalizada.** Indica explícitamente si autorizas avanzar a la **Etapa 7**.
