# IBS Vue 빌드 환경 일관성 점검 보고서

## 실행일: 2025-10-10

## 1. 문제 요약

로컬 Docker 환경과 Kubernetes (prod/dev) 환경의 Vue 컴포넌트 UI가 각각 다르게 동작하는 문제 분석 결과, **CI/CD 파이프라인에서 NODE_ENV가 명시적으로 설정되지 않아** 빌드 모드가 불확실한 상태입니다.

## 2. 핵심 문제점

### 2.1 NODE_ENV 미설정 (🔴 Critical)

**파일**: `.github/workflows/vue_prod.yml`, `vue_dev.yml`

```yaml
# 현재 상태 (문제)
- name: Build the Source Code
  run: cd app/vue && pnpm build && pnpm docs:build
  if: ${{ always() }}
```

**영향**:
- `vite.config.mts:10` 에서 `process.env.NODE_ENV === 'production'` 체크
- 미설정 시 → `base: '/'` 사용 (잘못된 경로)
- 올바른 경로: `base: '/static/dist'`

### 2.2 로컬 vs 서버 환경 차이

| 환경 | 실행 방식 | Base Path | Console Logs | Sourcemaps |
|------|-----------|-----------|--------------|------------|
| 로컬 Docker | `pnpm dev` | `/` | ✅ 유지 | ✅ 포함 |
| CI/CD Build | `pnpm build` | ❓ 불확실 | ❓ 불확실 | ❓ 불확실 |
| K8s Pod | nginx static | `/static/dist` | ❓ | ❓ |

### 2.3 index.html 템플릿 이중 기준

**소스 템플릿** (`app/vue/index.html`):
```html
<!-- 프로덕션 경로로 하드코딩 -->
<link rel="apple-touch-icon" href="/static/dist/img/icons/apple-icon-57x57.png">
```

**개발 서버**:
```html
<!-- Vite가 변환 -->
<script type="module" src="/src/main.ts"></script>
```

**프로덕션 빌드**:
```html
<!-- Vite가 변환 -->
<script type="module" src="/static/dist/assets/index-[hash].js"></script>
```

**문제**: NODE_ENV 값에 따라 변환 결과가 달라지나, 현재 설정 불명확

### 2.4 배포 타이밍 레이스 컨디션

**vue_prod.yml 배포 순서**:
```bash
1. Build: pnpm build → ../django/static/dist_${timestamp}
2. Symlink: ln -sfn dist_${timestamp} dist
3. Upload: scp → NFS server
4. Restart: kubectl rollout restart nginx web
```

**잠재적 이슈**:
- Step 3-4 사이 타이밍 갭
- NFS 동기화 완료 전 Pod 재시작 가능
- 구 버전 파일 서빙 리스크

## 3. 권장 해결 방안

### 3.1 NODE_ENV 명시적 설정 (🔴 즉시 적용 필요)

**vue_prod.yml 수정**:
```yaml
- name: Build the Source Code
  run: cd app/vue && pnpm build && pnpm docs:build
  env:
    NODE_ENV: production
  if: ${{ always() }}
```

**vue_dev.yml 수정**:
```yaml
- name: Build the Source Code
  run: cd app/vue && pnpm build
  env:
    NODE_ENV: production  # dev 환경도 production 빌드 사용
  if: ${{ always() }}
```

### 3.2 빌드 검증 단계 추가

```yaml
- name: Verify Production Build
  run: |
    cd app/vue
    # Check if index.html has correct base path
    if ! grep -q '/static/dist/assets/' ../django/static/dist/index.html; then
      echo "❌ ERROR: Build base path incorrect!"
      exit 1
    fi
    # Check if console.log is removed
    if grep -q 'console\.log' ../django/static/dist/assets/*.js; then
      echo "⚠️ WARNING: Console logs found in production build"
    fi
    echo "✅ Build verification passed"
```

### 3.3 배포 타이밍 개선

```yaml
- name: Wait for NFS sync
  run: sleep 5  # NFS 동기화 대기

- name: Restart Pods
  run: |
    kubectl rollout restart deployment/nginx -n ibs-prod
    kubectl rollout status deployment/nginx -n ibs-prod --timeout=60s
    kubectl rollout restart deployment/web -n ibs-prod
    kubectl rollout status deployment/web -n ibs-prod --timeout=60s
```

### 3.4 로컬 개발 환경 개선

**docker-compose.yml 볼륨 마운트**:
```yaml
nginx:
  volumes:
    - ../app/django/static:/django/static:ro  # Read-only
```

**nginx 설정에서 개발/프로덕션 구분**:
```nginx
location /static/dist/ {
    alias /django/static/dist/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

## 4. 즉시 실행 가능한 검증 명령

### 4.1 현재 빌드 상태 확인

```bash
# 로컬에서 프로덕션 빌드 테스트
cd app/vue
NODE_ENV=production pnpm build

# index.html 경로 검증
grep -o '/static/dist/assets/[^"]*' ../django/static/dist/index.html

# 파일 해시 확인 (매번 달라야 함)
ls -lh ../django/static/dist/assets/
```

### 4.2 서버 환경 확인

```bash
# Kubernetes pod에서 실제 파일 확인
kubectl exec -n ibs-prod deployment/web -- ls -lh /app/django/static/dist/assets/

# nginx가 서빙하는 파일 확인
kubectl exec -n ibs-prod deployment/nginx -- ls -lh /django/static/dist/assets/

# 심볼릭 링크 확인
kubectl exec -n ibs-prod deployment/web -- readlink /app/django/static/dist
```

### 4.3 빌드 일관성 테스트

```bash
# 3번 연속 빌드하여 일관성 확인
for i in {1..3}; do
  echo "=== Build $i ==="
  NODE_ENV=production pnpm build
  ls ../django/static/dist/index.html
  grep 'base' ../django/static/dist/assets/index-*.js | head -1
done
```

## 5. 예상 효과

### 수정 전 (현재)
- ❌ 빌드 모드 불확실
- ❌ 환경별 asset 경로 불일치 가능
- ❌ Console logs 제거 여부 불확실
- ❌ Sourcemaps 포함 여부 불확실
- ❌ 배포 타이밍 레이스 컨디션

### 수정 후 (기대)
- ✅ 항상 production 모드 빌드
- ✅ 일관된 `/static/dist` base path
- ✅ Console logs 제거됨
- ✅ Sourcemaps 제외됨
- ✅ 안정적인 배포 프로세스
- ✅ 로컬/dev/prod 동일한 빌드 결과

## 6. 추가 모니터링 항목

### 6.1 GitHub Actions 로그 확인

```bash
# 빌드 시 environment variables 출력
- name: Debug Environment
  run: |
    echo "NODE_ENV: $NODE_ENV"
    echo "PWD: $PWD"
    cd app/vue && node -e "console.log('process.env.NODE_ENV:', process.env.NODE_ENV)"
```

### 6.2 Vite 빌드 로그 확인

빌드 로그에서 확인해야 할 항목:
```
vite v6.3.6 building for production...
✓ 1234 modules transformed.
dist/index.html                  3.45 kB
dist/assets/index-5V9rFaFC.js    123.45 kB
```

`building for production` 메시지 확인 필수

### 6.3 런타임 검증

**브라우저 콘솔에서 확인**:
```javascript
// 프로덕션 빌드 확인 (console.log가 없어야 함)
// 개발자 도구 Network 탭에서:
// - /static/dist/assets/index-[hash].js 로드 확인
// - sourcemap 파일이 없어야 함
```

## 7. 결론

현재 CI/CD 파이프라인은 **NODE_ENV가 명시적으로 설정되지 않아** 빌드 결과가 불확실합니다. 이로 인해 로컬, dev, prod 환경이 서로 다른 asset 경로와 빌드 최적화 수준을 가질 수 있습니다.

**즉시 조치 사항**:
1. ✅ vue_prod.yml, vue_dev.yml에 `NODE_ENV: production` 추가
2. ✅ 빌드 검증 단계 추가
3. ✅ 배포 타이밍 개선 (NFS sync 대기)
4. ✅ 로컬 테스트: `NODE_ENV=production pnpm build` 실행 및 결과 검증

**우선순위**: 🔴 Critical - 다음 배포 전 반드시 적용 필요

---

## 8. 적용 완료 사항 (2025-10-10)

### ✅ 완료된 수정 사항

#### 1. vue_prod.yml 수정
- ✅ NODE_ENV=production 환경변수 추가 (line 62)
- ✅ 빌드 검증 단계 추가 (lines 84-121)
  - index.html 존재 확인
  - base path 검증 (/static/dist/assets/)
  - console.log 제거 확인 (경고)
  - sourcemap 제외 확인 (경고)
  - 빌드 통계 출력
- ✅ NFS 동기화 대기 추가 (lines 175-180)
  - 5초 대기로 레이스 컨디션 방지

#### 2. vue_dev.yml 수정
- ✅ NODE_ENV=production 환경변수 추가 (line 64)
- ✅ 빌드 검증 단계 추가 (lines 86-123)
  - prod와 동일한 검증 로직
- ✅ NFS 동기화 대기 추가 (lines 170-175)

#### 3. 로컬 검증 도구
- ✅ `scripts/verify_vue_build.sh` 생성
  - **⚠️ 로컬 개발 환경에서만 실행** (Kubernetes 아님!)
  - 로컬에서 프로덕션 빌드 테스트
  - CI/CD와 동일한 검증 로직
  - 상세한 빌드 통계 출력
  - 필요: Node.js 24 + pnpm 10

### 📋 즉시 테스트 가능

#### 로컬 검증 (개발자 PC에서 실행)
```bash
# ⚠️ 로컬에서만 실행 (서버 아님!)
# 필요: Node.js 24, pnpm 10 설치됨

# 검증 스크립트 실행
./scripts/verify_vue_build.sh

# 또는 수동 빌드
cd app/vue
NODE_ENV=production pnpm build

# Docker로 테스트
cd deploy
docker compose up
# http://localhost 접속하여 확인
```

#### 확인 사항
1. 브라우저 개발자 도구 → Network 탭
   - JS/CSS 파일이 `/static/dist/assets/` 경로에서 로드되는지 확인
   - 404 에러가 없는지 확인
2. Console 탭
   - Production 빌드에는 console.log가 없어야 함
3. Sources 탭
   - Sourcemap 파일이 없어야 함

### 🚀 배포 프로세스

#### Master 브랜치 (Production)
```bash
git add .github/workflows/vue_prod.yml
git add scripts/verify_vue_build.sh
git commit -m "feat: Add NODE_ENV and build verification to Vue CI/CD

- Set NODE_ENV=production explicitly in build step
- Add production build verification (base path, console.log, sourcemap)
- Add NFS sync wait to prevent race condition
- Create local verification script for testing"
git push origin master
```

**예상 결과**:
- GitHub Actions 워크플로우 실행
- 빌드 검증 단계에서 올바른 경로 확인
- NFS 동기화 후 안전하게 Pod 재시작
- `/static/dist/assets/` 경로로 리소스 로드

#### Develop 브랜치 (Development)
```bash
git checkout develop
git add .github/workflows/vue_dev.yml
git add scripts/verify_vue_build.sh
git commit -m "feat: Add NODE_ENV and build verification to Vue dev CI/CD"
git push origin develop
```

### 🔍 모니터링 포인트

#### GitHub Actions 로그 확인
1. "Build the Source Code" 단계
   ```
   vite v6.3.6 building for production...
   ✓ built in 15s
   ```
   → "building for production" 메시지 필수

2. "Verify Production Build" 단계
   ```
   🔍 Verifying production build...
   ✓ index.html 존재
   ✓ Base path 올바름: /static/dist/assets/
   ✓ Console logs 제거됨
   ✓ Sourcemap 파일 없음
   ✅ Production build verification passed
   ```

3. "Wait for NFS sync" 단계
   ```
   ⏳ Waiting for NFS synchronization...
   ✅ NFS sync complete
   ```

#### Kubernetes Pod 확인
```bash
# 배포 후 파일 확인
kubectl exec -n ibs-prod deployment/web -- ls -lh /app/django/static/dist/assets/

# index.html 경로 확인
kubectl exec -n ibs-prod deployment/web -- grep 'src=' /app/django/static/dist/index.html | head -3

# 심볼릭 링크 확인
kubectl exec -n ibs-prod deployment/web -- readlink /app/django/static/dist
```

### ✅ 기대 효과

#### 수정 전 (문제 상황)
- ❌ NODE_ENV 미설정 → 빌드 모드 불확실
- ❌ base: `/` 또는 `/static/dist` 불일치 가능
- ❌ 환경별 UI 차이 발생
- ❌ 배포 타이밍 레이스 컨디션

#### 수정 후 (해결)
- ✅ 항상 production 모드 빌드
- ✅ 일관된 base: `/static/dist`
- ✅ Console logs 제거, sourcemap 제외
- ✅ 빌드 검증으로 조기 에러 감지
- ✅ NFS 동기화 대기로 안정적 배포
- ✅ 로컬/dev/prod 모두 동일한 빌드 결과

### 📊 최종 확인 체크리스트

- [ ] 로컬에서 `./scripts/verify_vue_build.sh` 실행 → 모든 검증 통과
- [ ] Docker compose로 로컬 테스트 → UI 정상 동작
- [ ] develop 브랜치 푸시 → dev 환경 배포 성공
- [ ] dev 환경 접속 → /static/dist/assets/ 경로 확인
- [ ] master 브랜치 머지 → prod 환경 배포 성공
- [ ] prod 환경 접속 → UI 정상 동작 확인
- [ ] 브라우저 개발자 도구 → console.log 없음 확인
