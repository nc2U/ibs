# IBS 배포 스크립트

## Vue 프론트엔드 롤백

### 사용법

```bash
./rollback-vue.sh <build_timestamp>
```

### 예시

```bash
# 사용 가능한 빌드 목록 보기
./rollback-vue.sh

# 특정 빌드로 롤백
./rollback-vue.sh 123_abc123def456
```

### 작동 방식

1. 지정된 빌드 디렉터리 존재 확인
2. 현재 배포 버전 표시 및 확인 요청
3. 심볼릭 링크를 대상 빌드로 원자적 교체
4. Kubernetes Nginx 및 Web Pod 재시작
5. 배포 정보 출력

### 주의사항

- **서버에서 실행**: 이 스크립트는 Kubernetes 클러스터 접근이 가능한 서버에서 실행해야 합니다.
- **권한 필요**: kubectl 명령어 실행 권한이 필요합니다.
- **무중단 배포**: 심볼릭 링크 교체는 원자적이므로 서비스 중단이 없습니다.
- **Redis/Celery**: Redis와 Celery는 재시작하지 않습니다 (필요 없음).

### 설치

1. 서버에 스크립트 복사:
```bash
scp deploy/scripts/rollback-vue.sh user@server:/opt/ibs/scripts/
```

2. 실행 권한 부여:
```bash
chmod +x /opt/ibs/scripts/rollback-vue.sh
```

3. 경로 수정:
```bash
# 스크립트 내부의 STATIC_DIR 수정
STATIC_DIR="/actual/path/to/ibs/prod/app/django/static"
```

## CI/CD 워크플로우

### 자동 배포 프로세스

master 브랜치에 푸시하면 자동으로 다음 프로세스가 실행됩니다:

1. **빌드**: Vue 프로젝트를 `dist_<build_number>_<git_sha>` 디렉터리로 빌드
2. **메타데이터 생성**: deploy.json 파일에 배포 정보 저장
3. **테스트**: Vitest 단위 테스트 실행
4. **업로드**: 새 빌드만 서버로 전송 (전체 static이 아닌)
5. **원자적 배포**: 심볼릭 링크를 새 빌드로 교체
6. **자동 정리**: 오래된 빌드 삭제 (최근 2개만 유지)
7. **검증**: index.html 존재 확인 및 배포 정보 출력
8. **Pod 재시작**: Nginx와 Web Pod만 재시작

### 배포 메타데이터

각 빌드의 `deploy.json` 파일:

```json
{
  "build_time": "2025-01-15T10:30:00Z",
  "git_sha": "abc123def456",
  "git_branch": "master",
  "build_number": "123",
  "deployer": "github-actions"
}
```

### 빌드 디렉터리 구조

```
static/
├── dist -> dist_123_abc123def456/  (심볼릭 링크)
├── dist_123_abc123def456/          (현재 배포)
│   ├── index.html
│   ├── assets/
│   └── deploy.json
└── dist_122_def456abc789/          (이전 배포, 롤백용)
    ├── index.html
    ├── assets/
    └── deploy.json
```

## 로컬 개발 배포

### 로컬에서 무중단 배포

```bash
./deploy/scripts/deploy-build.sh
```

또는:

```bash
cd deploy/scripts
./deploy-build.sh
```

이 스크립트는:
1. Vue 프로젝트 빌드
2. 타임스탬프 디렉터리로 이동
3. 심볼릭 링크 원자적 교체
4. 오래된 빌드 정리 (최근 2개만 유지)

## 트러블슈팅

### 롤백 실패

```bash
# 현재 심볼릭 링크 확인
ls -la /path/to/static/dist

# 수동 롤백
cd /path/to/static
ln -sfn dist_<target> dist.tmp
mv -Tf dist.tmp dist
```

### Pod 재시작 실패

```bash
# 수동 재시작
kubectl rollout restart deployment/nginx -n ibs-prod
kubectl rollout restart deployment/web -n ibs-prod

# 상태 확인
kubectl rollout status deployment/nginx -n ibs-prod
kubectl rollout status deployment/web -n ibs-prod
```

### 빌드 디렉터리 정리

```bash
# 오래된 빌드 수동 삭제
cd /path/to/static
ls -dt dist_* | tail -n +3 | xargs rm -rf
```
