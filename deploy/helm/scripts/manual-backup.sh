#!/bin/bash
# CloudNativePG 수동 백업 스크립트 (Synology NAS PVC 백업 & 로컬 PC 다운로드 겸용)
#
# 사용법:
#   sh manual-backup.sh [dev|prod] [--local|-l]
#   sh manual-backup.sh prod              # 기본: K8s Job을 통해 시놀로지 NAS NFS 볼륨에 백업 저장
#   sh manual-backup.sh prod -l           # -l 또는 --local 옵션 시 개발자 로컬 PC (volume/backups/)에 백업 파일 저장
#   sh manual-backup.sh dev --local
#
set -e

ENV_ARG="dev"
IS_LOCAL=false

# 아규먼트 파싱
for arg in "$@"; do
  case "$arg" in
    prod|dev)
      ENV_ARG="$arg"
      ;;
    -l|--local)
      IS_LOCAL=true
      ;;
  esac
done

if [ "$ENV_ARG" = "prod" ]; then
  NAMESPACE="ibs-prod"
  ENV="prod"
  BACKUP_PVC="postgres-backup-prod-pvc"
elif [ "$ENV_ARG" = "dev" ]; then
  NAMESPACE="ibs-dev"
  ENV="dev"
  BACKUP_PVC="postgres-backup-dev-pvc"
else
  echo "❌ Error: Invalid environment '$ENV_ARG'"
  echo "Usage: $0 [dev|prod] [-l|--local]"
  exit 1
fi

RELEASE="${RELEASE:-ibs}"
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_PATH/../../.." && pwd)"

echo "=========================================="
echo "CloudNativePG Manual Backup"
echo "=========================================="
echo "Environment : $ENV"
echo "Namespace   : $NAMESPACE"
echo "Release     : $RELEASE"

if [ "$IS_LOCAL" = "true" ]; then
  LOCAL_BACKUP_DIR="$PROJECT_ROOT/volume/backups"
  mkdir -p "$LOCAL_BACKUP_DIR" 2>/dev/null || true
  DATE_STR=$(date +"%Y-%m-%d")
  DUMP_FILENAME="ibs-backup-postgres-${DATE_STR}.dump"
  LOCAL_DUMP_PATH="${LOCAL_BACKUP_DIR}/${DUMP_FILENAME}"
  echo "Target Mode : Local PC Download ($LOCAL_BACKUP_DIR)"
else
  echo "Target Mode : Synology NAS Storage ($BACKUP_PVC)"
fi
echo "=========================================="
echo ""

# Primary pod 찾기
CLUSTER_NAME=$(kubectl get cluster -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "postgres")
PRIMARY_POD=$(kubectl get cluster -n "$NAMESPACE" "$CLUSTER_NAME" -o jsonpath='{.status.currentPrimary}' 2>/dev/null || true)

if [ -z "$PRIMARY_POD" ]; then
  PRIMARY_POD=$(kubectl get pods -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME,cnpg.io/role=primary" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
fi

if [ -z "$PRIMARY_POD" ]; then
  PRIMARY_POD=$(kubectl get pods -n "$NAMESPACE" -l "cnpg.io/role=primary" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
fi

if [ -z "$PRIMARY_POD" ]; then
  echo "❌ Error: Cannot find primary postgres pod in namespace '$NAMESPACE'"
  exit 1
fi

echo "📌 Primary Pod: $PRIMARY_POD"

# DB 정보 자동 감지
DB_NAME=$(kubectl get cluster "$CLUSTER_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.bootstrap.initdb.database}' 2>/dev/null || true)
if [ -z "$DB_NAME" ]; then
  DB_NAME="ibs"
fi

# ---------------------------------------------------------
# 1. 로컬 PC 다운로드 백업 (-l / --local 옵션 지정 시)
# ---------------------------------------------------------
if [ "$IS_LOCAL" = "true" ]; then
  echo ""
  echo "🚀 Streaming pg_dump directly to local PC file (${LOCAL_DUMP_PATH})..."
  kubectl exec -n "$NAMESPACE" "$PRIMARY_POD" -c postgres -- \
    pg_dump -U postgres -d "$DB_NAME" -n ibs --data-only --exclude-table=ibs.django_migrations --column-inserts -Fc > "$LOCAL_DUMP_PATH"
  chmod 644 "$LOCAL_DUMP_PATH" 2>/dev/null || true

  echo ""
  echo "=========================================="
  echo "🎉 Local Dump Backup Completed Successfully!"
  echo "=========================================="
  echo "  File : $LOCAL_DUMP_PATH"
  echo "  Size : $(du -sh "$LOCAL_DUMP_PATH" | cut -f1)"
  echo "=========================================="
  exit 0
fi

# ---------------------------------------------------------
# 2. 시놀로지 NAS PVC 백업 (K8s Job 생성 - 기본 동작)
# ---------------------------------------------------------
JOB_NAME="postgres-backup-manual-$(date +%Y%m%d-%H%M%S)"
CRONJOB_NAME="postgres-backup"

# CronJob이 있으면 CronJob 기반으로 Job 실행
CRONJOB_CHECK=$(kubectl get cronjob -n "$NAMESPACE" "$CRONJOB_NAME" 2>&1 || true)
if echo "$CRONJOB_CHECK" | grep -q "NotFound" || [ -z "$CRONJOB_CHECK" ]; then
  echo "⚠️  CronJob not found, creating standalone backup job..."
  
  TEMP_JOB=$(mktemp)
  cat > "$TEMP_JOB" <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: ${JOB_NAME}
  namespace: ${NAMESPACE}
spec:
  ttlSecondsAfterFinished: 300
  template:
    metadata:
      labels:
        app.kubernetes.io/name: postgres
        app.kubernetes.io/component: backup
    spec:
      restartPolicy: OnFailure
      automountServiceAccountToken: false
      securityContext:
        fsGroup: 1026
      containers:
        - name: postgres-backup
          image: ghcr.io/cloudnative-pg/postgresql:18-bookworm
          imagePullPolicy: IfNotPresent
          securityContext:
            runAsUser: 1026
            runAsGroup: 100
          command:
            - /bin/bash
            - -c
            - |
              set -eu
              DATE=\$(date +"%Y-%m-%d-%H%M%S")
              DUMP_FILE=/var/backups/ibs-backup-postgres-\${DATE}.dump
              POSTGRES_SCHEMA="${DB_NAME}"
              POSTGRES_DATABASE="${DB_NAME}"
              POSTGRES_USER="app"
              POSTGRES_PASSWORD=\$(cat /run/secrets/postgres-password)
              PSQL_HOST="${CLUSTER_NAME}-rw"

              # 이전 백업 정리 (2일 이상 지난 파일)
              find /var/backups \( -name "*.dump" -o -name "*.log" \) -type f -mtime +2 -delete 2>/dev/null || true

              echo "Starting PostgreSQL backup: \${DUMP_FILE}"
              PGPASSWORD="\$POSTGRES_PASSWORD" pg_dump \\
                -h "\$PSQL_HOST" \\
                -U "\$POSTGRES_USER" \\
                -d "\$POSTGRES_DATABASE" \\
                -n "\$POSTGRES_SCHEMA" \\
                --data-only \\
                --exclude-table="\${POSTGRES_SCHEMA}.django_migrations" \\
                --column-inserts \\
                -Fc \\
                -f "\$DUMP_FILE"

              chmod 644 \${DUMP_FILE} 2>/dev/null || true
              echo "PostgreSQL Backup completed successfully: \${DUMP_FILE}"
              ls -lh "\$DUMP_FILE"
          volumeMounts:
            - name: backup-volume
              mountPath: /var/backups
            - name: postgres-password
              mountPath: /run/secrets
              readOnly: true
      volumes:
        - name: backup-volume
          persistentVolumeClaim:
            claimName: ${BACKUP_PVC}
        - name: postgres-password
          secret:
            secretName: ${CLUSTER_NAME}-app
            items:
              - key: password
                path: postgres-password
EOF

  if kubectl apply -f "$TEMP_JOB"; then
    rm -f "$TEMP_JOB"
    echo ""
    echo "✅ Backup job created successfully: ${JOB_NAME}"
    echo "Waiting for backup pod to start..."
    
    # 파드 생성 및 준비 상태 대기 로직 (에러 방지)
    POD_NAME=""
    for i in $(seq 1 30); do
      POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l "job-name=$JOB_NAME" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
      if [ -n "$POD_NAME" ]; then
        break
      fi
      sleep 1
    done

    if [ -n "$POD_NAME" ]; then
      echo "📌 Backup Pod: $POD_NAME"
      echo "----------------------------------------"
      # 파드가 Running 또는 Completed 상태가 될 때까지 기다린 후 안전하게 로그 출력
      kubectl wait --for=condition=Ready pod/"$POD_NAME" -n "$NAMESPACE" --timeout=60s 2>/dev/null || true
      kubectl logs -n "$NAMESPACE" pod/"$POD_NAME" -f 2>/dev/null || kubectl logs -n "$NAMESPACE" pod/"$POD_NAME"
    else
      echo "⚠️ Job created, but pod took longer to start. Check status with:"
      echo "   kubectl get jobs -n $NAMESPACE"
    fi
  else
    rm -f "$TEMP_JOB"
    echo "❌ Error: Failed to create backup job"
    exit 1
  fi
else
  echo "✅ CronJob '$CRONJOB_NAME' found, triggering job..."
  if kubectl create job -n "$NAMESPACE" "$JOB_NAME" --from="cronjob/$CRONJOB_NAME"; then
    echo ""
    echo "✅ Backup job created successfully: ${JOB_NAME}"
    echo "Following logs..."
    echo "----------------------------------------"
    kubectl wait --for=condition=ready pod -n "$NAMESPACE" -l "job-name=$JOB_NAME" --timeout=30s 2>/dev/null || true
    kubectl logs -n "$NAMESPACE" -l "job-name=$JOB_NAME" -f
  fi
fi