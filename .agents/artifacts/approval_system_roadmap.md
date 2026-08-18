# 전자결재 시스템 (Electronic Approval System) — 구현 현황 및 개선 로드맵

> 작성일: 2026-08-18
> 작성자: Antigravity AI
> 대상 브랜치: `develop` / `master`

---

## 1. 현재 구현 현황 (v0.1 — Baseline)

### 1-1. 백엔드 (`app/django/approval/`)

| 파일 | 상태 | 설명 |
|------|------|------|
| `models/document_type.py` | ✅ 완료 | `DocumentType`, `RouteTemplate` 모델 |
| `models/document.py` | ✅ 완료 | `ApprovalDocument`, `ApprovalStep`, `ApprovalAction` 모델 |
| `admin.py` | ✅ 완료 | Django Admin Inline 등록 |
| `tasks.py` | ✅ 완료 | Celery: FCM 푸시 알림, WeasyPrint PDF 생성 태스크 |
| `templates/approval/pdf_document.html` | ✅ 완료 | PDF 출력용 HTML 양식 |
| `fixtures/approval_document_types.json` | ✅ 완료 | 초기 seed: `업무품의서 (BIZ_APPROVAL)` |
| `migrations/0001_initial.py` | ✅ 완료 | DB 테이블 생성 완료 |

### 1-2. API (`app/django/apiV1/`)

| 파일 | 상태 | 설명 |
|------|------|------|
| `serializers/approval.py` | ✅ 완료 | 문서 유형·문서·단계·액션 Serializer |
| `views/approval.py` | ✅ 완료 | `DocumentTypeViewSet`, `ApprovalDocumentViewSet` |

#### 현재 API 엔드포인트

| Method | Endpoint | 기능 |
|--------|----------|------|
| `GET` | `/api/v1/approval-doc-type/` | 활성 문서 유형 목록 |
| `GET/POST` | `/api/v1/approval-document/` | 문서 목록 조회 / 임시저장 기안 |
| `GET/PATCH/DELETE` | `/api/v1/approval-document/{id}/` | 문서 상세/수정/삭제 |
| `POST` | `/api/v1/approval-document/{id}/submit/` | 상신 (결재선 인스턴스 생성) |
| `POST` | `/api/v1/approval-document/{id}/act/` | 승인 / 반려 / 의견 |
| `POST` | `/api/v1/approval-document/{id}/cancel/` | 기안 취소 |
| `GET` | `/api/v1/approval-document/my_pending/` | 내 결재 대기함 |
| `GET` | `/api/v1/approval-document/my_drafted/` | 내 기안함 |

### 1-3. 프론트엔드 (`app/vue/src/`)

| 파일 | 상태 | 설명 |
|------|------|------|
| `store/types/approval.ts` | ✅ 완료 | TypeScript 인터페이스 |
| `store/pinia/approval.ts` | ✅ 완료 | Pinia 스토어 (전체 CRUD + 결재 액션) |
| `router/modules/approval.ts` | ✅ 완료 | 라우터 모듈 |
| `layouts/_nav.ts` | ✅ 완료 | 사이드 네비게이션 등록 |
| `views/approval/PendingList.vue` | ✅ 완료 | 결재 대기함 (인라인 결재 모달) |
| `views/approval/DraftedList.vue` | ✅ 완료 | 기안함 (상신/취소/PDF 다운로드) |
| `views/approval/DocumentForm.vue` | ✅ 완료 | 기안서 작성/수정 (동적 양식 + 결재선 미리보기) |
| `views/approval/DocumentDetail.vue` | ✅ 완료 | 문서 상세 + 결재 진행 현황 + 결재 처리 |

---

## 2. 미구현 / 개선 필요 항목

### 🔴 P1 — 필수 (기능 완성도)

#### 2-1. 완료 문서함 (CompletedList)
- **현황**: 별도 완료 문서함 뷰 없음.
- **작업**:
  - `views/approval/CompletedList.vue` 신규 생성
  - `_nav.ts`에 `완료 문서함` 서브메뉴 추가
  - `router/modules/approval.ts`에 `/approval/completed` 라우트 추가
  - PDF 다운로드 버튼 강조 배치

#### 2-2. 문서 유형 관리 UI (현재 Admin 전용)
- **현황**: `DocumentType` 및 `RouteTemplate` 등록이 Django Admin에서만 가능.
- **작업**:
  - `settings` 하위에 Vue 문서 유형 관리 페이지 추가
  - `RouteTemplate` CRUD API 추가 (현재 ReadOnly)
  - 결재선 드래그-앤-드롭 순서 변경 UX

#### 2-3. 첨부파일 처리
- **현황**: `ApprovalDocument.attachment` 필드 정의됨, UI 미구현.
- **작업**:
  - `DocumentForm.vue`에 파일 업로드 UI 추가
  - API 호출 시 `multipart/form-data` 헤더 설정
  - 상세 페이지에서 첨부파일 다운로드 링크 표시

#### 2-4. 재상신(Resubmit) 사용자 안내
- **현황**: 반려 후 재상신 시 기존 단계 삭제됨. 사용자 피드백 부족.
- **작업**:
  - 재상신 전 "이전 결재 이력이 초기화됩니다" 확인 모달 추가
  - 백엔드: 단계 삭제 전 로그 보존 정책 결정

#### 2-5. 결재 알림 배지 (Notification Badge)
- **현황**: `결재 대기함` 메뉴에 배지 미적용.
- **작업**:
  - `useApproval().pendingList.length`를 네비게이션 배지에 연결
  - 앱 초기 로드 시 `fetchMyPending()` 호출 (`DefaultLayout.vue`)
  - Flutter: 탭바 배지 카운트 연동

---

### 🟡 P2 — 중요 (품질/보안)

#### 2-6. 권한 통제 강화
- **현황**: `IsAuthenticated`만 사용. 별도 결재 권한 클래스 없음.
- **작업**:
  - `approval.read`, `approval.create`, `approval.manage` 권한 코드 정의
  - `work.ProjectPermission` 패턴 참고 → `ApprovalPermission` 클래스 구현
  - `DocumentType` 관리는 `is_superuser` 또는 `work_manager`만 허용

#### 2-7. 최종 승인 문서 잠금(Lock)
- **현황**: `status=approved` 문서도 `PATCH`/`DELETE` 호출 가능.
- **작업**:
  - `perform_update` / `destroy` 오버라이드로 차단
  - `ApprovalDocument.save()` 오버라이드에서 validation 추가

#### 2-8. Pagination 적용
- **현황**: `my_drafted()`, `my_pending()` 전체 목록 반환. 성능 이슈 잠재.
- **작업**: `PageNumberPaginationTwenty` 적용 + 프론트 페이지네이션 추가

#### 2-9. PDF 생성 실패 재시도
- **현황**: 예외 발생 시 `print`로만 처리, 재시도 없음.
- **작업**:
  - Celery `max_retries=3`, `countdown=60` 설정
  - 실패 시 Slack 알림 연동
  - Admin action으로 수동 PDF 재생성 버튼 추가

#### 2-10. PDF 한글 폰트 로컬 처리
- **현황**: Google Fonts CDN 사용 → 네트워크 차단 시 한글 깨짐 가능.
- **작업**:
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

#### 2-11. 결재 의견(Comment) 전용 기능
- `ACTION_COMMENTED` 정의됨. UI에서 "의견만 남기기" 버튼 추가, 타임라인 표시.

#### 2-12. 결재 요청 메일 발송
- FCM 푸시만 구현. `notify_approvers_task`에 `send_mail()` 추가.
- 메일 HTML 템플릿 생성 (`templates/approval/email_notify.html`)

#### 2-13. 결재선 시각화 개선
- 단계 간 화살표 연결 (CSS 또는 SVG)
- AND/OR 조건에 따른 분기 표현

#### 2-14. 대시보드 위젯 연동
- 메인 대시보드에 "내 결재 대기" 카운트 위젯 추가

#### 2-15. 관리자용 전체 문서 조회 뷰
- `/approval/all` 라우트 추가 (관리자 전용)
- 필터: 유형, 상태, 기안자, 기간
- 엑셀/CSV 내보내기 (`django-import-export` 활용)

#### 2-16. 워크스페이스 연동 강화
- `DocumentForm.vue`에 워크스페이스 선택 드롭다운 추가
- 워크스페이스 상세 페이지에서 연관 결재 문서 목록 표시

---

## 3. 리팩토링 필요 사항

### 3-1. `DocumentDetail.vue` — `storeToRefs` 반응성

현황: `const { document } = approvalStore` 구조 분해 시 반응성 손실 가능.

```ts
// 개선
import { storeToRefs } from 'pinia'
const { document } = storeToRefs(approvalStore)
```

### 3-2. `DocumentForm.vue` — `dynamicContent` 초기화

현황: `Object.keys(dynamicContent).forEach(k => delete dynamicContent[k])` — Vue reactive에서 불안전.

```ts
// 개선
const dynamicContent = ref<Record<string, string>>({})
const onDocTypeChange = () => { dynamicContent.value = {} }
```

### 3-3. `generate_doc_number()` — Race Condition

현황: `count()` 방식은 동시 승인 시 번호 중복 가능.

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

### 3-4. `is_completed()` — N+1 쿼리 방지

현황: `ApprovalStep.is_completed()`가 매번 DB 쿼리 실행.
개선: ViewSet `get_queryset()`에 `prefetch_related('steps__actions')` 확인 후 인자로 prefetch 데이터 전달.

### 3-5. Serializer N+1 — List/Detail 분리 완성

현황: List/Detail Serializer 분리 구조 있으나 `steps` 미포함 여부 재확인 필요.
개선: `ApprovalDocumentListSerializer`에서 `steps` 필드 명시적 제외 확인.

---

## 4. Flutter 모바일 구현 계획 (미착수)

| 화면 | 설명 | 우선순위 |
|------|------|----------|
| 결재 대기함 | 결재 대기 목록 + 배지 카운트 | 🔴 P1 |
| 문서 상세 | 결재선 진행 현황 + 승인/반려 버튼 | 🔴 P1 |
| 기안함 | 내 기안 목록 (상태별 필터) | 🟡 P2 |
| 기안서 작성 | 동적 양식 렌더링 + 결재선 선택 | 🟡 P2 |
| PDF 뷰어 | 완료 문서 PDF 인앱 뷰어 | 🟢 P3 |

### Flutter 구현 시 고려사항

- FCM 토큰 연동 이미 완료 (`FCMDevice` + `push_service.py`)
- `category: 'approval'` 푸시 수신 시 결재 대기함으로 딥링크 처리 필요
- `form_schema`를 Flutter Widget으로 동적 렌더링:

```dart
Widget buildFormField(Map<String, dynamic> field) {
  switch (field['type']) {
    case 'textarea': return TextFormField(maxLines: 5);
    case 'number':   return TextFormField(keyboardType: TextInputType.number);
    default:         return TextFormField();
  }
}
```

---

## 5. 테스트 체크리스트

### 백엔드 (미작성)
- [ ] `DocumentType` CRUD 및 결재선 템플릿 등록
- [ ] `ApprovalDocument` 상신 → 결재선 인스턴스 생성 검증
- [ ] AND 조건: 복수 결재자 전원 승인 후 다음 단계 진행
- [ ] OR 조건: 1인 승인으로 다음 단계 진행
- [ ] 반려 후 재상신 검증 (기존 단계 초기화 확인)
- [ ] `generate_doc_number()` 중복 방지 검증
- [ ] 최종 승인 후 PDF 태스크 트리거 검증
- [ ] 승인된 문서 수정/삭제 차단 검증 (2-7 완료 후)

### 프론트엔드 (미작성)
- [ ] `DocumentForm.vue`: 동적 양식 렌더링 / 결재선 미리보기
- [ ] `PendingList.vue`: 승인/반려 모달 동작
- [ ] `DocumentDetail.vue`: 결재 단계별 상태 표시 / `storeToRefs` 반응성

---

## 6. 관련 파일 위치 참조

```
app/django/
├── approval/
│   ├── models/
│   │   ├── document_type.py      # DocumentType, RouteTemplate
│   │   └── document.py           # ApprovalDocument, ApprovalStep, ApprovalAction
│   ├── admin.py
│   ├── tasks.py                  # Celery: 알림, PDF 생성
│   ├── templates/approval/
│   │   └── pdf_document.html     # WeasyPrint PDF 양식
│   └── fixtures/
│       └── approval_document_types.json
├── apiV1/
│   ├── serializers/approval.py
│   └── views/approval.py

app/vue/src/
├── store/
│   ├── types/approval.ts
│   └── pinia/approval.ts
├── router/modules/approval.ts
├── layouts/_nav.ts
└── views/approval/
    ├── PendingList.vue
    ├── DraftedList.vue
    ├── DocumentForm.vue
    └── DocumentDetail.vue
```

---

## 7. 우선순위별 다음 작업 순서 (권장)

```
즉시 (v0.2)
  1. DocumentDetail.vue — storeToRefs 반응성 수정        (3-1)
  2. DocumentForm.vue   — dynamicContent 초기화 개선      (3-2)
  3. 첨부파일 업로드 UI 추가                               (2-3)
  4. 결재 대기 네비게이션 배지 연결                         (2-5)

단기 (v0.3)
  5. 완료 문서함 뷰 추가                                   (2-1)
  6. 최종 승인 문서 잠금(Lock) 처리                        (2-7)
  7. PDF 한글 폰트 로컬 처리 (Dockerfile 수정)             (2-10)
  8. Pagination 적용                                      (2-8)

중기 (v0.4)
  9. ApprovalPermission 클래스 구현                       (2-6)
 10. 결재 요청 메일 발송                                   (2-12)
 11. generate_doc_number Race Condition 수정               (3-3)
 12. 관리자 전체 문서 조회 뷰                               (2-15)

장기 (v1.0)
 13. Flutter 모바일 결재함 구현
 14. 결재 통계 대시보드 위젯                               (2-14)
 15. 문서 유형 관리 Vue UI                                 (2-2)
 16. 워크스페이스 연동 강화                                 (2-16)
```
