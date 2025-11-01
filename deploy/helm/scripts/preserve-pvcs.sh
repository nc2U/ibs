#!/bin/bash

# CloudNativePG PVC Preservation Script
# CNPG 1.27.1에서는 persistentVolumeClaimPolicy 기능이 없으므로
# Helm uninstall 전에 PVC의 ownerReferences를 제거하여 보존합니다.
#
# 사용법:
#   NAMESPACE=ibs-dev CLUSTER_NAME=postgres ./preserve-pvcs.sh
#
# 참고: https://github.com/cloudnative-pg/cloudnative-pg/discussions/5253

set -e

# 환경 변수 설정
NAMESPACE="${NAMESPACE:-ibs-dev}"
CLUSTER_NAME="${CLUSTER_NAME:-postgres}"

echo "🔒 CloudNativePG PVC 보존 스크립트"
echo "===================================="
echo "Namespace: $NAMESPACE"
echo "Cluster: $CLUSTER_NAME"
echo ""

# PVC 목록 확인
echo "📋 현재 PVC 목록:"
kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" -o name

PVC_COUNT=$(kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" --no-headers 2>/dev/null | wc -l)

if [ "$PVC_COUNT" -eq 0 ]; then
  echo ""
  echo "⚠️  CNPG PVC를 찾을 수 없습니다."
  exit 0
fi

echo ""
echo "🔓 PVC ownerReferences 제거 중..."

# 모든 CNPG PVC의 ownerReferences 제거
for pvc in $(kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" -o name); do
  echo "  - $pvc"
  kubectl patch "$pvc" -n "$NAMESPACE" --type=json -p='[{"op": "remove", "path": "/metadata/ownerReferences"}]' 2>/dev/null || true
done

echo ""
echo "✅ 완료! 이제 helm uninstall을 실행해도 PVC가 보존됩니다."
echo ""
echo "📌 보존될 PVC 목록:"
kubectl get pvc -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME" -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.resources.requests.storage,STATUS:.status.phase

echo ""
echo "💡 다음 단계:"
echo "   1. helm uninstall ibs -n $NAMESPACE"
echo "   2. PVC 확인: kubectl get pvc -n $NAMESPACE | grep postgres"
echo "   3. 재설치: helm upgrade ibs . -f values-dev.yaml --install -n $NAMESPACE"
echo ""
echo "⚠️  주의: 재설치 시 CNPG가 기존 PVC를 자동으로 재사용합니다."
echo "   단, PV의 reclaimPolicy가 Retain이어야 데이터가 완전히 보존됩니다."
