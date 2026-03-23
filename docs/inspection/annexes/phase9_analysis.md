# Technical Annex — Phase 9 Evaluation

## Scope used for this review
Phase 9 in `docs/mvp_scope.md` requires a **basic e-commerce flow with store pickup** and three indicators:

1. checkout success rate for pickup orders,
2. stock consistency between web and store,
3. valid order-state transitions.

The user story also requires that checkout creates an order in `received` state and associates the pickup branch.

## Evidence reviewed
- `docs/mvp_scope.md`
- `infra/migrations/0001_initial_schema.up.sql`
- `infra/migrations/README.md`
- `apps/web/README.md`
- `apps/api/app/modules/`
- `tests/test_migration_assets.py`

## Checks executed
1. `pytest -q tests/test_migration_assets.py`
   - Result: `3 passed`.
2. Repository inspection for e-commerce implementation
   - Result: `online_orders` and `pickup_slots` exist in schema assets, but no backend application modules or frontend checkout implementation were found.

## Findings
1. **Schema groundwork exists**
   - The migration includes `pickup_slots` and `online_orders`.
   - The data model already anticipates pickup branch linkage and order status transitions.

2. **Frontend implementation is not present**
   - `apps/web` currently contains only a README.
   - The README explicitly states that catalog and checkout with store pickup are pending future steps.

3. **Backend implementation is not present**
   - No `online_orders` or `pickup_slots` application modules exist under `apps/api/app/modules`.
   - No OpenAPI contract or API tests were found for order creation, pickup selection, or order-status progression.

4. **QA evidence for Phase 9 is absent**
   - No end-to-end checkout evidence exists.
   - No cross-channel stock checks were identified.
   - No tests were found for order-state transitions such as `received -> prepared -> ready_for_pickup`.

## Positive patterns
- The schema includes key e-commerce entities early.
- Order status values are modeled at database level.
- The frontend README keeps intended scope visible.

## Gaps / anti-patterns
- No executable web checkout flow.
- No backend slice for e-commerce/pickup operations.
- No e2e or API QA evidence.
- No stock synchronization evidence between channels.

## Recommended actions
1. Initialize the Next.js frontend and implement catalog + pickup checkout UI.
2. Add backend modules for `online_orders` and `pickup_slots`.
3. Expose API endpoints for order creation and order-status management.
4. Add QA coverage for store-pickup checkout and valid order transitions.
5. Add cross-channel stock consistency checks before closing Phase 9.

## Score rationale (24%)
- **+** E-commerce entities are already present in schema design.
- **+** Planned scope is visible in documentation.
- **-** No application implementation exists yet in frontend or backend.
- **-** No QA evidence exists for checkout, stock consistency, or status transitions.
