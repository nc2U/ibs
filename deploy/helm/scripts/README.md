# CloudNativePG Backup & Restore Scripts

CloudNativePG 환경에서 PostgreSQL 데이터베이스의 수동 백업과 복원을 위한 스크립트입니다.

## 📋 개요

- **자동 백업**: CronJob으로 매일 새벽 2시에 자동 백업 (설정 가능)
- **수동 백업**: 필요할 때 즉시 백업 실행
- **수동 복원**: 백업 파일로부터 데이터베이스 복원
- **저장소**: NFS 기반 영구 스토리지 (`/var/backups`)
- **배포**: GitHub Actions를 통해 CI/CD 서버로 자동 복사
- **PVC 보존**: Helm uninstall 시에도 PVC 보존 설정 적용
- **버전 업그레이드**: PostgreSQL 메이저 버전 업그레이드 가이드 제공

## 🚀 사용 방법

### 📍 CI/CD 서버에서 실행

GitHub Actions (`helm_dev.yml`)가 실행되면 이 스크립트들이 CI/CD 서버의 다음 경로로 복사됩니다:

```
$CICD_PATH/dev/deploy/helm/scripts/
```

### 1️⃣ 수동 백업

```bash
# CI/CD 서버에 SSH 접속 후
cd $CICD_PATH/dev/deploy/helm/scripts

# 기본 실행 (ibs-dev 네임스페이스)
./manual-backup.sh

# 프로덕션 환경 백업
./manual-backup.sh prod

# 로그 자동 추적 비활성화
FOLLOW_LOGS=false ./manual-backup.sh
```

**생성되는 백업 파일**:

- 파일명: `ibs-backup-postgres-YYYY-MM-DD.dump`
- 위치: NFS `/var/backups/` 디렉터리
- 형식: PostgreSQL custom format (`-Fc`)
- 내용: `ibs` 스키마의 데이터만 (마이그레이션 제외)

### 3️⃣ S3 기반 물리 백업 및 시점 복구 (S3 Backup & PITR Restore)

CloudNativePG (CNPG) In-tree Barman Cloud를 활용한 MinIO S3 오브젝트 스토리지 기반 초고속 물리 백업 및 PITR 복원 방식입니다.

```bash
# 1. S3 수동 물리 백업 (prod / dev)
./manual-s3-backup.sh prod
./manual-s3-backup.sh dev

# 2. S3 백업 기반 최신 시점 DB 복원
./manual-s3-restore.sh prod
./manual-s3-restore.sh dev

# 3. S3 특정 시점(KST 한국시간) 복구 (Point-in-Time Recovery)
./manual-s3-restore.sh prod "2026-08-01 15:30:00"

# 4. S3 복원 테스트 모드 (메인 DB 건드리지 않고 'postgres-restored' 파드 생성)
./manual-s3-restore.sh dev "" test
```

### ⚠️ 마이그레이션 디렉터리 리셋 절차 (Django Migrations Reset Workflow - 정석 지침)

Django `migrations` 디렉터리를 0001_initial로 리셋한 후 배포 및 DB 복원을 수행하는 **정석 절차**입니다. (Helm 프리훅 마이그레이션 충돌 방지)

1. **언인스톨 및 기존 DB 클러스터 선제 삭제**:
   - 기존 DB와 마이그레이션 훅 충돌을 막기 위해 Helm 언인스톨 및 DB 클러스터를 삭제합니다:
     ```bash
     helm uninstall ibs -n ibs-prod   # 또는 ibs-dev
     kubectl delete cluster postgres -n ibs-prod
     ```
2. **새 마이그레이션 코드 배포 (GitHub Actions / Git Push)**:
   - 로컬에서 리셋된 `migrations/0001_initial.py` 코드를 Git에 커밋/푸시하여 서버에 배포합니다.
3. **S3 수동 복구 & 마이그레이션 족보 동기화**:
   - S3 백업 데이터 기반으로 DB 복원 및 Django 마이그레이션 이력을 동기화합니다:
     ```bash
     ./manual-s3-restore.sh prod
     kubectl exec -it $(kubectl get pod -l app.kubernetes.io/name=web -n ibs-prod -o name | head -1) -n ibs-prod -- sh migrate.sh -r
     ```
4. **📌 [필수] S3 기준점 백업 생성 (Post-Migration Baseline S3 Backup)**:
   - 복원 및 마이그레이션 족보 동기화가 완료된 즉시 **새로운 S3 수동 백업을 생성하여 최신 마이그레이션 상태로 S3 아카이브 기준점을 재설정**합니다:
     ```bash
     ./manual-s3-backup.sh prod   # 또는 dev
     ```

### 3️⃣ kubectl로 직접 실행 (고급)

#### 수동 백업

```bash
# CronJob에서 즉시 Job 생성
kubectl create job -n ibs-dev postgres-backup-manual-$(date +%Y%m%d-%H%M%S) \
  --from=cronjob/ibs-postgres-backup

# 진행 상황 확인
kubectl get jobs -n ibs-dev
kubectl logs -n ibs-dev job/postgres-backup-manual-XXXXXX -f
```

#### 백업 파일 확인

```bash
# 임시 pod로 백업 파일 목록 조회
kubectl run -n ibs-dev backup-list --image=postgres:18.0 --rm -i \
  --overrides='
{
  "spec": {
    "containers": [{
      "name": "backup-list",
      "image": "postgres:18.0",
      "command": ["ls", "-lh", "/var/backups/"],
      "volumeMounts": [{
        "name": "backup-volume",
        "mountPath": "/var/backups"
      }]
    }],
    "volumes": [{
      "name": "backup-volume",
      "persistentVolumeClaim": {
        "claimName": "ibs-postgres-backup-pvc"
      }
    }]
  }
}'
```

#### 수동 복원 (kubectl)

복원은 `manual-restore.sh` 스크립트 사용을 권장하지만, kubectl로 직접 실행하려면:

```bash
# 1. charts/cnpg/restore-job.yaml.example 파일 참조
# 2. DUMP_FILE 환경변수를 복원할 백업 파일로 수정
# 3. kubectl apply로 Job 생성

# 예시는 charts/cnpg/restore-job.yaml.example 파일 참조
```

## 📦 자동 백업 설정

### CronJob 스케줄 변경

`deploy/helm/charts/cnpg/values.yaml`:

```yaml
backup:
  schedule: "0 2 * * *"  # 매일 새벽 2시 (KST)
  nfs:
    enabled: true
    storage: "1Gi"
```

**스케줄 예시**:

- `0 2 * * *` - 매일 새벽 2시
- `0 */6 * * *` - 6시간마다
- `0 0 * * 0` - 매주 일요일 자정
- `0 3 1 * *` - 매월 1일 새벽 3시

### 백업 보관 정책

기본 설정: 2일 이상된 백업 파일은 자동 삭제

변경하려면 `charts/cnpg/templates/backup-cronjob.yaml:44`:

```bash
find /var/backups \( -name "*.dump" -o -name "*.log" \) -type f -mtime +2 -delete
#                                                                        ^^
#                                                                        일수 조정
```

## 🔧 백업/복원 상세 설정

### 백업 내용

- **스키마**: `ibs` 스키마만
- **데이터**: 데이터만 백업 (`--data-only`)
- **형식**: PostgreSQL custom format (`-Fc`)
- **제외**: `django_migrations` 테이블
- **삽입 방식**: `--column-inserts` (호환성)

### 복원 옵션

- **데이터만**: 스키마 구조는 유지, 데이터만 교체
- **병렬 처리**: `--jobs=4` (4개 병렬 작업)
- **트리거 비활성화**: `--disable-triggers` (복원 속도 향상)
- **소유권/권한**: `--no-owner --no-privileges` (이식성)

## 📁 파일 구조

```
deploy/helm/
├── scripts/
│   ├── dev-deploy.sh             # Dev 환경 Helm 배포 스크립트
│   ├── prod-deploy.sh            # Prod 환경 Helm 배포 스크립트
│   ├── manual-backup.sh          # 수동 백업 스크립트
│   ├── manual-restore.sh         # 수동 복원 스크립트
│   ├── preserve-pvcs.sh          # PVC 보존 스크립트 (ownerReferences 제거)
│   └── README.md                 # 이 문서
└── charts/cnpg/
    ├── templates/
    │   ├── backup-cronjob.yaml   # 자동 백업 CronJob
    │   ├── backup-pv.yaml        # NFS PersistentVolume
    │   └── backup-pvc.yaml       # PersistentVolumeClaim
    └── restore-job.yaml.example  # 복원 Job 템플릿 예시 (참고용)
```

## 🔄 GitHub Actions 통합

### 자동 배포 흐름

1. **Trigger**: `deploy/helm/**` 경로 변경 시
2. **Copy**: 헬름 차트와 스크립트를 CI/CD 서버로 복사
3. **Deploy**: `values-{env}-custom.yaml` 존재 시 `scripts/{env}-deploy.sh` 실행
4. **Fallback**: 스크립트 실패 시 인라인 Helm 배포로 폴백
5. **Access**: CI/CD 서버에서 `kubectl` 명령 사용 가능
6. **Scripts**: `$CICD_PATH/{env}/deploy/helm/scripts/`에서 실행

### 배포 스크립트 우선순위

```bash
# 1순위: 커스텀 배포 스크립트 (values-{env}-custom.yaml 존재 시)
if [ -e "./values-dev-custom.yaml" ]; then
  sh scripts/dev-deploy.sh
fi

# 2순위: GitHub Actions 인라인 Helm 배포 (폴백)
if [ "$run_inline_helm_deploy" = true ]; then
  helm upgrade ibs . -f ./values-dev.yaml --install ...
fi
```

### 스크립트 업데이트

스크립트를 수정하고 Git에 푸시하면:

```bash
git add deploy/helm/scripts/
git commit -m "Update deployment/backup scripts"
git push origin develop  # develop 브랜치의 경우
```

자동으로 CI/CD 서버에 복사됩니다.

## 🚀 배포 스크립트 (dev-deploy.sh / prod-deploy.sh)

### 개요

Helm 차트 배포를 위한 환경별 스크립트입니다. `.env` 파일을 로드하고 `values-{env}-custom.yaml`을 사용하여 배포합니다.

### 사용법

```bash
# Dev 환경 배포
cd $CICD_PATH/dev/deploy/helm/scripts
./dev-deploy.sh

# Prod 환경 배포
cd $CICD_PATH/prod/deploy/helm/scripts
./prod-deploy.sh
```

### 요구사항

1. **values-{env}-custom.yaml 파일**: helm 디렉터리에 존재해야 함
2. **.env 파일**: `app/django/.env`에 환경변수 정의
3. **kubectl 접근**: CI/CD 서버에서 클러스터 접근 가능

### 스크립트 동작

1. `.env` 파일 로드 (환경변수 설정)
2. `values-{env}-custom.yaml` 존재 확인
3. NFS provisioner Helm repo 추가 (미설치 시)
4. NFS provisioner 설치 (미설치 시)
5. Kubernetes Role 적용
6. Helm upgrade/install 실행

### 경로 구조

스크립트는 `scripts/` 디렉터리에서 실행되므로 상대 경로가 조정되어 있습니다:

```bash
# scripts/ -> helm/ -> app/django/.env
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"          # scripts/
CURR_DIR="$(cd "$SCRIPT_PATH/.." && pwd)"             # helm/
SCRIPT_DIR="$(cd "$CURR_DIR/../../app/django" && pwd)" # app/django/
```

## 🐛 트러블슈팅

### 백업 파일이 없어요

```bash
# PVC 마운트 확인
kubectl get pvc -n ibs-dev ibs-postgres-backup-pvc

# PV 상태 확인
kubectl get pv | grep postgres-backup

# NFS 서버 연결 확인
kubectl describe pv ibs-postgres-backup-pv
```

### CronJob이 실행되지 않아요

```bash
# CronJob 상태 확인
kubectl get cronjob -n ibs-dev

# 최근 Job 확인
kubectl get jobs -n ibs-dev

# CronJob 수동 트리거
kubectl create job -n ibs-dev test-backup --from=cronjob/ibs-postgres-backup
```

### 복원이 실패해요

```bash
# 복원 Job 로그 확인
kubectl logs -n ibs-dev job/ibs-postgres-restore-XXXXXX

# 백업 파일 무결성 확인
kubectl run -n ibs-dev backup-check --image=postgres:18.0 --rm -i \
  --overrides='...' \
  -- pg_restore --list /var/backups/ibs-backup-postgres-2025-01-15.dump
```

### 디스크 공간 부족

```bash
# 오래된 백업 수동 삭제
kubectl run -n ibs-dev cleanup --image=postgres:18.0 --rm -i \
  --overrides='
{
  "spec": {
    "containers": [{
      "name": "cleanup",
      "image": "postgres:18.0",
      "command": ["/bin/bash", "-c", "find /var/backups -name \"*.dump\" -mtime +7 -delete"],
      "volumeMounts": [{
        "name": "backup-volume",
        "mountPath": "/var/backups"
      }]
    }],
    "volumes": [{
      "name": "backup-volume",
      "persistentVolumeClaim": {
        "claimName": "ibs-postgres-backup-pvc"
      }
    }]
  }
}'

# PVC 용량 확대 (values.yaml)
backup:
  nfs:
    storage: "5Gi"  # 1Gi → 5Gi
```

### CI/CD 서버 접근 방법

```bash
# SSH 접속
ssh $CICD_USER@$CICD_HOST

# 스크립트 위치 확인
ls -la $CICD_PATH/dev/deploy/helm/scripts/

# kubectl 동작 확인
kubectl get pods -n ibs-dev
```

## ⚙️ 환경 변수

| 변수          | 기본값    | 설명                    |
|---------------|-----------|-------------------------|
| `NAMESPACE`   | `ibs-dev` | Kubernetes 네임스페이스 |
| `RELEASE`     | `ibs`     | Helm 릴리스 이름        |
| `FOLLOW_LOGS` | `true`    | 로그 자동 추적 여부     |

## 📚 참고 자료

- [CloudNativePG Documentation](https://cloudnative-pg.io/)
- [PostgreSQL Backup/Restore](https://www.postgresql.org/docs/current/backup.html)
- [Kubernetes CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [NFS Persistent Volumes](https://kubernetes.io/docs/concepts/storage/volumes/#nfs)

## 🔐 보안 참고사항

- 백업 파일에는 민감한 데이터가 포함되어 있습니다
- NFS 서버 접근 권한을 적절히 관리하세요
- 프로덕션 환경에서는 백업 암호화를 고려하세요
- 정기적으로 복원 테스트를 수행하세요
- CI/CD 서버 접근 권한을 제한하세요

## ✅ 체크리스트

백업/복원 설정이 올바르게 되었는지 확인:

- [ ] CronJob이 생성되고 스케줄대로 실행되는가?
- [ ] 백업 파일이 NFS에 정상적으로 저장되는가?
- [ ] 수동 백업 스크립트가 정상 동작하는가?
- [ ] 복원 스크립트로 데이터를 복원할 수 있는가?
- [ ] 복원 후 시퀀스가 올바르게 조정되는가?
- [ ] 오래된 백업 파일이 자동으로 삭제되는가?
- [ ] GitHub Actions가 스크립트를 CI/CD 서버로 복사하는가?
- [ ] CI/CD 서버에서 kubectl 명령이 정상 동작하는가?

## 🎯 Quick Start

### CI/CD 서버에서 첫 백업 실행하기

```bash
# 1. CI/CD 서버 접속
ssh $CICD_USER@$CICD_HOST

# 2. 스크립트 디렉터리 이동
cd $CICD_PATH/dev/deploy/helm/scripts

# 3. 백업 실행
./manual-backup.sh

# 4. 백업 파일 확인
kubectl run -n ibs-dev check-backup --image=postgres:18.0 --rm -i \
  --overrides='...' -- ls -lh /var/backups/
```

### 백업 복원 테스트하기

```bash
# 1. 백업 실행 (위 참조)

# 2. 복원 스크립트 실행
cd $CICD_PATH/dev/deploy/helm/scripts
./manual-restore.sh

# 3. 백업 파일명 입력 (예: ibs-backup-postgres-2025-01-15.dump)

# 4. 확인 입력 (yes)

# 5. 복원 완료 확인
```