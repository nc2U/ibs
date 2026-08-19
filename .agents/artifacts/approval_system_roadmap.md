# 전자결재 시스템 (Electronic Approval System) — 구현 현황 및 개선 로드맵

> 최초 작성: 2026-08-18
> **최종 업데이트: 2026-08-19**
> 작성자: Antigravity AI

---

## 1. 현재 구현 현황

### 1-1. 백엔드 (`app/django/approval/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `models/document_type.py` | ✅ 완료 | `DocumentType`, `RouteTemplate` 모델 |
| `models/document.py` | ✅ 완료 + 🐛 버그 수정 | `doc_number` null 허용 수정 (0002 마이그레이션) |
| `admin.py` | ✅ 완료 | Django Admin Inline 등록 |
| `tasks.py` | ✅ 완료 | Celery: FCM 푸시 알림, WeasyPrint PDF 생성 |
| `templates/approval/pdf_document.html` | ✅ 완료 | PDF 출력용 HTML 양식 |
| `fixtures/approval_document_types.json` | ✅ 완료 | 초기 seed: `업무품의서 (BIZ_APPROVAL)` |
| `migrations/0001_initial.py` | ✅ 완료 | DB 테이블 생성 |
| `migrations/0002_alter_approvaldocument_doc_number.py` | ✅ 완료 | `doc_number` null=True 수정 |

### 1-2. API (`app/django/apiV1/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `serializers/approval.py` | ✅ 완료 + 🐛 버그 수정 | `SimpleUserSerializer.get_full_name()` 수정 |
| `views/approval.py` | ✅ 완료 + 개선 | `select_related`에 `profile` 추가 (N+1 방지) |

#### API 엔드포인트

| Method | Endpoint | 기능 |
|--------|----------|------|
| `GET` | `/api/v1/approval-doc-type/` | 활성 문서 유형 목록 |
| `GET/POST` | `/api/v1/approval-document/` | 문서 목록 / 임시저장 기안 생성 |
| `GET/PATCH/DELETE` | `/api/v1/approval-document/{id}/` | 문서 상세/수정/삭제 |
| `POST` | `/api/v1/approval-document/{id}/submit/` | 상신 (결재선 인스턴스 생성) |
| `POST` | `/api/v1/approval-document/{id}/act/` | 승인 / 반려 / 의견 |
| `POST` | `/api/v1/approval-document/{id}/cancel/` | 기안 취소 |
| `GET` | `/api/v1/approval-document/my_pending/` | 내 결재 대기함 |
| `GET` | `/api/v1/approval-document/my_drafted/` | 내 기안함 |

### 1-3. 프론트엔드 (`app/vue/src/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `store/types/approval.ts` | ✅ 완료 | TypeScript 인터페이스 |
| `store/pinia/approval.ts` | ✅ 완료 | Pinia 스토어 (전체 CRUD + 결재 액션) |
| `router/modules/approval.ts` | ✅ 완료 | 라우터 모듈 |
| `layouts/_nav.ts` | ✅ 완료 | 사이드 네비게이션 등록 |
| `views/approval/Index.vue` | ✅ 완료 | 라우트 기반 컴포넌트 전환 |
| `views/approval/components/PendingList.vue` | ✅ 완료 + 정비 | 사용자 직접 정비 완료 |
| `views/approval/components/DraftedList.vue` | ✅ 완료 + 정비 | 사용자 직접 정비 완료 |
| `views/approval/components/DocumentForm.vue` | ✅ 완료 + 정비 | 사용자 직접 정비 완료 |
| `views/approval/components/DocumentDetail.vue` | ✅ 완료 + 정비 | 사용자 직접 정비 완료 |

---

## 2. 해결된 버그 이력

### 🐛 Bug #1 — `doc_number` UNIQUE constraint 위반 (2026-08-18 해결)

**증상**: `POST /api/v1/approval-document/ 500 Internal Server Error`

**원인**:
```
IntegrityError: duplicate key value violates unique constraint "approval_approvaldocument_doc_number_key"
DETAIL: Key (doc_number)=() already exists.
```
`doc_number` 필드가 `unique=True, blank=True`이나 `null=True`가 없어, 임시저장 문서를 두 번째 생성 시 빈 문자열(`""`)이 중복으로 판정.

**수정**:
```diff
- doc_number = models.CharField(max_length=30, unique=True, blank=True, ...)
+ doc_number = models.CharField(max_length=30, unique=True, blank=True, null=True, default=None, ...)
```
- `0002_alter_approvaldocument_doc_number.py` 마이그레이션 생성 및 적용 완료
- 기존 DB 내 빈 문자열 1건 → `NULL` 변환 완료

---

### 🐛 Bug #2 — `get_full_name()` AttributeError (2026-08-18 해결)

**증상**: 문서 생성 후 응답 직렬화 시 500 오류

**원인**:
```
AttributeError: 'User' object has no attribute 'get_full_name'
```
커스텀 `User` 모델이 `AbstractBaseUser`를 상속받아 Django 기본 `get_full_name()` 메서드 없음.
프로젝트의 이름 필드는 `accounts.Profile.name`에 위치.

**수정** (`apiV1/serializers/approval.py`):
```python
def get_full_name(self, obj):
    try:
        return obj.profile.name or obj.username  # Profile.name 우선, fallback to username
    except Exception:
        return obj.username
```

**추가 개선** (`apiV1/views/approval.py`):
- `select_related`에 `'drafter__profile'` 추가
- `prefetch_related`에 `'steps__approvers__profile'`, `'steps__actions__approver__profile'` 추가
- `my_pending()`, `my_drafted()` 액션에도 동일 적용 → N+1 쿼리 방지

---

## 3. 미구현 / 개선 필요 항목

### 🔴 P1 — 필수 (기능 완성도)

#### 3-1. 완료 문서함 (CompletedList)
- `views/approval/components/CompletedList.vue` 신규 생성
- `_nav.ts`에 `완료 문서함` 서브메뉴 추가
- `/approval/completed` 라우트 추가
- PDF 다운로드 버튼 강조 배치

#### 3-2. 첨부파일 처리
- `DocumentForm.vue`에 파일 업로드 UI 추가 (`<input type="file">`)
- API 호출 시 `multipart/form-data` 헤더 설정
- `approval/attachments/%Y/%m/` 경로에 MinIO/S3 업로드
- 상세 페이지에서 첨부파일 다운로드 링크 표시

#### 3-3. 재상신(Resubmit) 사용자 안내
- 반려 후 재상신 시 "이전 결재 이력이 초기화됩니다" 확인 모달 추가 (현재 `DraftedList`의 상신은 확인 모달 있으나, 재상신 맥락 안내 없음)
- 백엔드: 기존 단계 삭제 전 이력 보존 정책 결정 (현재 CASCADE 삭제)

#### 3-4. 결재 알림 배지 (Notification Badge)
- `_nav.ts`의 `결재 대기함` 메뉴에 `pendingList.length` 배지 연결
- `DefaultLayout.vue` 또는 `App.vue`에서 초기 로드 시 `fetchMyPending()` 호출

---

### 🟡 P2 — 중요 (품질/보안)

#### 3-5. 권한 통제 강화
- 현황: `IsAuthenticated`만 사용
- `approval.read`, `approval.create`, `approval.manage` 권한 코드 정의
- `work.ProjectPermission` 패턴 참고 → `ApprovalPermission` 클래스 구현
- `DocumentType` 관리: `is_superuser` 또는 `work_manager`만 허용

#### 3-6. 최종 승인 문서 잠금(Lock)
- `status=approved` 문서도 `PATCH`/`DELETE` 호출 가능 (보안 취약)
- `perform_update` / `destroy` 오버라이드로 차단
- `ApprovalDocument.save()` 오버라이드에서 validation 추가

#### 3-7. Pagination 적용
- `my_drafted()`, `my_pending()` 전체 목록 반환 → 문서 증가 시 성능 저하
- `PageNumberPaginationTwenty` 적용 + 프론트 페이지네이션 추가

#### 3-8. PDF 생성 실패 재시도
- `generate_approval_pdf_task`에서 예외 발생 시 `print`로만 처리, 재시도 없음
- Celery `max_retries=3`, `countdown=60` 설정
- 실패 시 Slack 알림 연동
- Admin action으로 수동 PDF 재생성 버튼 추가

#### 3-9. PDF 한글 폰트 로컬 처리
- `pdf_document.html`이 Google Fonts CDN 사용 → 컨테이너 네트워크 차단 시 한글 깨짐 가능
- `Dockerfile`에 `fonts-noto-cjk` 패키지 설치
- WeasyPrint 로컬 폰트 참조로 변경:

```css
@font-face {
  font-family: 'NotoSansKR';
  src: local('Noto Sans CJK KR');
}
```

---

### 🟢 P3 — 개선 (UX / 고도화)

#### 3-10. 결재 의견(Comment) 전용 기능
- `ACTION_COMMENTED` 정의됨. UI에서 "의견만 남기기" 버튼 추가, 타임라인 표시

#### 3-11. 결재 요청 메일 발송
- FCM 푸시만 구현. `notify_approvers_task`에 `send_mail()` 추가
- 메일 HTML 템플릿 생성 (`templates/approval/email_notify.html`)

#### 3-12. 대시보드 위젯 연동
- 메인 대시보드에 "내 결재 대기" 카운트 위젯 추가 (`pendingList.length` 활용)

#### 3-13. 관리자용 전체 문서 조회 뷰
- `/approval/all` 라우트 추가 (관리자 전용)
- 필터: 유형, 상태, 기안자, 기간
- 엑셀/CSV 내보내기 (`django-import-export` 활용)

#### 3-14. 문서 유형 관리 Vue UI
- 현재 Django Admin에서만 `DocumentType` / `RouteTemplate` 등록 가능
- 권한 있는 사용자가 Vue에서 직접 관리할 수 있는 UI 추가
- 결재선 단계 드래그-앤-드롭 순서 변경

#### 3-15. 워크스페이스 연동 강화
- `ApprovalDocument.workspace` FK 있으나 API 필터/UI 미구현
- `DocumentForm`에 워크스페이스 선택 드롭다운 추가
- 워크스페이스 상세 페이지에서 연관 결재 문서 목록 표시

---

## 4. 남은 리팩토링 포인트

> 프론트 컴포넌트는 사용자가 직접 정비 완료. 아래는 백엔드 기준 잔여 항목.

### 4-1. `generate_doc_number()` — Race Condition

현황: `count()` 방식은 동시 최종 승인 시 번호 중복 가능.

```python
# 개선: select_for_update + atomic transaction
from django.db import transaction

def generate_doc_number(self):
    with transaction.atomic():
        count = ApprovalDocument.objects.select_for_update().filter(
            doc_type=self.doc_type,
            status=self.STATUS_APPROVED,
            completed_at__year=self.completed_at.year,
        ).count()
        return f'{self.doc_type.code}-{self.completed_at.year}-{str(count).zfill(4)}'
```

### 4-2. `is_completed()` — N+1 쿼리 방지

현황: `ApprovalStep.is_completed()`가 매번 DB 쿼리 실행.
개선: ViewSet의 `prefetch_related('steps__actions')` 이미 적용됨. `is_completed()` 내부에서 prefetch 캐시 활용 여부 재확인 필요.

### 4-3. `submit` 액션 — profile prefetch 누락

현황: `submit` 액션에서 반환하는 `ApprovalDocumentSerializer`가 `select_related` 없이 호출됨.
개선:
```python
# views/approval.py submit 액션 마지막
document.refresh_from_db()  # 또는 get_queryset()으로 재조회
serializer = ApprovalDocumentSerializer(
    self.get_object(),  # get_object()는 get_queryset() 거침
    context={'request': request}
)
```

---

## 5. Flutter 모바일 구현 계획 (미착수)

| 화면 | 설명 | 우선순위 |
|------|------|----------|
| 결재 대기함 | 결재 대기 목록 + FCM 배지 | 🔴 P1 |
| 문서 상세 | 결재선 진행 현황 + 승인/반려 | 🔴 P1 |
| 기안함 | 내 기안 목록 (상태별 필터) | 🟡 P2 |
| 기안서 작성 | 동적 양식 렌더링 + 결재선 선택 | 🟡 P2 |
| PDF 뷰어 | 완료 문서 PDF 인앱 뷰어 | 🟢 P3 |

**FCM 딥링크**: `category: 'approval'` 수신 시 결재 대기함으로 이동 처리 필요.

---

## 6. 테스트 체크리스트

### 백엔드 (미작성)
- [ ] 문서 생성 (임시저장) — 복수 생성 시 `doc_number` 중복 없음 확인
- [ ] 상신 → 결재선 인스턴스 생성 및 FCM 알림 발송 확인
- [ ] AND 조건: 복수 결재자 전원 승인 후 다음 단계 진행
- [ ] OR 조건: 1인 승인으로 다음 단계 진행
- [ ] 반려 후 재상신 검증 (기존 단계 초기화 확인)
- [ ] `generate_doc_number()` 중복 방지 검증
- [ ] 최종 승인 후 PDF Celery 태스크 트리거 검증
- [ ] 승인된 문서 수정/삭제 차단 검증 (3-6 완료 후)

### 프론트엔드 (✅ 컴포넌트 정비 완료 — 기능 테스트 필요)
- [ ] `DocumentForm`: 문서 생성 후 임시저장 → 상신 플로우
- [ ] `PendingList`: 검색 필터 + 결재 모달 승인/반려
- [ ] `DraftedList`: 상태 필터 + 상신/취소 모달
- [ ] `DocumentDetail`: 결재선 타임라인 + 진행률 표시 + 내 결재 버튼 노출

---

## 7. 관련 파일 위치 참조

```
app/django/
├── approval/
│   ├── models/
│   │   ├── document_type.py      # DocumentType, RouteTemplate
│   │   └── document.py           # ApprovalDocument(🐛수정), ApprovalStep, ApprovalAction
│   ├── admin.py
│   ├── tasks.py                  # Celery: FCM 알림, WeasyPrint PDF 생성
│   ├── templates/approval/
│   │   └── pdf_document.html
│   ├── fixtures/
│   │   └── approval_document_types.json
│   └── migrations/
│       ├── 0001_initial.py
│       └── 0002_alter_approvaldocument_doc_number.py  # 🐛 null 수정
├── apiV1/
│   ├── serializers/approval.py   # 🐛 get_full_name → profile.name 수정
│   └── views/approval.py         # profile select_related 추가

app/vue/src/
├── store/
│   ├── types/approval.ts
│   └── pinia/approval.ts
├── router/modules/approval.ts
├── layouts/_nav.ts
└── views/approval/
    ├── Index.vue
    └── components/
        ├── PendingList.vue       # ✅ 사용자 정비 완료
        ├── DraftedList.vue       # ✅ 사용자 정비 완료
        ├── DocumentForm.vue      # ✅ 사용자 정비 완료
        └── DocumentDetail.vue    # ✅ 사용자 정비 완료
```

---

## 8. 우선순위별 다음 작업 순서

```
즉시 (v0.2)
  1. 완료 문서함 뷰 추가                                   (3-1)
  2. 첨부파일 업로드 UI 추가                               (3-2)
  3. 결재 대기 네비게이션 배지 연결                         (3-4)
  4. submit 액션 profile prefetch 누락 수정                (4-3)

단기 (v0.3)
  5. 최종 승인 문서 잠금(Lock) 처리                        (3-6)
  6. PDF 한글 폰트 로컬 처리 (Dockerfile 수정)             (3-9)
  7. Pagination 적용                                      (3-7)
  8. generate_doc_number Race Condition 수정               (4-1)

중기 (v0.4)
  9. ApprovalPermission 클래스 구현                       (3-5)
 10. 결재 요청 메일 발송                                   (3-11)
 11. 관리자 전체 문서 조회 뷰                               (3-13)
 12. 워크스페이스 연동 강화                                 (3-15)

장기 (v1.0)
 13. Flutter 모바일 결재함 구현
 14. 결재 통계 대시보드 위젯                               (3-12)
 15. 문서 유형 관리 Vue UI                                 (3-14)
```
