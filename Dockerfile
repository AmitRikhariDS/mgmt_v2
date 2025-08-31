# Dockerfile
# Stage: build dependencies
FROM python:3.12-slim AS builder
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y build-essential gcc libpq-dev curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Stage: final
FROM python:3.12-slim AS final
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gettext libpq5 curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . /app

# static files collection will be run by entrypoint depending on env
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

# add entrypoint
COPY deploy/entrypoint.sh /app/entrypoint.sh
USER root
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
USER appuser
CMD ["/app/entrypoint.sh"]
