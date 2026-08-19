# 전자결재 시스템 (Electronic Approval System) — 구현 현황 및 개선 로드맵

> 최초 작성: 2026-08-18
> **최종 업데이트: 2026-08-20 (DYNAMIC / STATIC 하이브리드 전용 폼 시스템 연동)**
> 작성자: Antigravity AI

---

## 1. 현재 구현 현황

### 1-1. 백엔드 (`app/django/approval/` 및 `company/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `approval/models/document_type.py` | ✅ 완료 | `DocCategory`, `ApprovalPolicyRule`, `form_type`(`DYNAMIC`/`STATIC`), `form_template_key` 추가 |
| `company/models.py` | ✅ 완료 | `StaffAssignment` (보직/겸직/대표권), `Department.save()` 자동 레벨 계산 |
| `approval/models/document.py` | ✅ 완료 | `drafter_assignment` (기안 보직 연결), `doc_number` null 허용 |
| `approval/services/route_builder.py` | ✅ 완료 | **조직도 기반 동적 결재선 + 금액별 조건부 전결 규칙 평가 엔진** |
| `approval/admin.py` | ✅ 완료 | `DocCategoryAdmin`, `ApprovalPolicyRuleInline`, `form_type` 관리 |
| `approval/tasks.py` | ✅ 완료 | Celery: FCM 푸시 알림, WeasyPrint PDF 생성 |
| `approval/templates/approval/pdf_document.html` | ✅ 완료 | PDF 출력용 HTML 양식 |
| `approval/migrations/0005_...` | ✅ 완료 | `form_type`, `form_template_key` DB 반영 완료 |

### 1-2. API (`app/django/apiV1/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `serializers/approval.py` | ✅ 완료 | `DocCategorySerializer`, `ApprovalPolicyRuleSerializer`, `form_type`/`form_template_key` 직렬화 |
| `views/approval.py` | ✅ 완료 | `DocCategoryViewSet`, `for_draft` 권한 필터링, `preview_route` 실시간 금액 연동 |

#### API 엔드포인트

| Method | Endpoint | 기능 |
|--------|----------|------|
| `GET` | `/api/v1/approval-doc-category/` | 결재 카테고리 목록 (인사/근태, 회계/자금 등) |
| `GET` | `/api/v1/approval-doc-type/` | 활성 문서 유형 목록 |
| `GET` | `/api/v1/approval-doc-type/for_draft/` | 기안자의 소속 부서/직책에 따라 기안 가능한 문서 유형만 필터링 |
| `GET/POST` | `/api/v1/approval-document/` | 문서 목록 / 임시저장 기안 생성 |
| `GET/PATCH/DELETE` | `/api/v1/approval-document/{id}/` | 문서 상세/수정/삭제 |
| `GET` | `/api/v1/approval-document/my_assignments/` | 기안자의 주보직/겸직 목록 조회 |
| `GET` | `/api/v1/approval-document/preview_route/` | 문서유형/보직/금액(amount) 기준 실시간 결재선 미리보기 |
| `POST` | `/api/v1/approval-document/{id}/submit/` | 상신 (동적 결재선 자동 생성 + 결재 알림) |
| `POST` | `/api/v1/approval-document/{id}/act/` | 승인 / 반려 / 의견 |
| `POST` | `/api/v1/approval-document/{id}/cancel/` | 기안 취소 |
| `GET` | `/api/v1/approval-document/my_pending/` | 내 결재 대기함 |
| `GET` | `/api/v1/approval-document/my_drafted/` | 내 기안함 |

### 1-3. 프론트엔드 (`app/vue/src/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `store/types/approval.ts` | ✅ 완료 | `form_type`, `form_template_key` 인터페이스 확장 |
| `views/approval/forms/index.ts` | ✅ 완료 | **`STATIC_FORM_REGISTRY` 컴포넌트 레지스트리** |
| `views/approval/forms/LeaveApplicationForm.vue` | ✅ 완료 | **휴가/연차 전용 폼 (일수 자동계산, 대행자, 비상연락처)** |
| `views/approval/forms/ExpenseReportForm.vue` | ✅ 완료 | **지출결의서 전용 폼 (지출내역 그리드, 금액 자동합산, 계좌정보)** |
| `views/approval/forms/PurchaseOrderForm.vue` | ✅ 완료 | **구매품의서 전용 폼 (품목/수량/단가/공급가액/부가세 계산)** |
| `views/approval/forms/DynamicSchemaForm.vue` | ✅ 완료 | **관리자 정의 JSON Schema 기반 동적 폼** |
| `views/approval/components/DocumentForm.vue` | ✅ 완료 | **하이브리드 폼 분기 + 카테고리 optgroup + 금액별 실시간 전결 연동** |
| `views/approval/components/DocumentDetail.vue` | ✅ 완료 | **STATIC / DYNAMIC 양식별 맞춤 상세 뷰** |

---

## 2. DYNAMIC / STATIC 하이브리드 폼 아키텍처

```
[문서 유형 (DocumentType)]
   │
   ├── form_type = 'STATIC' ────► STATIC_FORM_REGISTRY 매칭
   │                               ├─ LEAVE_APPLICATION (휴가/연차 신청 폼)
   │                               ├─ EXPENSE_REPORT    (지출결의 품목 그리드 폼)
   │                               └─ PURCHASE_ORDER    (구매품의 공급가/세액 폼)
   │
   └── form_type = 'DYNAMIC' ───► DynamicSchemaForm.vue
                                   └─ form_schema JSON 기반 일반 폼 렌더링
```

* **데이터 일원화**: 양식 종류와 관계없이 백엔드에는 JSON 딕셔너리(`content`)로 저장되어 호환성 100% 유지.
* **실시간 결재선 연동**: 지출결의서나 구매품의서에서 테이블 행을 추가하고 금액을 입력하면, `amount` 합계가 자동 산출되어 **금액별 조건부 전결 결재선(`ApprovalPolicyRule`)에 즉각 반영**됨.

---

## 3. 해결된 버그 및 개선 이력

### 🐛 Bug #1 — `doc_number` UNIQUE constraint 위반 (해결)
- `doc_number` 필드 `null=True, default=None` 수정.

### 🐛 Bug #2 — `get_full_name()` AttributeError (해결)
- `Profile.name` 우선 조회 및 `select_related('drafter__profile')` 적용.

### 🐛 Bug #3 — 신입/일반 직원 기안 시 자동 승인되는 문제 (해결)
- 대표이사 본인 기안 시에만 자동 승인, 일반 직원은 400 에러로 차단.

### ✨ Feat #4 — `Department.level` 자동 계산 (해결)
- 프론트 수동 계산 제거 및 백엔드 `Department.save()`에서 상위 부서 기반 자동 산출 + 연쇄 갱신.

### ✨ Feat #5 — 결재 카테고리 및 금액별 조건부 전결 정책 (해결)
- `DocCategory`, `ApprovalPolicyRule` 신설 및 `route_builder.py` 실시간 금액 연동.

### ✨ Feat #6 — DYNAMIC / STATIC 하이브리드 폼 시스템 (해결)
- Vue 컴포넌트 레지스트리 및 전용 폼 3종(`LeaveApplication`, `ExpenseReport`, `PurchaseOrder`) 구축.

---

## 4. 미구현 / 개선 필요 항목

### 🔴 P1 — 필수 (기능 완성도)

#### 4-1. 완료 문서함 (CompletedList)
- `views/approval/components/CompletedList.vue` 신규 생성 및 PDF 다운로드 강조

#### 4-2. 첨부파일 처리
- `DocumentForm.vue` 파일 업로드 UI 및 MinIO/S3 업로드 연동

#### 4-3. 결재 알림 배지 (Notification Badge)
- `_nav.ts`의 `결재 대기함` 메뉴에 `pendingList.length` 실시간 배지 연결

---

## 5. 관련 파일 위치 참조

```
app/django/
├── approval/
│   ├── models/
│   │   ├── document_type.py      # DocCategory, DocumentType(form_type, form_template_key), ApprovalPolicyRule
│   │   └── document.py           # ApprovalDocument (drafter_assignment 연결)
│   ├── services/
│   │   └── route_builder.py      # 동적 결재선 및 조건부 전결 정책 평가 엔진
│   ├── admin.py
│   └── migrations/
│       ├── 0004_doccategory_alter_documenttype_options_and_more.py
│       └── 0005_documenttype_form_template_key_and_more.py
├── apiV1/
│   ├── serializers/approval.py
│   └── views/approval.py

app/vue/src/
├── store/
│   ├── types/approval.ts
│   └── pinia/approval.ts
└── views/approval/
    ├── forms/                    # ⭐ 하이브리드 폼 모듈
    │   ├── index.ts              # STATIC_FORM_REGISTRY
    │   ├── DynamicSchemaForm.vue # JSON Schema 동적 폼
    │   ├── LeaveApplicationForm.vue # 휴가/연차 전용 폼
    │   ├── ExpenseReportForm.vue    # 지출결의 전용 폼
    │   └── PurchaseOrderForm.vue    # 구매품의 전용 폼
    └── components/
        ├── DocumentForm.vue      # 하이브리드 폼 기안 작성
        ├── DocumentDetail.vue    # 하이브리드 폼 맞춤 상세 뷰
        ├── PendingList.vue       # 결재 대기함
        └── DraftedList.vue       # 기안함
```
