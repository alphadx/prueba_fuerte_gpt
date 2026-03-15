# Revisión final de infraestructura y arquitectura (pasos 9-12)

Fecha: 2026-03-14

## Objetivo
Asegurar, antes de seguir implementando, que la arquitectura base soporte:
- notificaciones por correo con soporte IMAP,
- interfaz gráfica usable en web y móviles,
- validación de transacciones entre pares mediante QR,
- cierre ordenado de pasos 9-12 del plan.

## Resultado ejecutivo
- **Infraestructura:** apta con ajustes mínimos (se agrega sandbox SMTP+IMAP en `compose full`).
- **Canal UI:** apto para evolución a responsive/PWA desde `apps/web`.
- **Flujos QR P2P:** definido como requerimiento de arquitectura para el paso 9.
- **Riesgo principal:** faltan componentes funcionales (dominio, estados y pruebas e2e), no de plataforma.

## Decisiones de arquitectura (congeladas para continuar)

1. **Correo con IMAP para pruebas y trazabilidad**
   - Se mantiene `mailhog` para inspección SMTP simple.
   - Se agrega `greenmail` en perfil `full` para pruebas reales SMTP + IMAP.
   - Uso recomendado:
     - API/worker envía notificaciones por SMTP a GreenMail.
     - Tests de integración verifican recepción y lectura vía IMAP.

2. **Interfaz gráfica web + móvil**
   - Se mantiene `apps/web` como canal único Next.js para desktop y móvil.
   - Patrón recomendado: diseño responsive mobile-first + PWA (sin app nativa en MVP).
   - Paso 9 debe incluir pruebas e2e en viewport móvil y desktop.

3. **QR para transacciones entre pares (P2P)**
   - El QR debe transportar un token firmado de transacción (id, monto, expiración, nonce).
   - Validación backend obligatoria (firma, expiración e idempotencia).
   - Confirmación por webhook/evento con persistencia auditable.

4. **Checklist de cierre pasos 9-12**
   - Paso 9: catálogo/checkout/retiro + flujo QR P2P.
   - Paso 10: RRHH documental + alertas por worker + canal email verificable por IMAP.
   - Paso 11: bootstrap QA reproducible con fixtures QR/pagos/alertas.
   - Paso 12: observabilidad y gates de release con SLO mínimos.

## Contratos técnicos mínimos a respetar
- OpenAPI primero para endpoints de QR y notificaciones.
- Máquina de estados explícita para órdenes y transacciones QR.
- Idempotencia en confirmaciones de pago/QR.
- Trazabilidad completa: request, evento emitido, estado final.

## Riesgos abiertos y mitigaciones
- **Riesgo:** sobrecarga de alcance MVP por QR + e-commerce + RRHH.
  - **Mitigación:** entregar QR P2P en versión mínima (emitir/validar/confirmar).
- **Riesgo:** brecha de calidad móvil.
  - **Mitigación:** criterio de aceptación con pruebas responsive por breakpoint.
- **Riesgo:** notificaciones no verificables extremo a extremo.
  - **Mitigación:** GreenMail + pruebas IMAP automatizadas desde paso 10.

## Señal de “todo en orden” para seguir
Se considera ordenado para continuar cuando se cumplan estos 4 puntos:
1. Perfil `full` disponible con servicios de correo de prueba SMTP+IMAP.
2. Documento de arquitectura contempla UX responsive y QR P2P.
3. Pasos 9-12 alineados con criterios medibles para esos requerimientos.
4. Existe comando/documento de revisión para recordar estas decisiones en cada sesión.
