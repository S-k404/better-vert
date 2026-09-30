# syntax=docker/dockerfile:1
FROM python:3.12-slim

# System dependencies:
# - ffmpeg: audio/video encoding, metadata, transcription
# - tesseract-ocr: image OCR
# - poppler-utils: PDF text & page extraction fallbacks
# - libmagic1: MIME type detection
# - imagemagick: image format conversion
# - pandoc: document conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        tesseract-ocr \
        tesseract-ocr-eng \
        poppler-utils \
        libmagic1 \
        imagemagick \
        pandoc \
        potrace \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend application and frontend assets
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create data directories and a non-root account to run the service.
# Conversion shells out to ffmpeg/imagemagick/pandoc on untrusted input, so the
# process should not be root inside the container.
#
# Docker Desktop (macOS/Windows) maps bind-mount ownership to the container user,
# so the defaults just work. On a Linux host, bind-mount permissions are enforced
# literally -- build with `--build-arg VERT_UID=$(id -u) --build-arg VERT_GID=$(id -g)`
# so the container can write to ./output and ./input.
ARG VERT_UID=10001
ARG VERT_GID=10001
RUN mkdir -p /data/input /data/output \
    && groupadd --gid "$VERT_GID" vert \
    && useradd --create-home --uid "$VERT_UID" --gid "$VERT_GID" vert \
    && chown -R vert:vert /data /app

ENV INPUT_DIR=/data/input
ENV OUTPUT_DIR=/data/output
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

USER vert

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/system-info || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
