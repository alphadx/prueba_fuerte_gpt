# Paso 08 — Integrar capa de pagos por adaptadores

## Modalidad de ejecución
- Este paso se ejecuta como **prototipo iterativo de 7 etapas**.
- **Regla obligatoria:** al cerrar cada etapa se debe solicitar orden explícita del usuario antes de iniciar la siguiente.

## Etapas del prototipo (controladas)
1. **Análisis funcional/técnico** y criterios de aceptación por canal/sucursal.
2. **Contrato `PaymentGateway`** + modelo canónico `PaymentIntent/PaymentResult` y errores normalizados.
3. **Adaptador `cash`** con cierre local y conciliación de caja.
4. **Adaptadores `transbank_stub` + `mercadopago_stub`** con autorización/captura simulada.
5. **Webhook unificado** (confirmación/rechazo) con firma, idempotencia y trazabilidad.
6. **Feature flags por sucursal/canal** + pruebas integrales (happy, duplicados, rechazos, timeout).
7. **Hardening final**: conciliación básica multi-medio, auditoría y checklist de salida.

## Estado actual del prototipo
- **Etapa en ejecución:** **Etapa 6 de 7 (completada)**.
- **Cumplimiento estimado del paso 8:** **90%** (6/7 con feature flags y pruebas integrales cerradas).
- **Semáforo:** 🟡 Amarillo (en progreso, base de diseño lista).

## Checklist de control por etapa
- [x] Etapa 1 — análisis y criterios iniciales.
- [x] Etapa 2 — contrato `PaymentGateway` y DTOs canónicos.
- [x] Etapa 3 — adaptador `cash` y conciliación de caja.
- [x] Etapa 4 — stubs `transbank_stub` y `mercadopago_stub`.
- [x] Etapa 5 — webhook unificado idempotente.
- [x] Etapa 6 — feature flags + pruebas integrales.
- [ ] Etapa 7 — hardening documental y cierre.

---

## Evidencia Etapa 1 — Análisis funcional/técnico

### 1) Contexto funcional esperado
El paso 8 debe habilitar una capa extensible para medios de pago con tres metas: (a) sumar proveedores sin acoplar el core de ventas, (b) evitar efectos duplicados por callbacks/reintentos, y (c) conciliar ventas vs resultado de cobro para reducir fugas de ingresos.

### 2) Diagnóstico AS-IS (estado actual)
- El módulo `payments` actual opera como CRUD en memoria (`method`, `status`, `idempotency_key`) y no modela intentos de pago ni callbacks de gateway.
- No existe aún una interfaz `PaymentGateway` ni drivers por proveedor (`cash`, `transbank_stub`, `mercadopago_stub`).
- No existe webhook unificado para confirmación/rechazo ni control de firma/metadata.
- No hay flags por sucursal/canal para despliegue progresivo de medios de pago.
- No existe proceso de conciliación explícito entre venta, intento de pago y resultado final.

### 3) Referencias aplicadas para la etapa
Se usó la skill local `payment-gateway-idempotency` y sus referencias:
- `payment-state-model.md`: estados canónicos base (`initiated`, `pending_confirmation`, `approved`, `rejected`, `reconciled`) y transición monotónica.
- `webhook-idempotency-checklist.md`: checklist de cierre de la arquitectura de idempotencia y conciliación.

### 4) Decisiones de diseño para etapas siguientes
1. Definir un **modelo canónico interno** para desacoplar payloads proveedor-específicos.
2. Imponer **transiciones monotónicas** de estado para ignorar callbacks obsoletos.
3. Separar **autorización/captura del cobro** de la finalización de negocio (side-effects de venta).
4. Persistir metadatos crudos (request/response/webhook) para diagnóstico y auditoría.
5. Introducir rollout por **feature flags** de `branch_id + channel` (POS/web).

### 5) Criterios de aceptación de Etapa 1 (cumplidos)
- [x] Se identificó brecha AS-IS vs TO-BE para adaptadores de pago.
- [x] Se fijó el conjunto de estados canónicos para el dominio de pagos.
- [x] Se definieron invariantes de confiabilidad para etapas 2–7.
- [x] Se dejó trazabilidad documental de fuentes y checklist de control.

### 6) Criterios de aceptación del paso 8 (objetivo final)
- `PaymentGateway` definido e implementado para `cash`, `transbank_stub`, `mercadopago_stub`.
- Webhook unificado con validación de firma/metadata + idempotencia por clave de evento.
- Feature flags funcionales por sucursal/canal.
- Conciliación básica operativa (venta vs intento vs resultado) con reporte de diferencias.
- Pruebas de idempotencia (duplicados), rechazos y timeout aprobadas.

### 7) Riesgos y mitigaciones identificadas
- **Riesgo:** callbacks fuera de orden.  
  **Mitigación:** estado monotónico + descarte de eventos stale.
- **Riesgo:** doble confirmación por webhook duplicado.  
  **Mitigación:** clave idempotente por evento y deduplicación persistente.
- **Riesgo:** acople de reglas proveedor en core de ventas.  
  **Mitigación:** adapters + mapeo canónico centralizado.
- **Riesgo:** habilitar medio de pago sin preparación operacional.  
  **Mitigación:** flags por sucursal/canal con rollout progresivo.

## Protocolo de interacción
1. Ejecutar una etapa.
2. Registrar evidencia y riesgos en este documento.
3. Solicitar orden explícita para iniciar la siguiente.



## Evidencia Etapa 2 — Contrato `PaymentGateway` y modelo canónico

### Implementación realizada
- Se incorporó `apps/api/app/modules/payments/gateway.py` con el contrato `PaymentGateway` (authorize/capture/parse_webhook/validate_signature).
- Se definieron DTOs canónicos `PaymentIntent`, `PaymentResult`, `WebhookEvent` para desacoplar proveedores del core de ventas.
- Se normalizaron estados (`PaymentStatus`) y errores (`PaymentErrorCode`) para un lenguaje interno estable entre adaptadores.
- Se agregó regla de transición monotónica `can_transition(current, target)` para soportar idempotencia y descarte de callbacks stale.

### Criterios de aceptación de Etapa 2 (cumplidos)
- [x] Contrato único de gateway definido para los tres drivers objetivo del MVP.
- [x] Modelo canónico de request/response de pagos definido y versionable.
- [x] Catálogo de errores normalizados disponible para mapear respuestas proveedor-específicas.
- [x] Regla de transición monotónica implementada para etapas de webhook/conciliación.

### Próximo impacto en Etapa 3
- El adaptador `cash` usará `PaymentIntent/PaymentResult` sin acoplarse al API surface actual de CRUD.
- La conciliación de caja podrá operar sobre estados canónicos (`approved`, `reconciled`) con semántica consistente entre medios.

## Evidencia Etapa 3 — Adaptador `cash` y conciliación mínima

### Implementación realizada
- Se creó `apps/api/app/modules/payments/cash_adapter.py` con `CashPaymentGateway`, implementando el contrato canónico (`authorize`, `capture`, `parse_webhook`, `validate_signature`).
- Se extendió `PaymentService` para crear cobros cash vía modelo canónico (`create_cash_payment`) y para emitir reporte de conciliación por sucursal (`reconcile_cash_by_branch`).
- Se habilitaron endpoints:
  - `POST /payments/cash` para registrar pago cash usando `PaymentIntent` canónico.
  - `GET /payments/cash/reconciliation/{branch_id}` para conciliación básica de caja por sucursal.
- Se añadieron schemas dedicados para request/respuesta de cash y reconciliación.

### Criterios de aceptación de Etapa 3 (cumplidos)
- [x] Adaptador `cash` implementado sin acoplar reglas al core de ventas.
- [x] Confirmación local de pago cash con estado canónico `approved`.
- [x] Conciliación mínima por sucursal disponible (totales, aprobados, pendientes, montos).
- [x] Cobertura de pruebas unitarias y API para flujo cash + conciliación.

### Riesgos controlados en esta etapa
- Duplicidad de operaciones cash: se mantiene restricción por `idempotency_key`.
- Inconsistencia de cierre por sucursal: reporte de conciliación segmentado por `branch_id`.

## Evidencia Etapa 4 — `transbank_stub` y `mercadopago_stub`

### Implementación realizada
- Se creó `apps/api/app/modules/payments/stub_adapters.py` con `TransbankStubGateway` y `MercadopagoStubGateway` sobre el contrato `PaymentGateway`.
- Se implementaron flujos simulados de `authorize` (estado `pending_confirmation`) y `capture` (estado `approved`), incluyendo rutas forzadas de rechazo/timeout por metadata.
- Se añadió `gateway_registry` para resolución por nombre de proveedor y desacople de router/servicio respecto de implementaciones concretas.
- Se extendió `PaymentService` con `create_stub_payment(...)` para ejecutar autorización + captura simulada y persistir resultado canónico.
- Se expuso endpoint `POST /payments/stubs/{provider}` para generar pagos con `transbank_stub` y `mercadopago_stub`.

### Criterios de aceptación de Etapa 4 (cumplidos)
- [x] `transbank_stub` implementado con flujo de autorización/captura simulado.
- [x] `mercadopago_stub` implementado con flujo de autorización/captura simulado.
- [x] Estados canónicos normalizados en persistencia de pagos (`approved`/`rejected`).
- [x] Cobertura de pruebas unitarias y API para providers soportados y provider inválido.

### Riesgos controlados en esta etapa
- Acoplamiento por proveedor: mitigado con `gateway_registry` y contrato único.
- Errores de enrutamiento por proveedor inválido: controlado con validación y `400 unsupported provider`.

## Evidencia Etapa 5 — Webhook unificado, firma e idempotencia

### Implementación realizada
- Se incorporó procesamiento de webhook unificado en `PaymentService.process_webhook_event(...)`, con soporte multi-provider y mapeo por `provider_payment_id`.
- Se añadió validación de firma vía `PaymentGateway.validate_signature(...)` por proveedor, devolviendo error explícito para firmas inválidas.
- Se implementó deduplicación por evento (`provider:event_id`) para garantizar idempotencia y evitar mutaciones repetidas de estado.
- Se aplicó transición monotónica con `can_transition(...)` para ignorar transiciones stale y mantener trazabilidad de estado previo/actual.
- Se expuso endpoint `POST /payments/webhooks/{provider}` con respuesta canónica de procesamiento (`duplicated`, `payment_id`, `previous_status`, `current_status`).

### Criterios de aceptación de Etapa 5 (cumplidos)
- [x] Webhook único disponible para confirmación/rechazo por proveedor.
- [x] Validación de firma/metadata activa en ingestión del webhook.
- [x] Idempotencia de evento aplicada y comprobada con duplicados.
- [x] Trazabilidad del efecto del webhook disponible en respuesta y auditoría.

### Riesgos controlados en esta etapa
- Reentrega de callbacks: controlada por deduplicación persistida en memoria.
- Callbacks fuera de orden: mitigado con transiciones monotónicas de estado.
- Inyección de callbacks inválidos: mitigada por validación de firma por provider.

## Evidencia Etapa 6 — Feature flags por sucursal/canal + pruebas integrales

### Implementación realizada
- Se añadió control de feature flags por (`branch_id`, `channel`, `method`) en `PaymentService`, con `set_method_flag`, `list_method_flags` y validación de habilitación antes de crear pagos.
- Se incorporaron endpoints de administración/consulta de flags:
  - `PUT /payments/flags` (upsert de habilitación por sucursal/canal/medio).
  - `GET /payments/flags` (listado de configuración activa).
- Los flujos `cash` y `stubs` ahora respetan flag y responden `403` cuando el medio está deshabilitado para esa combinación.
- Se ejecutó batería integral de escenarios: happy path, duplicados por `idempotency_key`, rechazo forzado y timeout forzado en stubs.

### Criterios de aceptación de Etapa 6 (cumplidos)
- [x] Feature flags operativos por sucursal/canal/medio de pago.
- [x] Bloqueo efectivo de medios deshabilitados con error de autorización funcional (`403`).
- [x] Pruebas integrales de escenarios críticos (`happy`, `duplicado`, `rechazo`, `timeout`).
- [x] Cobertura API y unidad para reglas de activación y flujo de stubs.

### Riesgos controlados en esta etapa
- Activación accidental de medios en sucursal no preparada: mitigado con flags explícitos.
- Drift de configuración entre canales: mitigado por clave compuesta (`branch+channel+method`).
- Reprocesos operativos por duplicidad/reintentos: cubierto por pruebas de duplicados e idempotencia existente.

**Solicitud de avance:** si estás de acuerdo, indícame **"avanzar etapa 7"** y continúo con hardening final, auditoría y checklist de salida.
