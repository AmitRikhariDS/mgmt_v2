#!/usr/bin/env bash
set -e

# Wait for DB service if you have a TCP DB (optional)
if [ -n "$DB_HOST" ]; then
  # wait up to 60s for DB to be ready
  for i in $(seq 1 60); do
    if python - <<PY
import sys, socket
h="$DB_HOST"
p=int("$DB_PORT" or 5432)
try:
    s=socket.create_connection((h,p), timeout=1)
    s.close()
    print("ok")
except Exception:
    sys.exit(1)
PY
    then break
    fi
    sleep 1
  done
fi

# optionally run migrations when env RUN_MIGRATIONS=true
if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput
fi

# optionally collect static
if [ "$COLLECT_STATIC" = "true" ]; then
  python manage.py collectstatic --noinput
fi

# Run Gunicorn (workers configurable)
exec gunicorn field_mgmt.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers ${GUNICORN_WORKERS:-3} \
  --access-logfile '-' --error-logfile '-'
