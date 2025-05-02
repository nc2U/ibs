#!/bin/bash
DATE=$(date +"%Y-%m-%d")
SQL_FILE="/var/backups/backup-postgres-${DATE}.dump"

psql -U ${USER} -d ${DATABASE} -c "DROP SCHEMA ibs CASCADE; CREATE SCHEMA ibs;"
pg_restore --clean --if-exists --no-owner -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" "${SQL_FILE}"

# 복원 성공 여부 확인
if [ $? -eq 0 ]; then
    echo "POSTGRES Database restoration completed successfully: ${SQL_FILE}"
else
    echo "POSTGRES Database restoration failed"
fi
