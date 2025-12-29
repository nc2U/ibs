#!/bin/bash

# Usage:
#   sh migrate.sh                      # migrate only (production/container)
#   sh migrate.sh --makemigrations     # makemigrations + migrate (local development)

APPS="accounts board book cash company contract docs ibs items ledger notice payment project work"

if [ "$1" = "--makemigrations" ] || [ "$1" = "-m" ]; then
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

echo "=========================================="
echo "Applying migrations to database"
echo "=========================================="
python manage.py migrate --database=default

if [ $? -eq 0 ]; then
    echo "Migration completed successfully!"
else
    echo "ERROR: Migration failed"
    exit 1
fi