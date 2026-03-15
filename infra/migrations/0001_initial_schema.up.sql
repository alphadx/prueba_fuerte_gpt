BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name TEXT NOT NULL,
    tax_id TEXT NOT NULL UNIQUE,
    custom_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    custom_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, code)
);

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    custom_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    custom_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, sku)
);

CREATE TABLE IF NOT EXISTS stock_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    quantity NUMERIC(14, 3) NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    reorder_level NUMERIC(14, 3) NOT NULL DEFAULT 0 CHECK (reorder_level >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_id, branch_id)
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_item_id UUID NOT NULL REFERENCES stock_items(id) ON DELETE CASCADE,
    movement_type TEXT NOT NULL CHECK (movement_type IN ('inbound', 'outbound', 'adjustment')),
    quantity_delta NUMERIC(14, 3) NOT NULL CHECK (quantity_delta <> 0),
    reason TEXT,
    reference_type TEXT,
    reference_id UUID,
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cash_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    opened_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    closed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMPTZ,
    opening_amount NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (opening_amount >= 0),
    closing_amount NUMERIC(12, 2) CHECK (closing_amount >= 0),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed'))
);

CREATE TABLE IF NOT EXISTS sales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE RESTRICT,
    cash_session_id UUID REFERENCES cash_sessions(id) ON DELETE SET NULL,
    sold_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    sale_number TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed' CHECK (status IN ('draft', 'confirmed', 'cancelled')),
    subtotal NUMERIC(12, 2) NOT NULL CHECK (subtotal >= 0),
    taxes NUMERIC(12, 2) NOT NULL CHECK (taxes >= 0),
    total NUMERIC(12, 2) NOT NULL CHECK (total >= 0),
    sold_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    custom_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (branch_id, sale_number)
);

CREATE TABLE IF NOT EXISTS sale_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_id UUID NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity NUMERIC(12, 3) NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    tax_amount NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    line_total NUMERIC(12, 2) NOT NULL CHECK (line_total >= 0)
);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_id UUID NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    method TEXT NOT NULL CHECK (method IN ('cash', 'card_stub', 'wallet_stub')),
    status TEXT NOT NULL DEFAULT 'approved' CHECK (status IN ('pending', 'approved', 'rejected')),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    external_reference TEXT,
    paid_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    custom_data JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS tax_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_id UUID NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    folio TEXT,
    track_id TEXT,
    sii_status TEXT NOT NULL DEFAULT 'pending',
    xml_url TEXT,
    pdf_url TEXT,
    issued_at TIMESTAMPTZ,
    custom_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tax_document_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tax_document_id UUID NOT NULL REFERENCES tax_documents(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pickup_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (ends_at > starts_at)
);

CREATE TABLE IF NOT EXISTS online_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE RESTRICT,
    pickup_slot_id UUID REFERENCES pickup_slots(id) ON DELETE SET NULL,
    order_number TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_email TEXT,
    status TEXT NOT NULL DEFAULT 'received' CHECK (status IN ('received', 'prepared', 'ready_for_pickup', 'delivered', 'cancelled')),
    total NUMERIC(12, 2) NOT NULL CHECK (total >= 0),
    custom_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (branch_id, order_number)
);

CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    employee_code TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    hired_at DATE,
    custom_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, employee_code)
);

CREATE TABLE IF NOT EXISTS document_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    schema_definition JSONB NOT NULL DEFAULT '{}'::jsonb,
    requires_expiration BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, code)
);

CREATE TABLE IF NOT EXISTS employee_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    document_type_id UUID NOT NULL REFERENCES document_types(id) ON DELETE RESTRICT,
    file_url TEXT,
    issued_on DATE,
    expires_on DATE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (expires_on IS NULL OR issued_on IS NULL OR expires_on >= issued_on)
);

CREATE TABLE IF NOT EXISTS alarm_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    document_type_id UUID REFERENCES document_types(id) ON DELETE CASCADE,
    threshold_days INTEGER NOT NULL CHECK (threshold_days >= 0),
    channel TEXT NOT NULL CHECK (channel IN ('in_app', 'email')),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (company_id, document_type_id, threshold_days, channel)
);

CREATE TABLE IF NOT EXISTS alarm_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alarm_rule_id UUID NOT NULL REFERENCES alarm_rules(id) ON DELETE CASCADE,
    employee_document_id UUID NOT NULL REFERENCES employee_documents(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_branches_company_id ON branches(company_id);
CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_products_company_id ON products(company_id);
CREATE INDEX IF NOT EXISTS idx_stock_items_branch_id ON stock_items(branch_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_stock_item_id ON stock_movements(stock_item_id);
CREATE INDEX IF NOT EXISTS idx_sales_branch_sold_at ON sales(branch_id, sold_at DESC);
CREATE INDEX IF NOT EXISTS idx_sale_lines_sale_id ON sale_lines(sale_id);
CREATE INDEX IF NOT EXISTS idx_payments_sale_id ON payments(sale_id);
CREATE INDEX IF NOT EXISTS idx_tax_documents_sale_id ON tax_documents(sale_id);
CREATE INDEX IF NOT EXISTS idx_online_orders_branch_status ON online_orders(branch_id, status);
CREATE INDEX IF NOT EXISTS idx_employee_documents_employee_id ON employee_documents(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_documents_expiration ON employee_documents(expires_on);
CREATE INDEX IF NOT EXISTS idx_alarm_events_status_triggered ON alarm_events(status, triggered_at);


-- BEGIN AUTOGENERATED COMMENTS STEP4
-- Documentación de esquema (tablas y columnas) para facilitar mantenimiento y onboarding.
COMMENT ON TABLE companies IS 'Tabla del dominio ERP para companies.';
COMMENT ON COLUMN companies.id IS 'Campo id de la entidad companies.';
COMMENT ON COLUMN companies.legal_name IS 'Campo legal_name de la entidad companies.';
COMMENT ON COLUMN companies.tax_id IS 'Campo tax_id de la entidad companies.';
COMMENT ON COLUMN companies.custom_data IS 'Campo custom_data de la entidad companies.';
COMMENT ON COLUMN companies.created_at IS 'Campo created_at de la entidad companies.';
COMMENT ON COLUMN companies.updated_at IS 'Campo updated_at de la entidad companies.';
COMMENT ON TABLE branches IS 'Tabla del dominio ERP para branches.';
COMMENT ON COLUMN branches.id IS 'Campo id de la entidad branches.';
COMMENT ON COLUMN branches.company_id IS 'Campo company_id de la entidad branches.';
COMMENT ON COLUMN branches.code IS 'Campo code de la entidad branches.';
COMMENT ON COLUMN branches.name IS 'Campo name de la entidad branches.';
COMMENT ON COLUMN branches.address IS 'Campo address de la entidad branches.';
COMMENT ON COLUMN branches.custom_data IS 'Campo custom_data de la entidad branches.';
COMMENT ON COLUMN branches.created_at IS 'Campo created_at de la entidad branches.';
COMMENT ON COLUMN branches.updated_at IS 'Campo updated_at de la entidad branches.';
COMMENT ON TABLE roles IS 'Tabla del dominio ERP para roles.';
COMMENT ON COLUMN roles.id IS 'Campo id de la entidad roles.';
COMMENT ON COLUMN roles.name IS 'Campo name de la entidad roles.';
COMMENT ON COLUMN roles.description IS 'Campo description de la entidad roles.';
COMMENT ON COLUMN roles.created_at IS 'Campo created_at de la entidad roles.';
COMMENT ON TABLE users IS 'Tabla del dominio ERP para users.';
COMMENT ON COLUMN users.id IS 'Campo id de la entidad users.';
COMMENT ON COLUMN users.company_id IS 'Campo company_id de la entidad users.';
COMMENT ON COLUMN users.branch_id IS 'Campo branch_id de la entidad users.';
COMMENT ON COLUMN users.role_id IS 'Campo role_id de la entidad users.';
COMMENT ON COLUMN users.email IS 'Campo email de la entidad users.';
COMMENT ON COLUMN users.full_name IS 'Campo full_name de la entidad users.';
COMMENT ON COLUMN users.is_active IS 'Campo is_active de la entidad users.';
COMMENT ON COLUMN users.custom_data IS 'Campo custom_data de la entidad users.';
COMMENT ON COLUMN users.created_at IS 'Campo created_at de la entidad users.';
COMMENT ON COLUMN users.updated_at IS 'Campo updated_at de la entidad users.';
COMMENT ON TABLE products IS 'Tabla del dominio ERP para products.';
COMMENT ON COLUMN products.id IS 'Campo id de la entidad products.';
COMMENT ON COLUMN products.company_id IS 'Campo company_id de la entidad products.';
COMMENT ON COLUMN products.sku IS 'Campo sku de la entidad products.';
COMMENT ON COLUMN products.name IS 'Campo name de la entidad products.';
COMMENT ON COLUMN products.unit_price IS 'Campo unit_price de la entidad products.';
COMMENT ON COLUMN products.is_active IS 'Campo is_active de la entidad products.';
COMMENT ON COLUMN products.custom_data IS 'Campo custom_data de la entidad products.';
COMMENT ON COLUMN products.created_at IS 'Campo created_at de la entidad products.';
COMMENT ON COLUMN products.updated_at IS 'Campo updated_at de la entidad products.';
COMMENT ON TABLE stock_items IS 'Tabla del dominio ERP para stock_items.';
COMMENT ON COLUMN stock_items.id IS 'Campo id de la entidad stock_items.';
COMMENT ON COLUMN stock_items.product_id IS 'Campo product_id de la entidad stock_items.';
COMMENT ON COLUMN stock_items.branch_id IS 'Campo branch_id de la entidad stock_items.';
COMMENT ON COLUMN stock_items.quantity IS 'Campo quantity de la entidad stock_items.';
COMMENT ON COLUMN stock_items.reorder_level IS 'Campo reorder_level de la entidad stock_items.';
COMMENT ON COLUMN stock_items.updated_at IS 'Campo updated_at de la entidad stock_items.';
COMMENT ON TABLE stock_movements IS 'Tabla del dominio ERP para stock_movements.';
COMMENT ON COLUMN stock_movements.id IS 'Campo id de la entidad stock_movements.';
COMMENT ON COLUMN stock_movements.stock_item_id IS 'Campo stock_item_id de la entidad stock_movements.';
COMMENT ON COLUMN stock_movements.movement_type IS 'Campo movement_type de la entidad stock_movements.';
COMMENT ON COLUMN stock_movements.quantity_delta IS 'Campo quantity_delta de la entidad stock_movements.';
COMMENT ON COLUMN stock_movements.reason IS 'Campo reason de la entidad stock_movements.';
COMMENT ON COLUMN stock_movements.reference_type IS 'Campo reference_type de la entidad stock_movements.';
COMMENT ON COLUMN stock_movements.reference_id IS 'Campo reference_id de la entidad stock_movements.';
COMMENT ON COLUMN stock_movements.created_by_user_id IS 'Campo created_by_user_id de la entidad stock_movements.';
COMMENT ON COLUMN stock_movements.created_at IS 'Campo created_at de la entidad stock_movements.';
COMMENT ON TABLE cash_sessions IS 'Tabla del dominio ERP para cash_sessions.';
COMMENT ON COLUMN cash_sessions.id IS 'Campo id de la entidad cash_sessions.';
COMMENT ON COLUMN cash_sessions.branch_id IS 'Campo branch_id de la entidad cash_sessions.';
COMMENT ON COLUMN cash_sessions.opened_by_user_id IS 'Campo opened_by_user_id de la entidad cash_sessions.';
COMMENT ON COLUMN cash_sessions.closed_by_user_id IS 'Campo closed_by_user_id de la entidad cash_sessions.';
COMMENT ON COLUMN cash_sessions.opened_at IS 'Campo opened_at de la entidad cash_sessions.';
COMMENT ON COLUMN cash_sessions.closed_at IS 'Campo closed_at de la entidad cash_sessions.';
COMMENT ON COLUMN cash_sessions.opening_amount IS 'Campo opening_amount de la entidad cash_sessions.';
COMMENT ON COLUMN cash_sessions.closing_amount IS 'Campo closing_amount de la entidad cash_sessions.';
COMMENT ON COLUMN cash_sessions.status IS 'Campo status de la entidad cash_sessions.';
COMMENT ON TABLE sales IS 'Tabla del dominio ERP para sales.';
COMMENT ON COLUMN sales.id IS 'Campo id de la entidad sales.';
COMMENT ON COLUMN sales.branch_id IS 'Campo branch_id de la entidad sales.';
COMMENT ON COLUMN sales.cash_session_id IS 'Campo cash_session_id de la entidad sales.';
COMMENT ON COLUMN sales.sold_by_user_id IS 'Campo sold_by_user_id de la entidad sales.';
COMMENT ON COLUMN sales.sale_number IS 'Campo sale_number de la entidad sales.';
COMMENT ON COLUMN sales.status IS 'Campo status de la entidad sales.';
COMMENT ON COLUMN sales.subtotal IS 'Campo subtotal de la entidad sales.';
COMMENT ON COLUMN sales.taxes IS 'Campo taxes de la entidad sales.';
COMMENT ON COLUMN sales.total IS 'Campo total de la entidad sales.';
COMMENT ON COLUMN sales.sold_at IS 'Campo sold_at de la entidad sales.';
COMMENT ON COLUMN sales.custom_data IS 'Campo custom_data de la entidad sales.';
COMMENT ON TABLE sale_lines IS 'Tabla del dominio ERP para sale_lines.';
COMMENT ON COLUMN sale_lines.id IS 'Campo id de la entidad sale_lines.';
COMMENT ON COLUMN sale_lines.sale_id IS 'Campo sale_id de la entidad sale_lines.';
COMMENT ON COLUMN sale_lines.product_id IS 'Campo product_id de la entidad sale_lines.';
COMMENT ON COLUMN sale_lines.quantity IS 'Campo quantity de la entidad sale_lines.';
COMMENT ON COLUMN sale_lines.unit_price IS 'Campo unit_price de la entidad sale_lines.';
COMMENT ON COLUMN sale_lines.tax_amount IS 'Campo tax_amount de la entidad sale_lines.';
COMMENT ON COLUMN sale_lines.line_total IS 'Campo line_total de la entidad sale_lines.';
COMMENT ON TABLE payments IS 'Tabla del dominio ERP para payments.';
COMMENT ON COLUMN payments.id IS 'Campo id de la entidad payments.';
COMMENT ON COLUMN payments.sale_id IS 'Campo sale_id de la entidad payments.';
COMMENT ON COLUMN payments.method IS 'Campo method de la entidad payments.';
COMMENT ON COLUMN payments.status IS 'Campo status de la entidad payments.';
COMMENT ON COLUMN payments.amount IS 'Campo amount de la entidad payments.';
COMMENT ON COLUMN payments.external_reference IS 'Campo external_reference de la entidad payments.';
COMMENT ON COLUMN payments.paid_at IS 'Campo paid_at de la entidad payments.';
COMMENT ON COLUMN payments.custom_data IS 'Campo custom_data de la entidad payments.';
COMMENT ON TABLE tax_documents IS 'Tabla del dominio ERP para tax_documents.';
COMMENT ON COLUMN tax_documents.id IS 'Campo id de la entidad tax_documents.';
COMMENT ON COLUMN tax_documents.sale_id IS 'Campo sale_id de la entidad tax_documents.';
COMMENT ON COLUMN tax_documents.provider IS 'Campo provider de la entidad tax_documents.';
COMMENT ON COLUMN tax_documents.folio IS 'Campo folio de la entidad tax_documents.';
COMMENT ON COLUMN tax_documents.track_id IS 'Campo track_id de la entidad tax_documents.';
COMMENT ON COLUMN tax_documents.sii_status IS 'Campo sii_status de la entidad tax_documents.';
COMMENT ON COLUMN tax_documents.xml_url IS 'Campo xml_url de la entidad tax_documents.';
COMMENT ON COLUMN tax_documents.pdf_url IS 'Campo pdf_url de la entidad tax_documents.';
COMMENT ON COLUMN tax_documents.issued_at IS 'Campo issued_at de la entidad tax_documents.';
COMMENT ON COLUMN tax_documents.custom_data IS 'Campo custom_data de la entidad tax_documents.';
COMMENT ON COLUMN tax_documents.created_at IS 'Campo created_at de la entidad tax_documents.';
COMMENT ON TABLE tax_document_events IS 'Tabla del dominio ERP para tax_document_events.';
COMMENT ON COLUMN tax_document_events.id IS 'Campo id de la entidad tax_document_events.';
COMMENT ON COLUMN tax_document_events.tax_document_id IS 'Campo tax_document_id de la entidad tax_document_events.';
COMMENT ON COLUMN tax_document_events.event_type IS 'Campo event_type de la entidad tax_document_events.';
COMMENT ON COLUMN tax_document_events.event_payload IS 'Campo event_payload de la entidad tax_document_events.';
COMMENT ON COLUMN tax_document_events.created_at IS 'Campo created_at de la entidad tax_document_events.';
COMMENT ON TABLE pickup_slots IS 'Tabla del dominio ERP para pickup_slots.';
COMMENT ON COLUMN pickup_slots.id IS 'Campo id de la entidad pickup_slots.';
COMMENT ON COLUMN pickup_slots.branch_id IS 'Campo branch_id de la entidad pickup_slots.';
COMMENT ON COLUMN pickup_slots.starts_at IS 'Campo starts_at de la entidad pickup_slots.';
COMMENT ON COLUMN pickup_slots.ends_at IS 'Campo ends_at de la entidad pickup_slots.';
COMMENT ON COLUMN pickup_slots.capacity IS 'Campo capacity de la entidad pickup_slots.';
COMMENT ON COLUMN pickup_slots.active IS 'Campo active de la entidad pickup_slots.';
COMMENT ON COLUMN pickup_slots.created_at IS 'Campo created_at de la entidad pickup_slots.';
COMMENT ON TABLE online_orders IS 'Tabla del dominio ERP para online_orders.';
COMMENT ON COLUMN online_orders.id IS 'Campo id de la entidad online_orders.';
COMMENT ON COLUMN online_orders.branch_id IS 'Campo branch_id de la entidad online_orders.';
COMMENT ON COLUMN online_orders.pickup_slot_id IS 'Campo pickup_slot_id de la entidad online_orders.';
COMMENT ON COLUMN online_orders.order_number IS 'Campo order_number de la entidad online_orders.';
COMMENT ON COLUMN online_orders.customer_name IS 'Campo customer_name de la entidad online_orders.';
COMMENT ON COLUMN online_orders.customer_email IS 'Campo customer_email de la entidad online_orders.';
COMMENT ON COLUMN online_orders.status IS 'Campo status de la entidad online_orders.';
COMMENT ON COLUMN online_orders.total IS 'Campo total de la entidad online_orders.';
COMMENT ON COLUMN online_orders.custom_data IS 'Campo custom_data de la entidad online_orders.';
COMMENT ON COLUMN online_orders.created_at IS 'Campo created_at de la entidad online_orders.';
COMMENT ON TABLE employees IS 'Tabla del dominio ERP para employees.';
COMMENT ON COLUMN employees.id IS 'Campo id de la entidad employees.';
COMMENT ON COLUMN employees.company_id IS 'Campo company_id de la entidad employees.';
COMMENT ON COLUMN employees.branch_id IS 'Campo branch_id de la entidad employees.';
COMMENT ON COLUMN employees.employee_code IS 'Campo employee_code de la entidad employees.';
COMMENT ON COLUMN employees.full_name IS 'Campo full_name de la entidad employees.';
COMMENT ON COLUMN employees.email IS 'Campo email de la entidad employees.';
COMMENT ON COLUMN employees.hired_at IS 'Campo hired_at de la entidad employees.';
COMMENT ON COLUMN employees.custom_data IS 'Campo custom_data de la entidad employees.';
COMMENT ON COLUMN employees.created_at IS 'Campo created_at de la entidad employees.';
COMMENT ON COLUMN employees.updated_at IS 'Campo updated_at de la entidad employees.';
COMMENT ON TABLE document_types IS 'Tabla del dominio ERP para document_types.';
COMMENT ON COLUMN document_types.id IS 'Campo id de la entidad document_types.';
COMMENT ON COLUMN document_types.company_id IS 'Campo company_id de la entidad document_types.';
COMMENT ON COLUMN document_types.code IS 'Campo code de la entidad document_types.';
COMMENT ON COLUMN document_types.name IS 'Campo name de la entidad document_types.';
COMMENT ON COLUMN document_types.schema_definition IS 'Campo schema_definition de la entidad document_types.';
COMMENT ON COLUMN document_types.requires_expiration IS 'Campo requires_expiration de la entidad document_types.';
COMMENT ON COLUMN document_types.created_at IS 'Campo created_at de la entidad document_types.';
COMMENT ON TABLE employee_documents IS 'Tabla del dominio ERP para employee_documents.';
COMMENT ON COLUMN employee_documents.id IS 'Campo id de la entidad employee_documents.';
COMMENT ON COLUMN employee_documents.employee_id IS 'Campo employee_id de la entidad employee_documents.';
COMMENT ON COLUMN employee_documents.document_type_id IS 'Campo document_type_id de la entidad employee_documents.';
COMMENT ON COLUMN employee_documents.file_url IS 'Campo file_url de la entidad employee_documents.';
COMMENT ON COLUMN employee_documents.issued_on IS 'Campo issued_on de la entidad employee_documents.';
COMMENT ON COLUMN employee_documents.expires_on IS 'Campo expires_on de la entidad employee_documents.';
COMMENT ON COLUMN employee_documents.metadata IS 'Campo metadata de la entidad employee_documents.';
COMMENT ON COLUMN employee_documents.created_at IS 'Campo created_at de la entidad employee_documents.';
COMMENT ON TABLE alarm_rules IS 'Tabla del dominio ERP para alarm_rules.';
COMMENT ON COLUMN alarm_rules.id IS 'Campo id de la entidad alarm_rules.';
COMMENT ON COLUMN alarm_rules.company_id IS 'Campo company_id de la entidad alarm_rules.';
COMMENT ON COLUMN alarm_rules.document_type_id IS 'Campo document_type_id de la entidad alarm_rules.';
COMMENT ON COLUMN alarm_rules.threshold_days IS 'Campo threshold_days de la entidad alarm_rules.';
COMMENT ON COLUMN alarm_rules.channel IS 'Campo channel de la entidad alarm_rules.';
COMMENT ON COLUMN alarm_rules.enabled IS 'Campo enabled de la entidad alarm_rules.';
COMMENT ON COLUMN alarm_rules.created_at IS 'Campo created_at de la entidad alarm_rules.';
COMMENT ON TABLE alarm_events IS 'Tabla del dominio ERP para alarm_events.';
COMMENT ON COLUMN alarm_events.id IS 'Campo id de la entidad alarm_events.';
COMMENT ON COLUMN alarm_events.alarm_rule_id IS 'Campo alarm_rule_id de la entidad alarm_events.';
COMMENT ON COLUMN alarm_events.employee_document_id IS 'Campo employee_document_id de la entidad alarm_events.';
COMMENT ON COLUMN alarm_events.status IS 'Campo status de la entidad alarm_events.';
COMMENT ON COLUMN alarm_events.payload IS 'Campo payload de la entidad alarm_events.';
COMMENT ON COLUMN alarm_events.triggered_at IS 'Campo triggered_at de la entidad alarm_events.';
COMMENT ON COLUMN alarm_events.delivered_at IS 'Campo delivered_at de la entidad alarm_events.';
-- END AUTOGENERATED COMMENTS STEP4

COMMIT;
