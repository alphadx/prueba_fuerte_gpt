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

## Índices clave de término por paso/etapa (1 a 12)

> Escala sugerida por índice: **Cumple / Parcial / No cumple**.
> Regla sugerida de cierre de etapa: **Terminado** cuando todos los índices críticos están en “Cumple” y no hay bloqueadores severos abiertos.

### Paso 1: Definir alcance MVP y criterios de aceptación
- **Índice de cobertura de alcance MVP:** % de módulos MVP con historia + criterio de aceptación documentado (meta: 100%).
- **Índice de trazabilidad funcional:** % de historias enlazadas a evidencia de validación (meta: >= 95%).
- **Índice de ambigüedad funcional:** # de dudas críticas abiertas en backlog (meta: 0).

### Paso 2: Crear arquitectura base y repositorio ejecutable
- **Índice de estructura base creada:** presencia de carpetas objetivo (`apps/api`, `apps/web`, `workers/alerts`, `infra`, `tests`) (meta: 100%).
- **Índice de ejecución local inicial:** `make up`, `make test`, `make seed` operativos en entorno limpio (meta: 3/3).
- **Índice de contrato API inicial:** endpoints base descritos en OpenAPI y versionados (meta: 100% de endpoints MVP definidos).

### Paso 3: Levantar servicios de soporte con Docker Compose
- **Índice de salud de servicios core:** % de servicios core en estado healthy (meta: 100%).
- **Índice de arranque reproducible:** tiempo de bootstrap desde cero (meta: <= 15 min).
- **Índice de paridad de entorno:** `.env.example` cubre todas las variables requeridas de ejecución (meta: 100%).

### Paso 4: Diseñar modelo de datos inicial y migraciones
- **Índice de cobertura de entidades MVP:** % de entidades del plan con migración aplicada (meta: 100%).
- **Índice de migraciones idempotentes:** ejecución up/down sin errores en entorno limpio (meta: 100%).
- **Índice de consistencia relacional:** # de errores de FK/constraints en pruebas de integración (meta: 0 críticos).

### Paso 5: Implementar API modular con autenticación y permisos
- **Índice de cobertura CRUD por módulo:** % de operaciones mínimas implementadas por módulo (meta: >= 90% MVP).
- **Índice de seguridad de acceso:** % de endpoints protegidos con JWT/roles según definición (meta: 100%).
- **Índice de auditoría crítica:** % de operaciones sensibles con registro auditable (meta: 100%).

### Paso 6: Implementar POS y flujo de caja mínimo operable
- **Índice de completitud de flujo POS:** apertura -> venta -> pago -> cierre ejecutable fin a fin (meta: 100%).
- **Índice de exactitud de caja:** diferencia arqueo vs transacciones (meta: 0 o dentro de tolerancia definida).
- **Índice de consistencia inventario-venta:** % de ventas que generan movimiento de stock correcto (meta: 100%).

### Paso 7: Integrar boleta electrónica vía proveedor (sandbox)
- **Índice de emisión sandbox exitosa:** % de boletas de prueba emitidas sin error (meta: >= 98%).
- **Índice de latencia de emisión:** tiempo p95 de emisión/acuse sandbox (meta: umbral definido por equipo).
- **Índice de resiliencia de cola:** tasa de reintentos exitosos tras fallo transitorio (meta: >= 95%).

### Paso 8: Integrar capa de pagos por adaptadores
- **Índice de cobertura de medios MVP:** drivers definidos y operativos (`cash`, stubs electrónicos) (meta: 100%).
- **Índice de idempotencia webhook:** duplicados que alteran estado de pago (meta: 0).
- **Índice de conciliación básica:** % de pagos conciliados vs ventas pagadas (meta: 100%).

### Paso 9: Construir e-commerce básico con retiro en tienda
- **Índice de éxito checkout retiro:** % de checkouts exitosos en e2e (meta: >= 95%).
- **Índice de consistencia stock web/tienda:** discrepancia de stock entre canales (meta: <= umbral definido).
- **Índice de transición de estados de pedido:** % de pedidos que siguen flujo válido de estados (meta: 100%).

### Paso 10: Implementar RRHH documental flexible y motor de alertas
- **Índice de cobertura documental:** % de empleados con documentos requeridos cargados en pruebas (meta: 100% fixture).
- **Índice de precisión de alertas:** % de alertas generadas correctamente según umbrales (meta: >= 95%).
- **Índice de entrega de notificaciones pruebas:** % de eventos entregados a canal in-app/email de prueba (meta: >= 95%).

### Paso 11: Crear estado inicial válido de pruebas
- **Índice de bootstrap QA:** tiempo para dejar entorno listo con `make bootstrap-test-state` (meta: <= 10 min).
- **Índice de completitud de fixtures críticos:** escenarios críticos disponibles y ejecutables (meta: 100%).
- **Índice de estabilidad de smoke tests:** tasa de éxito repetida (meta: >= 95% en corridas consecutivas).

### Paso 12: Validación final, observabilidad y checklist de salida
- **Índice de salud de pipeline:** % de jobs (lint/test/integración/smoke) en verde (meta: 100%).
- **Índice de SLO técnico mínimo:** cumplimiento de latencia/errores/cola definidos (meta: 100% de SLO MVP).
- **Índice de preparación go-live:** checklist de salida completo y aprobado (meta: 100% ítems críticos cerrados).

## Semáforo de avance recomendado
- **Verde (Terminado):** todos los índices críticos cumplen meta y sin bloqueadores severos.
- **Amarillo (Parcial):** 1 o más índices no críticos bajo meta, con plan de cierre fechado.
- **Rojo (No terminado):** 1 o más índices críticos fuera de meta o bloqueadores severos abiertos.
