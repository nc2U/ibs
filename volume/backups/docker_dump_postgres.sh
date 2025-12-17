#!/bin/bash

# 환경 변수 설정 (PGUSER, PGPASSWORD, PGDATABASE는 컨테이너 환경에서 직접 주입됨)
DATE=$(date +"%Y-%m-%d")
DUMP_FILE=/var/backups/ibs-backup-postgres-${DATE}.dump
# 기존 PGPASSWORD 및 POSTGRES_DATABASE 설정은 이제 필요 없음.
# pg_dump는 PGUSER, PGPASSWORD, PGDATABASE 환경 변수를 자동으로 사용함.

# 이전 백업 삭제 (예: 2일 이상된 파일)
find /var/backups \( -name "*.dump" -o -name "*.log" \) -type f -ctime +2 -delete

if [ -f "$DUMP_FILE" ]; then
    rm "$DUMP_FILE"
fi

# pg_dump로 ibs 스키마의 데이터만 추출 (django_migrations 제외)
pg_dump -n "${PGUSER}" \
  --data-only --exclude-table="${PGUSER}".django_migrations \
  --column-inserts -Fc -f "${DUMP_FILE}"

# 백업이 성공했는지 확인
if [ $? -ne 0 ]; then
    echo "PostgreSQL Backup failed." >&2
    exit 1
fi

echo "PostgreSQL Backup completed successfully: ${DUMP_FILE}"

# 퍼미션 변경
chmod 777 ${DUMP_FILE}
