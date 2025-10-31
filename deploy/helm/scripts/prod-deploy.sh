#!/usr/bin/env bash

# .env 스크립트가 있는 디렉터리 경로 계산
# scripts/ -> helm/ 로 이동
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"
CURR_DIR="$(cd "$SCRIPT_PATH/.." && pwd)"
SCRIPT_DIR="$(cd "$CURR_DIR/../../app/django" && pwd)"

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

    # Role 적용 및 Helm 배포
    kubectl apply -f "$CURR_DIR/../kubectl/class-roles"
    cd "$CURR_DIR"
    helm upgrade ${DATABASE_USER} . -f ./values-prod-custom.yaml \
      --install -n ibs-prod --create-namespace --history-max 5 --wait --timeout 10m \
      --atomic --cleanup-on-fail
  else
    echo "values-prod-custom.yaml file not found in Current directory."
    exit 1
  fi
else
  echo ".env file not found in $SCRIPT_DIR"
  exit 1
fi
