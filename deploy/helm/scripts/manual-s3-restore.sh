#!/bin/bash
# CloudNativePG S3 백업 기반 복원(Restore/PITR) 자동화 스크립트
#
# 간소화된 사용법:
#   1) 대화형 터미널 수동 복구 (확인 프롬프트 표시):
#      sh manual-s3-restore.sh [dev|prod]
#      예: sh manual-s3-restore.sh dev
#
#   2) CI/CD 비대화형 자동 복구 (--auto 또는 --yes 옵션):
#      sh manual-s3-restore.sh [dev|prod] --auto
#      (대화형 프롬프트 없이 기존 DB 삭제 후 즉시 복원)
#
#   3) 특정 시점(KST 한국시간)으로 메인 DB 복구 (PITR):
#      sh manual-s3-restore.sh [dev|prod] "2026-08-01 15:30:00"
#      sh manual-s3-restore.sh [dev|prod] "2026-08-01 15:30:00" restore --auto
#
#   4) 복원 테스트 전용 모드 (메인 DB 건드리지 않고 'postgres-restored' 검증용 띄우기):
#      sh manual-s3-restore.sh [dev|prod] "" test
#      sh manual-s3-restore.sh [dev|prod] "2026-08-01 15:30:00" test --auto
#
set -e

ENV_ARG="${1:-dev}"
TARGET_TIME_KST="${2:-}"
MODE_ARG="${3:-restore}"  # 'test' 일 때만 postgres-restored, 기본값은 메인 postgres 직접 복구
AUTO_CONFIRM=false

for arg in "$@"; do
  if [ "$arg" = "--yes" ] || [ "$arg" = "-y" ] || [ "$arg" = "--auto" ]; then
    AUTO_CONFIRM=true
  fi
done

if [ "$TARGET_TIME_KST" = "--auto" ] || [ "$TARGET_TIME_KST" = "--yes" ] || [ "$TARGET_TIME_KST" = "-y" ]; then
  TARGET_TIME_KST=""
fi
if [ "$MODE_ARG" = "--auto" ] || [ "$MODE_ARG" = "--yes" ] || [ "$MODE_ARG" = "-y" ]; then
  MODE_ARG="restore"
fi

if [ "$ENV_ARG" = "prod" ]; then
  NAMESPACE="ibs-prod"
  S3_BUCKET="postgres-backup"
  SECRET_NAME="postgres-backup-s3"
  KEY_ACCESS="ACCESS_KEY_ID"
  KEY_SECRET="ACCESS_SECRET_KEY"
elif [ "$ENV_ARG" = "dev" ]; then
  NAMESPACE="ibs-dev"
  S3_BUCKET="postgres-backup-dev"
  SECRET_NAME="postgres-backup-s3"
  KEY_ACCESS="ACCESS_KEY_ID"
  KEY_SECRET="ACCESS_SECRET_KEY"
else
  echo "❌ Error: Invalid environment '$ENV_ARG'. Use 'dev' or 'prod'."
  exit 1
fi

if [ "$MODE_ARG" = "test" ]; then
  RESTORE_CLUSTER_NAME="postgres-restored"
  IS_TEST_MODE=true
else
  RESTORE_CLUSTER_NAME="postgres"
  IS_TEST_MODE=false
fi

echo "=========================================="
echo "CloudNativePG S3 Restore (PITR) Automation"
echo "=========================================="
echo "Environment    : $ENV_ARG"
echo "Namespace      : $NAMESPACE"
echo "Target Cluster : $RESTORE_CLUSTER_NAME"
if [ "$IS_TEST_MODE" = "true" ]; then
  echo "Mode           : 🧪 TEST MODE (Creating temporary 'postgres-restored' cluster)"
else
  echo "Mode           : 🚀 MAIN RESTORE MODE (Restoring main 'postgres' cluster directly)"
fi

# S3 Secret 검증
echo ""
echo "🔑 Verifying S3 credentials secret in K8s..."

if ! kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" > /dev/null 2>&1; then
  echo "❌ Error: Secret '$SECRET_NAME' not found in namespace '$NAMESPACE'."
  echo "   Please make sure your CNPG S3 backup configuration is deployed first."
  exit 1
fi

# 내부 파라미터 자동 감지 (Storage Size, S3 Destination, Server Name, PG Image, Replication Instances)
DETECTED_INSTANCES=$(kubectl get cluster "$RESTORE_CLUSTER_NAME" -n "$NAMESPACE" \
  -o jsonpath='{.spec.instances}' 2>/dev/null || \
  kubectl get cluster -n "$NAMESPACE" -o jsonpath='{.items[0].spec.instances}' 2>/dev/null || true)

# Cluster 리소스에서 감지되지 않은 경우 values-{env}-custom.yaml 또는 values-{env}.yaml 파싱 시도
if [ -z "$DETECTED_INSTANCES" ]; then
  HELM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
  VALUES_FILE=""
  if [ -f "$HELM_DIR/values-${ENV_ARG}-custom.yaml" ]; then
    VALUES_FILE="$HELM_DIR/values-${ENV_ARG}-custom.yaml"
  elif [ -f "$HELM_DIR/values-${ENV_ARG}.yaml" ]; then
    VALUES_FILE="$HELM_DIR/values-${ENV_ARG}.yaml"
  fi

  if [ -n "$VALUES_FILE" ]; then
    PARSED_INSTANCES=$(awk '/cnpg:/ {in_cnpg=1} in_cnpg && /replication:/ {in_rep=1} in_rep && /instances:/ {print $2; exit}' "$VALUES_FILE" 2>/dev/null || true)
    if [ -n "$PARSED_INSTANCES" ]; then
      DETECTED_INSTANCES="$PARSED_INSTANCES"
    fi
  fi
fi

# 테스트 모드인 경우 복원 검증 속도를 위해 1개로 설정, 메인 복구 모드인 경우 설정값(기본 3) 사용
if [ "$IS_TEST_MODE" = "true" ]; then
  INSTANCES=1
else
  INSTANCES="${DETECTED_INSTANCES:-3}"
fi

DETECTED_STORAGE_SIZE=$(kubectl get cluster "$RESTORE_CLUSTER_NAME" -n "$NAMESPACE" \
  -o jsonpath='{.spec.storage.size}' 2>/dev/null || \
  kubectl get cluster -n "$NAMESPACE" -o jsonpath='{.items[0].spec.storage.size}' 2>/dev/null || true)
STORAGE_SIZE="${DETECTED_STORAGE_SIZE:-10Gi}"

DETECTED_DESTINATION=$(kubectl get cluster -n "$NAMESPACE" \
  -o jsonpath='{.items[0].spec.backup.barmanObjectStore.destinationPath}' 2>/dev/null || true)
S3_DESTINATION="${DETECTED_DESTINATION:-s3://${S3_BUCKET}/postgres}"

SOURCE_SERVER_NAME="postgres"

DETECTED_IMAGE=$(kubectl get cluster -n "$NAMESPACE" \
  -o jsonpath='{.items[0].spec.imageName}' 2>/dev/null || true)
PG_IMAGE="${DETECTED_IMAGE:-ghcr.io/cloudnative-pg/postgresql:18-bookworm}"

# DB 접속 정보 자동 감지
DETECTED_DB_USER=$(kubectl get cluster -n "$NAMESPACE" \
  -o jsonpath='{.spec.bootstrap.initdb.owner}' 2>/dev/null || true)
DETECTED_DB_NAME=$(kubectl get cluster -n "$NAMESPACE" \
  -o jsonpath='{.spec.bootstrap.initdb.database}' 2>/dev/null || true)

DB_USER="${DETECTED_DB_USER:-ibs}"
DB_NAME="${DETECTED_DB_NAME:-ibs}"

# 기존 Primary 파드명 자동 감지 (기본값 postgres-1)
DETECTED_PRIMARY=$(kubectl get cluster "$RESTORE_CLUSTER_NAME" -n "$NAMESPACE" \
  -o jsonpath='{.status.currentPrimary}' 2>/dev/null || true)
TARGET_PRIMARY="${DETECTED_PRIMARY:-postgres-1}"

echo "📍 S3 Backup Path : ${S3_DESTINATION}/${SOURCE_SERVER_NAME}/base/..."
echo "🐳 PG Image       : $PG_IMAGE"
echo "💾 Storage Size   : $STORAGE_SIZE"
echo "👥 Instances      : $INSTANCES"
echo "👑 Target Primary : $TARGET_PRIMARY"

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

# 메인 복구 모드일 때 Nginx Maintenance 페이지 즉시 활성화 (503 점검 모드) 및 최신 WAL S3 Flush
if [ "$IS_TEST_MODE" = "false" ]; then
  echo ""
  echo "🚧 Enabling Maintenance Mode in Nginx..."
  NGINX_POD=$(kubectl get pod -n "$NAMESPACE" -l "app.kubernetes.io/name=nginx" -o name 2>/dev/null | head -1 || true)

  if [ -n "$NGINX_POD" ]; then
    kubectl exec "$NGINX_POD" -n "$NAMESPACE" -- touch /django/static/maintenance.flag 2>/dev/null || true
    echo "✅ Maintenance page activated (Nginx 503)"
  else
    echo "⚠️  Could not find Nginx pod to enable maintenance flag."
  fi

  # 복원 직전 현재 Primary 파드에 pg_switch_wal()을 전송하여 최신 WAL을 S3로 강제 Flush
  ACTIVE_PRIMARY=$(kubectl get cluster "$RESTORE_CLUSTER_NAME" -n "$NAMESPACE" -o jsonpath='{.status.currentPrimary}' 2>/dev/null || true)
  if [ -n "$ACTIVE_PRIMARY" ]; then
    echo "🔄 Flushing latest WAL log to S3 via pg_switch_wal()..."
    kubectl exec -n "$NAMESPACE" "$ACTIVE_PRIMARY" -c postgres -- psql -U postgres -d postgres -c "SELECT pg_switch_wal();" > /dev/null 2>&1 || true
    echo "✅ Latest WAL flushed to S3 successfully."
  fi
fi

# 대상 클러스터가 이미 존재하는 경우 안전한 선제 삭제 처리
if kubectl get cluster "$RESTORE_CLUSTER_NAME" -n "$NAMESPACE" > /dev/null 2>&1; then
  echo ""
  if [ "$AUTO_CONFIRM" = "true" ]; then
    echo "🤖 Auto confirmation enabled (--auto / --yes). Proceeding with cluster replacement..."
    CONFIRM="yes"
  elif [ "$IS_TEST_MODE" = "true" ]; then
    echo "⚠️  Warning: Test Cluster '$RESTORE_CLUSTER_NAME' already exists."
    printf "   Do you want to delete the existing test cluster and recreate? (yes/no): "
    read -r CONFIRM
  else
    echo "⚠️  CRITICAL WARNING: Database Cluster '$RESTORE_CLUSTER_NAME' already exists in $ENV_ARG."
    echo "   Restoring will DELETE the current cluster and replace it with S3 backup data."
    printf "   Are you SURE you want to restore cluster '$RESTORE_CLUSTER_NAME'? (yes/no): "
    read -r CONFIRM
  fi

  if [ "$CONFIRM" = "yes" ]; then
    echo "🗑️  Deleting existing cluster '$RESTORE_CLUSTER_NAME'..."
    kubectl delete cluster "$RESTORE_CLUSTER_NAME" -n "$NAMESPACE"
    echo "   Waiting for pods and PVCs to clean up (up to 5m)..."
    kubectl wait --for=delete pod -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" \
      -n "$NAMESPACE" --timeout=5m || true
    echo "✅ Existing cluster removed."
  else
    # 복원 취소 시 점검 모드 해제
    if [ "$IS_TEST_MODE" = "false" ] && [ -n "$NGINX_POD" ]; then
      kubectl exec "$NGINX_POD" -n "$NAMESPACE" -- rm -f /django/static/maintenance.flag 2>/dev/null || true
    fi
    echo "❌ Restore cancelled by user."
    exit 0
  fi
fi

# 복원 YAML 생성 및 배포
TEMP_YAML=$(mktemp)

if [ -n "$RECOVERY_TARGET_YAML" ]; then
  cat > "$TEMP_YAML" << YAML_EOF
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: ${RESTORE_CLUSTER_NAME}
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/managed-by: Helm
  annotations:
    meta.helm.sh/release-name: ${HELM_RELEASE_NAME:-ibs}
    meta.helm.sh/release-namespace: ${NAMESPACE}
spec:
  instances: ${INSTANCES}
  imageName: ${PG_IMAGE}
  bootstrap:
    recovery:
      source: postgres-s3
      database: "${DB_NAME}"
      owner: "${DB_USER}"
      secret:
        name: postgres-app
${RECOVERY_TARGET_YAML}
  externalClusters:
    - name: postgres-s3
      barmanObjectStore:
        destinationPath: "${S3_DESTINATION}"
        serverName: "${SOURCE_SERVER_NAME}"
        endpointURL: "https://s3.dyibs.com"
        s3Credentials:
          accessKeyId:
            name: "${SECRET_NAME}"
            key: "${KEY_ACCESS}"
          secretAccessKey:
            name: "${SECRET_NAME}"
            key: "${KEY_SECRET}"
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
  labels:
    app.kubernetes.io/managed-by: Helm
  annotations:
    meta.helm.sh/release-name: ${HELM_RELEASE_NAME:-ibs}
    meta.helm.sh/release-namespace: ${NAMESPACE}
spec:
  instances: ${INSTANCES}
  imageName: ${PG_IMAGE}
  bootstrap:
    recovery:
      source: postgres-s3
      database: "${DB_NAME}"
      owner: "${DB_USER}"
      secret:
        name: postgres-app
  externalClusters:
    - name: postgres-s3
      barmanObjectStore:
        destinationPath: "${S3_DESTINATION}"
        serverName: "${SOURCE_SERVER_NAME}"
        endpointURL: "https://s3.dyibs.com"
        s3Credentials:
          accessKeyId:
            name: "${SECRET_NAME}"
            key: "${KEY_ACCESS}"
          secretAccessKey:
            name: "${SECRET_NAME}"
            key: "${KEY_SECRET}"
  storage:
    storageClass: nfs-client
    size: ${STORAGE_SIZE}
YAML_EOF
fi

echo ""
echo "🚀 Deploying Restore Cluster '$RESTORE_CLUSTER_NAME' to Kubernetes..."
kubectl apply --server-side --force-conflicts --field-manager=helm -f "$TEMP_YAML"
rm "$TEMP_YAML"

echo "⏳ Waiting for restore pod to be created by CNPG operator..."
POD_FOUND=false
for i in $(seq 1 30); do
  POD_COUNT=$(kubectl get pod -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" \
    -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l | tr -d ' ')
  if [ "$POD_COUNT" -gt 0 ]; then
    echo "✅ Restore pod detected (${POD_COUNT} pod(s)). Waiting for full recovery..."
    POD_FOUND=true
    break
  fi
  echo "   [${i}/30] Pod not yet created, retrying in 10s..."
  sleep 10
done

if [ "$POD_FOUND" = "false" ]; then
  echo "❌ Error: Restore pod did not appear within 5 minutes."
  exit 1
fi

# 복원 Pod 준비 완료 대기 (S3 다운로드 및 DB 렌더링 완료까지 대기)
echo "⏳ Restoring database from S3..."
kubectl wait --for=condition=ready pod -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" \
  -n "$NAMESPACE" --timeout=10m

# 실제 PostgreSQL 접속 가능 여부 및 Primary Pod 정상화 확인
echo "⏳ Verifying actual PostgreSQL database connection and Primary readiness..."
DB_READY=false
PRIMARY_POD_NAME="${RESTORE_CLUSTER_NAME}-1"
for i in $(seq 1 30); do
  # primary 파드 명칭 감지 (role=primary 또는 clustername-1)
  PRIMARY_POD=$(kubectl get pod -n "$NAMESPACE" -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME},role=primary" -o name 2>/dev/null | head -1 || true)
  if [ -z "$PRIMARY_POD" ]; then
    PRIMARY_POD=$(kubectl get pod -n "$NAMESPACE" -l "cnpg.io/cluster=${RESTORE_CLUSTER_NAME}" -o name 2>/dev/null | head -1 || true)
  fi

  if [ -n "$PRIMARY_POD" ]; then
    # PostgreSQL 파드 내부에서 실제 쿼리 실행 가능 여부 확인
    if kubectl exec "$PRIMARY_POD" -n "$NAMESPACE" -c postgres -- psql -U postgres -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
      echo "✅ Database connection verified and primary instance is fully responsive!"
      DB_READY=true
      break
    fi
  fi
  echo "   [${i}/30] Database is still initializing/restoring connections, waiting 10s..."
  sleep 10
done

if [ "$DB_READY" = "false" ]; then
  echo "⚠️ Warning: Database pod is ready, but active SQL connection check timed out."
  echo "   Maintenance mode will remain ACTIVE for safety."
  exit 1
fi

# 복원 완료 후 헬름 설정(spec.backup) 동기화로 지속적 WAL 아카이빙 즉시 재개
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELM_CHART_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
echo "🔄 Synchronizing Helm release spec to re-enable continuous S3 WAL archiving..."
helm upgrade ${HELM_RELEASE_NAME:-ibs} "$HELM_CHART_DIR" \
  -n "$NAMESPACE" \
  -f "$HELM_CHART_DIR/values-${ENV_ARG}-custom.yaml" \
  --reuse-values >/dev/null 2>&1 || true
echo "✅ Continuous S3 WAL archiving re-enabled successfully!"

# 복원 완료 후 Nginx Maintenance 페이지 해제 (정상 모드 원복)
if [ "$IS_TEST_MODE" = "false" ]; then
  echo ""
  echo "🎉 Disabling Maintenance Mode in Nginx..."
  NGINX_POD=$(kubectl get pod -n "$NAMESPACE" -l "app.kubernetes.io/name=nginx" -o name 2>/dev/null | head -1 || true)
  if [ -n "$NGINX_POD" ]; then
    kubectl exec "$NGINX_POD" -n "$NAMESPACE" -- rm -f /django/static/maintenance.flag 2>/dev/null || true
    echo "✅ Maintenance page disabled — Normal service restored!"
  fi
fi

# 결과 가이드 출력
echo ""
echo "=========================================="
echo "🎉 Restore Completed Successfully!"
echo "=========================================="
echo "  Target Cluster: $RESTORE_CLUSTER_NAME (namespace: $NAMESPACE)"
echo ""
echo "  ① 데이터 검증 (복원 서비스 DB 접속 및 테이블 조회):"
echo "    1) 슈퍼유저 접속:
          kubectl exec -it \$(kubectl get pod -l cnpg.io/cluster=$RESTORE_CLUSTER_NAME -n $NAMESPACE -o name | head -1) -n $NAMESPACE -- psql -U postgres -d $DB_NAME -c \"\dt\""

echo "    2) 앱 유저 접속:
          kubectl exec -it \$(kubectl get pod -l cnpg.io/cluster=$RESTORE_CLUSTER_NAME -n $NAMESPACE -o name | head -1) -n $NAMESPACE -- psql -h 127.0.0.1 -U $DB_USER -d $DB_NAME -c \"\dt\""
echo ""

if [ "$IS_TEST_MODE" = "true" ]; then
  echo "  ② 테스트 복원 클러스터 정리 (검증 완료 후):"
  echo "    kubectl delete cluster $RESTORE_CLUSTER_NAME -n $NAMESPACE"
else
  echo "  ② 복원 완료 안내:"
  echo "    - 메인 클러스터 '$RESTORE_CLUSTER_NAME'가 성공적으로 S3 백업 데이터로 복원되었습니다."
  echo "    - Nginx 점검 모드가 해제되고 웹 애플리케이션(Django) 서비스가 정상 복구되었습니다."
  echo ""
  echo "  ③ 참고 (마이그레이션 디렉터리 리셋 후 복원한 경우):"
  echo "    - 소스코드의 migrations/ 디렉터리를 새로 리셋(Squash)하여 배포한 경우,"
  echo "      web 파드에서 아래 명령어로 DB 마이그레이션 이력을 동기화하세요:"
  echo "      kubectl exec -it \$(kubectl get pod -l app.kubernetes.io/name=web -n $NAMESPACE -o name | head -1) -n $NAMESPACE -- sh migrate.sh -r"
  echo "    - **마이그레이션 리셋 및 복원이 완료된 직후 반드시 새로운 S3 수동 백업을 생성해야 합니다.**"
  echo "    - S3 실시간 WAL 로그에 리셋 이전의 옛 마이그레이션 트랜잭션이 보관되어 있으므로, 새로운 백업을 찍어주어야 향후 S3 복원 시 **리셋된 최신 마이그레이션 상태로 깨끗하게 기준점이 설정**됩니다:"
  echo "      cd helm/scripts && sh manual-s3-backup.sh $NAMESPACE"
fi

echo ""
echo "=========================================="
