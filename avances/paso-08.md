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
- **Etapa en ejecución:** **Etapa 2 de 7 (completada)**.
- **Cumplimiento estimado del paso 8:** **30%** (2/7 con análisis + contrato canónico implementado).
- **Semáforo:** 🟡 Amarillo (en progreso, base de diseño lista).

## Checklist de control por etapa
- [x] Etapa 1 — análisis y criterios iniciales.
- [x] Etapa 2 — contrato `PaymentGateway` y DTOs canónicos.
- [ ] Etapa 3 — adaptador `cash` y conciliación de caja.
- [ ] Etapa 4 — stubs `transbank_stub` y `mercadopago_stub`.
- [ ] Etapa 5 — webhook unificado idempotente.
- [ ] Etapa 6 — feature flags + pruebas integrales.
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


**Solicitud de avance:** si estás de acuerdo, indícame **"avanzar etapa 3"** y continúo con el adaptador `cash` + conciliación de caja mínima.
