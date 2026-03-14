---
name: data-model-migrations-blueprint
description: Design MVP data models and migration strategy with integrity, versioning, and rollback safety. Use when implementing or reviewing step 4, especially for PostgreSQL schemas, entity coverage, and migration quality gates.
---

# Data Model & Migrations Blueprint

Use this skill to transform domain requirements into robust schema evolution.

## Workflow
1. Map entities and relationships from scope to normalized tables.
2. Define keys, constraints, and audit fields consistently.
3. Use JSONB only for truly dynamic attributes with validation strategy.
4. Create forward and rollback migrations with explicit versioning.
5. Validate idempotency and relational integrity in clean databases.

## Design rules
- Prefer explicit constraints over app-only validation.
- Model events/history tables for auditable flows.
- Keep naming conventions stable (`snake_case`, singular/plural policy).
- Enforce UTC timestamps and deterministic defaults.

## Recommended references
- Use `references/entity-coverage.md` to track MVP completeness.
- Use `references/migration-gates.md` as pre-merge quality gate.
