FROM python:3.11-slim

WORKDIR /workspace

COPY apps/api/requirements.txt /tmp/requirements.txt
COPY apps/api/requirements-dev.txt /tmp/requirements-dev.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt -r /tmp/requirements-dev.txt

CMD ["python", "--version"]
