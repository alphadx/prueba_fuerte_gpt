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
- **Etapa en ejecución:** **Etapa 3 de 7 (completada)**.
- **Cumplimiento estimado del paso 7:** **43%** (3/7 completadas: análisis + contrato + adaptador sandbox reforzado).
- **Semáforo:** 🟡 Amarillo (En progreso controlado por etapas).
- **Observación:** Se asume enfoque iterativo; no se considera cierre definitivo del paso hasta completar 7/7 con aprobación explícita por etapa.

## Checklist de control por etapa
- [x] Etapa 1 — análisis y criterios iniciales.
- [x] Etapa 2 — contrato proveedor.
- [x] Etapa 3 — adaptador sandbox.
- [ ] Etapa 4 — desacople asíncrono POS.
- [ ] Etapa 5 — resiliencia/reintentos/idempotencia.
- [ ] Etapa 6 — consulta de estado + pruebas.
- [ ] Etapa 7 — hardening documental.

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
