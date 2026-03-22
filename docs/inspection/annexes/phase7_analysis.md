# Technical Annex — Phase 7 Evaluation

## Scope used for this review
Phase 7 in `docs/mvp_scope.md` requires **electronic receipt issuance through a sandbox provider** with three indicators:

1. successful sandbox issuance rate,
2. issuance latency,
3. retry resilience for transient failures.

It also defines a concrete user story where a paid sale should generate a tax-document record with an external identifier and a queryable initial status.

## Evidence reviewed
- `docs/mvp_scope.md`
- `infra/migrations/0001_initial_schema.up.sql`
- `infra/migrations/README.md`
- `tests/test_migration_assets.py`
- `apps/api/openapi.yaml`
- `apps/api/app/modules/`

## Checks executed
1. `pytest -q tests/test_migration_assets.py`
   - Result: `3 passed`.
2. Repository search for fiscal/sandbox API and module coverage
   - Result: fiscal tables exist in migrations, but no dedicated provider integration module or API route for sandbox issuance was found.

## Findings
1. **Foundational schema exists**
   - `tax_documents` and `tax_document_events` are present in the migration assets.
   - The migration README includes the fiscal domain in the ER coverage.

2. **Application implementation is absent**
   - No dedicated billing/fiscal module exists under `apps/api/app/modules`.
   - No OpenAPI route or application code was identified for sandbox receipt issuance or tax-document status queries.

3. **No QA coverage for Phase 7 behavior**
   - No unit tests or API tests were found for sandbox emission, provider responses, retry handling, or issuance latency.

4. **Operational indicators cannot be verified yet**
   - Because no provider workflow is implemented, the three Phase 7 indicators cannot currently be measured from repository evidence.

## Positive patterns
- The data model anticipated the fiscal domain early.
- The migration assets are already covered by regression tests.
- The repository keeps fiscal concerns structurally visible in schema documentation.

## Gaps / anti-patterns
- No adapter abstraction for sandbox provider integration.
- No end-to-end fiscal issuance flow from paid sale to tax document.
- No retry, queue, or resilience evidence specific to issuance failures.
- No QA contract for sandbox billing behavior.

## Recommended actions
1. Add a billing/fiscal module with provider adapter boundaries.
2. Implement sandbox issuance command flow from eligible paid sale to `tax_documents`.
3. Expose API endpoints to issue and query sandbox tax documents.
4. Add QA tests for success, failure, retry, and status polling scenarios.
5. Create a dedicated verification document for Phase 7 once implementation exists.

## Score rationale (22%)
- **+** Fiscal schema groundwork is present and regression-tested.
- **+** Domain intent is traceable in scope and ER documentation.
- **-** No sandbox provider implementation exists.
- **-** No API or QA evidence exists for issuance, latency, or resilience.
