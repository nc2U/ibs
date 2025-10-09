#!/bin/bash
# Vue 프론트엔드 롤백 스크립트
# 사용법: ./rollback-vue.sh <build_number_sha>
# 예시: ./rollback-vue.sh 123_abc123def

set -e

STATIC_DIR="/path/to/ibs/prod/app/django/static"
NAMESPACE="ibs-prod"

# 컬러 출력
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 사용법 출력
usage() {
  echo -e "${YELLOW}사용법:${NC} $0 <build_timestamp>"
  echo ""
  echo "예시: $0 123_abc123def"
  echo ""
  echo -e "${GREEN}사용 가능한 빌드:${NC}"
  cd "$STATIC_DIR" 2>/dev/null || {
    echo -e "${RED}❌ 디렉터리를 찾을 수 없습니다: $STATIC_DIR${NC}"
    exit 1
  }
  ls -lth | grep "^d" | grep "dist_" | awk '{print $9, "(modified:", $6, $7, $8")"}'
  exit 1
}

# 인자 확인
if [ -z "$1" ]; then
  usage
fi

BUILD_TIMESTAMP="$1"
TARGET="dist_${BUILD_TIMESTAMP}"

echo -e "${YELLOW}🔄 Vue 프론트엔드 롤백 시작...${NC}"
echo ""

# 대상 디렉터리 존재 확인
cd "$STATIC_DIR"

if [ ! -d "$TARGET" ]; then
  echo -e "${RED}❌ 빌드를 찾을 수 없습니다: $TARGET${NC}"
  echo ""
  echo -e "${GREEN}사용 가능한 빌드:${NC}"
  ls -lth | grep "^d" | grep "dist_" | awk '{print $9, "(modified:", $6, $7, $8")"}'
  exit 1
fi

# 현재 배포된 버전 확인
CURRENT=$(readlink dist)
echo -e "${YELLOW}현재 배포:${NC} $CURRENT"
echo -e "${YELLOW}롤백 대상:${NC} $TARGET"
echo ""

# 확인 요청
read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo -e "${YELLOW}⚠️  롤백이 취소되었습니다.${NC}"
  exit 0
fi

# 심볼릭 링크 교체
echo ""
echo -e "${GREEN}📦 심볼릭 링크 교체 중...${NC}"
ln -sfn "$TARGET" dist.tmp
mv -Tf dist.tmp dist

# 배포 정보 출력
echo ""
echo -e "${GREEN}✅ 롤백 완료!${NC}"
if [ -f "$TARGET/deploy.json" ]; then
  echo ""
  echo -e "${GREEN}배포 정보:${NC}"
  cat "$TARGET/deploy.json"
fi

# Kubernetes Pod 재시작
echo ""
echo -e "${YELLOW}🔄 Kubernetes Pod 재시작 중...${NC}"
kubectl rollout restart deployment/nginx -n "$NAMESPACE"
kubectl rollout restart deployment/web -n "$NAMESPACE"

echo -e "${YELLOW}⏳ Pod 재시작 대기 중...${NC}"
kubectl rollout status deployment/nginx -n "$NAMESPACE" --timeout=120s
kubectl rollout status deployment/web -n "$NAMESPACE" --timeout=120s

echo ""
echo -e "${GREEN}✅ 모든 작업이 완료되었습니다!${NC}"
echo ""
echo -e "${GREEN}현재 배포된 빌드:${NC}"
ls -lth | grep "^d" | grep "dist_" | head -3
