#!/bin/bash

# CloudNativePG Safe Uninstall Script
# CNPG 1.27.1에서는 persistentVolumeClaimPolicy 기능이 없으므로
# PVC의 ownerReferences를 제거한 후 Helm uninstall을 실행하여 데이터를 보존합니다.
#
# 사용법:
#   sh preserve-pvcs.sh [dev|prod]
#   sh preserve-pvcs.sh prod
#   sh preserve-pvcs.sh dev
#   sh preserve-pvcs.sh           # 기본값: dev
#
# 참고: https://github.com/cloudnative-pg/cloudnative-pg/discussions/5253

set -e

# 첫 번째 인자로 환경 설정
ENV_ARG="${1:-}"

# 환경 인자 처리
if [ -n "$ENV_ARG" ]; then
  if [ "$ENV_ARG" = "prod" ]; then
    NAMESPACE="ibs-prod"
  elif [ "$ENV_ARG" = "dev" ]; then
    NAMESPACE="ibs-dev"
  else
    echo "❌ Error: Invalid environment '$ENV_ARG'"
    echo "Usage: $0 [dev|prod]"
    echo "  dev  - Development environment (ibs-dev)"
    echo "  prod - Production environment (ibs-prod)"
    exit 1
  fi
else
  # 환경 변수로 설정 (기존 방식 호환)
  NAMESPACE="${NAMESPACE:-ibs-dev}"
fi

RELEASE="${RELEASE:-ibs}"
CLUSTER_NAME="${CLUSTER_NAME:-postgres}"

echo "🔒 CloudNativePG 안전한 Uninstall"
echo "===================================="
echo "Namespace: $NAMESPACE"
echo "Release: $RELEASE"
echo "Cluster: $CLUSTER_NAME"
echo ""

# 1. PV reclaimPolicy 확인 및 변경
echo "🔧 Step 1: PV reclaimPolicy 확인 중..."
for pvc in $(kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" -o name 2>/dev/null); do
  PV_NAME=$(kubectl get "$pvc" -n "$NAMESPACE" -o jsonpath='{.spec.volumeName}' 2>/dev/null)
  if [ -n "$PV_NAME" ]; then
    CURRENT_POLICY=$(kubectl get pv "$PV_NAME" -o jsonpath='{.spec.persistentVolumeReclaimPolicy}' 2>/dev/null)
    if [ "$CURRENT_POLICY" != "Retain" ]; then
      echo "  ⚠️  $PV_NAME: $CURRENT_POLICY → Retain 으로 변경"
      kubectl patch pv "$PV_NAME" -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}' >/dev/null
    else
      echo "  ✓ $PV_NAME: Retain (이미 설정됨)"
    fi
  fi
done

echo ""

# 2. 완료되지 않은 Job 삭제
echo "🧹 Step 2: 완료되지 않은 백업/복원 Job 확인 및 삭제..."
JOBS=$(kubectl get jobs -n "$NAMESPACE" -l "job-type in (backup,restore)" -o name 2>/dev/null || true)
if [ -n "$JOBS" ]; then
  echo "$JOBS" | while read -r job; do
    echo "  - 삭제 중: $job"
    kubectl delete "$job" -n "$NAMESPACE" 2>/dev/null || true
  done
  echo "  ✓ Job 정리 완료"
else
  echo "  ✓ 삭제할 Job이 없습니다"
fi

echo ""

# 3. PVC 목록 확인
echo "📋 Step 3: PVC 목록 확인..."
kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" -o name 2>/dev/null

PVC_COUNT=$(kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" --no-headers 2>/dev/null | wc -l)

if [ "$PVC_COUNT" -eq 0 ]; then
  echo ""
  echo "⚠️  CNPG PVC를 찾을 수 없습니다."
  echo ""
else
  echo ""

  # 4. PVC ownerReferences 제거
  echo "🔓 Step 4: PVC ownerReferences 제거 중..."
  for pvc in $(kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" -o name 2>/dev/null); do
    echo "  - $pvc"
    kubectl patch "$pvc" -n "$NAMESPACE" --type=json -p='[{"op": "remove", "path": "/metadata/ownerReferences"}]' 2>/dev/null || true
  done

  echo ""
  echo "✅ PVC 보존 준비 완료!"
  echo ""
fi

# 5. Helm uninstall 확인
echo "🗑️  Step 5: Helm Release Uninstall"
echo ""
read -p "정말로 '$RELEASE' 릴리즈를 삭제하시겠습니까? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo ""
  echo "❌ 취소되었습니다."
  exit 0
fi

echo ""
echo "⏳ Helm uninstall 실행 중..."
helm uninstall "$RELEASE" -n "$NAMESPACE"

echo ""
echo "✅ Uninstall 완료!"
echo ""

# 6. PVC 보존 확인
if [ "$PVC_COUNT" -gt 0 ]; then
  echo "📌 보존된 PVC 목록:"
  kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.resources.requests.storage,STATUS:.status.phase 2>/dev/null || echo "  (PVC가 삭제되었습니다)"
  echo ""
fi

echo "💡 다음 단계:"
echo "   1. PVC 확인: kubectl get pvc -n $NAMESPACE"
echo "   2. 재설치: helm upgrade $RELEASE . -f values-dev.yaml --install -n $NAMESPACE"
echo ""
echo "⚠️  참고: 재설치 시 CNPG가 기존 PVC를 자동으로 재사용하여 데이터가 복원됩니다."
