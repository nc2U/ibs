# CloudNativePG PostgreSQL Chart for IBS

CloudNativePG 기반의 PostgreSQL 클러스터 Helm 차트입니다. 기존 Bitnami PostgreSQL을 완전히 대체하며, 공식 PostgreSQL 이미지를 사용하여 이미지 풀 에러를 해결합니다.

## 특징

- ✅ **공식 PostgreSQL 이미지 사용**: `postgres:17.2`로 이미지 풀 에러 완전 해결
- ✅ **기존 서비스 호환**: `postgres-primary`, `postgres-read` 서비스로 Django 코드 변경 불필요
- ✅ **자동 레플리케이션**: Primary + Replica 아키텍처 지원
- ✅ **자동 백업**: 스케줄 백업 및 WAL 아카이빙
- ✅ **자동 페일오버**: 장애 시 자동 복구
- ✅ **Kubernetes Native**: CloudNativePG Operator 기반

## 사전 요구사항

- Kubernetes 1.21+
- Helm 3.0+
- CloudNativePG Operator 설치 필요
- NFS 스토리지 클래스 (또는 다른 RWO 스토리지)

## CloudNativePG Operator 설치

Helm 차트를 사용하기 전에 먼저 CloudNativePG Operator를 설치해야 합니다:

```bash
# Operator 설치 (클러스터에 한 번만)
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm repo update
helm install cnpg-operator cnpg/cloudnative-pg \
  --namespace cnpg-system \
  --create-namespace

# 설치 확인
kubectl get pods -n cnpg-system
kubectl get crd | grep postgresql.cnpg.io
```

## 설치 방법

### 옵션 1: Global Values 사용 (권장)

IBS 프로젝트의 `values-prod.yaml` 또는 `values-dev.yaml`에서 global 값을 자동으로 참조합니다:

```bash
# Production 환경
helm install postgres-cnpg ./deploy/helm/charts/cnpg-postgres \
  --namespace ibs-prod \
  -f ./deploy/helm/values-prod.yaml \
  --wait \
  --timeout 10m

# Development 환경
helm install postgres-cnpg ./deploy/helm/charts/cnpg-postgres \
  --namespace ibs-dev \
  -f ./deploy/helm/values-dev.yaml \
  --wait \
  --timeout 10m
```

**참조되는 값:**
- `global.dbPassword` → `auth.postgresPassword` 및 `auth.password`

### 옵션 2: 직접 비밀번호 지정

```bash
helm install postgres-cnpg ./deploy/helm/charts/cnpg-postgres \
  --namespace ibs-prod \
  --set auth.postgresPassword="your-postgres-password" \
  --set auth.password="your-user-password" \
  --wait
```

### 옵션 3: 환경별 Values 파일 생성

```bash
# values-prod.yaml 생성
cat > values-prod.yaml << EOF
global:
  dbPassword: "my-secret"

storage:
  size: "5Gi"

replication:
  instances: 2
EOF

# 설치
helm install postgres-cnpg ./deploy/helm/charts/cnpg-postgres \
  --namespace ibs-prod \
  -f values-prod.yaml
```

## 데이터 복원

### backup.dump에서 복원

```bash
# 1. 클러스터 준비 대기
kubectl wait --for=condition=Ready cluster/postgres -n ibs-prod --timeout=600s

# 2. Primary Pod 확인
PRIMARY_POD=$(kubectl get pods -n ibs-prod \
  -l cnpg.io/cluster=postgres,role=primary \
  -o jsonpath='{.items[0].metadata.name}')

# 3. backup.dump 복사
kubectl cp backup.dump ibs-prod/$PRIMARY_POD:/tmp/backup.dump

# 4. 데이터 복원
kubectl exec -n ibs-prod $PRIMARY_POD -- \
  psql -U postgres -d postgres -f /tmp/backup.dump

# 5. 복원 확인
kubectl exec -n ibs-prod $PRIMARY_POD -- \
  psql -U postgres -d ibs -c "\dt"
```

### 기존 Bitnami PostgreSQL에서 마이그레이션

```bash
# 1. 기존 데이터 백업
kubectl exec -n ibs-prod postgres-primary-0 -- \
  pg_dumpall -U postgres > ibs-full-backup.sql

# 2. CloudNativePG 설치
helm install postgres-cnpg ./deploy/helm/charts/cnpg-postgres \
  --namespace ibs-prod \
  -f ./deploy/helm/values-prod.yaml

# 3. 데이터 복원
PRIMARY_POD=$(kubectl get pods -n ibs-prod \
  -l cnpg.io/cluster=postgres,role=primary \
  -o jsonpath='{.items[0].metadata.name}')

kubectl cp ibs-full-backup.sql ibs-prod/$PRIMARY_POD:/tmp/backup.sql
kubectl exec -n ibs-prod $PRIMARY_POD -- \
  psql -U postgres -f /tmp/backup.sql
```

## 서비스 엔드포인트

CloudNativePG 클러스터는 자동으로 다음 서비스를 생성합니다:

| 서비스 이름 | 용도 | 엔드포인트 |
|------------|------|-----------|
| `postgres-cnpg-primary` | 쓰기 작업 (Primary) | `postgres-cnpg-primary.{NAMESPACE}.svc.cluster.local:5432` |
| `postgres-cnpg-read` | 읽기 작업 (Replica) | `postgres-cnpg-read.{NAMESPACE}.svc.cluster.local:5432` |
| `postgres-rw` | 모든 인스턴스 (읽기/쓰기) | `postgres-rw.{NAMESPACE}.svc.cluster.local:5432` |
| `postgres-ro` | 모든 인스턴스 (읽기 전용) | `postgres-ro.{NAMESPACE}.svc.cluster.local:5432` |

### Django 설정 변경

기존 Bitnami PostgreSQL과 **병행 운영**하기 위해 서비스 이름이 변경되었습니다.

**_config/settings.py 수정 필요:**

```python
# 기존
MASTER_HOST = f'{DATABASE_TYPE}-primary.{NAMESPACE}.svc.cluster.local'
# 변경
MASTER_HOST = f'{DATABASE_TYPE}-cnpg-primary.{NAMESPACE}.svc.cluster.local'

# 기존
'HOST': f'{DATABASE_TYPE}-read.{NAMESPACE}.svc.cluster.local'
# 변경
'HOST': f'{DATABASE_TYPE}-cnpg-read.{NAMESPACE}.svc.cluster.local'
```

또는 환경 변수로 관리:

```bash
# ConfigMap에 추가
DATABASE_PRIMARY_HOST: "postgres-cnpg-primary"
DATABASE_READ_HOST: "postgres-cnpg-read"
```

## 검증

### 클러스터 상태 확인

```bash
# 클러스터 상태
kubectl get cluster -n ibs-prod postgres

# Expected output:
# NAME       AGE   INSTANCES   READY   STATUS                     PRIMARY
# postgres   5m    2           2       Cluster in healthy state   postgres-1

# Pod 상태
kubectl get pods -n ibs-prod -l cnpg.io/cluster=postgres

# 레플리케이션 상태
kubectl exec -n ibs-prod postgres-1 -- \
  psql -U postgres -c "SELECT * FROM pg_stat_replication;"
```

### Django 애플리케이션 연결 테스트

```bash
# Django Pod에서 연결 테스트
kubectl exec -n ibs-prod deployment/web -- \
  python manage.py check --database default

kubectl exec -n ibs-prod deployment/web -- \
  python manage.py check --database replica
```

## 설정 커스터마이징

### 인스턴스 수 변경 (HA 강화)

```yaml
# values.yaml
replication:
  instances: 3  # 1 primary + 2 replicas
```

### 스토리지 증가

```yaml
# values.yaml
storage:
  size: "10Gi"
```

### PgBouncer 연결 풀링 활성화

```yaml
# values.yaml
pgbouncer:
  enabled: true
  instances: 2
  poolMode: "transaction"
  parameters:
    max_client_conn: "1000"
    default_pool_size: "25"
```

### S3 백업 활성화

**중요**: 백업 기능은 기본적으로 비활성화되어 있습니다. S3 자격증명 없이는 활성화할 수 없습니다.

```yaml
# values.yaml
backup:
  enabled: true  # S3 자격증명과 함께 활성화 필요
  s3:
    enabled: true
    bucket: "ibs-postgres-backups"
    region: "ap-northeast-2"
    endpoint: ""  # 선택사항: 커스텀 S3 엔드포인트
    accessKeyId: "YOUR_ACCESS_KEY"
    secretAccessKey: "YOUR_SECRET_KEY"
```

**수동 백업 대안** (S3 없이):

```bash
# pg_dump를 사용한 수동 백업
kubectl exec -n ibs-prod postgres-1 -- \
  pg_dump -U postgres ibs > backup-$(date +%Y%m%d).sql

# 복원
kubectl exec -n ibs-prod postgres-1 -- \
  psql -U postgres -d ibs < backup-20251030.sql
```

### PostgreSQL 파라미터 튜닝

```yaml
# values.yaml
postgresql:
  parameters:
    max_connections: "300"
    shared_buffers: "512MB"
    effective_cache_size: "2GB"
```

## 백업 및 복구

### 수동 백업 생성

```bash
kubectl apply -f - <<EOF
apiVersion: postgresql.cnpg.io/v1
kind: Backup
metadata:
  name: postgres-manual-backup-$(date +%Y%m%d-%H%M%S)
  namespace: ibs-prod
spec:
  cluster:
    name: postgres
EOF

# 백업 상태 확인
kubectl get backup -n ibs-prod
```

### Point-in-Time Recovery (PITR)

```bash
# 특정 시점으로 복구
kubectl apply -f - <<EOF
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-restored
  namespace: ibs-prod
spec:
  instances: 2
  bootstrap:
    recovery:
      source: postgres-backup
      recoveryTarget:
        targetTime: "2025-10-30 14:00:00+09"
  externalClusters:
    - name: postgres-backup
      barmanObjectStore:
        destinationPath: "file:///var/lib/postgresql/backup"
        serverName: postgres
EOF
```

## 모니터링

### 기본 메트릭 확인

```bash
# 클러스터 메트릭
kubectl get cluster -n ibs-prod postgres -o jsonpath='{.status}'

# Pod 메트릭
kubectl top pods -n ibs-prod -l cnpg.io/cluster=postgres
```

### Prometheus 연동 (선택사항)

```yaml
# values.yaml
monitoring:
  enabled: true
```

## 업그레이드

```bash
# 차트 업그레이드
helm upgrade postgres-cnpg ./deploy/helm/charts/cnpg-postgres \
  --namespace ibs-prod \
  -f ./deploy/helm/values-prod.yaml

# 롤링 업그레이드로 무중단 적용됨
```

## 삭제

```bash
# 차트 삭제 (데이터는 PVC에 남음)
helm uninstall postgres-cnpg -n ibs-prod

# PVC도 함께 삭제하려면
kubectl delete pvc -n ibs-prod -l cnpg.io/cluster=postgres
```

## 트러블슈팅

### Pod가 Ready 상태가 되지 않는 경우

```bash
# Operator 로그 확인
kubectl logs -n cnpg-system -l app.kubernetes.io/name=cloudnative-pg

# 클러스터 이벤트 확인
kubectl describe cluster -n ibs-prod postgres

# Pod 이벤트 확인
kubectl describe pod -n ibs-prod postgres-1
```

### 레플리케이션 지연 확인

```bash
kubectl exec -n ibs-prod postgres-1 -- \
  psql -U postgres -c "SELECT * FROM pg_stat_replication;"
```

### 디스크 공간 부족

```bash
# PVC 사용량 확인
kubectl exec -n ibs-prod postgres-1 -- df -h /var/lib/postgresql/data

# PVC 확장 (스토리지 클래스가 지원하는 경우)
kubectl patch pvc postgres-1 -n ibs-prod \
  -p '{"spec":{"resources":{"requests":{"storage":"10Gi"}}}}'
```

## 참고 자료

- [CloudNativePG 공식 문서](https://cloudnative-pg.io/documentation/)
- [PostgreSQL 17 문서](https://www.postgresql.org/docs/17/)
- [IBS 프로젝트 문서](../../README.md)

## 라이선스

Apache-2.0
