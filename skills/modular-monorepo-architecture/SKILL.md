---
name: modular-monorepo-architecture
description: Design a modular monorepo architecture with clear app boundaries, contracts, and developer workflows. Use when implementing or reviewing project step 2 (base architecture and executable repository) with emphasis on modularity and maintainability.
---

# Modular Monorepo Architecture

Create a repository baseline that enables fast iteration with low coupling.

## Workflow
1. Create top-level structure (`apps/`, `workers/`, `infra/`, `tests/`, `docs/`).
2. Define bounded contexts and ownership by module.
3. Establish API contract as source of truth (OpenAPI first).
4. Add deterministic task runners (`make up`, `make test`, `make seed`).
5. Validate developer experience in a clean environment.

## Good practices
- Keep domain rules inside domain modules, not in transport/framework glue.
- Define boundaries and anti-corruption points before coding internals.
- Version API contracts and change them intentionally.
- Keep CI and local commands aligned to avoid “works on my machine” drift.

## Bad practices
- Create a shared folder with hidden cross-module dependencies.
- Use direct imports across domains without explicit interfaces.
- Treat OpenAPI as documentation-only instead of executable contract.
- Add scripts with side effects and no deterministic output.

## Trends to adopt
- Internal developer platforms (IDP) principles for repeatable onboarding.
- Product-oriented architecture decisions documented as lightweight ADRs.
- Platform parity: dev/test/prod behavior differences minimized early.

## Reliability focus
- Enforce architecture checks in CI (lint boundaries, contract validation).
- Require one-command bootstrap and one-command quality check.
- Track architecture debt explicitly with owner and due date.

## Architecture constraints
- Keep domain logic out of framework-specific layers where possible.
- Define module interfaces before implementation.
- Treat shared packages as APIs, not dumping grounds.
- Document ADR-lite decisions for boundaries and trade-offs.


## Market aspirations alignment
- Optimize for scale: architecture must support parallel teams without friction.
- Reduce cost of change with explicit contracts and bounded contexts.
- Improve delivery confidence with deterministic local-to-CI workflows.

## Market reliability expectations
- Minimize architectural drift with enforceable boundaries and ownership.
- Make failures diagnosable quickly with consistent module interfaces.
- Preserve delivery speed while keeping quality gates automated.

## Recommended references
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
- Use `references/repo-checklist.md` for closure criteria.
- Use `references/adr-template.md` to record architecture decisions.
