#!/bin/bash

set -euo pipefail

# .env 스크립트가 있는 디렉터리 경로 계산
CURR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$(cd "$CURR_DIR/../../app/django" && pwd)"

# .env 파일 로드
if [ -f "$SCRIPT_DIR/.env" ]; then
  set -o allexport
  source "$SCRIPT_DIR/.env"
  set +o allexport
  echo "Loaded .env from $SCRIPT_DIR/.env"

  # 필수 환경변수 체크
  : "${CICD_HOST:?CICD_HOST is not set in .env}"
  : "${DATABASE_USER:?DATABASE_USER is not set in .env}"

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

    # Role 적용 및 Helm 배포
    kubectl apply -f ../kubectl/class-roles;
    helm upgrade ${DATABASE_USER} . -f ./values-dev-custom.yaml \
      --install -n ibs-dev --create-namespace --history-max 5 --wait --timeout 10m
  else
    echo "values-dev-custom.yaml file not found in $CURR_DIR."
    exit 1
  fi
else
  echo ".env file not found in $SCRIPT_DIR"
  exit 1
fi
