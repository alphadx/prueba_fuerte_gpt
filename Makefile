.PHONY: doctor-docker up test seed compose-up compose-up-full compose-down compose-smoke architecture-review

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
