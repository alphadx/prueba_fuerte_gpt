---
name: test-state-bootstrap-factory
description: Build deterministic seed/fixture pipelines that bootstrap a valid QA test state quickly for critical ERP scenarios. Use when implementing or reviewing step 11 with emphasis on reproducibility, speed, and scenario coverage.
---

# Test State Bootstrap Factory

Create a one-command QA-ready environment with deterministic data and smoke validation.

## Workflow
1. Define minimum seed dataset for company, branch, users, products, and HR docs.
2. Add fixtures for critical scenarios (cash sale, electronic sale, web pickup, billing sandbox, payment webhook).
3. Implement bootstrap command (`make bootstrap-test-state`) with idempotent behavior.
4. Add smoke checks to verify scenario readiness after bootstrap.
5. Measure bootstrap runtime and keep under target threshold.

## Good practices
- Make seeds deterministic with stable identifiers and predictable timestamps.
- Keep fixtures independent so failures isolate quickly.
- Verify post-bootstrap invariants automatically.
- Version test state changes with clear changelog intent.

## Bad practices
- Depend on manual data preparation for QA readiness.
- Use non-deterministic random data without reproducibility controls.
- Build fixtures tightly coupled to transient external services.
- Accept bootstrap success without scenario-level smoke verification.

## Trends to adopt
- Test data as product: governed, versioned, and observable.
- Shift-left QA with instant reproducible environment provisioning.
- Scenario contracts for critical business flows.

## Reliability focus
- Ensure repeated bootstrap runs produce equivalent states.
- Detect broken fixtures early via automated smoke checks.
- Keep runtime predictable to protect QA throughput.

## Market aspirations alignment
- Accelerate release cadence through rapid QA readiness.
- Reduce regression escape risk by standardizing critical scenarios.
- Improve cross-team productivity with shared deterministic environments.

## Market reliability expectations
- Maintain high bootstrap success rate.
- Keep scenario coverage complete for revenue-critical flows.
- Minimize flaky smoke tests and environment drift.

## Recommended references
- Use `references/bootstrap-checklist.md` for closure checks.
- Use `references/fixture-catalog-template.md` for scenario tracking.
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
