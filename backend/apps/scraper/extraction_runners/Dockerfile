# Isolated Scrapling adaptive-extraction runner (§15/§16) - REPRODUCIBLE
# RUNTIME ARTIFACT replacing the earlier ad-hoc local verification approach
# (`pip install --target $env:TEMP\...`). This image is built and run
# SEPARATELY from the main Django backend image/venv - never installed into
# backend/venv or backend/requirements.txt - because Scrapling pins
# `lxml>=6.1.1` while this project's `docling` (CV parser) requires
# `lxml<6.0.0` (a real, confirmed conflict, not a hypothetical one).
#
# Build (from repo root):
#   docker build -t usam-scrapling-runner:0.4.15 \
#       -f backend/apps/scraper/extraction_runners/Dockerfile \
#       backend/apps/scraper/extraction_runners
#
# Run a single extraction (protocol: JSON on stdin -> JSON on stdout, see
# scrapling_runner.py's module docstring):
#   echo '{"url": "https://example.com/careers"}' | \
#       docker run --rm -i usam-scrapling-runner:0.4.15
#
# Production wiring: Django's OutOfProcessBackend.runner_cmd expects a
# command list that speaks this stdin/stdout protocol. Point it at
# `docker run --rm -i usam-scrapling-runner:0.4.15` (via
# SCRAPLING_RUNNER_PYTHON pattern - see apps/scraper/tasks.py's
# _adaptive_fallback_runner and config/settings/base.py's
# SCRAPLING_RUNNER_DOCKER_IMAGE) OR install this image's requirements.txt
# into a plain isolated venv on the host and point runner_cmd at that venv's
# python + this directory's scrapling_runner.py directly. Both are
# equally valid; Docker is preferred for reproducibility across hosts.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps required by Scrapling's StealthyFetcher (Playwright/Patchright
# headless Chromium) - mirrors `playwright install-deps chromium`'s apt
# package set for Debian slim images.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libdbus-1-3 libxcb1 libxkbcommon0 libx11-6 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
    libasound2 libatspi2.0-0 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /runner

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    python -m playwright install chromium

COPY scrapling_runner.py .

# Protocol: read one JSON request from stdin, write one JSON response to
# stdout, exit 0. No server, no persistent process - one container run per
# extraction call (matches OutOfProcessBackend.extract()'s subprocess.run()).
ENTRYPOINT ["python", "scrapling_runner.py"]
