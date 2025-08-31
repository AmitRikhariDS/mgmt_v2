# --- Stage 1: build deps ---
FROM python:3.12-slim AS builder
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=off
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# --- Stage 2: runtime image ---
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=field_mgmt.settings \
    PYTHONDONTWRITEBYTECODE=1

# minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends gettext libpq5 curl \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user & workdir
WORKDIR /app
RUN useradd -m -u 1000 appuser

# Copy installed python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project source (adjust if you need to exclude dev stuff via .dockerignore)
COPY . /app

# Ensure entrypoint is executable at build-time (no root flip-flop needed)
# If your repo doesn’t have the executable bit, set it here:
RUN chmod 755 /app/deploy/entrypoint.sh

# Permissions
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
