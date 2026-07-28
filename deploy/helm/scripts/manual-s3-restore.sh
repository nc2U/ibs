#!/bin/bash
# CloudNativePG S3 백업 기반 복원(Restore/PITR) 자동화 스크립트
#
# 사용법:
#   sh manual-s3-restore.sh [dev|prod] [복원타겟시점-KST]
#
# 예시:
#   1) 최신 시점으로 복원:
#      sh manual-s3-restore.sh prod
#
#   2) 특정 시점(KST 한국시간)으로 복원 (자동으로 UTC 변환 처리):
#      sh manual-s3-restore.sh prod "2026-07-25 15:30:00"
#
set -e

ENV_ARG="${1:-dev}"
TARGET_TIME_KST="${2:-}"

if [ "$ENV_ARG" = "prod" ]; then
  NAMESPACE="ibs-prod"
  RESTORE_CLUSTER_NAME="postgres-restored"
  S3_BUCKET="postgres-backup"
  SECRET_NAME="postgres-backup-s3"
  KEY_ACCESS="ACCESS_KEY_ID"
  KEY_SECRET="ACCESS_SECRET_KEY"
elif [ "$ENV_ARG" = "dev" ]; then
  NAMESPACE="ibs-dev"
  RESTORE_CLUSTER_NAME="postgres-restored"
  S3_BUCKET="postgres-backup-dev"
  SECRET_NAME="postgres-backup-s3"
  KEY_ACCESS="ACCESS_KEY_ID"
  KEY_SECRET="ACCESS_SECRET_KEY"
else
  echo "❌ Error: Invalid environment '$ENV_ARG'. Use 'dev' or 'prod'."
  exit 1
fi

echo "=========================================="
echo "CloudNativePG S3 Restore (PITR) Automation"
echo "=========================================="
echo "Namespace: $NAMESPACE"
echo "Target Cluster Name: $RESTORE_CLUSTER_NAME"

# S3 시크릿에서 자격증명 정보 동적 추출
echo "🔑 Reading S3 credentials from K8s secrets..."

if ! kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
  echo "❌ Error: Secret '$SECRET_NAME' not found in namespace '$NAMESPACE'."
  echo "Please make sure your CNPG S3 backup configuration is deployed first."
  exit 1
fi

S3_ACCESS_KEY=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath="{.data.$KEY_ACCESS}" | base64 -d)
S3_SECRET_KEY=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath="{.data.$KEY_SECRET}" | base64 -d)

# 복원 시점 설정 및 KST -> UTC 변환
RECOVERY_TARGET_SECTION=""
if [ -n "$TARGET_TIME_KST" ]; then
  echo "🕒 Target Recovery Time (KST): $TARGET_TIME_KST"
  
  # macOS/Linux 호환 날짜 변환 (UTC 기준 포맷팅)
  if date --version >/dev/null 2>&1; then
    # GNU date (Linux)
    TARGET_TIME_UTC=$(date -d "$TARGET_TIME_KST 9 hours ago" +"%Y-%m-%d %H:%M:%S")
  else
    # BSD date (macOS)
    TARGET_TIME_UTC=$(date -v-9H -j -f "%Y-%m-%d %H:%M:%S" "$TARGET_TIME_KST" +"%Y-%m-%d %H:%M:%S" 2>/dev/null || \
                      date -v-9h -j -f "%Y-%m-%d %H:%M:%S" "$TARGET_TIME_KST" +"%Y-%m-%d %H:%M:%S")
  fi
  
  echo "🕒 Translated Target Time (UTC): $TARGET_TIME_UTC"
  RECOVERY_TARGET_SECTION="recoveryTarget:
        targetTime: \"${TARGET_TIME_UTC}\""
fi

# 기존 복원 클러스터가 존재할 경우 충돌 방지를 위해 선제 삭제 안내
if kubectl get cluster "$RESTORE_CLUSTER_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
  echo "⚠️  Warning: Cluster '$RESTORE_CLUSTER_NAME' already exists."
  read -p "Do you want to delete the existing restored cluster first? (yes/no): " DELETE_CONFIRM
  if [ "$DELETE_CONFIRM" = "yes" ]; then
    echo "🗑️ Deleting existing restored cluster..."
    kubectl delete cluster "$RESTORE_CLUSTER_NAME" -n "$NAMESPACE"
    echo "Waiting for pods to terminate..."
    kubectl wait --for=delete pod -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" -n "$NAMESPACE" --timeout=5m || true
  else
    echo "❌ Restore cancelled."
    exit 0
  fi
fi

# 임시 yaml 생성 및 배포
TEMP_YAML=$(mktemp)
cat > "$TEMP_YAML" <<EOF
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: ${RESTORE_CLUSTER_NAME}
  namespace: ${NAMESPACE}
spec:
  instances: 1
  bootstrap:
    recovery:
      source: postgres-s3
      ${RECOVERY_TARGET_SECTION}
  externalClusters:
    - name: postgres-s3
      barmanObjectStore:
        destinationPath: s3://${S3_BUCKET}/postgres/
        endpointURL: https://s3.dyibs.com
        s3Credentials:
          accessKeyId:
            name: ${SECRET_NAME}
            key: ${KEY_ACCESS}
          secretAccessKey:
            name: ${SECRET_NAME}
            key: ${KEY_SECRET}
  storage:
    storageClass: nfs-client
    size: 1Gi
EOF

echo "🚀 Deploying Restore Cluster resource to Kubernetes..."
kubectl apply -f "$TEMP_YAML"
rm "$TEMP_YAML"

echo "⏳ Waiting for restore pod to initialize..."
sleep 5

# 진행 상태 추적
echo "----------------------------------------"
echo "🔍 Monitoring recovery progress (Ctrl+C to stop following logs):"
echo "----------------------------------------"
kubectl wait --for=condition=ready pod -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" -n "$NAMESPACE" --timeout=3m || true
kubectl logs -n "$NAMESPACE" -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" -c full-recovery -f --tail=50
