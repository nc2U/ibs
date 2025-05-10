#!/bin/bash

# 복원 대상 파일 지정
DATE=$(date +"%Y-%m-%d")
DUMP_FILE="/var/backups/data-postgres-${DATE}.dump"

# 외래 키 제약 조건 비활성화
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
DO \$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT constraint_name, table_name FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'ibs')
    LOOP
        EXECUTE 'ALTER TABLE ibs.' || quote_ident(r.table_name) || ' DROP CONSTRAINT ' || quote_ident(r.constraint_name);
    END LOOP;
END \$\$;
"

# 서버 B의 ibs 스키마에서 django_migrations를 제외한 테이블 데이터 삭제
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
DO \$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = '${POSTGRES_USER}' AND tablename != 'django_migrations')
    LOOP
        EXECUTE 'TRUNCATE TABLE ${POSTGRES_USER}.' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END \$\$;
"

# TRUNCATE 결과 확인
if [ $? -ne 0 ]; then
    echo "테이블 데이터 삭제 실패" >&2
    exit 1
fi

# 백업 파일 복원
pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --data-only --no-owner --no-privileges --disable-triggers --jobs=4 "$DUMP_FILE"

# 복원 결과 확인
if [ $? -eq 0 ]; then
    echo "데이터 복원 완료"
else
    echo "데이터 복원 실패" >&2
    exit 1
fi

# 임시 파일 삭제
rm -f "$DUMP_FILE"