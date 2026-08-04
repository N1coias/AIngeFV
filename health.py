FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       tesseract-ocr \
       tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
COPY engine /app/engine

RUN pip install --no-cache-dir -r /app/backend/requirements.txt \
    && pip install --no-cache-dir -e /app/engine

COPY backend /app/backend

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 aingefv \
    && chown -R aingefv:aingefv /app
USER aingefv

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
