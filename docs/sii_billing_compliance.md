# Referencia de cumplimiento SII para integración de boleta electrónica (sandbox/prototipo)

> Objetivo: dejar trazabilidad documental de reglas mínimas SII que deben reflejarse en el adaptador y en futuras integraciones reales.

## 1) Marco normativo y técnico base

- El SII centraliza la documentación de **facturación electrónica** y servicios asociados en su portal oficial de documentación técnica. Fuente: https://www.sii.cl/servicios_online/1039-.html
- La operación de DTE está regida por el estándar XML definido por SII y sus esquemas/validaciones técnicas publicadas para emisores. Fuente: https://www.sii.cl/factura_electronica/form_ele.htm
- La boleta electrónica y sus flujos de envío/consulta se enmarcan en los servicios de facturación electrónica publicados por SII. Fuente: https://www.sii.cl/factura_electronica/factura_mercado/factura_mercado.htm

## 2) Reglas que este prototipo debe respetar

1. **No bloquear caja/POS por integración externa**
   - Emisión fiscal desacoplada y asíncrona (cola/worker).
2. **Trazabilidad documental**
   - Guardar referencia al payload crudo y metadatos de seguimiento (`track_id` / correlativo proveedor).
3. **Estados de emisión explícitos**
   - Mantener estado interno de documento y estado observado en SII/proveedor.
4. **Idempotencia operativa**
   - Evitar doble emisión para el mismo documento lógico.
5. **Manejo de fallas transitorias**
   - Reintentos acotados con estado terminal de error para revisión manual.

## 3) Criterios de diseño aplicados en el adaptador sandbox

- El adaptador mantiene un modelo de estados controlado para simular: aceptación, procesamiento y rechazo.
- Se incorpora `raw_payload_ref` para permitir auditoría técnica posterior.
- Se incorporan modos de simulación de fallas y transición progresiva de estado para robustecer pruebas de reconciliación.

## 4) Limitaciones explícitas del prototipo

- Este módulo **no implementa firma electrónica real**, ni envío real a endpoints productivos/certificación SII.
- La semántica de estado es simplificada para pruebas internas; la integración real deberá mapear catálogos y códigos oficiales del flujo SII vigente.
