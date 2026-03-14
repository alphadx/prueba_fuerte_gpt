---
name: hr-docs-alerts-engine
description: Implement flexible HR document management with dynamic document types, expiry thresholds, and reliable alert generation/notification. Use when implementing or reviewing step 10 with modularity, compliance, and reliability focus.
---

# HR Docs Alerts Engine

Build a compliant document lifecycle with deterministic alerting.

## Workflow
1. Define module boundaries for employee docs, document types, and alert rules.
2. Implement `DocumentType` with dynamic schema constraints.
3. Implement document ingestion (file metadata, expiration, ownership).
4. Implement daily alert evaluator for thresholds (30/15/7/1 days).
5. Emit `AlarmEvent` and notify in-app/email for test environments.

## Good practices
- Validate dynamic document metadata against schema at write time.
- Keep alert generation deterministic and idempotent per evaluation window.
- Separate storage concerns (files) from compliance metadata model.
- Version alert rules to keep traceability of compliance decisions.

## Bad practices
- Store unvalidated arbitrary metadata for compliance documents.
- Re-generate duplicate alerts with no deduplication strategy.
- Tie notification delivery success directly to event creation success.
- Mix HR policy rules inside generic file upload handlers.

## Trends to adopt
- Compliance-by-design with auditable rule engines.
- Event-driven alerts with multi-channel delivery adapters.
- Structured HR document models for automated risk scoring.

## Reliability focus
- Ensure alert jobs are safe to rerun without duplication.
- Preserve evidence of rule evaluation and notification outcomes.
- Keep degraded notification channels from blocking compliance event creation.

## Market aspirations alignment
- Strengthen compliance posture with proactive document risk detection.
- Reduce manual HR overhead through automation.
- Improve workforce governance visibility for operations leadership.

## Market reliability expectations
- Keep alert precision high for upcoming expirations.
- Ensure no critical expirations are missed by scheduler failures.
- Maintain traceable audit records for compliance reviews.

## Recommended references
- Use `references/hr-alerts-checklist.md` for closure checks.
- Use `references/document-schema-template.md` for dynamic field design.
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
