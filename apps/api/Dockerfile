FROM python:3.11-slim

WORKDIR /app
COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY apps/api /app
CMD ["uvicorn", "app.main:app", "--app-dir", "/app", "--host", "0.0.0.0", "--port", "8000"]
