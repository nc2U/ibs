#!/bin/bash

# .env 스크립트가 있는 디렉터리 경로 계산
CURR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$(realpath "$CURR_DIR/../../app/django")"

# .env 파일 로드
if [ -f "$SCRIPT_DIR/.env" ]; then
  set -o allexport
  source "$SCRIPT_DIR/.env"
  set +o allexport
  echo "Loaded .env from $SCRIPT_DIR/.env"

  if [ -e "./values-prod-custom.yaml" ]; then
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

    helm upgrade ${DATABASE_USER} . -f ./values-prod-custom.yaml \
      --install -n ibs-prod --create-namespace --history-max 5 --wait --timeout 10m
  else
    echo "values-prod-custom.yaml file not found in $CURR_DIR."
  fi
else
  echo ".env file not found in $SCRIPT_DIR"
  exit 1
fi
