#!/bin/bash
set -e

# 스크립트 위치 기준 상대 경로 자동 계산
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 설정
BUILD_DIR="$PROJECT_ROOT/app/vue"
DEPLOY_BASE="$PROJECT_ROOT/app/django/static"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NEW_BUILD="dist_${TIMESTAMP}"
CURRENT_LINK="dist"

echo "🚀 Starting local build deployment..."
echo "📍 Project root: $PROJECT_ROOT"
echo ""

# 1. Vue 프로젝트 빌드
cd "$BUILD_DIR"
echo "📦 Building Vue project..."
pnpm build

# 2. 빌드 결과를 새 디렉터리로 이동
echo "📂 Moving build to ${NEW_BUILD}..."
mv "$DEPLOY_BASE/dist" "$DEPLOY_BASE/$NEW_BUILD"

# 3. 심볼릭 링크 원자적 교체
cd "$DEPLOY_BASE"
echo "🔗 Swapping symlink..."
ln -sfn "$NEW_BUILD" "${CURRENT_LINK}.tmp"
mv -Tf "${CURRENT_LINK}.tmp" "$CURRENT_LINK"

# 4. 오래된 빌드 디렉터리 정리 (최근 2개만 유지: 현재 + 이전)
echo "🧹 Cleaning old builds..."
ls -dt dist_* 2>/dev/null | tail -n +3 | xargs rm -rf 2>/dev/null || true

echo ""
echo "✅ Deployment completed successfully!"
echo "📊 Current builds:"
ls -lth | grep "^d" | grep "dist_" | head -3

echo ""
echo "💡 Tip: Restart Docker containers to apply changes:"
echo "   docker compose -f $PROJECT_ROOT/deploy/docker-compose.yml restart web"
