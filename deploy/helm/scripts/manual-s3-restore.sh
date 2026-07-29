#!/bin/bash
# CloudNativePG S3 백업 기반 복원(Restore/PITR) 자동화 스크립트
#
# 사용법:
#   sh manual-s3-restore.sh [dev|prod] [복원타겟시점-KST] [storage-size] [s3-destination] [server-name]
#
# 예시:
#   1) 최신 시점으로 복원 (기본 storage 10Gi):
#      sh manual-s3-restore.sh prod
#
#   2) 특정 시점(KST 한국시간)으로 복원:
#      sh manual-s3-restore.sh prod "2026-07-25 15:30:00"
#
#   3) 특정 시점 + storage 크기 직접 지정:
#      sh manual-s3-restore.sh prod "2026-07-25 15:30:00" 20Gi
#
#   4) S3 경로 및 serverName 직접 지정 (mc ls로 실제 경로 확인 후 사용):
#      sh manual-s3-restore.sh dev "" 10Gi "s3://postgres-backup-dev/postgres" "postgres"
#
set -e

ENV_ARG="${1:-dev}"
TARGET_TIME_KST="${2:-}"
STORAGE_SIZE="${3:-10Gi}"
DESTINATION_OVERRIDE="${4:-}"  # 4번째 인자: S3 경로 직접 지정 (동적 감지 실패 시 사용)
SERVER_NAME_OVERRIDE="${5:-}"  # 5번째 인자: serverName 직접 지정 (원본 클러스터 이름)

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
echo "Environment    : $ENV_ARG"
echo "Namespace      : $NAMESPACE"
echo "Target Cluster : $RESTORE_CLUSTER_NAME"
echo "Storage Size   : $STORAGE_SIZE"

# S3 Secret 존재 여부 및 필수 키 포함 여부 검증
echo ""
echo "🔑 Verifying S3 credentials secret in K8s..."

if ! kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" > /dev/null 2>&1; then
  echo "❌ Error: Secret '$SECRET_NAME' not found in namespace '$NAMESPACE'."
  echo "   Please make sure your CNPG S3 backup configuration is deployed first."
  exit 1
fi

# 필수 키 포함 여부 확인 (실제 값은 CNPG 오퍼레이터가 직접 Secret 참조)
if ! kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" \
    -o jsonpath="{.data.${KEY_ACCESS}}" 2>/dev/null | grep -q .; then
  echo "❌ Error: Key '$KEY_ACCESS' not found in secret '$SECRET_NAME'."
  exit 1
fi

if ! kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" \
    -o jsonpath="{.data.${KEY_SECRET}}" 2>/dev/null | grep -q .; then
  echo "❌ Error: Key '$KEY_SECRET' not found in secret '$SECRET_NAME'."
  exit 1
fi

echo "✅ Secret '$SECRET_NAME' verified (keys: $KEY_ACCESS, $KEY_SECRET)"

# S3 destinationPath 결정 (우선순위: 4번째 인자 > 운영 Cluster 동적 감지 > 기본값)
echo ""
echo "📍 Resolving S3 backup destination path..."

if [ -n "$DESTINATION_OVERRIDE" ]; then
  S3_DESTINATION="$DESTINATION_OVERRIDE"
  echo "✅ Using explicitly specified destination: $S3_DESTINATION"
else
  ACTUAL_DESTINATION=$(kubectl get cluster -n "$NAMESPACE" \
    -o jsonpath='{.items[0].spec.backup.barmanObjectStore.destinationPath}' 2>/dev/null || true)

  if [ -n "$ACTUAL_DESTINATION" ]; then
    S3_DESTINATION="$ACTUAL_DESTINATION"
    echo "✅ Detected from running cluster: $S3_DESTINATION"
  else
    S3_DESTINATION="s3://${S3_BUCKET}/postgres"
    echo "⚠️  Could not detect from running cluster. Using fallback: $S3_DESTINATION"
  fi
fi

# serverName 결정
echo ""
echo "🏷️  Resolving source cluster serverName..."

if [ -n "$SERVER_NAME_OVERRIDE" ]; then
  SOURCE_SERVER_NAME="$SERVER_NAME_OVERRIDE"
  echo "✅ Using explicitly specified serverName: $SOURCE_SERVER_NAME"
else
  DETECTED_SERVER_NAME=$(kubectl get cluster -n "$NAMESPACE" \
    -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)

  if [ -n "$DETECTED_SERVER_NAME" ]; then
    SOURCE_SERVER_NAME="$DETECTED_SERVER_NAME"
    echo "✅ Detected from running cluster: $SOURCE_SERVER_NAME"
  else
    SOURCE_SERVER_NAME="postgres"
    echo "⚠️  Could not detect cluster name. Using fallback: $SOURCE_SERVER_NAME"
  fi
fi

echo "   → S3 lookup path: ${S3_DESTINATION}/${SOURCE_SERVER_NAME}/base/..."

# PostgreSQL Image 결정 (PG 18 기준 이미지 적용)
echo ""
echo "🐳 Resolving PostgreSQL image version..."

DETECTED_IMAGE=$(kubectl get cluster -n "$NAMESPACE" \
  -o jsonpath='{.items[0].spec.imageName}' 2>/dev/null || true)

if [ -n "$DETECTED_IMAGE" ]; then
  PG_IMAGE="$DETECTED_IMAGE"
  echo "✅ Detected from running cluster: $PG_IMAGE"
else
  PG_IMAGE="ghcr.io/cloudnative-pg/postgresql:18-bookworm"
  echo "⚠️  Could not detect image. Using default PG 18 image: $PG_IMAGE"
fi

# 복원 시점 설정 및 KST -> UTC 변환
RECOVERY_TARGET_YAML=""
if [ -n "$TARGET_TIME_KST" ]; then
  echo ""
  echo "🕒 Target Recovery Time (KST): $TARGET_TIME_KST"

  if date --version > /dev/null 2>&1; then
    TARGET_TIME_UTC=$(date -d "$TARGET_TIME_KST 9 hours ago" +"%Y-%m-%d %H:%M:%S")
  else
    TARGET_TIME_UTC=$(date -v-9H -j -f "%Y-%m-%d %H:%M:%S" "$TARGET_TIME_KST" +"%Y-%m-%d %H:%M:%S" 2>/dev/null || \
                      date -v-9h -j -f "%Y-%m-%d %H:%M:%S" "$TARGET_TIME_KST" +"%Y-%m-%d %H:%M:%S")
  fi

  echo "🕒 Translated Target Time (UTC): $TARGET_TIME_UTC"

  RECOVERY_TARGET_YAML="      recoveryTarget:
        targetTime: \"${TARGET_TIME_UTC}\""
else
  echo ""
  echo "🕒 No target time specified — restoring to latest available point."
fi

# 기존 복원 클러스터가 존재할 경우 충돌 방지를 위해 선제 삭제 안내
if kubectl get cluster "$RESTORE_CLUSTER_NAME" -n "$NAMESPACE" > /dev/null 2>&1; then
  echo ""
  echo "⚠️  Warning: Cluster '$RESTORE_CLUSTER_NAME' already exists in '$NAMESPACE'."
  printf "   Do you want to delete the existing restored cluster first? (yes/no): "
  read -r DELETE_CONFIRM
  if [ "$DELETE_CONFIRM" = "yes" ]; then
    echo "🗑️  Deleting existing restored cluster..."
    kubectl delete cluster "$RESTORE_CLUSTER_NAME" -n "$NAMESPACE"
    echo "   Waiting for pods to terminate (up to 5m)..."
    kubectl wait --for=delete pod -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" \
      -n "$NAMESPACE" --timeout=5m || true
    echo "✅ Existing cluster removed."
  else
    echo "❌ Restore cancelled by user."
    exit 0
  fi
fi

# 임시 yaml 생성 및 배포
TEMP_YAML=$(mktemp)

if [ -n "$RECOVERY_TARGET_YAML" ]; then
  cat > "$TEMP_YAML" << YAML_EOF
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: ${RESTORE_CLUSTER_NAME}
  namespace: ${NAMESPACE}
spec:
  instances: 1
  imageName: ${PG_IMAGE}
  bootstrap:
    recovery:
      source: postgres-s3
${RECOVERY_TARGET_YAML}
  externalClusters:
    - name: postgres-s3
      barmanObjectStore:
        destinationPath: ${S3_DESTINATION}
        serverName: ${SOURCE_SERVER_NAME}
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
    size: ${STORAGE_SIZE}
YAML_EOF
else
  cat > "$TEMP_YAML" << YAML_EOF
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: ${RESTORE_CLUSTER_NAME}
  namespace: ${NAMESPACE}
spec:
  instances: 1
  imageName: ${PG_IMAGE}
  bootstrap:
    recovery:
      source: postgres-s3
  externalClusters:
    - name: postgres-s3
      barmanObjectStore:
        destinationPath: ${S3_DESTINATION}
        serverName: ${SOURCE_SERVER_NAME}
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
    size: ${STORAGE_SIZE}
YAML_EOF
fi

echo ""
echo "🚀 Deploying Restore Cluster resource to Kubernetes..."
kubectl apply -f "$TEMP_YAML"
rm "$TEMP_YAML"

echo "⏳ Waiting for restore pod to be created by CNPG operator..."
POD_FOUND=false
for i in $(seq 1 30); do
  POD_COUNT=$(kubectl get pod -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" \
    -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l | tr -d ' ')
  if [ "$POD_COUNT" -gt 0 ]; then
    echo "✅ Restore pod detected (${POD_COUNT} pod(s)). Waiting for ready state..."
    POD_FOUND=true
    break
  fi
  echo "   [${i}/30] Pod not yet created, retrying in 10s..."
  sleep 10
done

if [ "$POD_FOUND" = "false" ]; then
  echo "⚠️  Pod did not appear within 5 minutes. Check cluster status:"
  echo "    kubectl describe cluster $RESTORE_CLUSTER_NAME -n $NAMESPACE"
  echo "    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'"
else
  # Pod 준비 대기 (최대 10분, 대용량 S3 복원 고려)
  kubectl wait --for=condition=ready pod -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" \
    -n "$NAMESPACE" --timeout=10m || true
fi

# 진행 상태 추적
echo ""
echo "----------------------------------------"
echo "🔍 Monitoring recovery progress (Ctrl+C to stop log tailing):"
echo "   Restore will continue running in background even if you stop."
echo "----------------------------------------"

POD_EXISTS=$(kubectl get pod -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" \
  -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l | tr -d ' ')

if [ "$POD_EXISTS" -gt 0 ]; then
  kubectl logs -n "$NAMESPACE" -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" \
    -c full-recovery -f --tail=50 || true
else
  echo "⚠️  No pods found. Check cluster events:"
  echo "    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | grep $RESTORE_CLUSTER_NAME"
  echo "    kubectl describe cluster $RESTORE_CLUSTER_NAME -n $NAMESPACE"
fi

# 복원 완료 후 서비스 전환 가이드
echo ""
echo "=========================================="
echo "📋 Post-Restore Checklist"
echo "=========================================="
echo ""
echo "  복원 클러스터: $RESTORE_CLUSTER_NAME (namespace: $NAMESPACE)"
echo "  현재 상태 확인:"
echo "    kubectl get cluster $RESTORE_CLUSTER_NAME -n $NAMESPACE"
echo "    kubectl get pods -l cnpg.io/cluster=$RESTORE_CLUSTER_NAME -n $NAMESPACE"
echo ""
echo "  ① 데이터 검증 (복원 DB 접속):"
echo "    kubectl exec -it \$(kubectl get pod -l cnpg.io/cluster=$RESTORE_CLUSTER_NAME \\"
echo "      -n $NAMESPACE -o name | head -1) -n $NAMESPACE -- psql -U postgres"
echo ""
echo "  ② 운영 서비스 전환이 필요한 경우 (선택):"
echo "    - Helm values에서 DB 연결 정보를 $RESTORE_CLUSTER_NAME 으로 변경 후 재배포"
echo "    - 또는 기존 postgres 클러스터 이름 변경 후 복원 클러스터를 postgres로 rename"
echo ""
echo "  ③ 복원 클러스터를 운영으로 격상 시 replication 인스턴스 수 확장:"
echo "    현재 instances: 1 → 운영 권장: instances: 3"
echo ""
echo "  ④ 복원 클러스터 정리 (검증 완료 후):"
echo "    kubectl delete cluster $RESTORE_CLUSTER_NAME -n $NAMESPACE"
echo ""
echo "=========================================="
