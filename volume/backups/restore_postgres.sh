#!/bin/bash

# 복원 대상 파일 지정
DATE=$(date +"%Y-%m-%d")
DUMP_FILE="/var/backups/bu-postgres-${DATE}.dump"

pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -n ibs \
   --clean --if-exists --no-owner --no-privileges --disable-triggers \
   --exit-on-error -Fc "${SQL_FILE}"

# 복원 성공 여부 확인
if [ $? -eq 0 ]; then
    echo "POSTGRES Database restoration completed successfully: ${DUMP_FILE}"
else
    echo "POSTGRES Database restoration failed"
fi


# 서버 B의 ibs 스키마에서 django_migrations를 제외한 테이블 데이터 삭제
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
DO \$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'ibs' AND tablename != 'django_migrations')
    LOOP
        EXECUTE 'TRUNCATE TABLE $POSTGRES_USER.' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END \$\$;
"

# TRUNCATE 결과 확인
if [ $? -ne 0 ]; then
    echo "테이블 데이터 삭제 실패" >&2
    exit 1
fi

# 백업 파일 복원
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$DUMP_FILE"

# 복원 결과 확인
if [ $? -eq 0 ]; then
    echo "데이터 복원 완료"
else
    echo "데이터 복원 실패" >&2
    exit 1
fi

# 임시 파일 삭제
rm -f "$DUMP_FILE"