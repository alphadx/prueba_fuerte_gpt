FROM python:3.11-slim

WORKDIR /worker
COPY workers/alerts/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY workers/alerts /worker
CMD ["python", "worker.py"]
