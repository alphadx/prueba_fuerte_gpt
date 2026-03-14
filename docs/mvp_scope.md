# Alcance MVP y criterios de aceptación

## Objetivo
Definir el alcance funcional mínimo (MVP) para el ERP de barrio en Chile y establecer criterios de aceptación verificables para una primera salida a QA.

## Alcance funcional del MVP

### 1) Inventario
- Mantención básica de productos (código, nombre, precio, estado).
- Visualización de stock por sucursal.
- Descuento automático de stock al confirmar una venta en POS.
- Registro de movimiento de inventario asociado a la venta.

### 2) POS básico
- Apertura de caja.
- Creación de venta con múltiples líneas.
- Cierre de venta con totales y detalle.
- Cierre de caja con resumen simple de operaciones.

### 3) Pagos
- Pago en efectivo.
- Pago electrónico por adaptador simulado (stub) para validar flujo técnico.
- Registro del resultado del pago (aprobado/rechazado) y trazabilidad.

### 4) Boleta electrónica (sandbox)
- Emisión de boleta electrónica de prueba vía integrador en sandbox.
- Almacenamiento de identificadores de seguimiento y estado del documento.
- Consulta del estado de emisión desde API.

### 5) E-commerce con retiro en tienda
- Catálogo básico y carrito.
- Checkout web para crear pedido.
- Selección de modalidad "retiro en tienda".
- Persistencia del pedido con estado inicial `recibido`.

### 6) RRHH documental con alertas
- Registro de documentos por empleado con fecha de vencimiento.
- Reglas de alerta para vencimiento próximo.
- Generación de alerta visible en sistema para seguimiento interno.

## Criterios de aceptación medibles

1. **Emisión de boleta de prueba sin error**
   - Dado un flujo de venta válido,
   - cuando se solicita emisión de boleta en sandbox,
   - entonces el sistema registra el documento con estado de envío exitoso y sin excepciones no controladas.

2. **Descuento de stock por venta**
   - Dado un producto con stock inicial conocido,
   - cuando una venta es confirmada,
   - entonces el stock final disminuye exactamente en la cantidad vendida,
   - y existe movimiento de inventario asociado.

3. **Creación de pedido web con retiro en tienda**
   - Dado un cliente navegando el canal web,
   - cuando confirma checkout con modalidad retiro en tienda,
   - entonces se crea el pedido con estado `recibido` y referencia de sucursal de retiro.

4. **Generación de alerta por documento próximo a vencer**
   - Dado un documento de empleado dentro del umbral de alerta configurado,
   - cuando corre el proceso de evaluación de alertas,
   - entonces se crea un evento de alerta visible y trazable.

## Historias de usuario

### HU-INV-01: Venta descuenta inventario
Como **encargado de caja**, quiero que al confirmar una venta se descuente automáticamente el stock para mantener inventario confiable.

**Criterios de aceptación (Gherkin):**
- **Given** producto con stock 10
- **When** se confirma venta por 2 unidades
- **Then** el stock queda en 8
- **And** se registra movimiento de salida con referencia a la venta

---

### HU-POS-01: Cierre de venta en POS
Como **cajero**, quiero cerrar una venta con detalle de ítems y total para cobrar correctamente.

**Criterios de aceptación (Gherkin):**
- **Given** una caja abierta
- **When** agrego productos y confirmo la venta
- **Then** la venta queda persistida con líneas, subtotal, impuestos y total
- **And** queda disponible para pagos

---

### HU-PAY-01: Pago efectivo
Como **cajero**, quiero registrar pago en efectivo para completar una venta presencial.

**Criterios de aceptación (Gherkin):**
- **Given** una venta pendiente de pago
- **When** selecciono medio de pago efectivo y confirmo
- **Then** la venta cambia a pagada
- **And** se registra transacción de pago con monto y timestamp

---

### HU-PAY-02: Pago electrónico simulado
Como **equipo técnico**, quiero un pago electrónico simulado para validar integración sin depender de un adquirente real.

**Criterios de aceptación (Gherkin):**
- **Given** una venta pendiente de pago
- **When** se procesa pago por gateway stub
- **Then** se recibe respuesta aprobada o rechazada
- **And** se guarda trazabilidad de request/response

---

### HU-BIL-01: Emisión de boleta sandbox
Como **cajero**, quiero emitir boleta electrónica en sandbox para validar cumplimiento fiscal del flujo MVP.

**Criterios de aceptación (Gherkin):**
- **Given** una venta pagada y apta para documento tributario
- **When** se invoca emisión de boleta en integrador sandbox
- **Then** se crea registro de documento tributario con identificador externo
- **And** su estado inicial queda consultable desde API

---

### HU-ECOM-01: Pedido web con retiro
Como **cliente**, quiero comprar online y retirar en tienda para asegurar disponibilidad antes de desplazarme.

**Criterios de aceptación (Gherkin):**
- **Given** carrito con productos válidos
- **When** confirmo checkout seleccionando retiro en tienda
- **Then** se crea pedido con estado `recibido`
- **And** queda asociada sucursal de retiro

---

### HU-HR-01: Alerta por vencimiento documental
Como **encargado RRHH**, quiero recibir alertas de documentos por vencer para evitar incumplimientos.

**Criterios de aceptación (Gherkin):**
- **Given** documento con vencimiento dentro de umbral (30/15/7/1 días)
- **When** corre el job de alertas
- **Then** se genera evento de alerta con severidad y fecha
- **And** la alerta queda visible para seguimiento

## Definition of Done (DoD) del paso 1
Un ítem del alcance MVP se considera "Done" cuando cumple todo lo siguiente:

1. **Definición funcional aprobada**
   - Historia de usuario redactada y validada por negocio/producto.

2. **Criterios de aceptación verificables**
   - Cada historia incluye criterios concretos tipo Given/When/Then.

3. **Trazabilidad mínima**
   - Existe mapeo explícito entre:
     - historia,
     - endpoint/proceso principal,
     - evidencia de prueba.

4. **Datos de prueba definidos**
   - Se especifican precondiciones mínimas para ejecutar pruebas funcionales.

5. **Resultado observable**
   - El flujo deja evidencia persistida (estado, evento o registro) auditable.

6. **Sin bloqueadores críticos abiertos**
   - No quedan dudas funcionales de alto impacto para iniciar implementación del paso 2.

## Fuera de alcance en este MVP
- Integración de pagos reales en producción.
- Emisión fiscal en ambiente productivo SII.
- Automatizaciones avanzadas de pricing/promociones.
- Workflows de RRHH no documentales (remuneraciones, asistencia avanzada).
