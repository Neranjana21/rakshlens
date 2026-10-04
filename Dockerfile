# One container serves the API and the PWA. Build context = repo root.
FROM python:3.12-slim

# Tesseract with English, Tamil and Hindi language packs for local screenshot reading.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-tam tesseract-ocr-hin \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY web /app/web
ENV WEB_DIR=/app/web PYTHONUNBUFFERED=1

RUN useradd -m -u 10001 rl
USER rl

# A single worker keeps the in-memory rate limiter accurate. Nothing is written to disk.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --no-access-log"]
