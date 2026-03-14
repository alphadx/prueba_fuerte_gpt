.PHONY: up test seed

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
