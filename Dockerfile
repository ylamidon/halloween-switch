# Container image for Railway (or any Docker host). Secrets: COMFY_URL, COMFY_API_KEY, APP_AUTH (see README).
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY space/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py LICENSE THIRD_PARTY_NOTICES.md ./
COPY pipeline/ pipeline/
COPY workflows/ workflows/

ENV PYTHONUNBUFFERED=1 GRADIO_SERVER_NAME=0.0.0.0 GRADIO_ANALYTICS_ENABLED=False
# Railway injects PORT; 7860 elsewhere.
CMD ["sh", "-c", "GRADIO_SERVER_PORT=${PORT:-7860} exec python app.py"]
