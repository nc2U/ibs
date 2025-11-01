#!/bin/bash
# CloudNativePG 수동 백업 스크립트
set -e

# 기본 설정
NAMESPACE="${NAMESPACE:-ibs-dev}"
RELEASE="${RELEASE:-ibs}"

echo "=========================================="
echo "CloudNativePG Manual Backup"
echo "=========================================="
echo "Namespace: $NAMESPACE"
echo "Release: $RELEASE"
echo ""

# CronJob 존재 확인
CRONJOB_NAME="postgres-backup"
if ! kubectl get cronjob -n "$NAMESPACE" "$CRONJOB_NAME" &>/dev/null; then
    echo "❌ Error: CronJob '$CRONJOB_NAME' not found in namespace '$NAMESPACE'"
    echo "Please deploy the Helm chart first."
    exit 1
fi

# Job 이름 생성 (타임스탬프 포함)
JOB_NAME="${CRONJOB_NAME}-manual-$(date +%Y%m%d-%H%M%S)"

echo "Creating backup job: $JOB_NAME"
kubectl create job -n "$NAMESPACE" "$JOB_NAME" --from="cronjob/$CRONJOB_NAME"

echo ""
echo "✅ Backup job created successfully!"
echo ""
echo "Monitor progress with:"
echo "  kubectl get jobs -n $NAMESPACE"
echo "  kubectl logs -n $NAMESPACE job/$JOB_NAME -f"
echo ""
echo "Check backup files:"
echo "  kubectl exec -n $NAMESPACE job/$JOB_NAME -- ls -lh /var/backups/"
echo ""

# 자동으로 로그 따라가기 (옵션)
if [ "${FOLLOW_LOGS:-true}" = "true" ]; then
    echo "Following logs (Ctrl+C to stop)..."
    echo "----------------------------------------"
    kubectl wait --for=condition=ready pod -n "$NAMESPACE" -l "job-name=$JOB_NAME" --timeout=30s
    kubectl logs -n "$NAMESPACE" -l "job-name=$JOB_NAME" -f
fi