#!/bin/bash
DATE=$(date +"%Y-%m-%d")
SQL_FILE=/var/backups/backup-postgres-${DATE}.dump

# (2) in case you run this more than once a day,
# remove the previous version of the file
# shellcheck disable=SC2046
find /var/backups -name "*.dump" -mtime +2 -type f -delete

# (3) do the postgres database backup (dump)
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --exclude-table=django_migrations -Fc -f "${SQL_FILE}"

# 백업이 성공했는지 확인
if [ $? -eq 0 ]; then
    echo "PostgreSQL Backup completed successfully: ${SQL_FILE}"
else
    echo "PostgreSQL Backup failed"
fi
