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
# 디렉터리 경로 계산
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"
CURR_DIR="$(cd "$SCRIPT_PATH/.." && pwd)"
SCRIPT_DIR="$(cd "$CURR_DIR/../../app/django" && pwd)"

# 인자 파싱
ENV_ARG=""
AUTO_MODE=false
DIRECT_MODE=false

for arg in "$@"; do
  case "$arg" in
    --auto)
      AUTO_MODE=true
      ;;
    --direct)
      DIRECT_MODE=true
      ;;
    dev|prod)
      ENV_ARG="$arg"
      ;;
    *)
      echo "❌ Error: Invalid argument '$arg'"
      echo "Usage: $0 [dev|prod] [--auto] [--direct]"
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

# Dev 환경이고 --direct 모드가 아닐 경우 GitHub Actions (db_sync.yml) 트리거
if [ "$NAMESPACE" = "ibs-dev" ] && [ "$DIRECT_MODE" = false ]; then
  # .env 수동 로딩
  if [ -f "$SCRIPT_DIR/.env" ]; then
    while IFS='=' read -r key value || [ -n "$key" ]; do
      case "$key" in
        ''|\#*) ;;
        *)
          clean_key="$(echo "$key" | sed -e 's/^\s*//' -e 's/\s*$//')"
          clean_value=$(echo "$value" | sed -e 's/^\\s*[\"\\'\\']//' -e 's/[\"\\'\\']\\s*$//')
          export "$clean_key=$clean_value"
          ;;
      esac
    done < "$SCRIPT_DIR/.env"
  fi

  if [ -n "$GITHUB_TOKEN" ]; then
    echo "=========================================="
    echo "🚀 Triggering GitHub Actions: Database Dev Sync (db_sync.yml)"
    echo "=========================================="
    echo "This will restore DB data & sync S3 media files (ibs-media -> ibs-media-dev)."

    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer ${GITHUB_TOKEN}" \
      https://api.github.com/repos/austinkho/ibs/actions/workflows/db_sync.yml/dispatches \
      -d '{"ref":"develop"}')

    HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_STATUS" = "204" ]; then
      echo "✅ Successfully triggered GitHub Actions db_sync.yml!"
      echo "Check progress at: https://github.com/austinkho/ibs/actions"
      exit 0
    else
      echo "⚠️ Failed to trigger GitHub Actions (HTTP $HTTP_STATUS). Falling back to direct restore..."
    fi
  else
    echo "ℹ️ GITHUB_TOKEN is not set in .env. Proceeding with direct DB restore..."
  fi
fi

# 사용 가능한 백업 파일 목록 조회 (임시 pod 사용)
echo "📋 Available backup files:"
echo "----------------------------------------"
echo "Checking backup files via temporary pod..."

# 백업 파일 목록을 배열로 가져오기
BACKUP_POD_NAME="backup-list-$(date +%s)"
kubectl run -n "$NAMESPACE" "$BACKUP_POD_NAME" \
  --image=postgres:18.0 \
  --restart=Never \
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
}' >/dev/null 2>&1

kubectl wait --for=condition=Ready "pod/$BACKUP_POD_NAME" -n "$NAMESPACE" --timeout=15s >/dev/null 2>&1 || true
BACKUP_FILES=$(kubectl logs "$BACKUP_POD_NAME" -n "$NAMESPACE" 2>/dev/null || true)
kubectl delete pod "$BACKUP_POD_NAME" -n "$NAMESPACE" >/dev/null 2>&1 || true

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
CLUSTER_NAME=$(kubectl get cluster -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
if [ -z "$CLUSTER_NAME" ]; then
    CLUSTER_NAME="postgres"
fi

PRIMARY_POD=$(kubectl get cluster -n "$NAMESPACE" "$CLUSTER_NAME" -o jsonpath='{.status.currentPrimary}' 2>/dev/null || true)

if [ -z "$PRIMARY_POD" ]; then
    # 클러스터 status 조회가 실패할 경우를 대비한 레이블 기반 폴백
    PRIMARY_POD=$(kubectl get pods -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME,cnpg.io/role=primary" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
fi

if [ -z "$PRIMARY_POD" ]; then
    # 클러스터 이름이 다를 수 있으므로 cnpg.io/role=primary 필터만 사용하여 조회 시도
    PRIMARY_POD=$(kubectl get pods -n "$NAMESPACE" -l "cnpg.io/role=primary" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
fi

if [ -z "$PRIMARY_POD" ]; then
    # 이전 버전 레이블 기반 폴백
    PRIMARY_POD=$(kubectl get pods -n "$NAMESPACE" -l "cnpg.io/cluster=postgres,role=primary" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
fi

if [ -z "$PRIMARY_POD" ]; then
    echo "❌ Error: Cannot find primary postgres pod"
    exit 1
fi

echo "Primary pod: $PRIMARY_POD"

# Secret에서 비밀번호 읽기
EXPECTED_PASSWORD=$(kubectl get secret -n "$NAMESPACE" postgres-superuser -o jsonpath='{.data.password}' 2>/dev/null | base64 -d || true)

if [ -z "$EXPECTED_PASSWORD" ]; then
    EXPECTED_PASSWORD=$(kubectl get secret -n "$NAMESPACE" postgres-app -o jsonpath='{.data.password}' 2>/dev/null | base64 -d || true)
fi

if [ -z "$EXPECTED_PASSWORD" ]; then
    EXPECTED_PASSWORD="secret"
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


echo "Launching temporary restore pod with Synology NAS PVC ($BACKUP_PVC) mounted..."
echo "----------------------------------------"

# 기존 수동 복구 파드 정리
kubectl delete pod -n "$NAMESPACE" -l "app.kubernetes.io/component=manual-restore" > /dev/null 2>&1 || true

RESTORE_POD_NAME="postgres-manual-restore-$(date +%s)"
TEMP_POD_MANIFEST=$(mktemp)

cat > "$TEMP_POD_MANIFEST" << EOF
apiVersion: v1
kind: Pod
metadata:
  name: $RESTORE_POD_NAME
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/component: manual-restore
spec:
  restartPolicy: Never
  containers:
    - name: manual-restore
      image: postgres:18.0
      command:
        - /bin/bash
        - -c
        - |
          set -eu
          export PGDATABASE="ibs"
          export PGUSER="postgres"
          export PGPASSWORD="$EXPECTED_PASSWORD"
          export PSQL_HOST="postgres-rw"
          export DUMP_FILE="$BACKUP_FILE"
          export LOG_FILE="/var/backups/restore-\$(date +%Y-%m-%d-%H%M%S).log"

          echo "=== 테이블 데이터 삭제 및 복원 시작 ===" | tee -a "\$LOG_FILE"
          psql -h "\$PSQL_HOST" -U "\$PGUSER" -d "\$PGDATABASE" -c "
          BEGIN;
          SET CONSTRAINTS ALL DEFERRED;

          DO '
          BEGIN
              IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = ''\$PGDATABASE'') THEN
                  RAISE EXCEPTION ''Schema \$PGDATABASE does not exist'';
              END IF;
          END;';

          DO '
          DECLARE
              r RECORD;
              has_sequence BOOLEAN;
          BEGIN
              FOR r IN (SELECT c.relname AS tablename FROM pg_class c WHERE c.relkind = ''r''
                        AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = ''\$PGDATABASE'')
                        AND c.relname != ''django_migrations'')
              LOOP
                  BEGIN
                      SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = ''\$PGDATABASE''
                                    AND table_name = r.tablename AND column_default LIKE ''nextval%'') INTO has_sequence;
                      IF has_sequence THEN
                          EXECUTE format(''TRUNCATE TABLE %I.%I CASCADE RESTART IDENTITY'', ''\$PGDATABASE'', r.tablename);
                          RAISE NOTICE ''Truncated table %.% with RESTART IDENTITY'', ''\$PGDATABASE'', r.tablename;
                      ELSE
                          EXECUTE format(''TRUNCATE TABLE %I.%I CASCADE'', ''\$PGDATABASE'', r.tablename);
                          RAISE NOTICE ''Truncated table %.% without RESTART IDENTITY'', ''\$PGDATABASE'', r.tablename;
                      END IF;
                  EXCEPTION WHEN OTHERS THEN
                      RAISE WARNING ''Failed to truncate table %.%: %'', ''\$PGDATABASE'', r.tablename, SQLERRM;
                      CONTINUE;
                  END;
              END LOOP;
              RAISE NOTICE ''Completed truncating tables in schema \$PGDATABASE'';
          END;';

          COMMIT;
          " >> "\$LOG_FILE" 2>&1

          echo "=== 백업 파일 복원 중: \$DUMP_FILE ===" | tee -a "\$LOG_FILE"
          PGPASSWORD="\$PGPASSWORD" pg_restore -h "\$PSQL_HOST" -U "\$PGUSER" -d "\$PGDATABASE" --data-only --no-owner --no-privileges --disable-triggers --jobs=4 "\$DUMP_FILE" >> "\$LOG_FILE" 2>&1 || true

          echo "=== 시퀀스 조정 (id 컬럼 기준) 시작 ===" | tee -a "\$LOG_FILE"
          psql -h "\$PSQL_HOST" -U "\$PGUSER" -d "\$PGDATABASE" -c "
          SELECT concat('SELECT setval(pg_get_serial_sequence(''ibs.', tablename, ''', ''id''), COALESCE(MAX(id), 1)) FROM ibs.', tablename, ';')
          FROM pg_tables WHERE schemaname='ibs' AND tablename != 'django_migrations';
          " -t | psql -h "\$PSQL_HOST" -U "\$PGUSER" -d "\$PGDATABASE" >> "\$LOG_FILE" 2>&1 || true

          echo "🎉🎉🎉 데이터 복원 완료 및 시퀀스 초기화 완료! 🎉🎉🎉" | tee -a "\$LOG_FILE"
      volumeMounts:
        - name: backup-volume
          mountPath: /var/backups
  volumes:
    - name: backup-volume
      persistentVolumeClaim:
        claimName: $BACKUP_PVC
EOF

kubectl apply -f "$TEMP_POD_MANIFEST" > /dev/null
rm -f "$TEMP_POD_MANIFEST"

echo "Waiting for restore pod to start running..."
while true; do
  PHASE=$(kubectl get pod "$RESTORE_POD_NAME" -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || true)
  if [ "$PHASE" = "Running" ] || [ "$PHASE" = "Succeeded" ] || [ "$PHASE" = "Failed" ]; then
    break
  fi
  sleep 1
done

echo "Streaming logs from restore pod (Ctrl+C to stop view)..."
kubectl logs -n "$NAMESPACE" -f "pod/$RESTORE_POD_NAME"
RESTORE_STATUS=$?

echo "----------------------------------------"
if [ $RESTORE_STATUS -eq 0 ]; then
  echo "✅ Manual restore completed successfully!"
  kubectl delete pod "$RESTORE_POD_NAME" -n "$NAMESPACE" > /dev/null 2>&1 || true
else
  echo "❌ Manual restore failed!"
  echo "Inspect pod logs with: kubectl logs -n $NAMESPACE $RESTORE_POD_NAME"
  exit 1
fi