#!/bin/bash
# CloudNativePG S3 즉시 백업(Base Backup) 트리거 스크립트
#
# 사용법:
#   sh manual-s3-backup.sh [dev|prod] [백업식별태그]
#   sh manual-s3-backup.sh prod post-reset
#   sh manual-s3-backup.sh dev
#
set -e

ENV_ARG="${1:-dev}"
TAG_ARG="${2:-manual}"

if [ "$ENV_ARG" = "prod" ]; then
  NAMESPACE="ibs-prod"
elif [ "$ENV_ARG" = "dev" ]; then
  NAMESPACE="ibs-dev"
else
  echo "❌ Error: Invalid environment '$ENV_ARG'. Use 'dev' or 'prod'."
  exit 1
fi

# 타임스탬프 기반 백업 이름 생성
DATE_TAG=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="s3-backup-${TAG_ARG}-${DATE_TAG}"

echo "=========================================="
echo "CloudNativePG Manual S3 Backup Trigger"
echo "=========================================="
echo "Namespace: $NAMESPACE"
echo "Backup Name: $BACKUP_NAME"
echo "----------------------------------------"

# 해당 네임스페이스의 실제 CNPG Cluster 이름 동적 감지
echo "🔍 Detecting CNPG cluster name in $NAMESPACE..."
CLUSTER_NAME=$(kubectl get cluster -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -z "$CLUSTER_NAME" ]; then
  echo "⚠️  Could not detect CNPG cluster automatically, falling back to 'postgres'"
  CLUSTER_NAME="postgres"
else
  echo "✅ Target CNPG Cluster: $CLUSTER_NAME"
fi

# 임시 yaml 생성 후 배포
TEMP_YAML=$(mktemp)
cat > "$TEMP_YAML" <<EOF
apiVersion: postgresql.cnpg.io/v1
kind: Backup
metadata:
  name: ${BACKUP_NAME}
  namespace: ${NAMESPACE}
spec:
  method: barmanObjectStore
  cluster:
    name: ${CLUSTER_NAME}
EOF

echo "🚀 Submitting Backup CRD to Kubernetes..."
kubectl apply -f "$TEMP_YAML"
rm "$TEMP_YAML"

echo "⏳ Waiting for backup initialization..."
sleep 5

# 진행 상태 추적
echo "----------------------------------------"
echo "🔍 Monitoring backup progress (Ctrl+C to exit monitoring, backup will run in background):"
echo "----------------------------------------"

while true; do
  STATUS=$(kubectl get backup "${BACKUP_NAME}" -n "${NAMESPACE}" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
  echo "[$(date +%H:%M:%S)] Backup Status: ${STATUS}"
  
  if [ "$STATUS" = "completed" ]; then
    echo "----------------------------------------"
    echo "✅ Success: CloudNativePG S3 Base Backup completed successfully!"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "----------------------------------------"
    echo "❌ Error: Backup failed. Please check CNPG operator logs."
    exit 1
  fi
  sleep 10
done
