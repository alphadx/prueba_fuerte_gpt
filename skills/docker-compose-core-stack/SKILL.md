---
name: docker-compose-core-stack
description: Build and validate a reproducible Docker Compose core stack (postgres, redis, api, worker, web) with environment parity and health checks. Use when executing step 3 or troubleshooting local service orchestration.
---

# Docker Compose Core Stack

Operationalize a reliable local platform baseline for development and QA.

## Workflow
1. Define `core` profile services (`postgres`, `redis`, `api`, `worker`, `web`).
2. Add health checks and explicit dependency conditions.
3. Define `.env.example` with all required runtime variables.
4. Add optional `full` profile services (MailHog/MinIO/observability).
5. Measure cold-start time and capture reproducibility evidence.

## Good practices
- Gate dependent services by health, not by start order.
- Pin image tags and document update policy.
- Keep service names stable to reduce environment drift.
- Version `docker-compose.yml` changes with clear migration notes.

## Bad practices
- Rely on `sleep` scripts for readiness.
- Use mutable `latest` tags in baseline environments.
- Hide required env vars outside `.env.example`.
- Couple optional services to core boot path.

## Trends to adopt
- Local-first observability (logs/metrics/traces) in dev stacks.
- Ephemeral environment mindset: recreate from scratch frequently.
- Profile-driven compose strategies (`core` vs `full`) for faster loops.

## Reliability focus
- Define SLO-like local reliability targets (boot success rate, p95 boot time).
- Validate stack startup from zero state repeatedly.
- Include failure drills: DB unavailable, Redis restart, worker reconnect.

## Reliability rules
- Never rely on implicit startup ordering.
- Prefer health-based readiness over sleep/wait hacks.
- Keep volumes and network names explicit.
- Keep image tags pinned for deterministic onboarding.


## Market aspirations alignment
- Optimize developer throughput with fast, reproducible environments.
- Reduce integration surprises by simulating production-like dependencies early.
- Strengthen DevEx as a competitive advantage for delivery velocity.

## Market reliability expectations
- Meet baseline startup reliability targets for daily usage.
- Ensure core services recover predictably from common fault scenarios.
- Prevent hidden configuration drift through explicit env contracts.

## Recommended references
- Use `references/market-aspirations.md` for KPI and market-alignment guidance.
- Use `references/compose-checklist.md` before marking step 3 as done.
- Use `references/env-matrix.md` to verify parity of env variables.
