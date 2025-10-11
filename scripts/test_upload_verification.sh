#!/bin/bash

# 로컬에서 업로드 검증 스크립트 테스트
# GitHub Actions에서 실행되는 것과 동일한 로직

set -e  # 에러 발생 시 즉시 종료

# 테스트용 빌드 디렉터리 생성
TEST_DIR="/tmp/test_build_verification"
NEW_BUILD="$TEST_DIR/dist_test_12345"

mkdir -p "$NEW_BUILD/assets"
echo "<html></html>" > "$NEW_BUILD/index.html"
echo "body { color: red; }" > "$NEW_BUILD/assets/style.css"
echo "console.log('test');" > "$NEW_BUILD/assets/index-ABC123.js"

# 테스트용 index.html 내용 (JS 참조 포함)
cat > "$NEW_BUILD/index.html" <<'EOF'
<!DOCTYPE html>
<html>
<head>
  <script src="/static/dist/assets/index-ABC123.js"></script>
</head>
<body></body>
</html>
EOF

# 여러 개의 assets 파일 생성 (최소 10개 필요)
for i in {1..15}; do
  echo "// vendor $i" > "$NEW_BUILD/assets/vendor-$i.js"
done

echo "🧪 테스트 환경 준비 완료"
echo "   디렉터리: $NEW_BUILD"
echo ""

# ===== 실제 검증 스크립트 (GitHub Actions와 동일) =====

cd "$TEST_DIR"

echo "🔍 Verifying uploaded files for: $(basename $NEW_BUILD)"

if [ ! -d "$NEW_BUILD" ]; then
  echo "❌ ERROR: Build directory not found: $NEW_BUILD"
  exit 1
fi

if [ ! -f "$NEW_BUILD/index.html" ]; then
  echo "❌ ERROR: index.html not uploaded!"
  exit 1
fi

if [ ! -d "$NEW_BUILD/assets" ]; then
  echo "❌ ERROR: assets directory not uploaded!"
  exit 1
fi

ASSET_COUNT=$(find "$NEW_BUILD/assets" -type f 2>/dev/null | wc -l)
if [ "$ASSET_COUNT" -lt 10 ]; then
  echo "❌ ERROR: Too few assets uploaded ($ASSET_COUNT files)"
  exit 1
fi

MAIN_JS=$(grep -o 'assets/index-[^"]*\.js' "$NEW_BUILD/index.html" 2>/dev/null | head -1)
if [ -n "$MAIN_JS" ]; then
  if [ ! -f "$NEW_BUILD/$MAIN_JS" ]; then
    echo "❌ ERROR: Referenced main JS file missing: $MAIN_JS"
    exit 1
  fi
  echo "  ✓ Main JS verified: $MAIN_JS"
fi

CSS_COUNT=$(find "$NEW_BUILD/assets" -name "*.css" 2>/dev/null | wc -l)
if [ "$CSS_COUNT" -eq 0 ]; then
  echo "⚠️  WARNING: No CSS files found!"
else
  echo "  ✓ CSS files: $CSS_COUNT"
fi

echo "✅ Upload integrity verified"
echo "📊 Upload summary:"
echo "  - index.html: $(wc -c < $NEW_BUILD/index.html) bytes"
echo "  - Total assets: $ASSET_COUNT files"
echo "  - Total size: $(du -sh $NEW_BUILD 2>/dev/null | cut -f1)"

echo ""
echo "✅ 모든 테스트 통과!"
echo "   Exit code: $?"

# 정리
rm -rf "$TEST_DIR"
