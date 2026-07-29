#!/usr/bin/env bash
set -e

# 사용법 안내
usage() {
  echo "Usage: $0 [prod|dev] [-u|--up|-d|--down|-c|--check]"
  echo "  -u, --up    : Sync local custom values to server (default)"
  echo "  -d, --down  : Download server custom values to local"
  echo "  -c, --check : Check and diff local vs server custom values"
  echo "Example:"
  echo "  $0 dev          # Upload to server (default)"
  echo "  $0 dev --down   # Download from server"
  echo "  $0 dev --check  # Check diff with server"
  exit 1
}

if [ -z "$1" ] || { [ "$1" != "prod" ] && [ "$1" != "dev" ]; }; then
  usage
fi

ENV="$1"
ACTION="up"

# 2번째 인자로 방향 감지
if [ -n "$2" ]; then
  case "$2" in
    -d|--down|--download) ACTION="down" ;;
    -u|--up|--upload)     ACTION="up" ;;
    -c|--check|--diff)    ACTION="check" ;;
    *) usage ;;
  esac
fi

# 디렉터리 경로 계산
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"
HELM_DIR="$(cd "$SCRIPT_PATH/.." && pwd)"
DJANGO_DIR="$(cd "$HELM_DIR/../../app/django" && pwd)"
CUSTOM_VAL_FILE="$HELM_DIR/values-${ENV}-custom.yaml"

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

ssh-keyscan -H "$CICD_HOST" >> ~/.ssh/known_hosts 2>/dev/null || true

if [ "$ACTION" = "check" ]; then
  echo "==================================================="
  echo " Checking diff: Local vs Server (${ENV})"
  echo " Local File  : $CUSTOM_VAL_FILE"
  echo " Server Path : ${CICD_USER}@${CICD_HOST}:${TARGET_FILE}"
  echo "==================================================="

  if [ ! -f "$CUSTOM_VAL_FILE" ]; then
    echo "Error: Local file not found: $CUSTOM_VAL_FILE"
    exit 1
  fi

  TEMP_SERVER_FILE=$(mktemp)
  if scp "${CICD_USER}@${CICD_HOST}:${TARGET_FILE}" "$TEMP_SERVER_FILE" >/dev/null 2>&1; then
    if diff -u "$CUSTOM_VAL_FILE" "$TEMP_SERVER_FILE" >/dev/null 2>&1; then
      echo "✅ Local and server custom values files are IDENTICAL!"
    else
      echo "⚠️  Differences found between local and server files:"
      echo "---------------------------------------------------"
      diff -u --color=auto "$CUSTOM_VAL_FILE" "$TEMP_SERVER_FILE" || true
      echo "---------------------------------------------------"
    fi
    rm -f "$TEMP_SERVER_FILE"
  else
    rm -f "$TEMP_SERVER_FILE"
    echo "❌ Error: Could not fetch target file from server."
    exit 1
  fi

elif [ "$ACTION" = "down" ]; then
  echo "==================================================="
  echo " Downloading custom values from server (${ENV})"
  echo " Server Path : ${CICD_USER}@${CICD_HOST}:${TARGET_FILE}"
  echo " Local File  : $CUSTOM_VAL_FILE"
  echo "==================================================="

  # 다운로드 전 기존 로컬 파일 안전 백업
  if [ -f "$CUSTOM_VAL_FILE" ]; then
    cp "$CUSTOM_VAL_FILE" "${CUSTOM_VAL_FILE}.bak"
    echo "  (Created local backup: values-${ENV}-custom.yaml.bak)"
  fi

  scp "${CICD_USER}@${CICD_HOST}:${TARGET_FILE}" "$CUSTOM_VAL_FILE"
  echo "✅ Successfully downloaded values-${ENV}-custom.yaml from ${CICD_HOST}"
else
  # 로컬 ➔ 서버 업로드 (기본값)
  if [ ! -f "$CUSTOM_VAL_FILE" ]; then
    echo "Error: Local file not found: $CUSTOM_VAL_FILE"
    exit 1
  fi

  echo "==================================================="
  echo " Syncing custom values to server (${ENV})"
  echo " Local File  : $CUSTOM_VAL_FILE"
  echo " Server Path : ${CICD_USER}@${CICD_HOST}:${TARGET_FILE}"
  echo "==================================================="

  # 1. 파일 SCP 전송
  scp "$CUSTOM_VAL_FILE" "${CICD_USER}@${CICD_HOST}:${TARGET_FILE}"

  # 2. 서버 디렉터리 생성 및 심볼릭 링크 연결
  ssh "${CICD_USER}@${CICD_HOST}" "
    mkdir -p ${DEPLOY_HELM_DIR} && \
    cd ${DEPLOY_HELM_DIR} && \
    ln -sf ../values-${ENV}-custom.yaml ./values-${ENV}-custom.yaml && \
    echo 'Symlink created: values-${ENV}-custom.yaml -> ../values-${ENV}-custom.yaml'
  "

  echo "✅ Successfully synced values-${ENV}-custom.yaml to ${CICD_HOST}"
fi
