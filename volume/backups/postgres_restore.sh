#!/bin/bash
set -eu

# 변수 설정
SCHEMA="${PGDATABASE}"
DATE=$(date +"%Y-%m-%d")
DUMP_FILE="/var/backups/ibs-backup-postgres-${DATE}.dump"
LOG_FILE="/var/backups/backup-${DATE}.log"

# 이전 백업 삭제 (예: 2일 이상된 파일)
find /var/backups \( -name "*.dump" -o -name "*.log" \) -type f -ctime +2 -delete

# 환경 변수 확인
if [ -z "$PGDATABASE" ] || [ -z "$DUMP_FILE" ]; then
    echo "Error: PGDATABASE, or DUMP_FILE is not set" >&2
    exit 1
fi

# 덤프 파일 존재 여부 확인
if [ ! -f "$DUMP_FILE" ]; then
    echo "Error: DUMP_FILE not found at $DUMP_FILE" >&2
    exit 1
fi

# 로그 파일 초기화
echo "=== Restore Log: ${DATE} ===" > "$LOG_FILE"

# 테이블 데이터 삭제(TRUNCATE) 및 복원을 트랜잭션 내에서 실행
echo "=== 테이블 데이터 삭제 및 복원 시작 ===" | tee -a "$LOG_FILE"
PGPASSWORD="$PGPASSWORD" psql -U "$PGUSER" -d "$PGDATABASE" -c "
BEGIN;
SET CONSTRAINTS ALL DEFERRED;

-- 스키마 존재 확인
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = '$SCHEMA') THEN
        RAISE EXCEPTION 'Schema $SCHEMA does not exist';
    END IF;
END \$\$;

-- django_migrations 제외한 테이블 TRUNCATE
DO \$\$
DECLARE
    r RECORD;
    has_sequence BOOLEAN;
BEGIN
    FOR r IN (SELECT c.relname AS tablename FROM pg_class c WHERE c.relkind = 'r'
              AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = '$SCHEMA')
              AND c.relname != 'django_migrations')
    LOOP
        BEGIN
            SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = '$SCHEMA'
                          AND table_name = r.tablename AND column_default LIKE 'nextval%') INTO has_sequence;
            IF has_sequence THEN
                EXECUTE format('TRUNCATE TABLE %I.%I CASCADE RESTART IDENTITY', '$SCHEMA', r.tablename);
                RAISE NOTICE 'Truncated table %.% with RESTART IDENTITY', '$SCHEMA', r.tablename;
            ELSE
                EXECUTE format('TRUNCATE TABLE %I.%I CASCADE', '$SCHEMA', r.tablename);
                RAISE NOTICE 'Truncated table %.% without RESTART IDENTITY', '$SCHEMA', r.tablename;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Failed to truncate table %.%: %', '$SCHEMA', r.tablename, SQLERRM;
            CONTINUE;
        END;
    END LOOP;
    RAISE NOTICE 'Completed truncating tables in schema $SCHEMA';
END \$\$;

COMMIT;
" >> "$LOG_FILE" 2>&1

# TRUNCATE 결과 확인
if [ $? -ne 0 ]; then
    echo "테이블 데이터 삭제 실패! 로그: $LOG_FILE" >&2
    cat "$LOG_FILE" >&2
    exit 1
fi

# TRUNCATE 후 테이블 비어 있는지 확인
echo "=== TRUNCATE 후 테이블 행 수 확인 ===" | tee -a "$LOG_FILE"
PGPASSWORD="$PGPASSWORD" psql -U "$PGUSER" -d "$PGDATABASE" -c "
DO \$\$
DECLARE
    r RECORD;
    row_count INTEGER;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = '$SCHEMA' AND tablename != 'django_migrations')
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I.%I', '$SCHEMA', r.tablename) INTO row_count;
        RAISE NOTICE 'Table %.% count: %', current_schema, r.tablename, row_count;
    END LOOP;
    RAISE NOTICE 'Completed checked each table data count 0 in schema $SCHEMA';
END \$\$;
" >> "$LOG_FILE" 2>&1

# 백업 파일 복원
echo "=== 백업 파일 복원 중: $DUMP_FILE ===" | tee -a "$LOG_FILE"
PGPASSWORD="$PGPASSWORD" pg_restore -U "$PGUSER" -d "$PGDATABASE" --data-only --no-owner --no-privileges --disable-triggers --jobs=4 "$DUMP_FILE" >> "$LOG_FILE" 2>&1
RESTORE_EXIT=$?
if [ $RESTORE_EXIT -ne 0 ]; then
    echo "⚠️  pg_restore exited with code $RESTORE_EXIT — checking for critical errors..." | tee -a "$LOG_FILE"
    CRITICAL_ERRORS=$(grep -i "^pg_restore: error:" "$LOG_FILE" | grep -v "already exists" || true)
    if [ -n "$CRITICAL_ERRORS" ]; then
        echo "❌ Critical restore errors detected:" | tee -a "$LOG_FILE"
        echo "$CRITICAL_ERRORS" | tee -a "$LOG_FILE"
        exit 1
    else
        echo "ℹ️  Only non-critical warnings found (e.g. already exists). Continuing..." | tee -a "$LOG_FILE"
    fi
fi

# 복원 결과 확인
if [ $RESTORE_EXIT -eq 0 ] || [ -z "$CRITICAL_ERRORS" ]; then
    # 시퀀스 조정
    echo "=== 시퀀스 조정 (id 컬럼 기준) 시작 ===" | tee -a "$LOG_FILE"
    PGPASSWORD="$PGPASSWORD" psql -U "$PGUSER" -d "$PGDATABASE" -c "
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
    " >> "$LOG_FILE" 2>&1

    # 복원 검증: 주요 테이블 건수 확인
    echo "=== 복원 검증: 주요 테이블 건수 확인 ===" | tee -a "$LOG_FILE"
    PGPASSWORD="$PGPASSWORD" psql -U "$PGUSER" -d "$PGDATABASE" -c "
    SELECT 'work_activitylogentry' AS table_name, COUNT(*) AS row_count FROM $SCHEMA.work_activitylogentry
    UNION ALL
    SELECT 'work_issuelogentry', COUNT(*) FROM $SCHEMA.work_issuelogentry
    UNION ALL
    SELECT 'work_issue', COUNT(*) FROM $SCHEMA.work_issue
    UNION ALL
    SELECT 'work_meeting', COUNT(*) FROM $SCHEMA.work_meeting
    UNION ALL
    SELECT 'accounts_user', COUNT(*) FROM $SCHEMA.accounts_user;
    " | tee -a "$LOG_FILE"

    # 임시 파일 삭제
    echo "=== 덤프 파일 삭제 ===" | tee -a "$LOG_FILE"
    rm -f "${DUMP_FILE}"

    echo "🎉🎉🎉 데이터 복원 완료 및 시퀀스 초기화 완료! 🎉🎉🎉" | tee -a "$LOG_FILE"
else
    echo "데이터 복원 실패! 로그: $LOG_FILE" >&2
    cat "$LOG_FILE" >&2
    exit 1
fi