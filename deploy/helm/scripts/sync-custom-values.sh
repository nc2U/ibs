#!/usr/bin/env bash
set -e

# 사용법 안내
if [ -z "$1" ] || { [ "$1" != "prod" ] && [ "$1" != "dev" ]; }; then
  echo "Usage: $0 [prod|dev]"
  echo "Example: $0 prod"
  exit 1
fi

ENV="$1"

# 디렉터리 경로 계산
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"
HELM_DIR="$(cd "$SCRIPT_PATH/.." && pwd)"
DJANGO_DIR="$(cd "$HELM_DIR/../../app/django" && pwd)"
CUSTOM_VAL_FILE="$HELM_DIR/values-${ENV}-custom.yaml"

# 로컬 values-${ENV}-custom.yaml 존재 여부 확인
if [ ! -f "$CUSTOM_VAL_FILE" ]; then
  echo "Error: Local file not found: $CUSTOM_VAL_FILE"
  exit 1
fi

# .env 수동 로딩 (POSIX 호환)
if [ -f "$DJANGO_DIR/.env" ]; then
  while IFS='=' read -r key value || [ -n "$key" ]; do
    case "$key" in
      ''|\#*) ;; # Ignore blank lines or comments
      *)
        clean_key="$(echo "$key" | sed -e 's/^\s*//' -e 's/\s*$//')"
        clean_value=$(echo "$value" | sed -e 's/^\\s*[\"\\'\\']//' -e 's/[\"\\'\\']\\s*$//')
        export "$clean_key=$clean_value"
        ;;
    esac
  done < "$DJANGO_DIR/.env"
else
  echo "Error: .env file not found in $DJANGO_DIR"
  exit 1
fi

# 필수 환경변수 검증
if [ -z "$CICD_HOST" ] || [ -z "$CICD_USER" ] || [ -z "$CICD_PATH" ]; then
  echo "Error: CICD_HOST, CICD_USER, or CICD_PATH is not set in $DJANGO_DIR/.env"
  exit 1
fi

TARGET_DIR="${CICD_PATH}/${ENV}/deploy"
TARGET_FILE="${TARGET_DIR}/values-${ENV}-custom.yaml"
DEPLOY_HELM_DIR="${TARGET_DIR}/helm"

echo "==================================================="
echo " Syncing custom values to server (${ENV})"
echo " Local File  : $CUSTOM_VAL_FILE"
echo " Server Path : ${CICD_USER}@${CICD_HOST}:${TARGET_FILE}"
echo "==================================================="

# 1. 파일 SCP 전송
ssh-keyscan -H "$CICD_HOST" >> ~/.ssh/known_hosts 2>/dev/null || true
scp "$CUSTOM_VAL_FILE" "${CICD_USER}@${CICD_HOST}:${TARGET_FILE}"

# 2. 서버 디렉터리 생성 및 심볼릭 링크 연결
ssh "${CICD_USER}@${CICD_HOST}" "
  mkdir -p ${DEPLOY_HELM_DIR} && \
  cd ${DEPLOY_HELM_DIR} && \
  ln -sf ../values-${ENV}-custom.yaml ./values-${ENV}-custom.yaml && \
  echo 'Symlink created: values-${ENV}-custom.yaml -> ../values-${ENV}-custom.yaml'
"

echo "✅ Successfully synced values-${ENV}-custom.yaml to ${CICD_HOST}"
