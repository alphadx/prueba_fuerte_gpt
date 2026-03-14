---
name: pos-cashflow-reliability
description: Implement POS and cash session flow with stock impact, kardex traceability, and reliable sale completion tests. Use when implementing or reviewing step 6 to optimize operational consistency and checkout reliability.
---

# POS Cashflow Reliability

Implement an end-to-end POS flow that is operationally safe and auditable.

## Workflow
1. Implement cash session lifecycle: open, transact, close, reconcile.
2. Implement sale creation with line validation and totals calculation.
3. Integrate payment capture (`cash` and electronic stub) with deterministic states.
4. On sale confirmation: decrement stock and persist kardex movement atomically.
5. Emit billing event asynchronously and validate integration tests for full flow.

## Good practices
- Use transactional boundaries for sale + stock movement consistency.
- Define state machine explicitly (session, sale, payment).
- Keep reconciliation formulas transparent and reproducible.
- Track cashier/operator identity for each critical action.

## Bad practices
- Update stock outside transactional context.
- Allow payment success without finalized sale state.
- Close session without reconciliation evidence.
- Hide rounding/tax rules in UI-only logic.

## Trends to adopt
- Event-driven checkout side-effects with clear outbox pattern.
- Domain events for observability and audit analytics.
- Real-time monitoring of checkout bottlenecks.

## Reliability focus
- Ensure no stock drift under retries/concurrency.
- Keep sale finalization idempotent under client retries.
- Require integration tests for complete “venta completa” scenarios.

## Market aspirations alignment
- Reduce checkout friction and waiting time at POS.
- Improve trust in inventory and cash accountability.
- Enable scalable retail operations with repeatable flows.

## Market reliability expectations
- Maintain high completion rate for checkout sessions.
- Keep reconciliation mismatches near zero.
- Ensure stock and sales consistency at all times.

## Recommended references
- Use `references/pos-integration-checklist.md` for closure checks.
- Use `references/state-machine-template.md` for flow consistency.
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
