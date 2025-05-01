#!/bin/bash
DATE=$(date +"%Y-%m-%d")
SQL_FILE=/var/backups/backup-postgres-${DATE}.sql

# (2) in case you run this more than once a day,
# remove the previous version of the file
# shellcheck disable=SC2046
find /var/backups -name "*.sql" -mtime +2 -type f -delete

# (3) do the mysql database backup (dump)
pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --data-only  --exclude-table=django_migrations --schema=public --file="${SQL_FILE}"

# 백업이 성공했는지 확인
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: ${SQL_FILE}"
else
    echo "Backup failed"
fi
