---
name: data-model-migrations-blueprint
description: Design MVP data models and migration strategy with integrity, versioning, and rollback safety. Use when implementing or reviewing step 4, especially for PostgreSQL schemas, entity coverage, and migration quality gates.
---

# Data Model & Migrations Blueprint

Transform functional scope into robust schema evolution with controlled risk.

## Workflow
1. Map entities and relationships from scope to normalized tables.
2. Define keys, constraints, indexes, and audit fields consistently.
3. Use JSONB only for dynamic attributes with validation strategy.
4. Create forward and rollback migrations with explicit versioning.
5. Validate idempotency and relational integrity in clean databases.

## Good practices
- Encode invariants in DB constraints, not only in application code.
- Add indexes for known access patterns and review query plans.
- Separate transactional tables from event/history tables.
- Keep migration files small, reviewable, and reversible.

## Bad practices
- Add nullable columns for required domain concepts by default.
- Use JSONB as a shortcut for undefined relational modeling.
- Bundle many risky schema changes in one migration.
- Skip rollback validation before merge.

## Trends to adopt
- Expand-and-contract migrations for safer production evolution.
- Online/backward-compatible changes first, destructive changes later.
- Schema governance with quality gates tied to CI.

## Reliability focus
- Guarantee migration chain reproducibility on fresh databases.
- Validate rollback path for the latest migration at minimum.
- Add data backfill strategies with checkpoints for long-running updates.

## Design rules
- Prefer explicit constraints over app-only validation.
- Model events/history tables for auditable flows.
- Keep naming conventions stable (`snake_case`, singular/plural policy).
- Enforce UTC timestamps and deterministic defaults.


## Market aspirations alignment
- Design schemas that support growth, analytics, and compliance without rework.
- Protect continuity by making migration risk visible and manageable.
- Improve long-term maintainability with explicit invariants and history models.

## Market reliability expectations
- Keep migration operations reversible and observable.
- Avoid high-blast-radius changes through incremental rollout patterns.
- Maintain query performance while evolving schema capabilities.

## Recommended references
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
- Use `references/entity-coverage.md` to track MVP completeness.
- Use `references/migration-gates.md` as pre-merge quality gate.
