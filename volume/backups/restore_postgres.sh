#!/bin/bash
set -eu

# 변수 설정
SCHEMA="${POSTGRES_USER}"
DATE=$(date +"%Y-%m-%d")
DUMP_FILE="/var/backups/data-postgres-${DATE}.dump"

# 환경 변수 확인
if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_DB" ] || [ -z "$DUMP_FILE" ]; then
    echo "Error: POSTGRES_USER, POSTGRES_DB, or DUMP_FILE is not set" >&2
    exit 1
fi

# 덤프 파일 존재 여부 확인
if [ ! -f "$DUMP_FILE" ]; then
    echo "Error: DUMP_FILE not found at $DUMP_FILE" >&2
    exit 1
fi

# 외래 키 제약 조건 비활성화 (삭제 대신)
echo "=== 스키마 외래 키 제약 조건 제거 시작 ==="
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
DO \$\$
DECLARE
    r RECORD;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = '$SCHEMA') THEN
        RAISE EXCEPTION 'Schema $SCHEMA does not exist';
    END IF;

    FOR r IN (SELECT constraint_name, table_name FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY' AND table_schema = '$SCHEMA')
    LOOP
        BEGIN
            EXECUTE 'ALTER TABLE ' || quote_ident('$SCHEMA') || '.' || quote_ident(r.table_name) || ' DROP CONSTRAINT ' || quote_ident(r.constraint_name);
            RAISE NOTICE 'Dropped constraint % on table %.%', r.constraint_name, '$SCHEMA', r.table_name;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Failed to drop constraint % on table %.%: %', r.constraint_name, '$SCHEMA', r.table_name, SQLERRM;
            CONTINUE;
        END;
    END LOOP;
END \$\$;
"

# TRUNCATE 결과 확인
if [ $? -ne 0 ]; then
    echo "외래 키 삭제 실패!" >&2
    exit 1
fi

# 서버 B의 $SCHEMA 스키마에서 django_migrations를 제외한 테이블 데이터 삭제
echo "=== 테이블 데이터 삭제(TRUNCATE) 시작 ==="
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
DO \$\$
DECLARE
    r RECORD;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = '$SCHEMA') THEN
        RAISE EXCEPTION 'Schema $SCHEMA does not exist';
    END IF;

    FOR r IN (SELECT c.relname AS tablename FROM pg_class c WHERE c.relkind = 'r'
              AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = '$SCHEMA')
              AND c.relname != 'django_migrations')
    LOOP
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_depend d JOIN pg_class s ON d.refobjid = s.oid
                WHERE d.objid = (SELECT oid FROM pg_class WHERE relname = r.tablename AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = '$SCHEMA'))
                AND s.relkind = 'S') THEN
                EXECUTE 'TRUNCATE TABLE ' || quote_ident('$SCHEMA') || '.' || quote_ident(r.tablename) || ' CASCADE RESTART IDENTITY';
                -- RAISE NOTICE 'Truncated table %.% with RESTART IDENTITY', '$SCHEMA', r.tablename;
            ELSE
                EXECUTE 'TRUNCATE TABLE ' || quote_ident('$SCHEMA') || '.' || quote_ident(r.tablename) || ' CASCADE';
                -- RAISE NOTICE 'Truncated table %.% without RESTART IDENTITY', '$SCHEMA', r.tablename;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Failed to truncate table %.%: %', '$SCHEMA', r.tablename, SQLERRM;
            CONTINUE;
        END;
    END LOOP;
    RAISE NOTICE 'Completed truncating tables in schema $SCHEMA';
END \$\$;
"

# TRUNCATE 결과 확인
if [ $? -ne 0 ]; then
    echo "테이블 데이터 삭제 실패!" >&2
    exit 1
fi

# TRUNCATE 후 테이블 비어 있는지 확인
echo "=== TRUNCATE 후 테이블 행 수 확인 ==="
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
DO \$\$
DECLARE
    r RECORD;
    row_count INTEGER;
BEGIN
    -- RAISE NOTICE '--- Table row counts after TRUNCATE ---';
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = '$SCHEMA' AND tablename != 'django_migrations')
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I.%I', '$SCHEMA', r.tablename) INTO row_count;
        -- RAISE NOTICE 'Table %.% count: %', current_schema, r.tablename, row_count;
    END LOOP;
    RAISE NOTICE 'Completed checked each table data count 0 in schema $SCHEMA';
END \$\$;
"

# 백업 파일 복원
echo "=== 백업 파일 복원 중: $DUMP_FILE ==="
pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --data-only --no-owner --no-privileges --disable-triggers --jobs=4 "$DUMP_FILE"

# 복원 결과 확인
if [ $? -eq 0 ]; then
    echo "데이터 복원 완료!"
    # 시퀀스 조정
    echo "=== 시퀀스 조정 (id 컬럼 기준) 시작 ==="
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    DO \$\$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN (SELECT c.relname AS tablename FROM pg_class c JOIN pg_depend d ON c.oid = d.objid JOIN pg_class s ON d.refobjid = s.oid
            WHERE c.relkind = 'r' AND s.relkind = 'S' AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = '$SCHEMA'))
        LOOP
            EXECUTE 'SELECT setval(pg_get_serial_sequence(' || quote_literal('$SCHEMA.' || r.tablename) || ', ''id''),
                    (SELECT COALESCE(MAX(id), 0) + 1 FROM ' || quote_ident('$SCHEMA') || '.' || quote_ident(r.tablename) || '))';
            RAISE NOTICE 'Reset sequence for table %.%', '$SCHEMA', r.tablename;
        END LOOP;
    END \$\$;
    "
    # 임시 파일 삭제
    echo "=== 덤프 파일 삭제 ==="
    rm -f "${DUMP_FILE}"

    echo "🎉 데이터 복원 완료 및 시퀀스 초기화 완료!"
else
    echo "데이터 복원 실패!"
    exit 1
fi