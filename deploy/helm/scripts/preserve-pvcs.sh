#!/bin/bash

# CloudNativePG Safe Uninstall Script
# CNPG 1.27.1에서는 persistentVolumeClaimPolicy 기능이 없으므로
# PVC의 ownerReferences를 제거한 후 Helm uninstall을 실행하여 데이터를 보존합니다.
#
# 사용법:
#   NAMESPACE=ibs-dev RELEASE=ibs ./preserve-pvcs.sh
#
# 참고: https://github.com/cloudnative-pg/cloudnative-pg/discussions/5253

set -e

# 환경 변수 설정
NAMESPACE="${NAMESPACE:-ibs-dev}"
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

# 2. PVC 목록 확인
echo "📋 Step 2: PVC 목록 확인..."
kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" -o name 2>/dev/null

PVC_COUNT=$(kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" --no-headers 2>/dev/null | wc -l)

if [ "$PVC_COUNT" -eq 0 ]; then
  echo ""
  echo "⚠️  CNPG PVC를 찾을 수 없습니다."
  echo ""
else
  echo ""

  # 3. PVC ownerReferences 제거
  echo "🔓 Step 3: PVC ownerReferences 제거 중..."
  for pvc in $(kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" -o name 2>/dev/null); do
    echo "  - $pvc"
    kubectl patch "$pvc" -n "$NAMESPACE" --type=json -p='[{"op": "remove", "path": "/metadata/ownerReferences"}]' 2>/dev/null || true
  done

  echo ""
  echo "✅ PVC 보존 준비 완료!"
  echo ""
fi

# 4. Helm uninstall 확인
echo "🗑️  Step 4: Helm Release Uninstall"
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

# 5. PVC 보존 확인
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
