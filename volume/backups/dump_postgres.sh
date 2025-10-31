#!/bin/bash
set -eu

# CloudNativePG 환경 변수 설정
DATE=$(date +"%Y-%m-%d")
DUMP_FILE=/var/backups/ibs-backup-postgres-${DATE}.dump

# CloudNativePG 비밀번호 처리 (Secret에서 마운트됨)
if [ -f "/controller/run/postgres-password" ]; then
    PGPASSWORD=$(cat /controller/run/postgres-password)
elif [ -n "${POSTGRES_PASSWORD:-}" ]; then
    PGPASSWORD="${POSTGRES_PASSWORD}"
else
    echo "Error: PostgreSQL password not found" >&2
    exit 1
fi

POSTGRES_DATABASE="${POSTGRES_DATABASE:-ibs}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_SCHEMA="${POSTGRES_SCHEMA:-ibs}"
# CloudNativePG는 localhost 연결 필요 (peer 인증 우회)
PSQL_HOST="localhost"

# 이전 백업 삭제 (예: 2일 이상된 파일)
find /var/backups \( -name "*.dump" -o -name "*.log" \) -type f -ctime +2 -delete

if [ -f "$DUMP_FILE" ]; then
    rm "$DUMP_FILE"
fi

# pg_dump로 ibs 스키마의 데이터만 추출 (django_migrations 제외)
PGPASSWORD="$PGPASSWORD" pg_dump -h "$PSQL_HOST" -U "${POSTGRES_USER}" -d "${POSTGRES_DATABASE}" -n "${POSTGRES_SCHEMA}" \
  --data-only --exclude-table="${POSTGRES_SCHEMA}".django_migrations \
  --column-inserts -Fc -f "${DUMP_FILE}"

# 퍼미션 변경
chmod 777 ${DUMP_FILE}

# 백업이 성공했는지 확인
if [ $? -eq 0 ]; then
    echo "PostgreSQL Backup completed successfully: ${DUMP_FILE}"
else
    echo "PostgreSQL Backup failed." >&2
    exit 1
fi
