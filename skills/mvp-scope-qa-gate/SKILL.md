---
name: mvp-scope-qa-gate
description: Define and quality-gate MVP scope with measurable acceptance criteria, user stories, and definition of done. Use when planning or validating implementation readiness for project step 1, especially to reduce ambiguity and increase QA traceability.
---

# MVP Scope QA Gate

Produce a step-1 scope document that is clear, testable, and ready for execution.

## Workflow
1. Extract MVP modules from the plan and convert each module into one explicit business outcome.
2. Write measurable acceptance criteria for each critical flow using observable evidence.
3. Create user stories with Gherkin (`Given/When/Then`) focused on verification.
4. Add Definition of Done gates with objective close conditions.
5. Validate quality with the reference checklist before marking step 1 as complete.

## Good practices
- Define criteria with measurable terms: success rate, exact state, timing, or count.
- Link each criterion to evidence: DB row, API status, event, or audit log.
- Declare out-of-scope explicitly to prevent roadmap drift.
- Keep stories independent and executable with minimum fixture data.

## Bad practices
- Use ambiguous language (`correcto`, `rápido`, `estable`) without thresholds.
- Mix implementation details inside business criteria.
- Close step 1 without unresolved critical assumptions.
- Write stories that cannot be validated with available test data.

## Trends to adopt
- Shift-left quality: convert requirements to test cases early.
- Contract-first mindset: ensure stories map cleanly to API/domain contracts.
- Traceability-by-default: keep explicit mapping story -> criterion -> evidence.

## Reliability focus
- Require repeatable validation for each critical flow (not one-off manual checks).
- Include at least one negative scenario per core capability.
- Define a “no critical ambiguity” gate as mandatory for closure.

## Non-negotiable output rules
- Use measurable language (`%`, counts, statuses, timings) instead of generic wording.
- Ensure each criterion maps to a persistent artifact (record, event, status, log).
- Declare out-of-scope explicitly to prevent scope drift.


## Market aspirations alignment
- Prioritize outcomes that improve time-to-market and reduce requirement churn.
- Define metrics that executives can track (quality, lead time, acceptance stability).
- Structure requirements for AI-assisted delivery and automated test generation.

## Market reliability expectations
- Keep acceptance criteria stable enough to avoid late rework.
- Require evidence that every critical flow can be validated repeatedly.
- Treat ambiguity as reliability risk, not documentation debt.

## Recommended references
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
- Use `references/qa-gate-checklist.md` to validate completeness.
- Use `references/template.md` as base structure for `docs/mvp_scope.md`-style outputs.
