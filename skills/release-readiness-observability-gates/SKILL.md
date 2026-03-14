---
name: release-readiness-observability-gates
description: Establish final validation gates with pipeline quality checks, observability baselines, and go-live readiness criteria. Use when implementing or reviewing step 12 to optimize release confidence and operational reliability.
---

# Release Readiness Observability Gates

Define objective go-live readiness using quality, performance, and risk controls.

## Workflow
1. Define pipeline gates: lint/format, unit, integration, and smoke e2e.
2. Set minimum observability metrics: API latency, worker queue health, billing/payment error rates.
3. Define SLO-aligned thresholds and alerting triggers.
4. Build release checklist with critical/non-critical risk categorization.
5. Produce execution report with pass/fail evidence and known risks.

## Good practices
- Treat release checklist as executable gate, not static document.
- Separate release blockers from follow-up improvements explicitly.
- Keep SLO thresholds realistic and tied to business impact.
- Include rollback strategy and ownership for each critical risk.

## Bad practices
- Ship with unresolved critical red gates.
- Use observability metrics with no alert/action mapping.
- Close release by “gut feeling” without evidence artifacts.
- Ignore queue degradation and async backlog growth before go-live.

## Trends to adopt
- Continuous verification across pre-release environments.
- SRE-inspired error-budget thinking adapted to MVP scale.
- Risk-based release governance with automated gates.

## Reliability focus
- Ensure repeatable pipeline outcomes before sign-off.
- Keep incident detection latency low with actionable telemetry.
- Require rollback readiness for critical deployment paths.

## Market aspirations alignment
- Increase release confidence while preserving delivery speed.
- Protect customer trust with stable production behavior.
- Improve decision quality through evidence-based go-live criteria.

## Market reliability expectations
- Maintain high release success rate without hotfix storms.
- Keep critical error rates and latency within agreed thresholds.
- Minimize post-release incident severity and duration.

## Recommended references
- Use `references/release-gates-checklist.md` for closure checks.
- Use `references/slo-template.md` to define operational thresholds.
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
