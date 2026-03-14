---
name: billing-sandbox-adapter
description: Implement a decoupled billing provider adapter for sandbox electronic receipts with async retries, document tracking, and status synchronization. Use when implementing or reviewing step 7 with focus on reliability and non-blocking POS operations.
---

# Billing Sandbox Adapter

Integrate electronic receipt issuance in sandbox without compromising checkout latency.

## Workflow
1. Define `BillingProvider` interface with stable request/response contract.
2. Implement sandbox adapter handling folio, XML/PDF artifacts, track ID, and status.
3. Dispatch billing emission asynchronously from POS flow.
4. Configure retry policy with bounded backoff and dead-letter handling.
5. Expose status query endpoints and traceability for each tax document.

## Good practices
- Keep provider-specific logic isolated behind adapter boundaries.
- Persist immutable request/response snapshots for auditability.
- Make retries explicit and observable (attempt count, last error).
- Use idempotency keys for duplicate emission prevention.

## Bad practices
- Call provider synchronously during POS payment critical path.
- Couple fiscal states directly to provider transport errors.
- Overwrite historical response payloads.
- Retry indefinitely without circuit/limit strategy.

## Trends to adopt
- Outbox + worker processing for guaranteed delivery semantics.
- Unified integration telemetry (latency, error classes, retry outcomes).
- Adapter plugability for future provider replacement.

## Reliability focus
- Protect POS flow from provider downtime.
- Guarantee eventual consistency for billing state transitions.
- Ensure deterministic duplicate handling and status reconciliation.

## Market aspirations alignment
- Improve fiscal automation maturity from MVP stage.
- Reduce compliance risk with traceable document lifecycle.
- Prepare for future provider switching with low rework cost.

## Market reliability expectations
- Keep sandbox issuance success high under transient failures.
- Minimize stuck documents without status visibility.
- Ensure retriable failures recover automatically.

## Recommended references
- Use `references/billing-reliability-checklist.md` for closure checks.
- Use `references/provider-contract-template.md` for interface consistency.
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
