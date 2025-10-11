# 배포 프로세스 파일 무결성 분석

## 문제 상황
- **로컬**: 정상 동작
- **Kubernetes 프로덕션**: 다르게 동작
- **의심**: 심볼릭 링크 배포 과정에서 파일 누락/잘못된 참조

## 현재 배포 프로세스 (vue_prod.yml)

```
Step 1: GitHub Actions Runner (Ubuntu)
├─ pnpm build → ../django/static/dist_${timestamp}/
└─ 빌드 파일 생성 완료

Step 2: SCP 업로드 (line 135-144)
├─ source: 'app/django/static/dist_${timestamp}'
├─ target: '${CICD_PATH}/prod/app/django/static/'
└─ ⚠️  검증 없음

Step 3: 심볼릭 링크 교체 (line 147-173)
├─ ln -sfn dist_${timestamp} dist.tmp
├─ mv -Tf dist.tmp dist
├─ 구 빌드 정리: tail -n +3 | xargs -r rm -rf
└─ ⚠️  파일 무결성 검증 없음

Step 4: NFS sync 대기 (line 175-180)
└─ sleep 5

Step 5: 배포 검증 (line 182-193)
├─ dist/index.html 존재 확인
└─ ⚠️  assets 파일 검증 없음

Step 6: Pod 재시작 (line 195-211)
└─ kubectl rollout restart nginx, web
```

## 🚨 발견된 위험 요소

### 1. SCP 업로드 검증 부재 (🔴 Critical)

**현재 코드** (line 135-144):
```yaml
- name: Upload new build to server
  uses: appleboy/scp-action@master
  with:
    source: 'app/django/static/dist_${{ github.run_number }}_${{ github.sha }}'
    target: ${{ secrets.CICD_PATH }}/prod/app/django/static/
```

**문제점**:
- SCP 성공 != 모든 파일 업로드 완료
- 네트워크 문제로 일부 파일만 업로드될 수 있음
- 업로드된 파일 개수/크기 검증 없음

**증상**:
```
로컬: 빌드 시 100개 파일 생성
서버: SCP로 95개만 업로드 (5개 누락)
결과: index.html이 참조하는 파일 404
```

### 2. index.html vs assets 해시 불일치 위험

**Vite 빌드 구조**:
```
dist_${timestamp}/
├── index.html              # 참조: index-ABC123.js
├── assets/
│   ├── index-ABC123.js     # 실제 파일
│   ├── vendor-DEF456.js
│   └── ...
```

**위험 시나리오**:
1. 빌드 완료: index.html이 `index-ABC123.js` 참조
2. SCP 중 네트워크 지연
3. `index-ABC123.js` 업로드 실패
4. index.html만 업로드 성공
5. 결과: nginx가 404 반환

### 3. 심볼릭 링크 참조 깨짐 가능성

**현재 로직** (line 163-165):
```bash
NEW_BUILD="dist_123_abc"
ln -sfn "$NEW_BUILD" dist.tmp
mv -Tf dist.tmp dist
```

**문제 가능성**:
- `ln -sfn`은 상대 경로로 심볼릭 링크 생성
- 만약 `$NEW_BUILD` 디렉터리가 제대로 업로드 안 되면?
- 심볼릭 링크는 생성되지만 **깨진 링크**(broken symlink)

**검증 방법**:
```bash
# 심볼릭 링크가 실제 디렉터리를 가리키는지 확인
if [ ! -d "dist" ]; then
  echo "ERROR: Symlink is broken!"
fi
```

### 4. 구 빌드 정리 타이밍 위험 (⚠️ Medium)

**현재 로직** (line 168-169):
```bash
ls -dt dist_* 2>/dev/null | tail -n +3 | xargs -r rm -rf
```

**시나리오**:
```
시간순: dist_A (3일 전) → dist_B (1일 전) → dist_C (방금)

1. 심볼릭 링크: dist → dist_C
2. ls -dt: dist_C, dist_B, dist_A
3. tail -n +3: dist_A 삭제
4. 결과: 안전 (dist_C, dist_B 유지)
```

**하지만 문제 상황**:
```
만약 SCP가 dist_C 일부만 업로드하고:
1. 심볼릭 링크: dist → dist_C (불완전)
2. nginx가 dist_C에서 파일 못 찾음
3. dist_B는 아직 완전하지만 참조 안 됨
4. Rollback 불가 (이미 전환됨)
```

### 5. NFS 캐시/동기화 지연

**현재 대기** (line 177-179):
```bash
sleep 5
```

**문제**:
- NFS 서버와 Kubernetes Persistent Volume 간 동기화 시간 불확실
- 5초로 충분한지 보장 없음
- 네트워크 상황에 따라 변동

**더 나은 방법**:
```bash
# 실제 파일 존재 확인
TIMEOUT=30
for i in $(seq 1 $TIMEOUT); do
  if [ -f "${CICD_PATH}/prod/app/django/static/dist/index.html" ]; then
    echo "NFS sync confirmed"
    break
  fi
  sleep 1
done
```

## ✅ 해결 방안

### 1. SCP 후 파일 무결성 검증 추가

```yaml
- name: Verify upload integrity
  uses: garygrossgarten/github-action-ssh@release
  with:
    command: |
      cd ${{ secrets.CICD_PATH }}/prod/app/django/static
      NEW_BUILD="dist_${{ github.run_number }}_${{ github.sha }}"

      echo "🔍 Verifying uploaded files..."

      # index.html 존재 확인
      if [ ! -f "$NEW_BUILD/index.html" ]; then
        echo "❌ ERROR: index.html not uploaded!"
        exit 1
      fi

      # assets 디렉터리 확인
      if [ ! -d "$NEW_BUILD/assets" ]; then
        echo "❌ ERROR: assets directory not uploaded!"
        exit 1
      fi

      # assets 파일 개수 확인 (최소 기대값)
      ASSET_COUNT=$(find "$NEW_BUILD/assets" -type f | wc -l)
      if [ "$ASSET_COUNT" -lt 10 ]; then
        echo "❌ ERROR: Too few assets uploaded ($ASSET_COUNT)"
        exit 1
      fi

      # index.html이 참조하는 주요 파일 존재 확인
      MAIN_JS=$(grep -o 'src="/static/dist/assets/index-[^"]*\.js"' "$NEW_BUILD/index.html" | head -1 | sed 's|.*/||' | sed 's/"$//')
      if [ -n "$MAIN_JS" ] && [ ! -f "$NEW_BUILD/assets/$MAIN_JS" ]; then
        echo "❌ ERROR: Referenced file missing: $MAIN_JS"
        exit 1
      fi

      echo "✅ Upload integrity verified"
      echo "  - index.html: $(wc -c < $NEW_BUILD/index.html) bytes"
      echo "  - Assets: $ASSET_COUNT files"
      echo "  - Total size: $(du -sh $NEW_BUILD | cut -f1)"
```

### 2. 심볼릭 링크 검증 강화

```yaml
- name: Atomic deployment with symlink swap
  command: |
    cd ${{ secrets.CICD_PATH }}/prod/app/django/static
    NEW_BUILD="dist_${{ github.run_number }}_${{ github.sha }}"

    # 새 빌드 디렉터리 존재 확인
    if [ ! -d "$NEW_BUILD" ]; then
      echo "❌ ERROR: Build directory not found: $NEW_BUILD"
      exit 1
    fi

    # 심볼릭 링크 원자적 교체
    ln -sfn "$NEW_BUILD" dist.tmp
    mv -Tf dist.tmp dist

    # 심볼릭 링크 검증
    if [ ! -d "dist" ]; then
      echo "❌ ERROR: Symlink is broken!"
      exit 1
    fi

    LINKED_DIR=$(readlink dist)
    if [ "$LINKED_DIR" != "$NEW_BUILD" ]; then
      echo "❌ ERROR: Symlink points to wrong target: $LINKED_DIR"
      exit 1
    fi

    echo "✅ Symlink verified: dist -> $LINKED_DIR"
```

### 3. 안전한 구 빌드 정리

```yaml
# 오래된 빌드 정리 (최근 3개 유지로 증가)
echo "🧹 Cleaning old builds..."

# 현재 활성 빌드 확인
CURRENT_BUILD=$(readlink dist)
echo "Current active: $CURRENT_BUILD"

# 모든 빌드 나열 (시간순 역순)
ALL_BUILDS=$(ls -dt dist_* 2>/dev/null | grep -v "^dist$")

# 최근 3개 제외하고 삭제
echo "$ALL_BUILDS" | tail -n +4 | while read OLD_BUILD; do
  # 현재 활성 빌드는 절대 삭제 안 함
  if [ "$OLD_BUILD" != "$CURRENT_BUILD" ]; then
    echo "  Removing: $OLD_BUILD"
    rm -rf "$OLD_BUILD"
  fi
done

echo "📊 Remaining builds:"
ls -lth | grep "^d" | grep "dist_" | head -5
```

### 4. NFS 동기화 확실하게 대기

```yaml
- name: Wait for NFS sync with verification
  run: |
    echo "⏳ Waiting for NFS synchronization..."

    MAX_WAIT=30
    for i in $(seq 1 $MAX_WAIT); do
      # SSH로 파일 존재 확인
      if ssh ${{ secrets.CICD_USER }}@${{ secrets.CICD_HOST }} \
         "test -f ${{ secrets.CICD_PATH }}/prod/app/django/static/dist/index.html"; then
        echo "✅ NFS sync verified (${i}s)"
        break
      fi

      if [ $i -eq $MAX_WAIT ]; then
        echo "❌ NFS sync timeout!"
        exit 1
      fi

      sleep 1
    done
```

### 5. 배포 검증 강화

```yaml
- name: Verify deployment integrity
  command: |
    cd ${{ secrets.CICD_PATH }}/prod/app/django/static

    # index.html 존재 확인
    if [ ! -f "dist/index.html" ]; then
      echo "❌ Deployment failed: index.html not found"
      exit 1
    fi

    # assets 디렉터리 확인
    if [ ! -d "dist/assets" ]; then
      echo "❌ Deployment failed: assets directory not found"
      exit 1
    fi

    # 주요 파일 참조 검증
    MAIN_JS=$(grep -o 'src="/static/dist/assets/index-[^"]*\.js"' dist/index.html | head -1 | sed 's|.*/||' | sed 's/"$//')
    if [ -n "$MAIN_JS" ] && [ ! -f "dist/assets/$MAIN_JS" ]; then
      echo "❌ Deployment failed: Referenced file missing: $MAIN_JS"
      echo "Available files:"
      ls dist/assets/index-*.js
      exit 1
    fi

    # CSS 파일 확인
    CSS_COUNT=$(find dist/assets -name "*.css" | wc -l)
    if [ "$CSS_COUNT" -eq 0 ]; then
      echo "❌ WARNING: No CSS files found!"
    fi

    echo "✅ Deployment integrity verified"
    echo "  - Main JS: $MAIN_JS"
    echo "  - CSS files: $CSS_COUNT"
    echo "  - Total assets: $(find dist/assets -type f | wc -l)"
```

## 🔧 즉시 적용 가능한 디버깅

### 서버에서 현재 상태 확인

```bash
# SSH로 서버 접속
ssh user@cicd-host

# 1. 심볼릭 링크 상태 확인
cd /path/to/prod/app/django/static
ls -la dist
readlink dist

# 2. 현재 빌드 디렉터리 확인
ls -lth | grep dist_

# 3. index.html이 참조하는 파일 확인
grep -o 'src="/static/dist/assets/[^"]*"' dist/index.html | head -10

# 4. 실제 파일 존재 확인
MAIN_JS=$(grep -o 'assets/index-[^"]*\.js' dist/index.html | head -1)
ls -lh "dist/$MAIN_JS"

# 5. 파일 개수 비교
echo "Expected (from index.html):"
grep -o 'href="/static/dist/assets/[^"]*"' dist/index.html | wc -l
echo "Actual (in directory):"
find dist/assets -type f | wc -l
```

### Kubernetes Pod에서 확인

```bash
# nginx pod에서 확인
kubectl exec -n ibs-prod deployment/nginx -- ls -la /django/static/dist/

# Web pod에서 확인
kubectl exec -n ibs-prod deployment/web -- ls -la /app/django/static/dist/

# 두 개가 같은 파일을 보는지 확인
kubectl exec -n ibs-prod deployment/nginx -- readlink /django/static/dist
kubectl exec -n ibs-prod deployment/web -- readlink /app/django/static/dist
```

## 📊 문제 진단 체크리스트

- [ ] SCP 업로드 완료 후 파일 개수 일치 확인
- [ ] index.html이 참조하는 모든 assets 파일 존재 확인
- [ ] 심볼릭 링크가 올바른 디렉터리를 가리키는지 확인
- [ ] NFS 동기화 완료 확인 (Pod에서 파일 보임)
- [ ] nginx가 404 반환하는 파일 추적
- [ ] 브라우저 개발자 도구 Network 탭에서 실제 요청 URL 확인
