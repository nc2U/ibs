#!/bin/bash

# 복원 대상 파일 지정
DATE=$(date +"%Y-%m-%d")
SQL_FILE="/var/backups/bu-postgres-${DATE}.dump"

pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
   --clean --if-exists --no-owner --no-privileges --disable-triggers \
   --exit-on-error -Fc "${SQL_FILE}"

# 복원 성공 여부 확인
if [ $? -eq 0 ]; then
    echo "POSTGRES Database restoration completed successfully: ${SQL_FILE}"
else
    echo "POSTGRES Database restoration failed"
fi
