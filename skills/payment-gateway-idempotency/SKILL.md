---
name: payment-gateway-idempotency
description: Build a payment adapter layer with unified webhook idempotency, feature flags by branch/channel, and basic reconciliation controls. Use when implementing or reviewing step 8 to optimize payment reliability and extensibility.
---

# Payment Gateway Idempotency

Implement payment integrations that are safe under retries, callbacks, and channel variability.

## Workflow
1. Define `PaymentGateway` interface and common payment state model.
2. Implement drivers for `cash`, `transbank_stub`, and `mercadopago_stub`.
3. Build unified webhook handler with idempotency key strategy.
4. Add feature flags by branch/channel to control payment method rollout.
5. Implement basic reconciliation process between sale, payment intent, and settlement result.

## Good practices
- Normalize gateway responses into internal canonical states.
- Enforce idempotency on webhook ingestion and state transitions.
- Separate payment authorization from business finalization side-effects.
- Record gateway request/response metadata for diagnostics.

## Bad practices
- Let duplicate webhooks mutate paid state repeatedly.
- Couple branch rollout to code deployment instead of flags.
- Mix gateway-specific rules in domain core.
- Assume callback order is deterministic.

## Trends to adopt
- Progressive rollout with feature flags and operational guardrails.
- Payment observability dashboards (approval, rejection, timeout, retries).
- Unified payment event model for multi-provider strategy.

## Reliability focus
- Guarantee webhook idempotency under duplicate delivery.
- Keep payment state machine monotonic and auditable.
- Detect and reconcile orphaned payment intents.

## Market aspirations alignment
- Increase conversion with resilient payment processing.
- Enable fast payment method expansion with adapter strategy.
- Reduce revenue leakage through reconciliation discipline.

## Market reliability expectations
- Keep payment confirmation consistency high across channels.
- Prevent duplicate charges or double-finalization events.
- Maintain fast issue detection for failed callbacks.

## Recommended references
- Use `references/webhook-idempotency-checklist.md` for closure checks.
- Use `references/payment-state-model.md` for canonical transitions.
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
