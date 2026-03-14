---
name: mvp-scope-qa-gate
description: Define and quality-gate MVP scope with measurable acceptance criteria, user stories, and definition of done. Use when planning or validating implementation readiness for project step 1, especially to reduce ambiguity and increase QA traceability.
---

# MVP Scope QA Gate

Use this workflow to produce a step-1 document that is testable and execution-ready.

## Workflow
1. Extract MVP modules from the plan and convert each into one clear outcome sentence.
2. Write measurable acceptance criteria for each critical flow using observable system evidence.
3. Create user stories with Gherkin (`Given/When/Then`) focused on testability.
4. Add a Definition of Done section with minimum approval gates.
5. Score quality with the reference checklist before closing the step.

## Non-negotiable output rules
- Use measurable language (`%`, counts, statuses, timings) instead of generic wording.
- Ensure each criterion maps to a persistent artifact (record, event, status, log).
- Declare out-of-scope explicitly to prevent scope drift.

## Recommended references
- Use `references/qa-gate-checklist.md` to validate completeness.
- Use `references/template.md` as base structure for `docs/mvp_scope.md`-style outputs.
