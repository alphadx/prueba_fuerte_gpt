# Paso 10 — Implementar RRHH documental flexible y motor de alertas

## Estado de iteración
- **Iteración actual:** Etapa 3 de 7 — flujo de carga documental (`archivo + metadatos + fechas`) con separación de almacenamiento y cumplimiento.
- **Estado:** ✅ Completada.
- **Regla de control aplicada:** no se inicia etapa 4 sin autorización explícita del usuario.

## Checklist de indicadores
- [ ] **Índice de cobertura documental** (meta: 100% fixture).
- [ ] **Índice de precisión de alertas** (meta: >= 95%).
- [ ] **Índice de entrega de notificaciones pruebas** (meta: >= 95%).

## Diagnóstico técnico del estado actual (baseline)

### Capacidades existentes
1. **Tipos documentales (`document_types`)**
   - Existe CRUD básico en memoria para tipos de documento.
   - Campos actuales: `code`, `name`, `requires_expiry`, `is_active`.
2. **Documentos de empleado (`employee_documents`)**
   - Existe CRUD básico en memoria para documento por empleado.
   - Campos actuales: `employee_id`, `document_type_code`, `expires_on`, `status`.
3. **Worker de alertas**
   - Existe worker que consume una cola Redis (`BLPOP`) e imprime payload.

### Brechas detectadas para cumplir paso 10
1. **Flexibilidad documental insuficiente**
   - No existe `JSON Schema` por tipo documental.
   - No hay validación de metadatos dinámicos al crear/editar documentos.
2. **Modelo de cumplimiento incompleto**
   - Falta separar metadatos de cumplimiento de almacenamiento de archivo.
   - No hay versionado de reglas/esquemas para trazabilidad.
3. **Motor de alertas no implementado**
   - No existe evaluación diaria de umbrales 30/15/7/1.
   - No existe deduplicación por ventana de evaluación.
   - No hay `AlarmEvent` persistido ni trazabilidad de evaluaciones.
4. **Notificaciones no desacopladas**
   - No existe capa de notificación in-app/email con tolerancia a fallas por canal.

## Definición funcional de la etapa 1 (acordada)

### Objetivo funcional
Dejar una definición cerrada del problema y de los criterios medibles que gobernarán las etapas 2–7, minimizando ambigüedad de implementación.

### Alcance aprobado para la solución del paso 10
- Gestión de `DocumentType` flexible con `JSON Schema` versionado.
- Ingesta de documentos de empleado con metadatos validados y fechas relevantes.
- Evaluador diario de vencimientos con umbrales **30/15/7/1 días**.
- Generación de `AlarmEvent` auditable e idempotente por ventana.
- Notificación desacoplada por canal (in-app + email en pruebas).

### Fuera de alcance del paso 10
- OCR, extracción automática de datos desde archivos.
- Integraciones externas de firma digital avanzada.
- Políticas de ML para scoring de riesgo documental.

## Criterios de aceptación medibles (definidos en etapa 1)

1. **Cobertura documental (fixture): 100%**
   - Dado el dataset de prueba del paso,
   - cuando se consulta el estado documental por empleado y tipo requerido,
   - entonces todos los tipos obligatorios definidos para el fixture están presentes.

2. **Validación estructural de metadatos: 100% en escritura**
   - Dado un `DocumentType` con `JSON Schema` activo,
   - cuando se ingresa/actualiza un documento con metadatos inválidos,
   - entonces la API rechaza la operación con error validado y trazable.

3. **Precisión de alertas: >= 95%**
   - Dado un conjunto controlado de documentos con fechas objetivo,
   - cuando corre el evaluador diario,
   - entonces las alertas generadas corresponden a ventanas 30/15/7/1 esperadas con precisión mínima 95%.

4. **Idempotencia por ventana: 100%**
   - Dado que el job diario se ejecuta más de una vez para la misma fecha de proceso,
   - cuando se evalúan los mismos documentos,
   - entonces no se generan duplicados de `AlarmEvent` para la misma combinación `(documento, umbral, fecha_evaluación)`.

5. **Entrega de notificaciones en pruebas: >= 95%**
   - Dado un conjunto de `AlarmEvent` en entorno de pruebas,
   - cuando se despachan notificaciones por canal,
   - entonces al menos 95% quedan registradas como entregadas o aceptadas por el canal.

6. **Trazabilidad de auditoría: 100% de eventos críticos**
   - Dado cualquier alerta generada,
   - cuando se revisa su historial,
   - entonces se puede reconstruir regla aplicada, fecha de evaluación, resultado de deduplicación y estado por canal.


## Implementación realizada en etapa 2

### Contrato `DocumentType` flexible
- Se extendió `DocumentType` con `schema_version` y `metadata_schema`.
- Se agregó validación de estructura de schema al crear/actualizar tipos documentales.
- Se incorporó control de versionado para impedir decremento de `schema_version`.

### Validación de metadatos en escritura
- La creación/actualización de `EmployeeDocument` ahora valida `metadata` contra el `metadata_schema` activo del `document_type_code`.
- Se rechazan payloads inválidos con estado HTTP `422` y detalle trazable de campo.

### Pruebas añadidas
- Unitarias: validación de schema y validación de metadatos por tipo documental.
- API: CRUD actualizado para contratos nuevos y rechazo de metadatos inválidos.


## Implementación realizada en etapa 3

### Flujo documental con fechas de cumplimiento
- `EmployeeDocument` ahora registra explícitamente `issue_on` y `expires_on` como metadatos de cumplimiento.
- Se mantuvo la validación de `metadata` contra `DocumentType.metadata_schema` al crear/editar documentos.

### Separación almacenamiento vs cumplimiento
- Se creó un servicio dedicado `EmployeeDocumentFileStorageService` para persistir metadatos de archivo (`file_name`, `content_type`, `storage_uri`, `uploaded_at`) desacoplados del modelo de cumplimiento documental.
- Se agregaron endpoints para adjuntar y listar archivos de un documento:
  - `POST /employee-documents/{document_id}/files`
  - `GET /employee-documents/{document_id}/files`

### Pruebas añadidas
- Unitaria nueva para almacenamiento de archivos por documento.
- API actualizada para validar el flujo completo create document + upload file + list files.

## Riesgos técnicos y mitigaciones iniciales
- **Riesgo:** deriva de esquemas JSON no versionados.
  - **Mitigación:** versionado explícito por `DocumentType` y uso de schema activo.
- **Riesgo:** duplicidad por reintentos del scheduler.
  - **Mitigación:** clave idempotente `(employee_document_id, threshold_days, evaluation_date)`.
- **Riesgo:** caída de canal email bloquea cumplimiento.
  - **Mitigación:** crear `AlarmEvent` como operación principal y desacoplar envío por adaptadores.

## Avance de cumplimiento del paso
- **Cobertura documental:** 50% (carga documental implementada con separación de almacenamiento/cumplimiento).
- **Precisión de alertas:** 20% (datos de fechas listos para motor diario).
- **Entrega de notificaciones:** 5% (sin adaptadores activos).
- **Cumplimiento estimado total del paso 10:** **35%**.
- **Semáforo:** 🟡 Amarillo (avance sólido de dominio, faltan motor y canales).

## Próxima etapa propuesta (Etapa 4)
Implementar motor diario de evaluación de vencimientos (30/15/7/1 días) con reglas determinísticas e idempotencia por ventana.

---

**Solicitud de control:** etapa 3 finalizada. Indica “avanzar etapa 4” para continuar con la siguiente iteración.
