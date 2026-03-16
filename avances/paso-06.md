# Paso 06 — Implementar POS y flujo de caja mínimo operable

## Diagnóstico de partida (análisis)
- Se considera el desarrollo previo como **borrador técnico inicial**, no como implementación cerrada.
- Para esta nueva ejecución, el paso 6 reinicia su medición con foco en trazabilidad, validación incremental y aceptación explícita por etapa.
- **Cumplimiento estimado base:** **0%**.

## Objetivo operativo del paso 6
Implementar un POS mínimo operable con flujo de caja confiable, asegurando que cada venta tenga impacto coherente en pagos, stock, kardex y arqueo de caja, con validaciones automatizadas para escenarios exitosos y de falla.

## Plan minucioso en 7 etapas

### Etapa 1 — Análisis detallado y criterios de aceptación
- Levantar reglas funcionales obligatorias del flujo POS/caja.
- Definir casos borde críticos (sesión cerrada, stock insuficiente, pago pendiente, etc.).
- Acordar métricas de aceptación por subflujo (venta, caja, inventario).
- **Salida de etapa:** documento de criterios + matriz de escenarios. ✅ Completada (ver `docs/paso6_etapa1_analisis.md`).

### Etapa 2 — Contratos API del flujo POS + caja
- Revisar y ajustar contratos de endpoints clave (`cash-sessions`, `sales`, `payments`).
- Estandarizar códigos de error y mensajes por regla de dominio.
- Definir payloads mínimos y campos obligatorios para trazabilidad.
- **Salida de etapa:** contrato API validado y versionado.

### Etapa 3 — Reglas de caja y arqueo mínimo operable
- Formalizar invariantes de apertura/cierre (una caja abierta por operador/sucursal, según regla acordada).
- Implementar cálculo determinístico de `expected_amount` y `difference_amount`.
- Asegurar cierre de caja con validaciones de estado y consistencia.
- **Salida de etapa:** flujo de caja verificable extremo a extremo.

### Etapa 4 — Confirmación de venta y estados de pago
- Definir secuencia transaccional de venta completa.
- Aplicar estados de pago determinísticos por medio de pago.
- Integrar validaciones de sesión de caja activa + sucursal coherente.
- **Salida de etapa:** venta confirmada con estados consistentes y auditables.

### Etapa 5 — Consistencia stock/kardex y rollback
- Garantizar descuento de stock por línea con trazabilidad de referencia de venta.
- Registrar movimiento kardex de salida por ítem vendido.
- Implementar rollback completo cuando falle cualquier paso crítico de confirmación.
- **Salida de etapa:** consistencia inventario-venta validada en happy/failure path.

### Etapa 6 — Pruebas automatizadas por etapas
- Construir/ajustar pruebas unitarias por regla crítica de dominio.
- Ejecutar pruebas de integración del flujo completo POS+caja+stock.
- Incorporar casos de error e idempotencia operativa.
- **Salida de etapa:** suite de pruebas estable con cobertura de escenarios críticos.

### Etapa 7 — Hardening y cierre del paso
- Reforzar auditoría en operaciones sensibles (apertura, cierre, confirmación de venta).
- Verificar observabilidad mínima (logs de eventos y fallos de negocio).
- Consolidar checklist de aceptación final del paso 6.
- **Salida de etapa:** reporte de cierre con evidencia técnica y estado final.

## Estado de avance del paso
- **Cumplimiento estimado:** **14%** (1/7 etapas cerradas)
- **Semáforo:** 🟡 Amarillo (en ejecución controlada)
- **Regla de ejecución:** se avanza etapa por etapa únicamente cuando el usuario dé la orden explícita.
- **Etapa actual:** lista para iniciar **Etapa 2 — Contratos API del flujo POS + caja**.
