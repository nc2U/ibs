#!/bin/bash
# CloudNativePG 수동 복원 스크립트
#
# 사용법:
#   sh manual-restore.sh [dev|prod] [--auto]
#   sh manual-restore.sh prod         # 대화형 모드
#   sh manual-restore.sh dev          # 대화형 모드
#   sh manual-restore.sh dev --auto   # 자동 모드 (최신 백업 파일 사용)
#   sh manual-restore.sh              # 기본값: dev, 대화형
#
set -e

# 인자 파싱
ENV_ARG=""
AUTO_MODE=false

for arg in "$@"; do
  case "$arg" in
    --auto)
      AUTO_MODE=true
      ;;
    dev|prod)
      ENV_ARG="$arg"
      ;;
    *)
      echo "❌ Error: Invalid argument '$arg'"
      echo "Usage: $0 [dev|prod] [--auto]"
      exit 1
      ;;
  esac
done

# 환경 인자 처리
if [ -n "$ENV_ARG" ]; then
  if [ "$ENV_ARG" = "prod" ]; then
    NAMESPACE="ibs-prod"
  elif [ "$ENV_ARG" = "dev" ]; then
    NAMESPACE="ibs-dev"
  fi
else
  # 환경 변수로 설정 (기존 방식 호환)
  NAMESPACE="${NAMESPACE:-ibs-dev}"
fi

RELEASE="${RELEASE:-ibs}"

# 환경별 PVC 이름 설정 (Helm 템플릿 패턴 일치)
if [ "$NAMESPACE" = "ibs-prod" ]; then
  BACKUP_PVC="postgres-backup-prod-pvc"
else
  BACKUP_PVC="postgres-backup-dev-pvc"
fi

echo "=========================================="
echo "CloudNativePG Manual Restore"
echo "=========================================="
echo "Namespace: $NAMESPACE"
echo "Backup PVC: $BACKUP_PVC"
echo "Release: $RELEASE"
echo ""

# 사용 가능한 백업 파일 목록 조회 (임시 pod 사용)
echo "📋 Available backup files:"
echo "----------------------------------------"
echo "Checking backup files via temporary pod..."

# 백업 파일 목록을 배열로 가져오기
BACKUP_FILES=$(kubectl run -n "$NAMESPACE" backup-list-tmp \
  --image=postgres:18.0 \
  --restart=Never \
  --rm -i --quiet \
  --overrides='
{
  "spec": {
    "containers": [{
      "name": "backup-list",
      "image": "postgres:18.0",
      "command": ["/bin/bash", "-c", "ls -1 /var/backups/*.dump 2>/dev/null | xargs -n1 basename || echo '\''No backup files found'\''"],
      "volumeMounts": [{
        "name": "backup-volume",
        "mountPath": "/var/backups"
      }]
    }],
    "volumes": [{
      "name": "backup-volume",
      "persistentVolumeClaim": {
        "claimName": "'"$BACKUP_PVC"'"
      }
    }]
  }
}' -- /bin/bash -c "ls -1 /var/backups/*.dump 2>/dev/null | xargs -n1 basename || echo 'No backup files found'")

if [ -z "$BACKUP_FILES" ] || [ "$BACKUP_FILES" = "No backup files found" ]; then
    echo "❌ Error: No backup files found in /var/backups/"
    exit 1
fi

# 백업 파일 선택 로직
if [ "$AUTO_MODE" = true ]; then
  # 자동 모드: 가장 최신 백업 파일 선택
  echo ""
  echo "🤖 Auto mode: Selecting latest backup file..."

  LATEST_BACKUP=$(kubectl run -n "$NAMESPACE" backup-find-latest \
    --image=postgres:18.0 \
    --restart=Never \
    --rm -i --quiet \
    --overrides='
{
  "spec": {
    "containers": [{
      "name": "backup-find",
      "image": "postgres:18.0",
      "command": ["/bin/bash", "-c", "ls -1t /var/backups/*.dump 2>/dev/null | head -1 | xargs -n1 basename || echo '\''No backup files found'\''"],
      "volumeMounts": [{
        "name": "backup-volume",
        "mountPath": "/var/backups"
      }]
    }],
    "volumes": [{
      "name": "backup-volume",
      "persistentVolumeClaim": {
        "claimName": "'"$BACKUP_PVC"'"
      }
    }]
  }
}' -- /bin/bash -c "ls -1t /var/backups/*.dump 2>/dev/null | head -1 | xargs -n1 basename || echo 'No backup files found'")

  if [ -z "$LATEST_BACKUP" ] || [ "$LATEST_BACKUP" = "No backup files found" ]; then
    echo "❌ Error: No backup files found"
    exit 1
  fi

  BACKUP_FILE="/var/backups/$LATEST_BACKUP"
  echo "Selected: $BACKUP_FILE"
  echo ""
  echo "⚠️  WARNING: Auto mode will TRUNCATE all tables and restore!"
  echo "Proceeding in 3 seconds... (Ctrl+C to cancel)"
  sleep 3
else
  # 대화형 모드: 사용자가 파일 선택
  TEMP_LIST=$(mktemp)
  echo "$BACKUP_FILES" > "$TEMP_LIST"

  # 번호와 함께 파일 목록 출력
  echo ""
  echo "Select a backup file to restore:"
  i=1
  while IFS= read -r file; do
      [ -n "$file" ] && printf "%2d) %s\n" "$i" "$file"
      i=$((i+1))
  done < "$TEMP_LIST"

  TOTAL_FILES=$((i-1))

  echo ""
  echo "=========================================="
  echo "⚠️  WARNING: This will TRUNCATE all tables!"
  echo "=========================================="
  echo ""
  read -p "Enter number (1-$TOTAL_FILES) or 'q' to quit: " SELECTION

  if [ "$SELECTION" = "q" ] || [ "$SELECTION" = "Q" ]; then
      echo "Restore cancelled."
      rm "$TEMP_LIST"
      exit 0
  fi

  # 선택 검증
  if ! echo "$SELECTION" | grep -qE '^[0-9]+$' || [ "$SELECTION" -lt 1 ] || [ "$SELECTION" -gt "$TOTAL_FILES" ]; then
      echo "❌ Error: Invalid selection"
      rm "$TEMP_LIST"
      exit 1
  fi

  # 선택된 파일
  BACKUP_FILE="/var/backups/$(sed -n "${SELECTION}p" "$TEMP_LIST")"
  rm "$TEMP_LIST"

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
fi

# postgres 비밀번호 확인 및 설정
echo ""
echo "🔑 Verifying postgres password..."
echo "----------------------------------------"

# Primary pod 찾기
PRIMARY_POD=$(kubectl get pods -n "$NAMESPACE" -l "cnpg.io/cluster=postgres,role=primary" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$PRIMARY_POD" ]; then
    echo "❌ Error: Cannot find primary postgres pod"
    exit 1
fi

echo "Primary pod: $PRIMARY_POD"

# Secret에서 비밀번호 읽기
EXPECTED_PASSWORD=$(kubectl get secret -n "$NAMESPACE" postgres-superuser -o jsonpath='{.data.password}' 2>/dev/null | base64 -d)

if [ -z "$EXPECTED_PASSWORD" ]; then
    echo "❌ Error: Cannot read password from secret postgres-superuser"
    exit 1
fi

echo "Testing postgres authentication..."

# postgres 서비스로 연결 테스트
if kubectl exec -n "$NAMESPACE" "$PRIMARY_POD" -c postgres -- bash -c "PGPASSWORD='$EXPECTED_PASSWORD' psql -h postgres-rw -U postgres -d ibs -c 'SELECT 1;'" > /dev/null 2>&1; then
    echo "✅ postgres password is correct"
else
    echo "⚠️  postgres password mismatch detected"
    echo "🔧 Setting postgres password to match secret..."

    if kubectl exec -n "$NAMESPACE" "$PRIMARY_POD" -c postgres -- psql -U postgres -c "ALTER USER postgres WITH PASSWORD '$EXPECTED_PASSWORD';" > /dev/null 2>&1; then
        echo "✅ postgres password updated successfully"

        # 비밀번호 변경 후 재확인
        sleep 2
        if kubectl exec -n "$NAMESPACE" "$PRIMARY_POD" -c postgres -- bash -c "PGPASSWORD='$EXPECTED_PASSWORD' psql -h postgres-rw -U postgres -d ibs -c 'SELECT 1;'" > /dev/null 2>&1; then
            echo "✅ Password verified after update"
        else
            echo "❌ Error: Password verification failed after update"
            exit 1
        fi
    else
        echo "❌ Error: Failed to update postgres password"
        exit 1
    fi
fi

echo ""

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
  ttlSecondsAfterFinished: 300
  template:
    spec:
      restartPolicy: Never
      automountServiceAccountToken: false
      containers:
      - name: postgres-restore
        image: postgres:18.0
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
            PSQL_HOST="postgres-rw"

            echo "=== PostgreSQL Restore Started ===" | tee "\$LOG_FILE"
            echo "Backup file: \$DUMP_FILE" | tee -a "\$LOG_FILE"
            echo "Database: \$POSTGRES_DATABASE" | tee -a "\$LOG_FILE"
            echo "Schema: \$SCHEMA" | tee -a "\$LOG_FILE"
            echo "Host: \$PSQL_HOST" | tee -a "\$LOG_FILE"
            echo "" | tee -a "\$LOG_FILE"

            # 스키마 존재 확인 및 생성
            echo "=== Checking/Creating schema ===" | tee -a "\$LOG_FILE"
            PGPASSWORD="\$POSTGRES_PASSWORD" psql -h "\$PSQL_HOST" -U "\$POSTGRES_USER" -d "\$POSTGRES_DATABASE" -c "
            DO \\\$\\\$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = '\$SCHEMA') THEN
                    RAISE NOTICE 'Schema \$SCHEMA does not exist, creating...';
                    EXECUTE format('CREATE SCHEMA %I AUTHORIZATION ibs', '\$SCHEMA');
                    EXECUTE format('GRANT ALL ON SCHEMA %I TO ibs', '\$SCHEMA');
                    RAISE NOTICE 'Schema \$SCHEMA created successfully';
                ELSE
                    RAISE NOTICE 'Schema \$SCHEMA already exists';
                END IF;
            END \\\$\\\$;
            ALTER DATABASE \$POSTGRES_DATABASE SET search_path TO \$SCHEMA, public;
            " 2>&1 | tee -a "\$LOG_FILE"

            if [ \${PIPESTATUS[0]} -ne 0 ]; then
                echo "❌ Schema check/creation failed!" >&2
                cat "\$LOG_FILE" >&2
                exit 1
            fi

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
                         AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = '\$SCHEMA'))
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
            " 2>&1 | tee -a "\$LOG_FILE"

            if [ \${PIPESTATUS[0]} -ne 0 ]; then
                echo "❌ Truncate failed! Check log: \$LOG_FILE" >&2
                cat "\$LOG_FILE" >&2
                exit 1
            fi

            # 백업 파일 복원 (NFS 환경 고속화를 위해 단일 트랜잭션 적용)
            echo "=== Restoring from backup file ===" | tee -a "\$LOG_FILE"
            echo "Progress will be displayed below..." | tee -a "\$LOG_FILE"
            PGPASSWORD="\$POSTGRES_PASSWORD" pg_restore \
              -h "\$PSQL_HOST" \
              -U "\$POSTGRES_USER" \
              -d "\$POSTGRES_DATABASE" \
              --data-only \
              --no-owner \
              --no-privileges \
              --disable-triggers \
              --single-transaction \
              --verbose \
              "\$DUMP_FILE" 2>&1 | tee -a "\$LOG_FILE"

            RESTORE_EXIT_CODE=\${PIPESTATUS[0]}
            if [ \$RESTORE_EXIT_CODE -eq 0 ]; then
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
                " 2>&1 | tee -a "\$LOG_FILE"

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
            claimName: $BACKUP_PVC
        - name: postgres-password
          secret:
            secretName: postgres-superuser
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