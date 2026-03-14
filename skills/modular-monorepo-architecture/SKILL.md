---
name: modular-monorepo-architecture
description: Design a modular monorepo architecture with clear app boundaries, contracts, and developer workflows. Use when implementing or reviewing project step 2 (base architecture and executable repository) with emphasis on modularity and maintainability.
---

# Modular Monorepo Architecture

Create a repository skeleton that supports fast iteration and low coupling.

## Workflow
1. Create top-level structure (`apps/`, `workers/`, `infra/`, `tests/`, `docs/`).
2. Define bounded contexts per module and map ownership.
3. Establish API contract as source of truth (OpenAPI first).
4. Add task runners (`make up`, `make test`, `make seed`) with deterministic behavior.
5. Validate developer experience in a clean environment.

## Architecture constraints
- Keep domain logic out of framework-specific layers where possible.
- Define module interfaces before implementation.
- Treat shared packages as APIs, not dumping grounds.
- Document ADR-lite decisions for boundaries and trade-offs.

## Recommended references
- Use `references/repo-checklist.md` for closure criteria.
- Use `references/adr-template.md` to record architecture decisions.
