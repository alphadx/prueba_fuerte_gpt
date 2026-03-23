# Technical Annex — Phase 10 Evaluation

## Scope used for this review
Phase 10 in `docs/mvp_scope.md` requires **flexible HR document management plus an alert engine** with three indicators:

1. document coverage in test fixtures,
2. alert precision by configured thresholds,
3. delivery of notifications through test channels.

The user story also requires that expiring employee documents generate visible, traceable alert events.

## Evidence reviewed
- `docs/mvp_scope.md`
- `apps/api/app/modules/employees/`
- `apps/api/app/modules/document_types/`
- `apps/api/app/modules/employee_documents/`
- `apps/api/app/main.py`
- `apps/api/app/services/queue.py`
- `workers/alerts/worker.py`
- `tests/unit/test_employee_service.py`
- `tests/unit/test_document_type_service.py`
- `tests/unit/test_employee_document_service.py`
- `tests/api/test_employees.py`
- `tests/api/test_document_types.py`
- `tests/api/test_employee_documents.py`
- `tests/api/test_health.py`
- `infra/scripts/verify_step5.py`

## Checks executed
1. `pytest -q tests/unit/test_employee_service.py tests/unit/test_document_type_service.py tests/unit/test_employee_document_service.py`
   - Result: `6 passed`.
2. `pytest -q tests/api/test_employees.py tests/api/test_document_types.py tests/api/test_employee_documents.py tests/api/test_health.py`
   - Result: `4 skipped`.
3. `python3 infra/scripts/verify_step5.py`
   - Result: `OK`.

## Findings
1. **HR documentary baseline is strong**
   - Employees, document types, and employee documents are implemented as modular slices.
   - Unit tests validate CRUD rules and duplicate protections.
   - API tests exist for RRHH-focused permissions and flows.

2. **Alert dispatch plumbing exists**
   - The API exposes `POST /alerts/dispatch`.
   - Queue publication exists with Redis and in-memory fallback.
   - A worker consumes alert payloads asynchronously.

3. **Alert engine is still incomplete at business level**
   - No repository evidence was found for automatic threshold evaluation over `expires_on` values.
   - No application service was identified that converts expiring employee documents into `alarm_events` according to 30/15/7/1-day rules.
   - No alert-tracking API or visibility endpoint was identified for follow-up.

4. **Notification delivery evidence is partial**
   - The dispatch endpoint proves queueing capability.
   - There is no end-to-end evidence in this repository review for email/in-app delivery success metrics.

## Positive patterns
- Clear modular separation for HR entities.
- Good unit-test coverage for documentary CRUD flows.
- Async alert infrastructure already seeded in API + worker.
- Static verification confirms RRHH slices are present in the modular API baseline.

## Gaps / anti-patterns
- Missing rule engine for expiration-threshold evaluation.
- Missing persistence/visibility workflow for generated alert events.
- Missing end-to-end QA evidence for alert generation and delivery channels.
- Alert plumbing exists, but business semantics remain only partially implemented.

## Recommended actions
1. Implement a rule-evaluation service that scans expiring documents and generates alert events.
2. Add APIs or views to inspect generated alert state for follow-up.
3. Add QA scenarios for 30/15/7/1-day threshold triggering.
4. Add delivery verification for in-app/email channels using the existing async infrastructure.
5. Add a dedicated Phase 10 verification document once automatic alert generation is executable end to end.

## Score rationale (76%)
- **+** Documentary HR slices are implemented and tested.
- **+** Alert queueing and worker infrastructure are present.
- **-** Automatic alert generation logic is not yet evidenced.
- **-** Delivery precision and follow-up visibility are not yet demonstrated end to end.
