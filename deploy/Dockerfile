# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt deploy/constraints.txt ./
RUN --mount=type=secret,id=build_ca,mode=0444 \
    if [ -f /run/secrets/build_ca ]; then export PIP_CERT=/run/secrets/build_ca; fi; \
    pip install --no-cache-dir -r requirements.txt -c constraints.txt && pip check

FROM python:3.11-slim
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:/app/backend" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/opt/nltk_data \
    RESUME_UPLOAD_DIR=/var/data/resumes
WORKDIR /app
RUN --mount=type=secret,id=build_ca,mode=0444 \
    if [ -f /run/secrets/build_ca ]; then \
      printf 'Acquire::https::CaInfo "/run/secrets/build_ca";\n' > /etc/apt/apt.conf.d/99build-ca; \
    fi; \
    sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    libpq5 tesseract-ocr tesseract-ocr-eng tesseract-ocr-fra poppler-utils gosu \
    && rm -rf /var/lib/apt/lists/* /etc/apt/apt.conf.d/99build-ca \
    && useradd --create-home --uid 1000 appuser
COPY --from=builder /opt/venv /opt/venv
COPY deploy/download_nltk.py /app/deploy/download_nltk.py
RUN --mount=type=secret,id=build_ca,mode=0444 \
    if [ -f /run/secrets/build_ca ]; then export SSL_CERT_FILE=/run/secrets/build_ca; fi; \
    python deploy/download_nltk.py
COPY backend/ ./backend/
COPY config/ ./config/
COPY utils/ ./utils/
COPY deploy/ ./deploy/
RUN chmod -R a+rX /app
EXPOSE 8000
CMD ["bash", "deploy/start.sh"]
