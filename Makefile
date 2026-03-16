.PHONY: doctor-docker up test seed seed-validate seed-pipeline fixtures fixtures-validate fixtures-pipeline smoke-test-state smoke-pipeline bootstrap-test-state bootstrap-validate bootstrap-stability migrate-up migrate-down migrate-status verify-step4 verify-step5 compose-up compose-up-full compose-down compose-smoke architecture-review

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
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r apps/api/requirements.txt
	. .venv/bin/activate && uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8000

test:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt
	. .venv/bin/activate && pytest -q

seed:
	python3 infra/scripts/seed.py

seed-validate:
	python3 infra/scripts/validate_seed.py

seed-pipeline: seed seed-validate
	@echo "[seed] Pipeline idempotente OK"

fixtures:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt
	. .venv/bin/activate && python infra/scripts/load_fixtures.py

fixtures-validate:
	python3 infra/scripts/validate_fixtures.py


fixtures-pipeline: fixtures fixtures-validate
	@echo "[fixtures] Pipeline crítico OK"

smoke-test-state:
	python3 infra/scripts/smoke_test_state.py

smoke-pipeline: seed-pipeline fixtures-pipeline smoke-test-state
	@echo "[smoke] Pipeline de estado QA OK"

bootstrap-test-state:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt
	. .venv/bin/activate && python infra/scripts/bootstrap_test_state.py --max-seconds 600 --retries 1 --step-timeout-seconds 240 --verbose

bootstrap-validate:
	python3 infra/scripts/validate_bootstrap_report.py --path infra/seeds/bootstrap_report.json --max-seconds 600

bootstrap-stability:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt
	. .venv/bin/activate && python infra/scripts/bootstrap_stability.py --runs 3 --min-success-rate 95 --max-seconds 600

migrate-up:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r apps/api/requirements.txt
	. .venv/bin/activate && python infra/scripts/migrate.py up

migrate-down:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r apps/api/requirements.txt
	. .venv/bin/activate && python infra/scripts/migrate.py down --version $${VERSION:-0001}

migrate-status:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r apps/api/requirements.txt
	. .venv/bin/activate && python infra/scripts/migrate.py status

verify-step4:
	python3 infra/scripts/verify_step4.py

compose-up:
	docker compose --profile core --env-file .env.example up -d --build

compose-up-full:
	docker compose --profile full --env-file .env.example up -d --build

compose-down:
	docker compose --env-file .env.example down


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
	python3 infra/scripts/verify_step5.py
