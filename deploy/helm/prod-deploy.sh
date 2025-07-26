#!/bin/bash

# .env 스크립트가 있는 디렉터리 경로 계산
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../app/django"

# .env 파일 로드
if [ -f "$SCRIPT_DIR/.env" ]; then
  set -o allexport
  source "$SCRIPT_DIR/.env"
  set +o allexport

  if [ -e "./prod-values-custom.yaml" ] then
    if ! helm repo list | grep -q 'nfs-subdir-external-provisioner'; then
      helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner
    fi
    if ! helm status nfs-subdir-external-provisioner -n kube-system >/dev/null 2>&1; then
      helm upgrade --install nfs-subdir-external-provisioner \
        nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
          -n kube-system \
          --set nfs.server=${CICD_HOST} \
          --set nfs.path=/mnt/nfs-subdir-external-provisioner
    fi

    kubectl apply -f ../kubectl/class-roles;

    helm upgrade ${DATABASE_USER} . -f ./prod-values-custom.yaml \
      --install -n ibs-prod --create-namespace --history-max 5 --wait --timeout 10m
  else
    echo 'prod-values-custom.yaml 파일이 없습니다.'
  fi
else
  echo ".env 파일이 없습니다"
  exit 1
fi
