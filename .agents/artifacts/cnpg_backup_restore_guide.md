# CNPG 백업 & 복원 개념 가이드

> IBS 프로젝트 기준 (`ibs-prod` 네임스페이스, MinIO S3 `s3.dyibs.com`)

---

## 1. 핵심 개념: 두 계층의 백업

CNPG는 **두 가지 백업**이 항상 함께 동작합니다.

```
┌──────────────────────────────────────────────────────────────────┐
│  계층 1: WAL 아카이빙 (Write-Ahead Log)                           │
│                                                                  │
│  PostgreSQL Primary → WAL 파일 생성 → S3 자동 업로드 (연속)       │
│                                                                  │
│  - 트랜잭션이 발생할 때마다 자동으로 S3에 스트리밍                  │
│  - 수 초 ~ 수 분 단위 (사실상 실시간)                              │
│  - PITR(특정 시점 복구)의 핵심 재료                                │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  계층 2: 베이스 백업 (ScheduledBackup)                            │
│                                                                  │
│  CNPG ScheduledBackup CRD → 매일 새벽 2시 전체 스냅샷 → S3 저장   │
│                                                                  │
│  - 하루 1회 전체 데이터 스냅샷                                     │
│  - WAL 재생의 시작점(Base) 역할                                    │
│  - 베이스 백업이 없으면 WAL만으로 처음부터 재생해야 해서 오래 걸림    │
└──────────────────────────────────────────────────────────────────┘
```

### 비유: 베이스 백업 vs WAL

| 개념 | 비유 |
|------|------|
| 베이스 백업 | 게임 세이브 파일 (오전 2시 체크포인트) |
| WAL 아카이빙 | 그 이후의 모든 행동 기록 (replay log) |
| PITR 복원 | 체크포인트 불러오기 + 행동 기록 재생 |

---

## 2. IBS 프로젝트 실제 구성

```
CNPG Cluster (ibs-prod)
  ├── postgres-1 (Primary)  ──→ WAL 생성 즉시 ──→ S3 (s3.dyibs.com)
  ├── postgres-2 (Replica)                          bucket: postgres-backup
  └── postgres-3 (Replica)                          path:   postgres-backup/postgres/
                                                      ├── base/        ← 베이스 백업
                                                      └── wals/        ← WAL 파일들
                                                          ├── 000000010000000000000001
                                                          ├── 000000010000000000000002
                                                          └── ...

ScheduledBackup: "0 0 2 * * *"  (매일 새벽 2시)
retentionPolicy: "30d"          (30일치 자동 보관, 이후 자동 삭제)
```

---

## 3. S3 저장 구조

```
postgres-backup/              ← MinIO 버킷
└── postgres/                 ← CNPG 클러스터명
    ├── base/                 ← 베이스 백업
    │   ├── 20260724T020000/  ← 날짜별 스냅샷
    │   └── 20260725T020000/
    └── wals/                 ← WAL 아카이브
        └── 0000000100000000/
            ├── 000000010000000000000001.gz
            ├── 000000010000000000000002.gz
            └── ...           ← 수 분마다 자동 업로드
```

---

## 4. 복원 원리 (PITR)

```
시간 흐름 →

오전 2:00   오전 9:30   오후 3:27   오후 3:30
    │            │           │           │
[베이스백업]  [WAL 축적]  [장애 발생]  [복구 시작]
    │←──────────────────────→│
         이 구간 WAL 재생으로
         오후 3:27분까지 복구 가능
```

**복구 과정:**
1. S3에서 가장 가까운 베이스 백업 다운로드
2. 목표 시점까지의 WAL 파일을 순서대로 재생(replay)
3. 목표 시점 직전 상태로 DB 복원 완료

---

## 5. 복원 시나리오별 방법

### 시나리오 A: 특정 시점 복구 (PITR) — "언제로 돌릴지 알 때"

```bash
cat <<EOF | kubectl apply -f - -n ibs-prod
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-restored
  namespace: ibs-prod
spec:
  instances: 1

  bootstrap:
    recovery:
      source: postgres-s3
      recoveryTarget:
        targetTime: "2026-07-24 06:27:00"  # UTC 기준 (KST -9h)

  externalClusters:
    - name: postgres-s3
      barmanObjectStore:
        destinationPath: s3://postgres-backup/postgres
        endpointURL: https://s3.dyibs.com
        s3Credentials:
          accessKeyId:
            name: postgres-backup-s3
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: postgres-backup-s3
            key: ACCESS_SECRET_KEY

  storage:
    storageClass: nfs-client
    size: 1Gi
EOF

# 복원 진행 상태 모니터링
kubectl get cluster postgres-restored -n ibs-prod -w
```

> [!IMPORTANT]
> `targetTime`은 **UTC 기준**입니다. KST(한국 시간)에서 9시간을 빼야 합니다.
> 예) KST 오후 3:27 → UTC 오전 6:27 → `"2026-07-24 06:27:00"`

---

### 시나리오 B: 최신 상태 복구 — "그냥 가장 최근으로"

`targetTime` 없이 `recovery`만 지정하면 최신 WAL까지 자동 재생합니다.

```bash
cat <<EOF | kubectl apply -f - -n ibs-prod
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-restored
  namespace: ibs-prod
spec:
  instances: 1
  bootstrap:
    recovery:
      source: postgres-s3    # targetTime 생략 → 최신 상태로 복원

  externalClusters:
    - name: postgres-s3
      barmanObjectStore:
        destinationPath: s3://postgres-backup/postgres
        endpointURL: https://s3.dyibs.com
        s3Credentials:
          accessKeyId:
            name: postgres-backup-s3
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: postgres-backup-s3
            key: ACCESS_SECRET_KEY

  storage:
    storageClass: nfs-client
    size: 1Gi
EOF
```

---

### 시나리오 C: NFS pg_dump 파일에서 복원 — "구형 방식 (수동)"

`manual-restore.sh`가 이 방식을 처리합니다. S3 PITR보다 오래 걸리고 정밀도가 낮습니다.

```bash
# CICD 서버에서 실행
cd /mnt/nfs/ibs/prod/deploy/helm/scripts

sh manual-restore.sh prod         # 대화형 (파일 직접 선택)
sh manual-restore.sh prod --auto  # 자동 (가장 최신 파일)
```

> [!WARNING]
> 이 방식은 기존 테이블을 **TRUNCATE 후 재적재**합니다. 복원 대상 시점 이후의
> 데이터는 완전히 유실됩니다. S3 PITR 방식이 가능하면 항상 PITR을 우선하십시오.

---

## 6. 복원 후 서비스 전환 절차

```bash
# 1. 복원 완료 확인
kubectl get cluster postgres-restored -n ibs-prod
# STATUS: Cluster in healthy state

# 2. 데이터 검증
kubectl exec -it postgres-restored-1 -n ibs-prod -c postgres -- \
  psql -U postgres -d ibs -c "SELECT COUNT(*) FROM ibs.accounts_user;"

# 3. Django web pod가 복원된 DB로 접속하도록 서비스 전환
kubectl patch service postgres-rw -n ibs-prod \
  -p '{"spec":{"selector":{"cnpg.io/cluster":"postgres-restored"}}}'

# 4. 검증 후 원본 클러스터 교체 또는 Helm 재배포
```

---

## 7. 백업 상태 모니터링 명령어

```bash
# ScheduledBackup 목록 및 상태
kubectl get scheduledbackup -n ibs-prod

# 실행된 백업 목록
kubectl get backup -n ibs-prod

# 특정 백업 상세 정보
kubectl describe backup <backup-name> -n ibs-prod

# S3에서 직접 백업 파일 목록 확인
mc ls myminio/postgres-backup/postgres/base/
mc ls myminio/postgres-backup/postgres/wals/0000000100000000/

# CNPG 클러스터 백업 설정 확인
kubectl get cluster postgres -n ibs-prod -o jsonpath='{.spec.backup}' | jq .
```

---

## 8. 긴급 수동 백업 트리거

```bash
# kubectl로 직접 Backup CRD 생성 (배포 직전 등)
kubectl create -f - <<EOF
apiVersion: postgresql.cnpg.io/v1
kind: Backup
metadata:
  name: pre-deploy-$(date +%Y%m%d-%H%M%S)
  namespace: ibs-prod
spec:
  method: barmanObjectStore
  cluster:
    name: postgres
EOF

# 또는 GitHub Actions 수동 트리거
# → Actions 탭 → "Database Backup (Manual)" → "Run workflow"
```

---

## 9. 구형 방식 vs 신형 방식 비교

| 항목 | 구형 (pg_dump + NFS) | 신형 (CNPG barman + S3) |
|------|---------------------|------------------------|
| 백업 주기 | 8시간마다 (크론) | 실시간 WAL + 1일 1회 베이스 |
| 최대 데이터 유실 | 최대 8시간 | 수 분 이내 |
| PITR 지원 | ❌ 불가 | ✅ 1초 단위 가능 |
| 복원 정밀도 | 백업 파일 시점만 | 임의 시점 지정 가능 |
| 자동화 | GitHub Actions + SSH | K8s 내부 자동화 |
| 외부 의존성 | CICD 서버 | 없음 (K8s 자체 처리) |
| 보존 관리 | 수동 (`mtime +2` 삭제) | 자동 (`retentionPolicy: 30d`) |
| 저장소 | 시놀로지 NAS (NFS PVC) | 시놀로지 NAS (MinIO S3) |
