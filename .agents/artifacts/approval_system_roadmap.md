# 전자결재 시스템 (Electronic Approval System) — 구현 현황 및 개선 로드맵

> 최초 작성: 2026-08-18
> **최종 업데이트: 2026-08-20 (결재 카테고리, 금액별 조건부 전결 정책, 기안 권한 제어 연동)**
> 작성자: Antigravity AI

---

## 1. 현재 구현 현황

### 1-1. 백엔드 (`app/django/approval/` 및 `company/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `approval/models/document_type.py` | ✅ 완료 | `DocCategory` (카테고리), `ApprovalPolicyRule` (금액별 전결), 기안 권한 필드 추가 |
| `company/models.py` | ✅ 완료 | `StaffAssignment` (보직/겸직/대표권), `Department.save()` 자동 레벨 계산 |
| `approval/models/document.py` | ✅ 완료 | `drafter_assignment` (기안 보직 연결), `doc_number` null 허용 |
| `approval/services/route_builder.py` | ✅ 완료 | **조직도 기반 동적 결재선 + 금액별 조건부 전결 규칙 평가 엔진** |
| `approval/admin.py` | ✅ 완료 | `DocCategoryAdmin`, `ApprovalPolicyRuleInline`, M2M 필터 등록 |
| `approval/tasks.py` | ✅ 완료 | Celery: FCM 푸시 알림, WeasyPrint PDF 생성 |
| `approval/templates/approval/pdf_document.html` | ✅ 완료 | PDF 출력용 HTML 양식 |
| `approval/migrations/0004_...` | ✅ 완료 | 카테고리 및 조건부 전결 정책 DB 반영 완료 |

### 1-2. API (`app/django/apiV1/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `serializers/approval.py` | ✅ 완료 | `DocCategorySerializer`, `ApprovalPolicyRuleSerializer`, `DocumentTypeSerializer` 확장 |
| `views/approval.py` | ✅ 완료 | `DocCategoryViewSet` (`/api/v1/approval-doc-category/`), `for_draft` 기안 권한 필터링 액션, `preview_route` 금액(amount) 파라미터 지원 |

#### API 엔드포인트

| Method | Endpoint | 기능 |
|--------|----------|------|
| `GET` | `/api/v1/approval-doc-category/` | **결재 카테고리 목록 (인사/근태, 회계/자금 등)** |
| `GET` | `/api/v1/approval-doc-type/` | 활성 문서 유형 목록 |
| `GET` | `/api/v1/approval-doc-type/for_draft/` | **기안자의 소속 부서/직책에 따라 기안 가능한 문서 유형만 필터링** |
| `GET/POST` | `/api/v1/approval-document/` | 문서 목록 / 임시저장 기안 생성 |
| `GET/PATCH/DELETE` | `/api/v1/approval-document/{id}/` | 문서 상세/수정/삭제 |
| `GET` | `/api/v1/approval-document/my_assignments/` | 기안자의 주보직/겸직 목록 조회 |
| `GET` | `/api/v1/approval-document/preview_route/` | **문서유형/보직/금액(amount) 기준 실시간 결재선 미리보기** |
| `POST` | `/api/v1/approval-document/{id}/submit/` | 상신 (동적 결재선 자동 생성 + 결재 알림) |
| `POST` | `/api/v1/approval-document/{id}/act/` | 승인 / 반려 / 의견 |
| `POST` | `/api/v1/approval-document/{id}/cancel/` | 기안 취소 |
| `GET` | `/api/v1/approval-document/my_pending/` | 내 결재 대기함 |
| `GET` | `/api/v1/approval-document/my_drafted/` | 내 기안함 |

### 1-3. 프론트엔드 (`app/vue/src/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `store/types/approval.ts` | ✅ 완료 | `DocCategory`, `ApprovalPolicyRule`, `DocumentType` 타입 확장 |
| `store/pinia/approval.ts` | ✅ 완료 | `fetchDocCategoryList`, `fetchForDraftDocTypeList`, `previewRoute(amount)` 액션 |
| `views/approval/components/DocumentForm.vue` | ✅ 완료 | **카테고리별 optgroup 그룹화 + 기안 권한 필터링 + 금액 입력 시 실시간 전결 결재선 변경** |
| `views/approval/components/DocumentDetail.vue` | ✅ 완료 | 기안자 소속 보직 표출 + 결재선 타임라인 |
| `views/approval/components/PendingList.vue` | ✅ 완료 | 결재 대기함 |
| `views/approval/components/DraftedList.vue` | ✅ 완료 | 기안함 |

---

## 2. 동적 결재선 및 조건부 전결 정책 (Approval Policy Rules) 아키텍처

### 2-1. 핵심 평가 흐름

```
[1. 기안 작성]
   - 기안 보직 선택 (주보직/겸직)
   - 기안 가능한 문서 유형 선택 (카테고리별 그룹화)
   - 양식 필드에 금액(amount) 입력
   ↓
[2. 조건부 전결 정책 (ApprovalPolicyRule) 평가]
   - 입력된 금액이 속하는 정책 규칙 매칭
   - 예: 500만원 이하 -> 팀장 전결
   - 예: 500만원 초과 ~ 5,000만원 이하 -> 본부장 전결
   - 예: 5,000만원 초과 -> 대표이사 최종 승인
   ↓
[3. 조직도 트리 상향 탐색 (Department Traversal)]
   - 직속 부서 책임자 -> 상위 부서 책임자 -> ...
   - 매칭된 전결 직책/부서 레벨 도달 시 결재선 즉시 종료
   - 전결에 미도달한 경우 대표이사(공동대표 AND / 단독대표 OR) 최종 결재 추가
   ↓
[4. 실시간 UI 반영]
   - 사용자가 금액을 수정할 때마다 결재선 미리보기가 즉시 반응형으로 단축/확장
```

### 2-2. 기안 권한 통제 (RBAC on DocumentType)
* `allowed_departments`: 특정 부서만 기안 가능한 문서 제한 (비어있으면 전사 공통)
* `allowed_duties`: 특정 직책(팀장 이상 등)만 기안 가능한 문서 제한
* `allowed_positions`: 특정 직위만 기안 가능한 문서 제한
* 프론트엔드에서는 `for_draft` API를 호출하여 현재 선택한 보직에서 기안할 수 있는 문서만 셀렉트박스에 노출.

---

## 3. 해결된 버그 이력

### 🐛 Bug #1 — `doc_number` UNIQUE constraint 위반 (2026-08-18 해결)
- `doc_number` 필드가 `unique=True, blank=True`이나 `null=True`가 없어 임시저장 빈 문자열 중복 에러 발생.
- `null=True, default=None` 수정 및 0002 마이그레이션 적용.

### 🐛 Bug #2 — `get_full_name()` AttributeError (2026-08-18 해결)
- 커스텀 `User` 모델에 `get_full_name()`이 없어 직렬화 에러 발생.
- `Profile.name` 우선 조회 및 `select_related('drafter__profile')` 적용.

### 🐛 Bug #3 — 신입/일반 직원 기안 시 자동 승인되는 문제 (2026-08-19 해결)
- 결재자가 0명일 때 무조건 자동 승인 처리하던 로직으로 인해, 부서장/대표이사 계정 미연동 시 일반 직원 기안이 즉시 최종 승인되는 결함 발생.
- **오직 대표이사 본인 기안인 경우에만 자동 승인**하도록 검증 조건을 강화하고, 일반 직원은 400 에러로 상신을 차단하도록 수정.

---

## 4. 미구현 / 개선 필요 항목

### 🔴 P1 — 필수 (기능 완성도)

#### 4-1. 완료 문서함 (CompletedList)
- `views/approval/components/CompletedList.vue` 신규 생성
- `_nav.ts`에 `완료 문서함` 서브메뉴 추가
- `/approval/completed` 라우트 추가 및 PDF 다운로드 강조

#### 4-2. 첨부파일 처리
- `DocumentForm.vue`에 파일 업로드 UI 추가 (`<input type="file">`)
- API 호출 시 `multipart/form-data` 헤더 설정
- `approval/attachments/%Y/%m/` 경로에 MinIO/S3 업로드 및 상세 페이지 다운로드 링크 제공

#### 4-3. 재상신(Resubmit) 사용자 안내
- 반려 후 재상신 시 "이전 결재 이력이 초기화됩니다" 확인 모달 추가
- 기존 단계 삭제 전 로그 보존 정책 결정

#### 4-4. 결재 알림 배지 (Notification Badge)
- `_nav.ts`의 `결재 대기함` 메뉴에 `pendingList.length` 실시간 배지 연결

---

### 🟡 P2 — 중요 (품질/보안)

#### 4-5. 권한 통제 강화
- `ApprovalPermission` 클래스 구현 (`approval.read`, `approval.create`, `approval.manage`)
- `DocumentType` 관리: `is_superuser` 또는 `work_manager`만 허용

#### 4-6. 최종 승인 문서 잠금(Lock)
- `status=approved` 문서에 대한 `PATCH`/`DELETE` API 호출 차단 (`perform_update`, `destroy` 오버라이드)

#### 4-7. Pagination 적용
- `my_drafted()`, `my_pending()` 목록 조회 시 `PageNumberPaginationTwenty` 및 페이지네이션 UI 연동

#### 4-8. PDF 생성 실패 재시도
- `generate_approval_pdf_task` Celery `max_retries=3` 자동 재시도 및 Slack 알림 연동

#### 4-9. PDF 한글 폰트 로컬 처리
- `Dockerfile`에 `fonts-noto-cjk` 설치 및 WeasyPrint 로컬 폰트 참조 설정

---

### 🟢 P3 — 개선 (UX / 고도화)

#### 4-10. 결재 의견(Comment) 전용 기능
- `ACTION_COMMENTED` 전용 "의견만 남기기" 버튼 및 타임라인 표시

#### 4-11. 결재 요청 메일 발송
- `notify_approvers_task`에 이메일 발송 (`send_mail`) 추가

#### 4-12. 대시보드 위젯 연동
- 메인 대시보드에 "내 결재 대기" 건수 카드 위젯 추가

#### 4-13. 관리자용 전체 문서 조회 뷰
- `/approval/all` 라우트 (관리자 전용 전체 결재 문서 현황 및 엑셀 다운로드)

#### 4-14. 문서 유형 관리 Vue UI
- 관리자가 Vue 화면에서 문서 유형 양식(`form_schema`), 결재 방식(`route_type`), 전결 직책, 조건부 정책 규칙을 직접 등록/수정하는 UI

---

## 5. 남은 리팩토링 포인트

### 5-1. `generate_doc_number()` — Race Condition 방지
```python
with transaction.atomic():
    count = ApprovalDocument.objects.select_for_update().filter(
        doc_type=self.doc_type,
        status=self.STATUS_APPROVED,
        completed_at__year=self.completed_at.year,
    ).count()
    return f'{self.doc_type.code}-{self.completed_at.year}-{str(count).zfill(4)}'
```

---

## 6. 관련 파일 위치 참조

```
app/django/
├── company/
│   ├── models.py                 # Staff, StaffAssignment, Department(save 레벨 자동계산)
│   └── admin.py                  # StaffAssignmentInline
├── approval/
│   ├── models/
│   │   ├── document_type.py      # DocCategory, DocumentType(기안권한/카테고리), ApprovalPolicyRule
│   │   └── document.py           # ApprovalDocument (drafter_assignment 연결)
│   ├── services/
│   │   └── route_builder.py      # ⭐ 동적 결재선 및 조건부 전결 정책 평가 엔진
│   ├── admin.py
│   ├── tasks.py                  # Celery: FCM 알림, WeasyPrint PDF 생성
│   └── migrations/
│       ├── 0001_initial.py
│       ├── 0002_alter_approvaldocument_doc_number.py
│       ├── 0003_approvaldocument_drafter_assignment_and_more.py
│       └── 0004_doccategory_alter_documenttype_options_and_more.py
├── apiV1/
│   ├── serializers/
│   │   ├── company.py            # StaffAssignmentSerializer
│   │   └── approval.py           # DocCategorySerializer, ApprovalPolicyRuleSerializer
│   └── views/
│       ├── company.py            # StaffAssignmentViewSet
│       └── approval.py           # DocCategoryViewSet, for_draft, preview_route(amount), submit

app/vue/src/
├── store/
│   ├── types/approval.ts         # DocCategory, ApprovalPolicyRule, DocumentType
│   └── pinia/approval.ts         # fetchDocCategoryList, fetchForDraftDocTypeList, previewRoute(amount)
├── router/modules/approval.ts
├── layouts/_nav.ts
└── views/approval/
    ├── Index.vue
    └── components/
        ├── DocumentForm.vue      # ⭐ 카테고리 optgroup + 기안 권한 필터 + 실시간 금액별 전결 결재선 미리보기
        ├── DocumentDetail.vue    # 기안 보직 표출 + 결재 타임라인
        ├── PendingList.vue       # 결재 대기함
        └── DraftedList.vue       # 기안함
```
