#!/bin/bash
# CloudNativePG 수동 복원 스크립트
set -e

# 기본 설정
NAMESPACE="${NAMESPACE:-ibs-dev}"
RELEASE="${RELEASE:-ibs}"

echo "=========================================="
echo "CloudNativePG Manual Restore"
echo "=========================================="
echo "Namespace: $NAMESPACE"
echo "Release: $RELEASE"
echo ""

# 사용 가능한 백업 파일 목록 조회
echo "📋 Available backup files:"
echo "----------------------------------------"
BACKUP_POD=$(kubectl get pods -n "$NAMESPACE" -l "cnpg.io/cluster=${RELEASE}-postgres,role=primary" -o jsonpath='{.items[0].metadata.name}')

if [ -z "$BACKUP_POD" ]; then
    echo "❌ Error: No PostgreSQL primary pod found"
    exit 1
fi

# NFS 마운트된 백업 파일 확인 (임시 pod 사용)
echo "Checking backup files via temporary pod..."
kubectl run -n "$NAMESPACE" backup-list-tmp \
  --image=postgres:17.2 \
  --restart=Never \
  --rm -i --quiet \
  --overrides='
{
  "spec": {
    "containers": [{
      "name": "backup-list",
      "image": "postgres:17.2",
      "command": ["/bin/bash", "-c", "ls -lh /var/backups/*.dump 2>/dev/null || echo '\''No backup files found'\''"],
      "volumeMounts": [{
        "name": "backup-volume",
        "mountPath": "/var/backups"
      }]
    }],
    "volumes": [{
      "name": "backup-volume",
      "persistentVolumeClaim": {
        "claimName": "'"${RELEASE}"'-postgres-backup-pvc"
      }
    }]
  }
}' -- /bin/bash -c "ls -lh /var/backups/*.dump 2>/dev/null || echo 'No backup files found'"

echo ""
echo "=========================================="
echo "⚠️  WARNING: This will TRUNCATE all tables!"
echo "=========================================="
echo ""
read -p "Enter the backup filename to restore (e.g., ibs-backup-postgres-2025-01-15.dump): " BACKUP_FILE

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Error: No backup file specified"
    exit 1
fi

# 전체 경로 생성
if [[ ! "$BACKUP_FILE" =~ ^/ ]]; then
    BACKUP_FILE="/var/backups/$BACKUP_FILE"
fi

echo ""
echo "Restore settings:"
echo "  Backup file: $BACKUP_FILE"
echo "  Namespace: $NAMESPACE"
echo "  Release: $RELEASE"
echo ""
read -p "Are you sure you want to proceed? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Helm template으로 Job manifest 생성
echo ""
echo "Generating restore job manifest..."
TEMP_JOB=$(mktemp)

cat > "$TEMP_JOB" <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: ${RELEASE}-postgres-restore-$(date +%Y%m%d-%H%M%S)
  namespace: ${NAMESPACE}
spec:
  ttlSecondsAfterFinished: 86400
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: postgres-restore
        image: postgres:17.2
        command:
          - /bin/bash
          - -c
          - |
            set -eu

            DUMP_FILE="$BACKUP_FILE"

            if [ ! -f "\$DUMP_FILE" ]; then
                echo "❌ Error: Backup file not found: \$DUMP_FILE" >&2
                echo "Available backups:" >&2
                ls -lh /var/backups/*.dump 2>/dev/null || echo "No backup files found" >&2
                exit 1
            fi

            SCHEMA="ibs"
            DATE=\$(date +"%Y-%m-%d-%H%M%S")
            LOG_FILE="/var/backups/restore-\${DATE}.log"
            POSTGRES_DATABASE="ibs"
            POSTGRES_USER="postgres"
            POSTGRES_PASSWORD=\$(cat /run/secrets/postgres-password)
            PSQL_HOST="${RELEASE}-postgres-rw"

            echo "=== PostgreSQL Restore Started ===" | tee "\$LOG_FILE"
            echo "Backup file: \$DUMP_FILE" | tee -a "\$LOG_FILE"
            echo "Database: \$POSTGRES_DATABASE" | tee -a "\$LOG_FILE"
            echo "Schema: \$SCHEMA" | tee -a "\$LOG_FILE"
            echo "Host: \$PSQL_HOST" | tee -a "\$LOG_FILE"
            echo "" | tee -a "\$LOG_FILE"

            # 스키마 존재 확인
            echo "=== Checking schema existence ===" | tee -a "\$LOG_FILE"
            PGPASSWORD="\$POSTGRES_PASSWORD" psql -h "\$PSQL_HOST" -U "\$POSTGRES_USER" -d "\$POSTGRES_DATABASE" -c "
            DO \\\$\\\$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = '\$SCHEMA') THEN
                    RAISE EXCEPTION 'Schema \$SCHEMA does not exist';
                END IF;
                RAISE NOTICE 'Schema \$SCHEMA exists';
            END \\\$\\\$;
            " >> "\$LOG_FILE" 2>&1

            # 테이블 데이터 삭제
            echo "=== Truncating tables (excluding django_migrations) ===" | tee -a "\$LOG_FILE"
            PGPASSWORD="\$POSTGRES_PASSWORD" psql -h "\$PSQL_HOST" -U "\$POSTGRES_USER" -d "\$POSTGRES_DATABASE" -c "
            BEGIN;
            SET CONSTRAINTS ALL DEFERRED;

            DO \\\$\\\$
            DECLARE
                r RECORD;
                has_sequence BOOLEAN;
            BEGIN
                FOR r IN (SELECT c.relname AS tablename FROM pg_class c
                         WHERE c.relkind = 'r'
                         AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = '\$SCHEMA')
                         AND c.relname != 'django_migrations')
                LOOP
                    BEGIN
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_schema = '\$SCHEMA'
                            AND table_name = r.tablename
                            AND column_default LIKE 'nextval%'
                        ) INTO has_sequence;

                        IF has_sequence THEN
                            EXECUTE format('TRUNCATE TABLE %I.%I CASCADE RESTART IDENTITY', '\$SCHEMA', r.tablename);
                            RAISE NOTICE 'Truncated table %.% with RESTART IDENTITY', '\$SCHEMA', r.tablename;
                        ELSE
                            EXECUTE format('TRUNCATE TABLE %I.%I CASCADE', '\$SCHEMA', r.tablename);
                            RAISE NOTICE 'Truncated table %.%', '\$SCHEMA', r.tablename;
                        END IF;
                    EXCEPTION WHEN OTHERS THEN
                        RAISE WARNING 'Failed to truncate table %.%: %', '\$SCHEMA', r.tablename, SQLERRM;
                        CONTINUE;
                    END;
                END LOOP;
                RAISE NOTICE 'Completed truncating tables in schema \$SCHEMA';
            END \\\$\\\$;

            COMMIT;
            " >> "\$LOG_FILE" 2>&1

            if [ \$? -ne 0 ]; then
                echo "❌ Truncate failed! Check log: \$LOG_FILE" >&2
                cat "\$LOG_FILE" >&2
                exit 1
            fi

            # 백업 파일 복원
            echo "=== Restoring from backup file ===" | tee -a "\$LOG_FILE"
            PGPASSWORD="\$POSTGRES_PASSWORD" pg_restore \
              -h "\$PSQL_HOST" \
              -U "\$POSTGRES_USER" \
              -d "\$POSTGRES_DATABASE" \
              --data-only \
              --no-owner \
              --no-privileges \
              --disable-triggers \
              --jobs=4 \
              "\$DUMP_FILE" >> "\$LOG_FILE" 2>&1

            if [ \$? -eq 0 ]; then
                # 시퀀스 조정
                echo "=== Adjusting sequences ===" | tee -a "\$LOG_FILE"
                PGPASSWORD="\$POSTGRES_PASSWORD" psql -h "\$PSQL_HOST" -U "\$POSTGRES_USER" -d "\$POSTGRES_DATABASE" -c "
                DO \\\$\\\$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT c.relname AS tablename
                        FROM pg_class c
                        JOIN pg_depend d ON c.oid = d.objid
                        JOIN pg_class s ON d.refobjid = s.oid
                        WHERE c.relkind = 'r'
                        AND s.relkind = 'S'
                        AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = '\$SCHEMA')
                    )
                    LOOP
                        EXECUTE 'SELECT setval(pg_get_serial_sequence(' || quote_literal('\$SCHEMA.' || r.tablename) || ', ''id''),
                                (SELECT COALESCE(MAX(id), 0) + 1 FROM ' || quote_ident('\$SCHEMA') || '.' || quote_ident(r.tablename) || '))';
                        RAISE NOTICE 'Reset sequence for table %.%', '\$SCHEMA', r.tablename;
                    END LOOP;
                    RAISE NOTICE 'All sequences adjusted';
                END \\\$\\\$;
                " >> "\$LOG_FILE" 2>&1

                echo "" | tee -a "\$LOG_FILE"
                echo "🎉 PostgreSQL Restore completed successfully!" | tee -a "\$LOG_FILE"
                echo "Log file: \$LOG_FILE" | tee -a "\$LOG_FILE"
                exit 0
            else
                echo "❌ Restore failed! Check log: \$LOG_FILE" >&2
                cat "\$LOG_FILE" >&2
                exit 1
            fi
        env:
          - name: BACKUP_FILE
            value: "$BACKUP_FILE"
        volumeMounts:
          - name: backup-volume
            mountPath: /var/backups
          - name: postgres-password
            mountPath: /run/secrets
            readOnly: true
      volumes:
        - name: backup-volume
          persistentVolumeClaim:
            claimName: ${RELEASE}-postgres-backup-pvc
        - name: postgres-password
          secret:
            secretName: ${RELEASE}-postgres-superuser
            items:
              - key: password
                path: postgres-password
EOF

# Job 생성
echo "Creating restore job..."
JOB_NAME=$(kubectl apply -f "$TEMP_JOB" -o jsonpath='{.metadata.name}')
rm "$TEMP_JOB"

echo ""
echo "✅ Restore job created: $JOB_NAME"
echo ""
echo "Monitor progress with:"
echo "  kubectl get jobs -n $NAMESPACE"
echo "  kubectl logs -n $NAMESPACE job/$JOB_NAME -f"
echo ""

# 자동으로 로그 따라가기
echo "Following logs (Ctrl+C to stop)..."
echo "----------------------------------------"
kubectl wait --for=condition=ready pod -n "$NAMESPACE" -l "job-name=$JOB_NAME" --timeout=60s
kubectl logs -n "$NAMESPACE" -l "job-name=$JOB_NAME" -f