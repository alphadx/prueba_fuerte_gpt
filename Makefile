.PHONY: doctor-docker up test seed seed-validate seed-pipeline fixtures fixtures-validate fixtures-pipeline smoke-test-state smoke-pipeline bootstrap-test-state bootstrap-validate bootstrap-stability migrate-up migrate-down migrate-status verify-step4 verify-step5 compose-up compose-up-full compose-down compose-smoke architecture-review release-evidence-stage9 release-validate-stage9 release-evidence-pipeline-stage9 bootstrap

COMPOSE = docker compose --env-file .env.example
RUN_TOOLING = $(COMPOSE) run --rm tooling

bootstrap:
	@chmod +x scripts/bootstrap.sh
	./scripts/bootstrap.sh --profile full

urls:
	@API_PORT=$$(grep -E '^API_PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]'); API_PORT=$${API_PORT:-8000}; \
	 WEB_PORT=$$(grep -E '^WEB_PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]'); WEB_PORT=$${WEB_PORT:-3000}; \
	 MH=$$(grep -E '^MAILHOG_UI_PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]'); MH=$${MH:-8025}; \
	 MC=$$(grep -E '^MINIO_CONSOLE_PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]'); MC=$${MC:-9001}; \
	 KC=$$(grep -E '^KEYCLOAK_PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]'); KC=$${KC:-8081}; \
	 GM=$$(grep -E '^GREENMAIL_WEB_PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]'); GM=$${GM:-8082}; \
	 if [ -n "$$CODESPACE_NAME" ]; then \
	   DOMAIN=$${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}; \
	   BASE="https://$$CODESPACE_NAME"; \
	   echo "── Codespaces URLs ──────────────────────────────────────────"; \
	   echo "API /health   : $${BASE}-$${API_PORT}.$${DOMAIN}/health"; \
	   echo "API /docs     : $${BASE}-$${API_PORT}.$${DOMAIN}/docs"; \
	   echo "Web UI        : $${BASE}-$${WEB_PORT}.$${DOMAIN}"; \
	   echo "Mailhog UI    : $${BASE}-$${MH}.$${DOMAIN}"; \
	   echo "MinIO Console : $${BASE}-$${MC}.$${DOMAIN}"; \
	   echo "Keycloak      : $${BASE}-$${KC}.$${DOMAIN}"; \
	   echo "GreenMail Web : $${BASE}-$${GM}.$${DOMAIN}"; \
	   echo "─────────────────────────────────────────────────────────────"; \
	   echo "ℹ  Puertos PRIVATE por defecto. Cambia visibilidad en la pestaña Ports de VS Code."; \
	 else \
	   echo "── URLs locales ─────────────────────────────────────────────"; \
	   echo "API /health   : http://127.0.0.1:$${API_PORT}/health"; \
	   echo "API /docs     : http://127.0.0.1:$${API_PORT}/docs"; \
	   echo "Web UI        : http://127.0.0.1:$${WEB_PORT}"; \
	   echo "Mailhog UI    : http://127.0.0.1:$${MH}"; \
	   echo "MinIO Console : http://127.0.0.1:$${MC}"; \
	   echo "Keycloak      : http://127.0.0.1:$${KC}"; \
	   echo "GreenMail Web : http://127.0.0.1:$${GM}"; \
	 fi

doctor-docker:
	@echo "[doctor] Verificando Docker y Docker Compose..."
	@if command -v docker >/dev/null 2>&1; then \
		docker --version; \
		docker compose version || true; \
		echo "[doctor] OK: Docker disponible."; \
	else \
		echo "[doctor] ERROR: Docker no está instalado/disponible."; \
		echo "[doctor] Acción requerida: instalar Docker Engine + Docker Compose antes de ejecutar pruebas reales."; \
		exit 1; \
	fi

up:
	$(COMPOSE) --profile core up -d --build

test:
	$(RUN_TOOLING) pytest -q

seed:
	$(RUN_TOOLING) python infra/scripts/seed.py

seed-validate:
	$(RUN_TOOLING) python infra/scripts/validate_seed.py

seed-pipeline: seed seed-validate
	@echo "[seed] Pipeline idempotente OK"

fixtures:
	$(RUN_TOOLING) python infra/scripts/load_fixtures.py

fixtures-validate:
	$(RUN_TOOLING) python infra/scripts/validate_fixtures.py


fixtures-pipeline: fixtures fixtures-validate
	@echo "[fixtures] Pipeline crítico OK"

smoke-test-state:
	$(RUN_TOOLING) python infra/scripts/smoke_test_state.py

smoke-pipeline: seed-pipeline fixtures-pipeline smoke-test-state
	@echo "[smoke] Pipeline de estado QA OK"

bootstrap-test-state:
	$(RUN_TOOLING) python infra/scripts/bootstrap_test_state.py --max-seconds 600 --retries 1 --step-timeout-seconds 240 --verbose

bootstrap-validate:
	$(RUN_TOOLING) python infra/scripts/validate_bootstrap_report.py --path infra/seeds/bootstrap_report.json --max-seconds 600

bootstrap-stability:
	$(RUN_TOOLING) python infra/scripts/bootstrap_stability.py --runs 3 --min-success-rate 95 --max-seconds 600

migrate-up:
	$(RUN_TOOLING) python infra/scripts/migrate.py up

migrate-down:
	$(RUN_TOOLING) python infra/scripts/migrate.py down --version $${VERSION:-0001}

migrate-status:
	$(RUN_TOOLING) python infra/scripts/migrate.py status

verify-step4:
	$(RUN_TOOLING) python infra/scripts/verify_step4.py

compose-up:
	$(COMPOSE) --profile core up -d --build

compose-up-full:
	$(COMPOSE) --profile full up -d --build

compose-down:
	$(COMPOSE) down


compose-smoke:
	@echo "[smoke] Verificando endpoints del stack core..."
	@curl -fsS http://127.0.0.1:$${API_PORT:-8000}/health >/dev/null
	@curl -fsS http://127.0.0.1:$${API_PORT:-8000}/ready >/dev/null
	@echo "[smoke] OK: /health y /ready responden correctamente."


architecture-review:
	@echo "[arch] Revisando requerimientos críticos de arquitectura..."
	@echo "- Perfil full incluye sandbox SMTP+IMAP (greenmail)"
	@echo "- Frontend web existente para evolución responsive/PWA"
	@echo "- QR P2P definido en documentación de pasos 9-12"


verify-step5:
	$(RUN_TOOLING) python infra/scripts/verify_step5.py


release-evidence-stage9:
	$(RUN_TOOLING) sh -c 'JWT_HS256_SECRET=$${JWT_HS256_SECRET:-test-secret} PYTHONPATH=apps/api python infra/scripts/generate_release_evidence.py --stage 9'


release-validate-stage9:
	$(RUN_TOOLING) python infra/scripts/validate_release_evidence.py --path docs/release_validation_stage9.yaml

release-evidence-pipeline-stage9: release-evidence-stage9 release-validate-stage9
	@echo "[release-evidence] Pipeline stage9 consistente"

release-closure-acta-stage9:
	$(RUN_TOOLING) python infra/scripts/generate_release_closure_acta.py --input docs/release_validation_stage9.yaml --output docs/release_stage12_closure_acta.md

release-closure-pipeline-stage9: release-evidence-pipeline-stage9 release-closure-acta-stage9
	@echo "[release-closure-acta] Acta stage12 generada"
