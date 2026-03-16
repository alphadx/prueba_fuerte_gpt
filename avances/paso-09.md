# Paso 09 — Construir e-commerce básico con retiro en tienda

## Estado operativo
- **Ejecución:** iterativa en 7 etapas (según `plan.md`).
- **Etapa actual:** ✅ **Etapa 3 completada** (frontend MVP catálogo/carrito/checkout con `PickupSlot`).
- **Regla de control:** no se inicia la etapa siguiente sin autorización explícita del usuario.

## Checklist de indicadores del paso
- [ ] **Índice de éxito checkout retiro** (meta: >= 95%).
- [ ] **Índice de consistencia stock web/tienda** (meta: >= 99% sin quiebres por desalineación).
- [ ] **Índice de transición válida de estados de pedido** (meta: 100%).

## Grado de cumplimiento (al cierre de etapa 3)
- **Éxito checkout retiro:** 35% (flujo visual de checkout habilitado en frontend MVP).
- **Consistencia stock web/tienda:** 20% (stock visible por sucursal en UI, sin reserva backend todavía).
- **Transición de estados de pedido:** 15% (diseño contractual definido, falta enforcement en servicio).

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

## Estado de avance del paso
- **Cumplimiento estimado total del paso 9:** **45%** (análisis + contratos + frontend MVP).
- **Semáforo:** 🟡 Amarillo (avance sólido, falta integración backend).
- **Próximo hito:** etapa 4 (backend de creación de pedido + reserva/descuento de stock + idempotencia).

## Solicitud de control de avance
**Etapa 3 finalizada.** Indica explícitamente si autorizas avanzar a la **Etapa 4**.
