# Paso 11 — Etapa 2: Diseño canónico de seed y fixtures

## Objetivo de la etapa
Definir una especificación determinística de datos semilla y fixtures críticos para habilitar la implementación idempotente del bootstrap QA en etapas siguientes.

## Reglas de diseño
1. **Determinismo:** identificadores estables y timestamps controlados.
2. **Idempotencia:** re-ejecutar carga debe producir estado equivalente.
3. **Trazabilidad:** cada fixture crítico debe tener ID funcional y resultado esperado.
4. **Aislamiento:** fixtures deben poder validarse por smoke sin dependencias implícitas ocultas.

## Seed mínimo canónico (paso 11)

### Entidades obligatorias
- **Company (1):** `comp-001`.
- **Branch (1):** `branch-001` asociada a `comp-001`.
- **Users por rol (4):** `admin`, `cajero`, `bodega`, `rrhh`.
- **Products (20):** `prod-001` a `prod-020` con SKU estable y stock inicial.
- **Employees (2):** `emp-001`, `emp-002`.
- **EmployeeDocuments (2):**
  - documento de `emp-001` con vencimiento cercano para activar alertas,
  - documento de `emp-002` sin vencimiento cercano.
- **AlarmRules por defecto:** umbrales `30/15/7/1` habilitados.

### Convención de IDs estables
- `comp-001`, `branch-001`
- `usr-admin-001`, `usr-cajero-001`, `usr-bodega-001`, `usr-rrhh-001`
- `prod-001..prod-020`
- `emp-001`, `emp-002`
- `edoc-001`, `edoc-002`
- `arule-030`, `arule-015`, `arule-007`, `arule-001`

### Fechas de referencia
- `seed_reference_date`: fecha fija configurable (ej: `2025-01-15`).
- Documento cercano a vencer: `expires_on = seed_reference_date + 7 días`.
- Documento en cumplimiento: `expires_on = seed_reference_date + 90 días`.

### Orden de carga recomendado
1. Company/Branch.
2. Users/Roles.
3. Products + stock inicial.
4. Employees.
5. DocumentType(s) y EmployeeDocuments.
6. AlarmRules por defecto.
7. Validación de invariantes post-seed.

## Invariantes post-seed (check automático)
1. Existe exactamente 1 compañía y 1 sucursal base.
2. Existen al menos 4 usuarios cubriendo todos los roles objetivo.
3. Existen exactamente 20 productos semilla con stock positivo.
4. Existen 2 empleados y 2 documentos asociados.
5. Al menos 1 documento queda dentro de ventana de alerta (<= 7 días).
6. Existen reglas de alerta activas para `30/15/7/1`.

## Catálogo canónico de fixtures críticos

| Escenario | Fixture ID | Precondición | Resultado esperado | Smoke check |
|---|---|---|---|---|
| Venta efectivo | `FX-SALE-CASH` | sesión de caja abierta + stock disponible | venta `paid`, pago `approved`, stock decrementado | `PASS/FAIL` |
| Venta electrónica | `FX-SALE-ELECTRONIC` | producto semilla + método `card_stub` | venta `confirmed`, pago en flujo electrónico | `PASS/FAIL` |
| Pedido web retiro | `FX-WEB-PICKUP` | catálogo activo en `branch-001` | orden creada en estado `recibido` | `PASS/FAIL` |
| Emisión boleta sandbox | `FX-BILLING-SBX` | venta facturable creada | documento tributario emitido en sandbox | `PASS/FAIL` |
| Webhook pago | `FX-PAYMENT-WEBHOOK` | pago stub existente con idempotency key | webhook reconciliado idempotente (sin duplicados) | `PASS/FAIL` |

## Matriz requisito ↔ verificación
- **Dataset mínimo completo** → check de cardinalidades e IDs canónicos.
- **Cobertura de fixtures críticos** → catálogo con 5 escenarios obligatorios.
- **Idempotencia de bootstrap** → doble ejecución produce invariantes idénticos.
- **Preparación QA operable** → smoke por fixture crítico en una corrida.
- **Meta de tiempo** → registrar runtime total del comando de bootstrap.

## Definición de salida de la etapa 2
La etapa 2 se considera cerrada cuando:
1. Existe especificación canónica aprobada de seed (este documento).
2. Está definido el catálogo de fixtures críticos con contratos verificables.
3. Queda explícito el orden de carga e invariantes para implementación de etapa 3.
