# Paso 7 — Hardening y checklist de cierre (boleta electrónica sandbox)

## Objetivo
Cerrar el paso 7 con criterios verificables de robustez mínima para operación de prototipo y trazabilidad hacia integración real con SII.

## Checklist de salida

### A. Arquitectura y desacople
- [x] Emisión fiscal desacoplada del flujo síncrono POS/caja.
- [x] Worker/batch de billing procesa cola de emisión fuera del cierre de venta.

### B. Confiabilidad e idempotencia
- [x] Idempotencia por `(sale_id, document_type)` en documentos y eventos.
- [x] Reintentos acotados con backoff por lotes (`retry_after_batches`).
- [x] Estado terminal de error (`failed`) + marca `dead_lettered`.

### C. Observabilidad funcional
- [x] Endpoint de consulta documental (`GET /billing/documents/{sale_id}`) con soporte `document_type`.
- [x] Endpoint de reconciliación explícita (`POST /billing/documents/{sale_id}/refresh-status`).
- [x] Endpoint de worker con métricas (`enqueued`, `processed`, `succeeded`, `failed`, `dead_lettered`).

### D. Cumplimiento documental y SII
- [x] Referencias y criterios SII documentados en `docs/sii_billing_compliance.md`.
- [x] Comentarios de trazabilidad SII incorporados en adaptador sandbox.

### E. Pruebas mínimas de cierre
- [x] Unit tests del adaptador sandbox.
- [x] Unit tests del servicio billing (cola, retries, dead-letter).
- [x] API tests de consulta, procesamiento y refresh de estado.

## Riesgos conocidos (prototipo)
1. Persistencia in-memory: no sobrevive reinicios de proceso.
2. No existe firma electrónica real ni integración directa a endpoints de certificación/producción SII.
3. Catálogos/códigos SII están simplificados a estados canónicos para pruebas.

## Decisión de cierre
- Estado del paso 7: **Aprobado para prototipo**.
- Siguiente objetivo recomendado: migrar cola/estado a backend durable (Redis/outbox DB) y preparar driver real de proveedor.
