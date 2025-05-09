#!/bin/bash

# 환경 변수 설정
DATE=$(date +"%Y-%m-%d")
SQL_FILE=/var/backups/bu-postgres-${DATE}.dump

# 이전 백업 삭제 (예: 2일 이상된 파일)
find /var/backups -name "*.dump" -mtime +2 -type f -delete

# 백업 실행 (시퀀스 포함)
pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
  --schema="${POSTGRES_USER}" \
  --exclude-table="${POSTGRES_USER}".django_migrations \
  --no-owner --no-privileges --column-inserts  \
  -Fc -f "${SQL_FILE}"

# 백업이 성공했는지 확인
if [ $? -eq 0 ]; then
    echo "PostgreSQL Backup completed successfully: ${SQL_FILE}"
else
    echo "PostgreSQL Backup failed"
fi
