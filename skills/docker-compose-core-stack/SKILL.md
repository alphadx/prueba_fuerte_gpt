---
name: docker-compose-core-stack
description: Build and validate a reproducible Docker Compose core stack (postgres, redis, api, worker, web) with environment parity and health checks. Use when executing step 3 or troubleshooting local service orchestration.
---

# Docker Compose Core Stack

Use this skill to operationalize a reliable local platform baseline.

## Workflow
1. Define `core` profile services (`postgres`, `redis`, `api`, `worker`, `web`).
2. Add health checks and explicit dependencies.
3. Define `.env.example` with every required runtime variable.
4. Add optional `full` profile services (MailHog/MinIO/observability).
5. Measure cold-start time and record reproducibility result.

## Reliability rules
- Never rely on implicit startup ordering.
- Prefer health-based readiness over sleep/wait hacks.
- Keep volumes and network names explicit.
- Keep image tags pinned for deterministic onboarding.

## Recommended references
- Use `references/compose-checklist.md` before marking step 3 as done.
- Use `references/env-matrix.md` to verify parity of env variables.
