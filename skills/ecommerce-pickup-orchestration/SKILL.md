---
name: ecommerce-pickup-orchestration
description: Build e-commerce checkout with in-store pickup orchestration, stock consistency by branch, and robust order state transitions. Use when implementing or reviewing step 9 with focus on modular architecture and operational reliability.
---

# E-commerce Pickup Orchestration

Implement a resilient web-to-store order flow with clear state management.

## Workflow
1. Define modular boundaries for catalog, cart, checkout, inventory, and pickup slot services.
2. Implement branch-aware stock visibility and reservation rules.
3. Implement checkout with pickup selection and order creation.
4. Enforce valid order state transitions (`recibido -> preparado -> listo para retiro -> entregado`).
5. Validate end-to-end purchase with pickup through integration/e2e tests.

## Good practices
- Keep order state machine explicit and immutable in history.
- Isolate pricing/cart logic from fulfillment transitions.
- Enforce stock checks at checkout confirmation boundary.
- Track customer-facing and internal statuses separately when needed.

## Bad practices
- Let UI state be the source of truth for order status.
- Allow invalid state jumps without audit trail.
- Ignore branch-level stock when confirming pickup orders.
- Couple map/location rendering logic to core order domain logic.

## Trends to adopt
- Omnichannel order orchestration with branch-level fulfillment intelligence.
- Event-driven order updates to decouple checkout and fulfillment operations.
- SLA tracking for pickup readiness and customer notifications.

## Reliability focus
- Prevent overselling with deterministic stock reservation/release rules.
- Ensure state transitions are idempotent and auditable.
- Keep checkout path resilient under partial downstream failures.

## Market aspirations alignment
- Increase digital conversion with predictable pickup experience.
- Improve store operations through reliable omnichannel coordination.
- Reduce cancellation/friction by aligning promised and actual pickup readiness.

## Market reliability expectations
- Maintain high checkout success rate for pickup flows.
- Keep order state consistency across web and store channels.
- Minimize stock mismatch incidents affecting customer fulfillment.

## Recommended references
- Use `references/ecommerce-e2e-checklist.md` for closure checks.
- Use `references/order-state-machine-template.md` for transition rules.
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
