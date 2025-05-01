#!/bin/bash
DATE=$(date +"%Y-%m-%d")
SQL_FILE="/var/backups/backup-postgres-${DATE}.dump"

pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -F c "${SQL_FILE}" 2> restore_error.log


# 복원 성공 여부 확인
if [ $? -eq 0 ]; then
    echo "POSTGRES Database restoration completed successfully: ${SQL_FILE}"
else
    echo "POSTGRES Database restoration failed"
fi
