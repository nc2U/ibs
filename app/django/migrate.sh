#!/bin/bash

# Usage:
#   sh migrate.sh                      # 일반 migrate
#   sh migrate.sh -m                   # makemigrations + migrate
#   sh migrate.sh -f                   # 단순 migrate --fake
#   sh migrate.sh -r                   # TRUNCATE django_migrations + migrate --fake
#   sh migrate.sh -mf / -fm            # makemigrations + migrate --fake
#   sh migrate.sh -mr / -rm            # makemigrations + TRUNCATE django_migrations + migrate --fake

APPS="accounts book company contract docs forum ibs items ledger notice payment project work"

DO_MAKEMIGRATIONS=false
DO_FAKE=false
DO_RESET=false

for arg in "$@"; do
  case "$arg" in
    -m|--makemigrations) DO_MAKEMIGRATIONS=true ;;
    -f|--fake)           DO_FAKE=true ;;
    -r|--reset)          DO_RESET=true ;;
    -mf|-fm)             DO_MAKEMIGRATIONS=true; DO_FAKE=true ;;
    -mr|-rm)             DO_MAKEMIGRATIONS=true; DO_RESET=true ;;
  esac
done

if [ "$DO_MAKEMIGRATIONS" = "true" ]; then
    echo "=========================================="
    echo "Creating migrations for apps: $APPS"
    echo "=========================================="
    python manage.py makemigrations $APPS
    if [ $? -ne 0 ]; then
        echo "ERROR: makemigrations failed"
        exit 1
    fi
    echo ""
fi

if [ "$DO_RESET" = "true" ]; then
    echo "=========================================="
    echo "Clearing django_migrations table & applying --fake"
    echo "=========================================="
    python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('TRUNCATE TABLE django_migrations CASCADE;')" 2>/dev/null || true
    python manage.py migrate --database=default --fake
elif [ "$DO_FAKE" = "true" ]; then
    echo "=========================================="
    echo "Applying migrations to database (--fake)"
    echo "=========================================="
    python manage.py migrate --database=default --fake
else
    echo "=========================================="
    echo "Applying migrations to database"
    echo "=========================================="
    python manage.py migrate --database=default
fi

if [ $? -eq 0 ]; then
    echo "Migration completed successfully!"
else
    echo "ERROR: Migration failed"
    exit 1
fi