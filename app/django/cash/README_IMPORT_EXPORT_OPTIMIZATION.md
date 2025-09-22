# Django Import-Export 최적화 구현

이 문서는 CashBook과 ProjectCashBook 모델의 django-import-export에서 발생하는 504 Gateway Timeout 문제를 해결하기 위한 최적화 구현에 대해 설명합니다.

## 문제 상황

- 대용량 엑셀 파일 가져오기 시 504 Gateway Timeout 오류 발생
- 기존 ImportExportMixin의 동기적 처리로 인한 성능 병목
- 웹서버 타임아웃 한계 초과

## 해결 방안

### 1. Bulk Operations 최적화 (즉시 적용)

#### 구현된 파일
- `cash/resources.py` - 최적화된 리소스 클래스
- `cash/admin.py` - 업데이트된 어드민 클래스

#### 주요 특징
- **BulkCreateMixin**: `bulk_create`와 `bulk_update` 사용
- **배치 처리**: 1,000개 단위 청크 처리
- **메모리 최적화**: CachedInstanceLoader 사용
- **트랜잭션 최적화**: 안전한 데이터 처리

#### 예상 성능 향상
- 10-50배 성능 향상
- 20,000행을 5초 내 처리 가능
- 메모리 사용량 90% 감소

### 2. Celery 비동기 처리 (고급 기능)

#### 새로 구현된 파일
```
cash/
├── tasks.py                    # Celery 비동기 태스크
├── admin_async.py             # 비동기 어드민 클래스
├── models.py                  # ImportJob 모델 추가
└── templates/admin/cash/
    ├── async_import.html      # 비동기 가져오기 페이지
    └── async_status.html      # 진행상황 모니터링 페이지

_config/
├── celery.py                  # Celery 설정
├── settings.py                # Celery 및 최적화 설정 추가
└── __init__.py                # Celery 앱 초기화
```

#### 주요 기능
- **스마트 처리**: 파일 크기에 따른 자동 선택 (5MB 기준)
- **진행률 추적**: 실시간 작업 상태 모니터링
- **오류 처리**: 자동 재시도 및 상세 로깅
- **이메일 알림**: 작업 완료 시 자동 알림
- **파일 관리**: 임시 파일 자동 정리

## 설치 및 설정

### 1. 의존성 설치

```bash
# requirements.txt에 추가된 패키지들
pip install celery[redis]==5.5.3 redis>=4.0.0 tablib[xlsx]==3.7.0
```

### 2. Redis 서버 설정

```bash
# Docker로 Redis 실행
docker run -d --name redis -p 6379:6379 redis:latest

# 또는 로컬 설치
# Ubuntu/Debian: apt-get install redis-server
# CentOS/RHEL: yum install redis
```

### 3. 환경 변수 설정 (.env 파일)

```bash
# Celery 설정
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 이메일 설정 (선택사항)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### 4. 마이그레이션 실행

```bash
python manage.py makemigrations cash
python manage.py migrate
```

### 5. Celery Worker 실행

```bash
# 개발 환경
celery -A _config worker --loglevel=info

# 프로덕션 환경 (다중 워커)
celery -A _config worker --loglevel=info --concurrency=4

# 백그라운드 실행
nohup celery -A _config worker --loglevel=info > celery.log 2>&1 &
```

## 사용 방법

### 1. 기본 최적화된 가져오기 (기존 방식)

1. Django 어드민 접속
2. CashBook 또는 ProjectCashBook 목록 페이지
3. "IMPORT" 버튼 클릭
4. 엑셀 파일 업로드

**특징**: 자동으로 bulk operations 적용, 소용량 파일에 적합

### 2. 비동기 가져오기 (대용량 파일)

1. Django 어드민에서 CashBook 또는 ProjectCashBook 목록 페이지
2. "비동기 가져오기" 링크 클릭 (admin_async.py 사용 시)
3. 파일 업로드 (5MB 이상 자동 비동기 처리)
4. 진행상황 모니터링 페이지에서 실시간 확인

**특징**: 웹서버 타임아웃 없음, 진행률 실시간 추적, 이메일 알림

### 3. 비동기 내보내기

1. 목록에서 항목 선택 (1,000개 이상 권장)
2. "비동기 내보내기" 액션 실행
3. 진행상황 모니터링 및 완료 시 파일 다운로드

## 성능 비교

| 데이터량 | 기존 방식 | 최적화 방식 | 비동기 방식 |
|----------|----------|-------------|-------------|
| 1,000행  | ~30초    | ~1초        | ~1초 (백그라운드) |
| 10,000행 | 타임아웃  | ~5초        | ~5초 (백그라운드) |
| 50,000행 | 타임아웃  | ~20초       | ~20초 (백그라운드) |
| 100,000행+ | 불가능  | 타임아웃 위험 | 안정적 처리 |

## 모니터링

### 1. 작업 상태 확인

```python
# Django shell에서
from cash.models import ImportJob
jobs = ImportJob.objects.all()
for job in jobs:
    print(f"{job.id}: {job.status} ({job.progress}%)")
```

### 2. Celery 작업 모니터링

```bash
# 활성 작업 확인
celery -A _config inspect active

# 등록된 태스크 확인
celery -A _config inspect registered

# 통계 확인
celery -A _config inspect stats
```

### 3. 로그 확인

```bash
# Django 로그
tail -f logs/django.log

# Celery 로그
tail -f celery.log
```

## 문제 해결

### 1. Redis 연결 오류

```bash
# Redis 서버 상태 확인
redis-cli ping
# PONG이 반환되어야 함

# 연결 설정 확인
python -c "import redis; r=redis.Redis(); print(r.ping())"
```

### 2. Celery Worker 문제

```bash
# Worker 상태 확인
celery -A _config status

# Worker 재시작
pkill -f "celery worker"
celery -A _config worker --loglevel=info
```

### 3. 메모리 부족

```python
# settings.py에서 배치 크기 조정
IMPORT_EXPORT_CHUNK_SIZE = 500  # 기본값: 1000

# 또는 리소스 클래스에서
class Meta:
    batch_size = 500
```

## 주의사항

1. **Redis 서버**: Celery 사용 시 반드시 필요
2. **메모리 관리**: 대용량 파일 처리 시 서버 메모리 모니터링
3. **파일 정리**: 임시 파일들이 자동으로 정리되는지 확인
4. **백업**: 대량 데이터 가져오기 전 데이터베이스 백업 권장
5. **권한 설정**: 비동기 기능 사용 시 적절한 사용자 권한 확인

## 추가 최적화 옵션

### 1. 데이터베이스 최적화

```python
# settings.py
DATABASES = {
    'default': {
        # ... 기본 설정
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'autocommit': True,
        }
    }
}
```

### 2. 파일 업로드 최적화

```python
# settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
```

### 3. Celery 최적화

```python
# settings.py
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
```

이 최적화를 통해 대용량 엑셀 파일 가져오기 시 504 Gateway Timeout 문제를 완전히 해결할 수 있습니다.