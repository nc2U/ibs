#!/bin/bash
# CloudNativePG 수동 백업 스크립트
#
# 사용법:
#   sh manual-backup.sh [dev|prod]
#   sh manual-backup.sh prod
#   sh manual-backup.sh dev
#   sh manual-backup.sh           # 기본값: dev
#
set -e

# 첫 번째 인자로 환경 설정
ENV_ARG="${1:-}"

# 환경 인자 처리
if [ -n "$ENV_ARG" ]; then
  if [ "$ENV_ARG" = "prod" ]; then
    NAMESPACE="ibs-prod"
    ENV="prod"
  elif [ "$ENV_ARG" = "dev" ]; then
    NAMESPACE="ibs-dev"
    ENV="dev"
  else
    echo "❌ Error: Invalid environment '$ENV_ARG'"
    echo "Usage: $0 [dev|prod]"
    echo "  dev  - Development environment (ibs-dev)"
    echo "  prod - Production environment (ibs-prod)"
    exit 1
  fi
else
  # 환경 변수로 설정 (기존 방식 호환)
  NAMESPACE="${NAMESPACE:-ibs-dev}"
  ENV="${ENV:-dev}"
fi

RELEASE="${RELEASE:-ibs}"

# 환경별 PVC 이름 설정 (Helm 템플릿 패턴 일치)
if [ "$NAMESPACE" = "ibs-prod" ]; then
  BACKUP_PVC="postgres-backup-prod-pvc"
else
  BACKUP_PVC="postgres-backup-dev-pvc"
fi

echo "=========================================="
echo "CloudNativePG Manual Backup"
echo "=========================================="
echo "Namespace: $NAMESPACE"
echo "Release: $RELEASE"
echo "Backup PVC: $BACKUP_PVC"
echo ""

# postgres 비밀번호 확인 및 동기화
echo "🔑 Verifying postgres password..."
echo "----------------------------------------"

# Primary pod 찾기
PRIMARY_POD=$(kubectl get pods -n "$NAMESPACE" -l "cnpg.io/cluster=postgres,role=primary" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$PRIMARY_POD" ]; then
    echo "❌ Error: Cannot find primary postgres pod"
    exit 1
fi

echo "Primary pod: $PRIMARY_POD"

# Secret에서 비밀번호 읽기
EXPECTED_PASSWORD=$(kubectl get secret -n "$NAMESPACE" postgres-superuser -o jsonpath='{.data.password}' 2>/dev/null | base64 -d)

if [ -z "$EXPECTED_PASSWORD" ]; then
    echo "❌ Error: Cannot read password from secret postgres-superuser"
    exit 1
fi

echo "Testing postgres authentication..."

# postgres 서비스로 연결 테스트
if kubectl exec -n "$NAMESPACE" "$PRIMARY_POD" -c postgres -- bash -c "PGPASSWORD='$EXPECTED_PASSWORD' psql -h postgres-rw -U postgres -d ibs -c 'SELECT 1;'" > /dev/null 2>&1; then
    echo "✅ postgres password is correct"
else
    echo "⚠️  postgres password mismatch detected"
    echo "🔧 Setting postgres password to match secret..."

    if kubectl exec -n "$NAMESPACE" "$PRIMARY_POD" -c postgres -- psql -U postgres -c "ALTER USER postgres WITH PASSWORD '$EXPECTED_PASSWORD';" > /dev/null 2>&1; then
        echo "✅ postgres password updated successfully"

        # 비밀번호 변경 후 재확인
        sleep 2
        if kubectl exec -n "$NAMESPACE" "$PRIMARY_POD" -c postgres -- bash -c "PGPASSWORD='$EXPECTED_PASSWORD' psql -h postgres-rw -U postgres -d ibs -c 'SELECT 1;'" > /dev/null 2>&1; then
            echo "✅ Password verified after update"
        else
            echo "❌ Error: Password verification failed after update"
            exit 1
        fi
    else
        echo "❌ Error: Failed to update postgres password"
        exit 1
    fi
fi

echo ""

# Job 이름 생성 (타임스탬프 포함)
JOB_NAME="postgres-backup-manual-$(date +%Y%m%d-%H%M%S)"

# CronJob 존재 확인
CRONJOB_NAME="postgres-backup"
# kubectl alias 우회를 위해 출력 결과를 직접 체크
# set -e 우회: || true로 에러 무시
CRONJOB_CHECK=$(kubectl get cronjob -n "$NAMESPACE" "$CRONJOB_NAME" 2>&1 || true)
if echo "$CRONJOB_CHECK" | grep -q "NotFound"; then
    echo "⚠️  CronJob not found, creating standalone backup job..."
    echo "This is normal for dev environment (manual backup only)"
    echo ""
elif [ -z "$CRONJOB_CHECK" ]; then
    echo "⚠️  Cannot check CronJob, creating standalone backup job..."
    echo ""
else
    echo "✅ CronJob '$CRONJOB_NAME' found, creating job from CronJob..."

    # Job 생성 및 성공 확인 (ShellCheck 권장 방식)
    if kubectl create job -n "$NAMESPACE" "$JOB_NAME" --from="cronjob/$CRONJOB_NAME"; then
        echo ""
        echo "✅ Backup job created successfully!"
        echo ""
        echo "Monitor progress with:"
        echo "  kubectl get jobs -n $NAMESPACE"
        echo "  kubectl logs -n $NAMESPACE job/$JOB_NAME -f"
        echo ""

        # 자동으로 로그 따라가기 (옵션)
        if [ "${FOLLOW_LOGS:-true}" = "true" ]; then
            echo "Following logs (Ctrl+C to stop)..."
            echo "----------------------------------------"
            kubectl wait --for=condition=ready pod -n "$NAMESPACE" -l "job-name=$JOB_NAME" --timeout=30s
            kubectl logs -n "$NAMESPACE" -l "job-name=$JOB_NAME" -f
        fi
        exit 0
    fi
    echo "⚠️  Failed to create job from CronJob, falling back to standalone job..."
    echo ""

    # 직접 Job manifest 생성
    TEMP_JOB=$(mktemp)

    cat > "$TEMP_JOB" <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: ${JOB_NAME}
  namespace: ${NAMESPACE}
spec:
  ttlSecondsAfterFinished: 300
  template:
    metadata:
      labels:
        app.kubernetes.io/name: postgres
        app.kubernetes.io/component: backup
    spec:
      restartPolicy: OnFailure
      automountServiceAccountToken: false
      containers:
        - name: postgres-backup
          image: postgres:18.0
          imagePullPolicy: IfNotPresent
          command:
            - /bin/bash
            - -c
            - |
              set -eu

              # CloudNativePG 환경 변수 설정
              DATE=\$(date +"%Y-%m-%d-%H%M%S")
              DUMP_FILE=/var/backups/ibs-backup-postgres-\${DATE}.dump
              POSTGRES_SCHEMA="ibs"
              POSTGRES_DATABASE="ibs"
              POSTGRES_USER="postgres"
              POSTGRES_PASSWORD=\$(cat /run/secrets/postgres-password)
              PSQL_HOST="postgres-rw"

              # 이전 백업 삭제 (2일 이상된 파일)
              find /var/backups \( -name "*.dump" -o -name "*.log" \) -type f -mtime +2 -delete

              if [ -f "\$DUMP_FILE" ]; then
                  rm "\$DUMP_FILE"
              fi

              echo "Starting PostgreSQL backup: \${DUMP_FILE}"

              # pg_dump로 백업 실행
              PGPASSWORD="\$POSTGRES_PASSWORD" pg_dump \\
                -h "\$PSQL_HOST" \\
                -U "\$POSTGRES_USER" \\
                -d "\$POSTGRES_DATABASE" \\
                -n "\$POSTGRES_SCHEMA" \\
                --data-only \\
                --exclude-table="\${POSTGRES_SCHEMA}.django_migrations" \\
                --column-inserts \\
                -Fc \\
                -f "\$DUMP_FILE"

              # 퍼미션 변경
              chmod 644 \${DUMP_FILE}

              # 백업 성공 확인
              if [ \$? -eq 0 ]; then
                  echo "PostgreSQL Backup completed successfully: \${DUMP_FILE}"
                  ls -lh "\$DUMP_FILE"
              else
                  echo "PostgreSQL Backup failed." >&2
                  exit 1
              fi
          volumeMounts:
            - name: backup-volume
              mountPath: /var/backups
            - name: postgres-password
              mountPath: /run/secrets
              readOnly: true
      volumes:
        - name: backup-volume
          persistentVolumeClaim:
            claimName: ${BACKUP_PVC}
        - name: postgres-password
          secret:
            secretName: postgres-superuser
            items:
              - key: password
                path: postgres-password
EOF

    # Job 생성
    kubectl apply -f "$TEMP_JOB"
    rm "$TEMP_JOB"
fi

echo ""
echo "✅ Backup job created successfully!"
echo ""
echo "Monitor progress with:"
echo "  kubectl get jobs -n $NAMESPACE"
echo "  kubectl logs -n $NAMESPACE job/$JOB_NAME -f"
echo ""
echo "Check backup files:"
echo "  kubectl exec -n $NAMESPACE -l job-name=$JOB_NAME -- ls -lh /var/backups/"
echo ""

# 자동으로 로그 따라가기 (옵션)
if [ "${FOLLOW_LOGS:-true}" = "true" ]; then
    echo "Following logs (Ctrl+C to stop)..."
    echo "----------------------------------------"
    kubectl wait --for=condition=ready pod -n "$NAMESPACE" -l "job-name=$JOB_NAME" --timeout=30s
    kubectl logs -n "$NAMESPACE" -l "job-name=$JOB_NAME" -f
fi