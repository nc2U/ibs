# SCP 업로드 실패 원인 분석

## 문제 상황
```
❌ ERROR: Build directory not found
```

빌드 디렉터리 `dist_2789_d40a321c1bacaea252d9a5bbfcd7694b3366ad54`가 서버에 없음.

## 가능한 원인

### 1. SCP 액션이 실패했지만 워크플로우 계속 진행
```yaml
- name: Upload new build to server
  uses: appleboy/scp-action@master
  # 실패해도 다음 단계로 진행될 수 있음
```

**해결**: 실패 시 워크플로우 중단 확인

### 2. 경로 불일치
```yaml
source: 'app/django/static/dist_${{ github.run_number }}_${{ github.sha }}'
target: ${{ secrets.CICD_PATH }}/prod/app/django/static/
```

**문제 가능성**:
- `source` 경로에 `app/django/static/` 포함
- `target`에도 `/prod/app/django/static/` 포함
- 결과: `/prod/app/django/static/app/django/static/dist_xxx` (중복 경로)

### 3. appleboy/scp-action의 경로 처리 방식

**scp-action 동작 방식**:
```
source: 'app/django/static/dist_xxx'
target: '/path/to/prod/app/django/static/'

실제 업로드 경로:
/path/to/prod/app/django/static/app/django/static/dist_xxx
```

**왜냐하면**: scp-action은 source의 **전체 경로 구조를 유지**하면서 복사

## 즉시 확인 방법

### SSH로 서버 접속하여 확인
```bash
ssh user@server

# 1. 예상 경로 확인
ls -la /path/to/prod/app/django/static/

# 2. 중복 경로 확인
ls -la /path/to/prod/app/django/static/app/django/static/

# 3. 실제 업로드된 위치 찾기
find /path/to/prod -name "dist_2789_*" -type d

# 4. 최근 생성된 디렉터리 확인
find /path/to/prod -type d -name "dist_*" -mtime -1
```

## 해결 방안

### 옵션 1: source 경로를 상대 경로로 변경 (권장)

**문제 있는 현재 코드**:
```yaml
- name: Upload new build to server
  uses: appleboy/scp-action@master
  with:
    source: 'app/django/static/dist_${{ github.run_number }}_${{ github.sha }}'
    target: ${{ secrets.CICD_PATH }}/prod/app/django/static/
```

**수정 방법 1**: source를 디렉터리명만으로
```yaml
- name: Upload new build to server
  uses: appleboy/scp-action@master
  with:
    source: 'app/django/static/dist_${{ github.run_number }}_${{ github.sha }}'
    target: ${{ secrets.CICD_PATH }}/prod/
    strip_components: 2  # app/django/ 제거
```

**수정 방법 2**: target을 루트로, source를 전체 경로로
```yaml
- name: Upload new build to server
  uses: appleboy/scp-action@master
  with:
    source: 'app/django/static/dist_${{ github.run_number }}_${{ github.sha }}'
    target: ${{ secrets.CICD_PATH }}/prod/
```
→ 결과: `/prod/app/django/static/dist_xxx` (올바름)

### 옵션 2: 빌드 디렉터리를 임시 위치에 복사 후 업로드

```yaml
- name: Prepare for upload
  run: |
    BUILD_NAME="dist_${{ github.run_number }}_${{ github.sha }}"
    mkdir -p upload_temp
    cp -r "app/django/static/${BUILD_NAME}" "upload_temp/"

- name: Upload new build to server
  uses: appleboy/scp-action@master
  with:
    source: 'upload_temp/*'
    target: ${{ secrets.CICD_PATH }}/prod/app/django/static/
```

### 옵션 3: rsync 사용 (가장 안정적)

```yaml
- name: Upload new build to server
  uses: garygrossgarten/github-action-ssh@release
  with:
    command: |
      # GitHub Actions runner에서 서버로 rsync
      rsync -avz --progress \
        "app/django/static/dist_${{ github.run_number }}_${{ github.sha }}/" \
        "${{ secrets.CICD_USER }}@${{ secrets.CICD_HOST }}:${{ secrets.CICD_PATH }}/prod/app/django/static/dist_${{ github.run_number }}_${{ github.sha }}/"
```

## 디버깅: SCP 업로드 직후 확인

```yaml
- name: Upload new build to server
  uses: appleboy/scp-action@master
  with:
    source: 'app/django/static/dist_${{ github.run_number }}_${{ github.sha }}'
    target: ${{ secrets.CICD_PATH }}/prod/app/django/static/

# 디버깅: 업로드된 위치 확인
- name: Debug - Check uploaded location
  uses: garygrossgarten/github-action-ssh@release
  with:
    command: |
      echo "🔍 Searching for uploaded files..."

      # 예상 경로 1
      echo "Option 1: Direct path"
      ls -la "${{ secrets.CICD_PATH }}/prod/app/django/static/" | grep dist_${{ github.run_number }}

      # 예상 경로 2: 중복 경로
      echo "Option 2: Nested path"
      if [ -d "${{ secrets.CICD_PATH }}/prod/app/django/static/app/django/static/" ]; then
        ls -la "${{ secrets.CICD_PATH }}/prod/app/django/static/app/django/static/" | grep dist_${{ github.run_number }}
      fi

      # 전체 검색
      echo "Option 3: Full search"
      find "${{ secrets.CICD_PATH }}/prod" -name "dist_${{ github.run_number }}_*" -type d
```
