#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/home/deploy/app}
cd "$APP_DIR"

echo ">>> Starting deployment in $APP_DIR"

# Ensure env file exists
if [ ! -f .env.production ]; then
  echo "ERROR: .env.production missing - aborting!"
  exit 1
fi

# Pull latest images
echo ">>> Pulling latest Docker images..."
docker compose pull

# Recreate containers safely
echo ">>> Restarting containers..."
docker compose up -d --remove-orphans --force-recreate

# Run migrations in a one-off container if enabled
if [ "${AUTO_MIGRATE:-false}" = "true" ]; then
  echo ">>> Running migrations..."
  docker compose run --rm web python manage.py migrate --noinput
fi

# Cleanup old images (safe filter)
echo ">>> Cleaning up old images..."
docker image prune -f --filter "until=24h"

echo ">>> Deployment completed successfully."
