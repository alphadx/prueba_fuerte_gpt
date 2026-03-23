# Paso 07 — Integrar boleta electrónica vía proveedor (sandbox)

## Modalidad de ejecución
- Este paso se considera **prototipo iterativo**.
- Se divide en **7 etapas secuenciales**.
- **Regla obligatoria:** al cerrar cada etapa, se debe pedir al usuario la orden de avance para continuar.

## Etapas del prototipo (controladas)
1. **Análisis funcional/técnico** y criterios de aceptación fiscal sandbox.
2. **Contrato `BillingProvider`** y DTOs canónicos (request/response).
3. **Adaptador sandbox** con folio, XML/PDF, track ID y estado SII.
4. **Desacople POS/caja** con emisión asíncrona (sin bloqueo de venta).
5. **Resiliencia** con reintentos acotados, idempotencia y estados terminales.
6. **Consulta de estado + pruebas** de integración (happy/failure/duplicados).
7. **Hardening documental** y checklist de cierre del paso.

## Estado actual del prototipo
- **Etapa en ejecución:** **Etapa 7 de 7 (completada)**.
- **Cumplimiento estimado del paso 7:** **100%** (7/7 completadas; hardening y checklist final cerrados).
- **Semáforo:** 🟢 Verde (Terminado).
- **Observación:** Se asume enfoque iterativo; no se considera cierre definitivo del paso hasta completar 7/7 con aprobación explícita por etapa.

## Checklist de control por etapa
- [x] Etapa 1 — análisis y criterios iniciales.
- [x] Etapa 2 — contrato proveedor.
- [x] Etapa 3 — adaptador sandbox.
- [x] Etapa 4 — desacople asíncrono POS.
- [x] Etapa 5 — resiliencia/reintentos/idempotencia.
- [x] Etapa 6 — consulta de estado + pruebas.
- [x] Etapa 7 — hardening documental.

## Protocolo de interacción
1. Ejecutar una etapa.
2. Registrar evidencia y riesgos en este documento.
3. Pedir al usuario: **"Indícame avanzar a la Etapa N"**.
4. No iniciar la siguiente etapa sin esa orden.

## Evidencia etapa 2
- Contrato canónico mantiene `company_id`, `branch_id`, `sale_id`, `document_type`, `totals`, `idempotency_key` en `BillingEmissionRequest` y `provider_document_id`, `track_id`, `status`, `raw_payload_ref` en respuesta.
- Se corrigió almacenamiento para soportar múltiples documentos por venta (`(sale_id, document_type)`), evitando colisiones de idempotencia entre tipos documentales.
- Se expuso `raw_payload_ref` en schema/router/OpenAPI para trazabilidad auditable.


## Evidencia etapa 3
- Adaptador sandbox ampliado con modos configurables por entorno: `BILLING_SANDBOX_FAIL_FIRST_N`, `BILLING_SANDBOX_EMIT_STATUS`, `BILLING_SANDBOX_STATUS_MODE`, además de `BILLING_SANDBOX_FORCE_ERROR`.
- `raw_payload_ref` ahora incluye contexto (`company_id/branch_id`) para mejorar trazabilidad por tenant/sucursal.
- Se agregó estado interno del adaptador para simular transición progresiva `processing -> accepted` y para contabilizar intentos por idempotency key.
- Se incorporó `reset_state()` en el provider y el `BillingService.reset_state()` ahora reinicia también el estado interno del adaptador cuando está disponible.
- Pruebas unitarias nuevas del adaptador cubren: fail-first-N, estado progresivo y rechazo explícito.


## Refuerzo de cumplimiento SII
- Se agregó marco documental y referencias técnicas SII en `docs/sii_billing_compliance.md`.
- Se añadieron comentarios con referencias SII en el adaptador sandbox para trazabilidad de diseño durante el prototipo.
- Este refuerzo se considera prerequisito de gobernanza antes de iniciar la siguiente etapa (Etapa 4).


## Evidencia etapa 4
- El flujo POS ahora encola eventos de emisión (`enqueue_sale_emission_event`) en vez de crear documento tributario directamente en la confirmación de venta.
- Se agregó cola interna de emisión en `BillingService` con `drain_emission_events` y procesamiento en lote de worker (`process_worker_batch`).
- `GET /billing/documents/{sale_id}` mantiene visibilidad de estado `queued` incluso antes del drenado por worker (placeholder derivado de cola).
- `POST /billing/worker/process` ahora reporta `enqueued` + `processed/succeeded/failed` para observabilidad del desacople asincrónico.
- Se agregaron pruebas para validar desacople: documento en `queued` con `attempts=0` antes del worker y transición luego de ejecutar batch.


## Evidencia etapa 5
- Se agregó backoff por lotes (`retry_after_batches`) para errores transitorios, evitando reintentos agresivos en cada ciclo de worker.
- Se agregó marcación de dead-letter (`dead_lettered`) al agotar intentos máximos y contador global de documentos en dead-letter.
- El endpoint del worker ahora reporta `dead_lettered` además de `enqueued/processed/succeeded/failed`.
- Se añadieron pruebas unitarias y API para validar backoff, transición a dead-letter y observabilidad del contador.


## Evidencia etapa 6
- La consulta de documento ahora soporta `document_type` por query param para evitar ambigüedad entre boleta/factura de una misma venta.
- Se agregó endpoint de reconciliación `POST /billing/documents/{sale_id}/refresh-status` para actualizar estado observado en proveedor/SII.
- Se amplió la batería de pruebas API con casos de refresh progresivo y búsqueda por tipo documental.


## Evidencia etapa 7
- Se consolidó checklist de hardening y salida en `docs/paso7_hardening_checklist.md`.
- Se validó cobertura de confiabilidad: desacople POS, retries/backoff, dead-letter y reconciliación de estado.
- Se cerró formalmente el paso 7 como prototipo completo (7/7).
