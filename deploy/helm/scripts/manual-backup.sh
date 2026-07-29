#!/bin/bash
# PostgreSQL DB Dump 수동 백업 및 로컬 다운로드 스크립트
#
# 사용법:
#   sh manual-backup.sh [dev|prod]
#   sh manual-backup.sh dev          # 기본값: dev
#   sh manual-backup.sh prod
#
# 결과:
#   프로젝트 루트의 volume/backups/ibs-backup-postgres-YYYY-MM-DD.dump 파일로 바로 다운로드됩니다.
#
set -e

ENV_ARG="${1:-dev}"

if [ "$ENV_ARG" = "prod" ]; then
  NAMESPACE="ibs-prod"
elif [ "$ENV_ARG" = "dev" ]; then
  NAMESPACE="ibs-dev"
else
  echo "❌ Error: Invalid environment '$ENV_ARG'. Use 'dev' or 'prod'."
  exit 1
fi

SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_PATH/../../.." && pwd)"
LOCAL_BACKUP_DIR="$PROJECT_ROOT/volume/backups"

mkdir -p "$LOCAL_BACKUP_DIR"

DATE_STR=$(date +"%Y-%m-%d")
DUMP_FILENAME="ibs-backup-postgres-${DATE_STR}.dump"
LOCAL_DUMP_PATH="${LOCAL_BACKUP_DIR}/${DUMP_FILENAME}"

echo "=========================================="
echo "PostgreSQL Local Dump Backup"
echo "=========================================="
echo "Environment : $ENV_ARG"
echo "Namespace   : $NAMESPACE"
echo "Target Path : $LOCAL_DUMP_PATH"
echo "=========================================="

# Primary Pod 찾기
CLUSTER_NAME=$(kubectl get cluster -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "postgres")
PRIMARY_POD=$(kubectl get cluster -n "$NAMESPACE" "$CLUSTER_NAME" -o jsonpath='{.status.currentPrimary}' 2>/dev/null || true)

if [ -z "$PRIMARY_POD" ]; then
  PRIMARY_POD=$(kubectl get pods -n "$NAMESPACE" -l "cnpg.io/cluster=$CLUSTER_NAME,cnpg.io/role=primary" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
fi

if [ -z "$PRIMARY_POD" ]; then
  PRIMARY_POD=$(kubectl get pods -n "$NAMESPACE" -l "cnpg.io/role=primary" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
fi

if [ -z "$PRIMARY_POD" ]; then
  echo "❌ Error: Cannot find primary postgres pod in namespace '$NAMESPACE'"
  exit 1
fi

echo "📌 Primary Pod: $PRIMARY_POD"

# DB 정보 자동 감지
DB_NAME=$(kubectl get cluster "$CLUSTER_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.bootstrap.initdb.database}' 2>/dev/null || echo "ibs")

echo ""
echo "🚀 Streaming pg_dump directly to local file..."
kubectl exec -n "$NAMESPACE" "$PRIMARY_POD" -c postgres -- \
  pg_dump -U postgres -d "$DB_NAME" -n ibs --data-only --exclude-table=ibs.django_migrations --column-inserts -Fc > "$LOCAL_DUMP_PATH"

echo ""
echo "=========================================="
echo "🎉 Local Dump Backup Completed Successfully!"
echo "=========================================="
echo "  File: $LOCAL_DUMP_PATH"
echo "  Size: $(du -sh "$LOCAL_DUMP_PATH" | cut -f1)"
echo "=========================================="