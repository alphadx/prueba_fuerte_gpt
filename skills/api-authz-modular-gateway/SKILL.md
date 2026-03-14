---
name: api-authz-modular-gateway
description: Build a modular API layer with JWT authentication, role-based authorization, and auditable critical operations. Use when implementing or reviewing step 5 (inventory, sales, billing, orders, hr_docs, alerts) with focus on architecture boundaries and security reliability.
---

# API AuthZ Modular Gateway

Implement a secure, modular API baseline that scales with low coupling.

## Workflow
1. Define module boundaries and route namespaces per domain (`inventory`, `sales`, `billing`, `orders`, `hr_docs`, `alerts`).
2. Implement JWT authentication with explicit token lifecycle and claim strategy.
3. Implement role-based authorization (`admin`, `cajero`, `bodega`, `rrhh`) via policy checks.
4. Add audit trails for critical operations (who, what, when, before/after state).
5. Publish and version OpenAPI/Swagger as contract of behavior.

## Good practices
- Enforce auth and authorization at boundary layer and critical domain actions.
- Centralize permission matrix in one place to avoid drift.
- Return consistent error contracts for `401`, `403`, and domain failures.
- Log security-relevant events with correlation IDs.

## Bad practices
- Hardcode role checks in random handlers.
- Mix authentication concerns with domain business logic.
- Expose write endpoints without auditability.
- Change security behavior without contract/version notes.

## Trends to adopt
- Policy-as-code for maintainable authorization.
- Contract testing for API behavior and permission rules.
- Zero-trust mindset for internal endpoints.

## Reliability focus
- Test permission matrix with positive and negative cases.
- Enforce idempotency where write endpoints can be retried.
- Require deterministic API error semantics for automation.

## Market aspirations alignment
- Improve enterprise trust with secure-by-default APIs.
- Accelerate partner integration with stable contracts.
- Reduce incident cost through clear access governance.

## Market reliability expectations
- Keep auth failures diagnosable and observable.
- Minimize unauthorized action risk to near zero.
- Maintain predictable API behavior under retry/load conditions.

## Recommended references
- Use `references/security-checklist.md` for closure checks.
- Use `references/permission-matrix-template.md` to define role capabilities.
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
