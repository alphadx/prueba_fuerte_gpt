# Plan de implementación (12 pasos) para un ERP de barrio en Chile con estado inicial válido de pruebas

## Decisión técnica tomada
Se implementará un **programa autocontenido** basado en **FastAPI + PostgreSQL + Redis + worker asíncrono + frontend Next.js**, ejecutado localmente con **Docker Compose** para asegurar reproducibilidad.  

Sí: **algunas tecnologías deben montarse como servicios** (PostgreSQL, Redis, worker y, opcionalmente, MailHog/MinIO para pruebas), por lo que **usaremos Docker** desde el inicio.

---

## 1) Definir alcance MVP y criterios de aceptación
- Alcance inicial: inventario, POS básico, pagos (efectivo + stub electrónico), boleta electrónica vía integrador sandbox, e-commerce con retiro en tienda, RRHH documental con alertas.
- Criterios de aceptación medibles:
  - emitir boleta de prueba sin error,
  - descontar stock por venta,
  - crear pedido web con retiro,
  - generar alerta de documento cercano a vencimiento.
- Entregable: documento `docs/mvp_scope.md` con historias de usuario y Definition of Done.

## 2) Crear arquitectura base y repositorio ejecutable
- Estructura mono-repo sugerida:
  - `apps/api` (FastAPI),
  - `apps/web` (Next.js),
  - `workers/alerts` (jobs),
  - `infra/` (Docker, seeds, observabilidad),
  - `tests/` (unitarios + integración + e2e API).
- Definir contrato OpenAPI como fuente de verdad.
- Entregable: esqueleto de proyecto con README y scripts `make up`, `make test`, `make seed`.

## 3) Levantar servicios de soporte con Docker Compose
- Servicios mínimos:
  - `postgres` (datos ERP),
  - `redis` (colas/cache),
  - `api` (FastAPI),
  - `worker` (colas/cron de alertas),
  - `web` (Next.js).
- Servicios opcionales de pruebas:
  - `mailhog` (captura de emails),
  - `minio` (adjuntos de documentos),
  - `jaeger` o stack simple de logs.
- Entregable: `docker-compose.yml` + `.env.example` con perfiles `core` y `full`.

## 4) Diseñar modelo de datos inicial y migraciones
- Crear entidades mínimas del MVP:
  - Core: `Company`, `Branch`, `User`, `Role`.
  - Inventario: `Product`, `StockItem`, `StockMovement`.
  - Ventas: `Sale`, `SaleLine`, `Payment`, `CashSession`.
  - Fiscal: `TaxDocument`, `TaxDocumentEvent`.
  - E-commerce: `OnlineOrder`, `PickupSlot`.
  - RRHH: `Employee`, `DocumentType`, `EmployeeDocument`, `AlarmRule`, `AlarmEvent`.
- Usar `JSONB` para `custom_data` y esquema dinámico de documentos.
- Entregable: migraciones versionadas y diagrama ER base.

## 5) Implementar API modular con autenticación y permisos
- Módulos API: `inventory`, `sales`, `billing`, `orders`, `hr_docs`, `alerts`.
- Seguridad:
  - JWT,
  - roles (`admin`, `cajero`, `bodega`, `rrhh`),
  - auditoría en operaciones críticas.
- Entregable: endpoints CRUD y flujos principales documentados en Swagger.

## 6) Implementar POS y flujo de caja mínimo operable
- **Estado actual asumido:** borrador inicial con **cumplimiento estimado 0%** para ejecución minuciosa por etapas.
- **Estrategia de ejecución:** dividir el paso 6 en **7 etapas secuenciales** con salida verificable por etapa:
  1. análisis funcional/técnico y criterios de aceptación medibles,
  2. contratos API POS+caja (requests/responses/errores),
  3. reglas de caja (apertura/cierre/arqueo) con invariantes,
  4. reglas de venta y pagos con estados determinísticos,
  5. consistencia stock/kardex + rollback e idempotencia operativa,
  6. pruebas automáticas por etapa (unitarias + integración happy/failure),
  7. hardening final (auditoría, observabilidad mínima y checklist de cierre).
- **Entregable de planificación:** `avances/paso-06.md` actualizado con análisis, plan de 7 etapas y protocolo de ejecución por orden del usuario.

## 7) Integrar boleta electrónica vía proveedor (sandbox)
- **Estado operativo:** este paso se ejecuta como **prototipo iterativo en 7 etapas**.
- **Regla de control:** al cierre de cada etapa, el equipo debe **solicitar orden de avance** antes de iniciar la siguiente.
- **Etapas del prototipo (paso 7):**
  1. análisis funcional/técnico y criterios de aceptación fiscal sandbox,
  2. contrato `BillingProvider` y modelo canónico de request/response,
  3. adaptador sandbox (folio, XML/PDF, track ID, estado SII),
  4. desacople de caja/POS con encolado asíncrono de emisión,
  5. resiliencia (reintentos acotados, idempotencia, estados terminales),
  6. consulta de estado/API + pruebas de integración por escenarios,
  7. hardening documental y checklist de cierre del paso.
- **Entregable por etapa:** evidencia en `avances/paso-07.md` + solicitud explícita al usuario para autorizar la siguiente iteración.

## 8) Integrar capa de pagos por adaptadores
- Interface `PaymentGateway` con drivers:
  - `cash` (local),
  - `transbank_stub`, `mercadopago_stub` para MVP,
  - webhook unificado de confirmación/rechazo.
- Mantener feature flags por sucursal/canal para activar medios de pago.
- Entregable: conciliación básica de pagos + test de webhook idempotente.

## 9) Construir e-commerce básico con retiro en tienda
- Frontend con:
  - catálogo y stock por sucursal,
  - carrito + checkout,
  - selección de `PickupSlot`.
- Backend de estados de pedido:
  - `recibido -> preparado -> listo para retiro -> entregado`.
- Integrar Bing Maps solo en vista pública de tienda.
- Entregable: flujo e2e de compra web con retiro.

## 10) Implementar RRHH documental flexible y motor de alertas
- Configurar `DocumentType` con campos dinámicos (JSON schema).
- Crear carga de documentos (archivo + metadatos + fechas).
- Job diario en worker:
  - evalúa umbrales (30/15/7/1 días),
  - genera `AlarmEvent`,
  - notifica (in-app + email en entorno de pruebas).
- Entregable: alerta generada y visible para documento de prueba próximo a vencer.

## 11) Crear estado inicial válido de pruebas (seed + fixtures + smoke tests)
- Datos semilla mínimos:
  - 1 empresa, 1 sucursal,
  - usuarios por rol,
  - 20 productos con stock,
  - 2 empleados con documentos (1 próximo a vencer),
  - reglas de alerta por defecto.
- Fixtures para escenarios críticos:
  - venta efectivo,
  - venta electrónica,
  - pedido web retiro en tienda,
  - emisión de boleta sandbox,
  - webhook pago.
- Entregable: comando único `make bootstrap-test-state` que deja el sistema listo para QA en menos de 10 minutos.

## 12) Validación final, observabilidad y checklist de salida
- Ejecutar pipeline local:
  - lint/format,
  - tests unitarios,
  - integración API,
  - smoke e2e.
- Métricas mínimas de salud:
  - latencia API,
  - cola de trabajos,
  - tasa de error de boletas/pagos.
- Definir checklist de go-live MVP y riesgos conocidos.
- Entregable: `docs/release_checklist.md` + reporte de ejecución del pipeline.

---

## ¿Qué va como servicio en Docker y qué no?
- **Sí, en Docker (servicio):** PostgreSQL, Redis, API, worker, frontend, MailHog/MinIO opcionales.
- **No necesariamente como servicio externo:** lógica de negocio, validaciones de dominio, adaptadores (se ejecutan dentro de API/worker).

## Resultado esperado de este plan
Al terminar los 12 pasos, el equipo tendrá un entorno reproducible, un MVP operativo y un **estado inicial de pruebas válido** para QA funcional/técnica, con integraciones críticas simuladas o sandbox y posibilidad de evolucionar a producción por fases.
