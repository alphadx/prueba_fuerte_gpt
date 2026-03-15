# Migraciones SQL — Paso 4

Este directorio contiene la cadena inicial de migraciones para el MVP ERP.

## Versionado

- `0001_initial_schema.up.sql`: crea el esquema base de entidades MVP.
- `0001_initial_schema.down.sql`: revierte completamente la migración 0001.

## Entidades cubiertas

- Core: `companies`, `branches`, `users`, `roles`
- Inventario: `products`, `stock_items`, `stock_movements`
- Ventas: `sales`, `sale_lines`, `payments`, `cash_sessions`
- Fiscal: `tax_documents`, `tax_document_events`
- E-commerce: `online_orders`, `pickup_slots`
- RRHH: `employees`, `document_types`, `employee_documents`, `alarm_rules`, `alarm_events`

## Ejecución

```bash
make migrate-up
make migrate-status
make migrate-down VERSION=0001
make verify-step4
```

Variable opcional:

- `DATABASE_URL` (por defecto `postgresql://erp_user:erp_pass@127.0.0.1:5432/erp_barrio`)

## Diagrama ER (base)

```mermaid
erDiagram
    companies ||--o{ branches : has
    companies ||--o{ users : has
    roles ||--o{ users : assigned

    companies ||--o{ products : owns
    products ||--o{ stock_items : tracked
    branches ||--o{ stock_items : stored
    stock_items ||--o{ stock_movements : movement

    branches ||--o{ cash_sessions : opens
    users ||--o{ cash_sessions : operates
    branches ||--o{ sales : sells
    cash_sessions ||--o{ sales : contains
    users ||--o{ sales : registers
    sales ||--o{ sale_lines : has
    products ||--o{ sale_lines : references
    sales ||--o{ payments : settles

    sales ||--o{ tax_documents : fiscalized
    tax_documents ||--o{ tax_document_events : emits

    branches ||--o{ pickup_slots : defines
    branches ||--o{ online_orders : receives
    pickup_slots ||--o{ online_orders : selected

    companies ||--o{ employees : employs
    companies ||--o{ document_types : configures
    employees ||--o{ employee_documents : uploads
    document_types ||--o{ employee_documents : typed
    document_types ||--o{ alarm_rules : scoped
    companies ||--o{ alarm_rules : configures
    alarm_rules ||--o{ alarm_events : triggers
    employee_documents ||--o{ alarm_events : targets
```


## Validación rápida en este repositorio

- `make verify-step4` ejecuta chequeos estáticos de cobertura de entidades, JSONB, índices críticos y presencia de diagrama ER.


## Convención de documentación SQL

- La migración `0001` incluye `COMMENT ON TABLE` y `COMMENT ON COLUMN` para documentar entidades y campos clave del esquema.
- Esto mejora onboarding, mantenibilidad y trazabilidad del modelo de datos del MVP.
