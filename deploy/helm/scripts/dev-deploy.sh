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

  # values-dev-custom.yaml 존재 여부 확인
  if [ -e "$CURR_DIR/values-dev-custom.yaml" ]; then
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

    # Pending 락 및 이전 migration-job 자동 청소
    kubectl delete secret -n ibs-dev -l owner=helm,status=pending-upgrade --ignore-not-found=true 2>/dev/null || true
    kubectl delete job -n ibs-dev -l app.kubernetes.io/name=web --ignore-not-found=true 2>/dev/null || true
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
    helm upgrade ${RELEASE_NAME} . -f ./values-dev-custom.yaml \
      ${IMAGE_TAG_ARG} \
      --install -n ibs-dev --create-namespace --history-max 5
  else
    echo "values-dev-custom.yaml file not found in Current directory."
    exit 1
  fi
else
  echo ".env file not found in $SCRIPT_DIR"
  exit 1
fi

exit 0
