#!/usr/bin/env bash
set -e

# .env 스크립트가 있는 디렉터리 경로 계산
# scripts/ -> helm/ 로 이동
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"
CURR_DIR="$(cd "$SCRIPT_PATH/.." && pwd)"
SCRIPT_DIR="$(cd "$CURR_DIR/../../app/django" && pwd)"

# KUBECONFIG 위치 지정 (~/.kube/config 우선 참조)
if [ -f "$HOME/.kube/config" ]; then
  export KUBECONFIG="$HOME/.kube/config"
fi

RELEASE_NAME="${HELM_RELEASE_NAME:-ibs}"

# .env 수동 로딩 (POSIX 호환)
if [ -f "$SCRIPT_DIR/.env" ]; then
  while IFS='=' read -r key value || [ -n "$key" ]; do
    case "$key" in
      ''|\#*) ;; # Ignore blank lines or comments
      *)
        # Remove quotes and export
        clean_key="$(echo "$key" | sed -e 's/^\s*//' -e 's/\s*$//')"
        clean_value=$(echo "$value" | sed -e 's/^\\s*[\"\\'\\']//' -e 's/[\"\\'\\']\\s*$//')
        export "$clean_key=$clean_value"
        ;;
    esac
  done < "$SCRIPT_DIR/.env"

  # values-prod-custom.yaml 존재 여부 확인
  if [ -e "$CURR_DIR/values-prod-custom.yaml" ]; then
    # Helm repo 등록 여부 확인 후 추가
    if ! helm repo list | grep -q 'nfs-subdir-external-provisioner'; then
      helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner
    fi
    # Helm nfs-provisioner 설치 여부 확인 후 설치
    if ! helm status nfs-subdir-external-provisioner -n kube-system >/dev/null 2>&1; then
      helm upgrade --install nfs-subdir-external-provisioner \
        nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
          -n kube-system \
          --set nfs.server=${CICD_HOST} \
          --set nfs.path=/mnt/nfs-subdir-external-provisioner
    fi

    # Pending 락 및 이전 migration-job/pod 자동 강제 청소
    kubectl delete secret -n ibs-prod -l owner=helm,status=pending-upgrade --ignore-not-found=true 2>/dev/null || true
    kubectl delete job -n ibs-prod -l app.kubernetes.io/component=migration --ignore-not-found=true 2>/dev/null || true
    kubectl delete pod -n ibs-prod -l app.kubernetes.io/component=migration --ignore-not-found=true 2>/dev/null || true
    if kubectl get cluster postgres -n ibs-prod > /dev/null 2>&1; then
      kubectl label cluster postgres -n ibs-prod app.kubernetes.io/managed-by=Helm --overwrite || true
      kubectl annotate cluster postgres -n ibs-prod meta.helm.sh/release-name=${RELEASE_NAME} meta.helm.sh/release-namespace=ibs-prod --overwrite || true
      # spec.instances 필드를 직접 패치하여 "kubectl" -> "helm" field manager 소유권 강제 이전
      # (SSA 전체 re-apply는 값 변경 없는 필드의 소유권을 갱신하지 않는 문제가 있음)
      CURRENT_INST=$(kubectl get cluster postgres -n ibs-prod -o jsonpath='{.spec.instances}' 2>/dev/null || echo "3")
      kubectl patch cluster postgres -n ibs-prod \
        --server-side --force-conflicts --field-manager=helm --type=merge \
        -p "{\"spec\":{\"instances\":${CURRENT_INST}}}" 2>/dev/null || true
    fi
    kubectl apply -f "$CURR_DIR/../kubectl/class-roles"
    cd "$CURR_DIR"
    # IMAGE_TAG가 전달된 경우 --set으로 이미지 태그를 주입하여 Pod 롤아웃을 강제합니다.
    IMAGE_TAG_ARG=""
    if [ -n "${IMAGE_TAG:-}" ]; then
      IMAGE_TAG_ARG="--set web.image.tag=${IMAGE_TAG}"
      echo "Using image tag: ${IMAGE_TAG}"
    else
      echo "IMAGE_TAG not set, using default tag from values (latest)"
    fi
    helm upgrade ${RELEASE_NAME} . -f ./values-prod-custom.yaml \
      ${IMAGE_TAG_ARG} \
      --install -n ibs-prod --create-namespace --history-max 5
  else
    echo "values-prod-custom.yaml file not found in Current directory."
    exit 1
  fi
else
  echo ".env file not found in $SCRIPT_DIR"
  exit 1
fi

exit 0
