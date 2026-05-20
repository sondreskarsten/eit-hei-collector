FROM python:3.12-slim

RUN pip install --no-cache-dir \
    requests \
    google-cloud-storage

COPY client.py storage.py collector.py entrypoint.py /app/

WORKDIR /app

CMD ["python", "entrypoint.py"]
