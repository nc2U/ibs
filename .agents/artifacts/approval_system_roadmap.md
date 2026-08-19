# 전자결재 시스템 (Electronic Approval System) — 구현 현황 및 개선 로드맵

> 최초 작성: 2026-08-18
> **최종 업데이트: 2026-08-19 (조직도 기반 동적 결재선 및 전결 규정 연동)**
> 작성자: Antigravity AI

---

## 1. 현재 구현 현황

### 1-1. 백엔드 (`app/django/approval/` 및 `company/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `company/models.py` | ✅ 완료 | `StaffAssignment` (보직/겸직/대표권 구분) 모델 추가 |
| `approval/models/document_type.py` | ✅ 완료 | `route_type`, `final_approval_duty`, `final_dept_level` 전결 필드 추가 |
| `approval/models/document.py` | ✅ 완료 | `drafter_assignment` (기안 보직 연결), `doc_number` null 허용 |
| `approval/services/route_builder.py` | ✅ 완료 | **조직도 기반 동적 결재선 자동 생성 서비스** 신설 |
| `approval/admin.py` | ✅ 완료 | Django Admin Inline 등록 |
| `approval/tasks.py` | ✅ 완료 | Celery: FCM 푸시 알림, WeasyPrint PDF 생성 |
| `approval/templates/approval/pdf_document.html` | ✅ 완료 | PDF 출력용 HTML 양식 |
| `approval/migrations/0003_...` | ✅ 완료 | 동적 결재선 및 전결 필드 DB 반영 완료 |

### 1-2. API (`app/django/apiV1/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `serializers/company.py` | ✅ 완료 | `StaffAssignmentSerializer` 추가, `StaffSerializer`에 `assignments` 포함 |
| `views/company.py` | ✅ 완료 | `StaffAssignmentViewSet` (`/api/v1/staff-assignment/`) 등록 |
| `serializers/approval.py` | ✅ 완료 | `RoutePreviewStepSerializer`, 전결/보직 필드 직렬화 |
| `views/approval.py` | ✅ 완료 | `submit` 동적 결재선 연동, `my_assignments`, `preview_route` 액션 추가 |

#### API 엔드포인트

| Method | Endpoint | 기능 |
|--------|----------|------|
| `GET` | `/api/v1/approval-doc-type/` | 활성 문서 유형 목록 (전결 정보 포함) |
| `GET/POST` | `/api/v1/approval-document/` | 문서 목록 / 임시저장 기안 생성 |
| `GET/PATCH/DELETE` | `/api/v1/approval-document/{id}/` | 문서 상세/수정/삭제 |
| `GET` | `/api/v1/approval-document/my_assignments/` | **기안자의 주보직/겸직 목록 조회 (기안 폼 선택용)** |
| `GET` | `/api/v1/approval-document/preview_route/` | **문서유형/기안보직 기준 실시간 결재선 미리보기** |
| `POST` | `/api/v1/approval-document/{id}/submit/` | **상신 (동적 결재선 자동 생성 + 결재 알림)** |
| `POST` | `/api/v1/approval-document/{id}/act/` | 승인 / 반려 / 의견 |
| `POST` | `/api/v1/approval-document/{id}/cancel/` | 기안 취소 |
| `GET` | `/api/v1/approval-document/my_pending/` | 내 결재 대기함 |
| `GET` | `/api/v1/approval-document/my_drafted/` | 내 기안함 |

### 1-3. 프론트엔드 (`app/vue/src/`)

| 파일 | 상태 | 비고 |
|------|------|------|
| `store/types/approval.ts` | ✅ 완료 | `StaffAssignmentItem`, `RoutePreviewStep`, 전결 인터페이스 추가 |
| `store/pinia/approval.ts` | ✅ 완료 | `fetchMyAssignments`, `fetchRoutePreview` 액션 추가 |
| `views/approval/components/DocumentForm.vue` | ✅ 완료 | **기안 보직 선택 셀렉트박스 + 동적 결재선 실시간 미리보기 연동** |
| `views/approval/components/DocumentDetail.vue` | ✅ 완료 | 기안자 소속 보직 표출 + 결재선 타임라인 |
| `views/approval/components/PendingList.vue` | ✅ 완료 | 결재 대기함 (검색, 결재 모달) |
| `views/approval/components/DraftedList.vue` | ✅ 완료 | 기안함 (상태 필터, 상신/취소 모달) |

---

## 2. 조직도 기반 동적 결재선 (Dynamic Approval Route) 아키텍처

### 2-1. 핵심 동작 원리 (Algorithm)

```
[기안 작성] (기안 보직 선택: 예: 경영지원팀 사원 or 프로젝트1팀 겸직사원)
   ↓
[1. 직속 부서 탐색] (Department.manager)
   - 기안자가 부서장 본인이면 -> 본인 단계 생략 후 상위 부서로 직행
   - 기안자가 팀원이면 -> [1단계: 직속 부서장 검토] 생성
   ↓
[2. 전결 규정 검사]
   - 문서 유형의 final_approval_duty (예: 팀장 전결)와 일치하면 -> 즉시 결재선 종료
   - final_dept_level (예: 1레벨)에 도달하면 -> 즉시 결재선 종료
   ↓
[3. 부서 트리 상향 순회] (upper_depart.manager)
   - 상위 부서(본부/실) 책임자를 결재선에 순차 추가 (예: [2단계: 사업운영본부장 승인])
   - 전결 규정에 도달할 때까지 최상위 부서까지 반복
   ↓
[4. 대표이사 최종 결재]
   - 전결에 미도달한 경우 회사 대표이사(DutyTitle='대표이사') 결재선 자동 추가
   - 공동대표(represent_type='joint') -> AND 병렬 결재 (전원 승인 필요)
   - 단독/각자대표 -> OR / 단독 결재
```

### 2-2. 특수 예외 처리 및 검증 규칙

1. **Self-Approval (본인 결재) 방지**:
   - 부서장(팀장/본부장) 본인이 기안할 경우, 본인 결재 단계는 자동으로 건너뛰고 상위 결재권자에게 상신됩니다.
2. **대표이사 기안 시 즉시 자동 승인**:
   - 단독/각자대표가 기안하는 경우, 상신할 상위 결재자가 없으므로 상신(`submit`) 즉시 `STATUS_APPROVED`(최종 승인) 처리 및 PDF가 생성됩니다.
   - 공동대표(`joint`)가 기안하는 경우, 본인을 제외한 다른 공동대표가 최종 결재자로 지정됩니다.
3. **일반 직원의 결재선 누락 방지 (상신 차단)**:
   - 일반 직원이 기안했으나 부서장 미지정 또는 계정 미연동으로 결재선이 0단계로 계산된 경우, 자동 승인되지 않고 **"지정된 결재선이 없습니다. 소속 부서의 책임자(부서장) 또는 대표이사 계정 연동 상태를 확인해 주세요."** 안내와 함께 400 에러로 상신을 안전하게 차단합니다.
4. **겸직(Dual Role) 다중 결재선 분기**:
   - 한 직원이 '경영지원팀' 주보직과 '프로젝트1팀' 겸직을 보유한 경우, 기안 시 선택한 보직에 따라 완전히 분리된 결재선이 자동 생성됩니다.

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
- 관리자가 Vue 화면에서 문서 유형 양식(`form_schema`), 결재 방식(`route_type`), 전결 직책을 직접 등록/수정하는 UI

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

### 5-2. `is_completed()` — prefetch 캐시 활용
- `prefetch_related('steps__actions')` 캐시를 활용하여 단계 완료 여부 검사 시 추가 쿼리 발생 차단.

---

## 6. Flutter 모바일 구현 계획 (미착수)

| 화면 | 설명 | 우선순위 |
|------|------|----------|
| 결재 대기함 | 결재 대기 목록 + FCM 배지 | 🔴 P1 |
| 문서 상세 | 결재선 진행 현황 + 승인/반려 | 🔴 P1 |
| 기안함 | 내 기안 목록 (상태별 필터) | 🟡 P2 |
| 기안서 작성 | 동적 양식 렌더링 + 보직 선택 + 결재선 미리보기 | 🟡 P2 |
| PDF 뷰어 | 완료 문서 PDF 인앱 뷰어 | 🟢 P3 |

---

## 7. 관련 파일 위치 참조

```
app/django/
├── company/
│   ├── models.py                 # Staff, StaffAssignment(보직/겸직)
│   └── admin.py                  # StaffAssignmentInline
├── approval/
│   ├── models/
│   │   ├── document_type.py      # DocumentType (전결규정/생성방식), RouteTemplate
│   │   └── document.py           # ApprovalDocument (drafter_assignment 연결)
│   ├── services/
│   │   └── route_builder.py      # ⭐ 조직도 기반 동적 결재선 자동 생성기
│   ├── admin.py
│   ├── tasks.py                  # Celery: FCM 알림, WeasyPrint PDF 생성
│   └── migrations/
│       ├── 0001_initial.py
│       ├── 0002_alter_approvaldocument_doc_number.py
│       └── 0003_approvaldocument_drafter_assignment_and_more.py
├── apiV1/
│   ├── serializers/
│   │   ├── company.py            # StaffAssignmentSerializer
│   │   └── approval.py           # RoutePreviewStepSerializer
│   └── views/
│       ├── company.py            # StaffAssignmentViewSet
│       └── approval.py           # preview_route, my_assignments, submit

app/vue/src/
├── store/
│   ├── types/approval.ts         # StaffAssignmentItem, RoutePreviewStep
│   └── pinia/approval.ts         # fetchMyAssignments, fetchRoutePreview
├── router/modules/approval.ts
├── layouts/_nav.ts
└── views/approval/
    ├── Index.vue
    └── components/
        ├── DocumentForm.vue      # ⭐ 기안 보직 선택 + 실시간 동적 결재선 미리보기
        ├── DocumentDetail.vue    # 기안 보직 표출 + 결재 타임라인
        ├── PendingList.vue       # 결재 대기함
        └── DraftedList.vue       # 기안함
```

---

## 8. 우선순위별 다음 작업 순서

```
즉시 (v0.2)
  1. 완료 문서함 뷰 추가                                   (4-1)
  2. 첨부파일 업로드 UI 추가                               (4-2)
  3. 결재 대기 네비게이션 배지 연결                         (4-4)

단기 (v0.3)
  4. 최종 승인 문서 잠금(Lock) 처리                        (4-6)
  5. PDF 한글 폰트 로컬 처리 (Dockerfile 수정)             (4-9)
  6. Pagination 적용                                      (4-7)
  7. generate_doc_number Race Condition 수정               (5-1)

중기 (v0.4)
  8. ApprovalPermission 클래스 구현                       (4-5)
  9. 결재 요청 메일 발송                                   (4-11)
 10. 관리자 전체 문서 조회 뷰                               (4-13)
 11. 문서 유형 관리 Vue UI                                 (4-14)

장기 (v1.0)
 12. Flutter 모바일 결재함 구현
 13. 결재 통계 대시보드 위젯                               (4-12)
```
