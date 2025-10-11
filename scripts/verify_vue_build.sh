#!/bin/bash

# Vue 프로덕션 빌드 검증 스크립트
#
# ⚠️  주의: 이 스크립트는 로컬 개발 환경에서만 실행됩니다!
# - Kubernetes 컨테이너에서 실행하지 않음
# - 로컬에 Node.js 24 + pnpm 10 설치 필요
#
# 목적: 서버 배포 전 로컬에서 프로덕션 빌드를 테스트
# 실행: ./scripts/verify_vue_build.sh
#
# CI/CD에서의 검증은 GitHub Actions workflow에 포함되어 있음:
# - .github/workflows/vue_prod.yml (line 84-121)
# - .github/workflows/vue_dev.yml (line 86-123)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VUE_DIR="$PROJECT_ROOT/app/vue"
DIST_DIR="$PROJECT_ROOT/app/django/static/dist"

echo "🚀 Vue 프로덕션 빌드 검증 시작..."
echo "📂 프로젝트 경로: $PROJECT_ROOT"

# 1. 이전 빌드 정리
echo ""
echo "🧹 이전 빌드 정리..."
if [ -d "$DIST_DIR" ]; then
  rm -rf "$DIST_DIR"
  echo "  ✓ 이전 dist 디렉터리 삭제됨"
fi

# 2. 프로덕션 빌드 실행
echo ""
echo "🔨 NODE_ENV=production으로 빌드 중..."
cd "$VUE_DIR"

export NODE_ENV=production
pnpm build

if [ $? -ne 0 ]; then
  echo "❌ 빌드 실패!"
  exit 1
fi

echo "  ✓ 빌드 완료"

# 3. 빌드 결과 검증
echo ""
echo "🔍 빌드 결과 검증 중..."

cd "$DIST_DIR"

# 3.1 index.html 존재 확인
if [ ! -f "index.html" ]; then
  echo "  ❌ ERROR: index.html not found!"
  exit 1
fi
echo "  ✓ index.html 존재"

# 3.2 Base path 검증
if ! grep -q '/static/dist/assets/' index.html; then
  echo "  ❌ ERROR: Build base path incorrect!"
  echo "  Expected: /static/dist/assets/"
  echo "  Found:"
  grep -o 'src="[^"]*"' index.html | head -5
  exit 1
fi
echo "  ✓ Base path 올바름: /static/dist/assets/"

# 3.3 Assets 디렉터리 확인
if [ ! -d "assets" ]; then
  echo "  ❌ ERROR: assets directory not found!"
  exit 1
fi
echo "  ✓ Assets 디렉터리 존재"

# 3.4 필수 파일 확인
JS_FILES=$(find assets -name "index-*.js" | wc -l)
if [ "$JS_FILES" -eq 0 ]; then
  echo "  ❌ ERROR: No index JS files found!"
  exit 1
fi
echo "  ✓ JavaScript 파일 존재 ($JS_FILES 개)"

CSS_FILES=$(find assets -name "*.css" | wc -l)
if [ "$CSS_FILES" -eq 0 ]; then
  echo "  ❌ ERROR: No CSS files found!"
  exit 1
fi
echo "  ✓ CSS 파일 존재 ($CSS_FILES 개)"

# 3.5 Console.log 검사 (경고)
echo ""
echo "🔍 Console.log 검사..."
CONSOLE_LOGS=$(find assets -name "*.js" -exec grep -l 'console\.log' {} \; 2>/dev/null | wc -l)
if [ "$CONSOLE_LOGS" -gt 0 ]; then
  echo "  ⚠️  WARNING: Console logs found in $CONSOLE_LOGS files"
  echo "  Files with console.log:"
  find assets -name "*.js" -exec grep -l 'console\.log' {} \; 2>/dev/null
else
  echo "  ✓ Console logs 제거됨"
fi

# 3.6 Sourcemap 검사 (경고)
echo ""
echo "🔍 Sourcemap 검사..."
SOURCEMAPS=$(find assets -name "*.map" 2>/dev/null | wc -l)
if [ "$SOURCEMAPS" -gt 0 ]; then
  echo "  ⚠️  WARNING: Sourcemap files found ($SOURCEMAPS 개)"
else
  echo "  ✓ Sourcemap 파일 없음 (프로덕션 최적화)"
fi

# 4. 빌드 통계
echo ""
echo "📊 빌드 통계:"
INDEX_SIZE=$(wc -c < index.html)
TOTAL_FILES=$(find assets -type f | wc -l)
TOTAL_SIZE=$(du -sh assets 2>/dev/null | cut -f1)

echo "  • index.html: $INDEX_SIZE bytes"
echo "  • Total assets: $TOTAL_FILES files"
echo "  • Total size: $TOTAL_SIZE"

# 5. 샘플 파일 경로 출력
echo ""
echo "📄 생성된 파일 샘플:"
find assets -type f | head -10 | sed 's/^/  • /'

# 6. index.html에서 로드하는 리소스 확인
echo ""
echo "🔗 index.html이 참조하는 리소스:"
grep -o 'href="[^"]*"' index.html | head -5 | sed 's/^/  • /'
grep -o 'src="[^"]*"' index.html | head -5 | sed 's/^/  • /'

# 최종 결과
echo ""
echo "✅ 모든 검증 통과!"
echo ""
echo "📝 다음 단계:"
echo "  1. 로컬 Docker에서 테스트: docker compose up"
echo "  2. http://localhost 접속하여 UI 확인"
echo "  3. 개발자 도구 Network 탭에서 /static/dist/assets/ 경로 확인"
echo "  4. master 브랜치에 푸시하여 CI/CD 파이프라인 테스트"
echo ""
echo "🔧 참고: 현재 빌드 설정"
echo "  • NODE_ENV: production"
echo "  • base: /static/dist"
echo "  • minify: terser"
echo "  • drop_console: true"
echo "  • sourcemap: false"
