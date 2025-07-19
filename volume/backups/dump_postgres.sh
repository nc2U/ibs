#!/bin/bash

# 환경 변수 설정
DATE=$(date +"%Y-%m-%d")
DUMP_FILE=/var/backups/backup-postgres-${DATE}.dump
PGPASSWORD="${POSTGRES_PASSWORD:-$( [ -f "$POSTGRES_PASSWORD_FILE" ] && cat "$POSTGRES_PASSWORD_FILE" || echo '')}"
POSTGRES_DATABASE="${POSTGRES_DATABASE:-${POSTGRES_DB}}"

# 이전 백업 삭제 (예: 2일 이상된 파일)
find /var/backups \( -name "*.dump" -o -name "*.log" \) -type f -ctime +2 -delete

# pg_dump로 ibs 스키마의 데이터만 추출 (django_migrations 제외)
PGPASSWORD="$PGPASSWORD" pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DATABASE}" -n "${POSTGRES_SCHEMA}" \
  --data-only --exclude-table="${POSTGRES_SCHEMA}".django_migrations \
  --column-inserts -Fc -f "${DUMP_FILE}"

# 백업이 성공했는지 확인
if [ $? -eq 0 ]; then
    echo "PostgreSQL Backup completed successfully: ${DUMP_FILE}"
else
    echo "PostgreSQL Backup failed." >&2
    exit 1
fi
