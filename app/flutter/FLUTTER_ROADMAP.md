# IBS Flutter 모바일 앱 개발 로드맵 & 가이드

이 문서는 IBS 시스템의 Flutter 기반 모바일 앱 개발 진행 상황, 로드맵, 그리고 타 컴퓨터 (집/사무실)에서 이어 개발하기 위한 가이드를 제공합니다.

---

## 📌 1. 프로젝트 정보

* **위치**: `app/flutter`
* **Package Name**: `mobile_ibs`
* **App Display Name**: IBS워크스페이스
* **주요 개발 환경**: Flutter 3.x, Dart 3.9.x+, Android Studio / PyCharm / Xcode
* **핵심 패키지**:
    * 상태관리: `flutter_riverpod` + `riverpod_annotation` (코드 생성)
    * 라우팅: `go_router` (ShellRoute 기반 하단탭 유지)
    * 네트워킹: `dio` (AuthInterceptor 토큰 자동 갱신), `web_socket_channel` (실시간 메신저)
    * 보안저장소: `flutter_secure_storage`
    * 모델: `freezed` + `json_serializable` (코드 생성)
    * UI: `google_fonts` (Noto Sans KR), `shimmer`, `cached_network_image`
    * 기타: `image_picker`, `hive_flutter`, `flutter_svg`, `open_filex`, `share_plus`

---

## 🏛️ 2. 도메인 용어 체계 (Domain Terminology Architecture)

| 구분           | 백엔드 모델                         | 비즈니스 도메인 범위                                    | 웹(Vue) & 모바일(Flutter) 용어 |
|:---------------|:------------------------------------|:--------------------------------------------------------|:-------------------------------|
| **Work Core**  | `work.IssueProject`                 | 본사관리(1) / 부동산개발(2) / 기타(3) 통합 협업 공간    | **`워크스페이스` (Workspace)** |
| **IBS Global** | `project.IssueProject` (`type='2'`) | 분양, 수납, 입출금, 소송문서 등 부동산 개발 전용 사업지 | **`프로젝트` (Project)**       |

* **'현장' 용어 사용 엄금**: 코드베이스 및 UI에서 '현장'이라는 용어 대신 '워크스페이스' 또는 '프로젝트'를 명확히 구분하여 사용합니다.
* **워크스페이스 (`work_core`)**: 업무 (Issue), 회의록 (Meeting), 실시간 소통(Chat/Notice), 공지사항 등 본사/프로젝트 전반의 협업 공간.
* **프로젝트 (`ibs_global`)**: 부동산 개발 (`type='2'`)에 한정되어 계약 (Contract), 수납 (Payment), 재무 (Ledger), 소송/공용문서 (Docs), 설정 (Settings)을 관리하는 사업지.

---

## 📱 3. 모바일 앱 메인 카테고리 구조

```text
 📱 IBS워크스페이스 (Mobile App Architecture)
  ├── 1️⃣ [홈 / 대시보드] (Home Dashboard)
  │    ├── 🏢 통합 워크스페이스/프로젝트 셀렉터
  │    ├── 📊 오늘의 현황, 내 할당 업무 & 최근 회의록 요약
  │    ├── 🔴 결재 대기 건수 실시간 배지 및 바로가기
  │    └── ⚡ 퀵 액션 (새 업무 등록, 회의록 작성, 새 결재 기안, 문서 등록)
  │
  ├── 2️⃣ [업무 관리] (Work Core)
  │    ├── 📅 회의록 목록, 의제 & 결정사항/액션아이템 (Meeting)
  │    ├── 📋 할당 업무 목록, 진척률(0~100%) 및 댓글/파일 (Issue)
  │    └── ✏️ 회의록 & 업무 신규 생성 및 수정 폼 (Meeting / Issue CRUD)
  │
  ├── 3️⃣ [프로젝트 관리] (Project Core) *radius = 0 직각 미니멀 디자인
  │    ├── 🏗️ 사업지 선택 (Project Selector - type='2' 전용) & 개요
  │    ├── 📄 계약 관리 (Contract - 분양/계약자/동호수 배치)
  │    ├── 💳 대금 수납 관리 (Payment - 차수별 수납/미납 현황)
  │    ├── 💰 자금 / 재무 관리 (Ledger - 입출금 내역 및 캐시플로우)
  │    ├── 📂 문서 / 소송 관리 (Docs - 인허가/공용문서/소송사건)
  │    └── ⚙️ 프로젝트 설정 (Settings - 차수/유닛배치/예산)
  │
  ├── 4️⃣ [채널 & 전사 라운지] (Channel & Corporate Lounge)
  │    ├── 💬 [소통 피드]: 워크스페이스별 공지사항(Notice) & 게시판(Forum)
  │    └── 🏢 [전사 라운지]: 
  │         ├── 🏛️ 회사소개 (기업 목적, 사명 2035, 5대 핵심 가치관, 조직도, 사규집)
  │         ├── 🔰 온보딩·가이드 (4단계 로드맵, 체크리스트, 시스템 사용법)
  │         └── ❓ FAQ·기술지원 (인사/전산/경비 Q&A 아코디언 및 문의 폼)
  │
  ├── 5️⃣ [전자 결재] (Approval Core) *구현 완료 (17종 전 양식 지원)
  │    ├── 🔴 4대 탭: 결재 대기함(미결 배지) | 내 기안함 | 결재 문서함(완료/공람) | 전체 문서함(관리자)
  │    ├── 📝 17종 맞춤 기안 폼 (금액 실시간 전결 연동, 보직/겸직 선택)
  │    ├── 👁️ 17종 전 양식 맞춤 상세 뷰 & ApprovalRouteTimeline 결재선 시각화
  │    ├── ✍️ 원터치 승인/반려/의견/회수 바텀시트 모달
  │    └── 📄 WeasyPrint PDF 네이티브 뷰어 및 외부 공유
  │
  └── 6️⃣ [실시간 메신저] (Real-Time Messenger Core) *Phase 3-1 계획
       ├── 🏢 워크스페이스 공용 채널 (슬랙형 단체 대화방)
       ├── 🔒 1:1 다이렉트 메시지 (카카오톡형 사내 비밀 DM)
       ├── ⚡ 0.1초 실시간 수발신 (WebSocket + Redis Channel Layer)
       ├── 📋 업무(Issue) / 회의록 / 도면 링크 미리보기 카드 공유
       └── 🔔 FCM 백그라운드 푸시 알림
```

---

## 🟢 4. 현재 진행 상황 (Current Status)

- [x] **Step 0**: `app/flutter` 디렉토리에 Flutter 프로젝트 생성 (`mobile_ibs`)
- [x] **Step 0-1**: 핵심 패키지 설치 완료 (`dio`, `flutter_riverpod`, `flutter_secure_storage`, `go_router`)
- [x] **Step 1**: Android Studio SDK 37 설정 & 에뮬레이터 세팅 및 첫 스마트폰 빌드 성공
- [x] **Step 2**: Feature-First 기반 폴더 구조 생성 (`core/`, `features/`)
- [x] **Step 3**: Dio API Client 및 보안 토큰 저장소 (`flutter_secure_storage`) 작성
- [x] **Step 4**: 웹 자원 브랜드 동기화 (`IBS워크스페이스` 타이틀 및 `assets/images/logo.png` 적용)
- [x] **Step 5**: Django SimpleJWT (`/api/v1/token/`, Email 기반) 인증 연동 완료
- [x] **Step 6**: 모바일 로그인 화면 (UI) 작성 및 실제 서버 계정 인증 성공
- [x] **Step 7**: 로그인 성공 시 메인 대시보드 리다이렉트 & 상단 로그아웃 폼 구축
- [x] **Step 8**: 모바일 메인 대시보드 레이아웃 (워크스페이스 셀렉터, 퀵 메뉴, 하단 탭 바) 구현
- [x] **Step 9**: Phase 1 - 업무/회의 모듈 (Issue / Meeting) API 연동, CRUD 폼, 실시간 필터 동기화 구현 완료
- [x] **Step 9-1**: 도메인 용어 체계 정립 (`work_core: 워크스페이스` vs `ibs_global: 프로젝트`) 및 Vue 3 웹 & Flutter 모바일 100% 동기화
- [x] **Step 9-2**: `ProjectScreen` (프로젝트 탭) 5대 핵심 모듈 카드 리팩토링 (계약/수납/자금/문서/설정, `radius = 0` 직각 스타일 적용)
- [x] **Step 9-3**: 메인 통합 검색 결과 (`search_results_screen.dart`) 공지사항/게시판 바텀시트 연동 및 전체 채널 상세 연결
- [x] **Step 9-4**: 닫힌 워크스페이스 (`status='2'`) 읽기 전용 보안 방어 (백엔드 권한 필터링 + `can()` 판정 엔진 + UI 수정/삭제 버튼 원천 비노출)
- [x] **Step 9-5**: 3-Way 테마 시스템 구축 (`ThemeMode.light` / `ThemeMode.dark` / `ThemeMode.system`) 및 `AppColorsExtension`, `themeModeProvider`, 프로필 설정 연동
- [x] **Step 9-6**: 채널 탭 2단 네비게이션 개편 완료 (상단 36px 슬림 캡슐 스위치: `소통 피드` ↔ `전사 라운지 & 온보딩`)
- [x] **Step 9-7**: 전사 라운지 하이엔드 럭셔리 브랜드 모노그래프 & 캠페인 에디토리얼 레이아웃 구축 완료 (기업 목적, 사명 2035, 5대 핵심 가치관, 조직도, 사규집, 온보딩 로드맵, FAQ 아코디언 완비)
- [x] **Step 9-8**: 브랜드 컬러 청량한 `Luminous Azure (#38BDF8 / #0284C7)` 전환 및 라운지 3대 시맨틱 포인트 컬러(Blue·Green·Amber) 연동
- [x] **Step 12**: Phase 3-2 - **모바일 전자결재 (Approval Core) 시스템 전면 구축 완료**
  - **17종 전 양식 기안 폼 (`ApprovalDraftScreen`) 완비**:
    - 일반품의, 공문발신, 휴가신청, 출장신청, 연장근무, 인사발령, 인사신청
    - 구매품의, 지출결의, 경비정산, 선급금신청, 계약품의, 계약변경
    - 법무검토, 사업검토(수지분석), 사업추진승인, 프로젝트 주요의사결정
  - **17종 전 양식 맞춤 상세 뷰 (`ApprovalDetailScreen`) 완비**:
    - 양식별 전용 카드/테이블 뷰, 결재선 타임라인 (`ApprovalRouteTimeline`)
  - **Freezed 모델 & 안정적 역직렬화**:
    - `@JsonKey(readValue: ...)` 방어 헬퍼로 `pk`/`id`, `company`(String/int 혼용) 완전 대응
    - `approval_repository.dart`: List 및 Map 페이징 응답 자동 판별 안전 파싱
  - **4대 탭 네비게이션**: `결재 대기함` (미결 배지 카운트) | `내 기안함` | `결재 문서함` (완료/공람) | `전체 문서함` (관리자 전용 검색/필터)
  - **다크 모드 가시성 개선**:
    - TabBar `labelColor`: `accentApproval` (밝은 Amber `#FBBF24`)
    - 다크 테마 `accentApprovalDeep`: `#78350F` → `#FCD34D` (Amber 300)
  - **원터치 액션 & PDF 연동**:
    - 승인/반려/의견/회수 바텀시트 모달 (`ApprovalActionBottomSheet`)
    - WeasyPrint PDF 네이티브 뷰어/외부 공유 (`approval_pdf_helper.dart`)
  - **홈 대시보드 연동**: `HomeTab` 실시간 미결 건수 배지 및 `AppRoutes.approval` 라우터 연결
- [ ] **Step 10**: Phase 2 - 프로젝트별 계약 관리 (`Contract`) 및 수납/입출금 상세 조회 모듈 연동 (다음 진행 예정)
- [ ] **Step 11**: Phase 3-1 - 실시간 워크스페이스 메신저 (Real-Time Chat & Direct Message) 시스템 구축

---

## 🎨 5. 테마 시스템(Theme) 아키텍처 & 개발 시 유의사항

IBS 모바일 앱은 Vue 웹의 테마 체계와 100% 호환되는 **3-Way 테마(라이트 | 다크 | 기기 설정)** 인프라가 구축되어 있습니다.

### 1) 테마 아키텍처 구성요소
- **[`AppColorsExtension`](file:///Users/austinkho/Git/Pro/ibs/app/flutter/lib/core/theme/app_colors_extension.dart)**: `ThemeExtension` 기반의 테마별 색상 토큰 정의 (`AppColorsExtension.light` & `AppColorsExtension.dark`).
- **[`AppTheme`](file:///Users/austinkho/Git/Pro/ibs/app/flutter/lib/core/theme/app_theme.dart)**: Material 3 기반 라이트/다크 `ThemeData` 정의.
- **[`themeModeProvider`](file:///Users/austinkho/Git/Pro/ibs/app/flutter/lib/core/providers/theme_provider.dart)**: `FlutterSecureStorage`(`APP_THEME_MODE`)를 사용한 테마 설정 영구 보관.
- **[`BuildContextThemeX`](file:///Users/austinkho/Git/Pro/ibs/app/flutter/lib/core/theme/app_colors_extension.dart)**: `context.colors` 확장 게터를 통해 위젯에서 현재 활성 테마 색상 즉시 접근.

### 2) UI 개발 시 색상 사용 규칙 (중요 ⚠️)
신규 화면 및 컴포넌트를 작성할 때는 **다크모드 고정 색상 하드코딩을 피하고 `context.colors` 토큰을 사용**합니다.

```dart
// ❌ 피해야 할 방식: 다크모드 고정 색상 직접 참조
color: AppColors.bgCard
color: AppColors.bgPrimary
color: Colors.white
color: Colors.black

// ✅ 권장 방식: BuildContext의 테마 확장 토큰 사용
color: context.colors.bgPrimary      // 배경색 (Dark: #202336 / Light: #F1F5F9)
color: context.colors.bgCard         // 카드/모달 (Dark: #2A2E47 / Light: #FFFFFF)
color: context.colors.textPrimary    // 메인 텍스트 (Dark: #FFFFFF / Light: #0F172A)
color: context.colors.textSecond     // 보조 텍스트 (Dark: #CBD5E1 / Light: #475569)
color: context.colors.textMuted      // 설명/메타 (Dark: #94A3B8 / Light: #64748B)
color: context.colors.border         // 테두리선 (Dark: #3B4061 / Light: #E2E8F0)
color: context.colors.accentWork     // 업무관리 액센트 (Dark: #38BDF8 / Light: #0284C7)
color: context.colors.accentProject  // 프로젝트 액센트 (Dark: #34D399 / Light: #059669)
color: context.colors.accentApproval // 전자결재 액센트 (Dark: #FBBF24 / Light: #D97706)
color: context.colors.accentCorp     // 전사정보 액센트 (Dark: #38BDF8 / Light: #0284C7)
```

---

## 🗺️ 6. 단계별 개발 로드맵 (Detailed Roadmap)

### Phase 1: 업무관리 핵심 모듈 (입출력 및 진행 현황) [완료]

* **1-1. 회의록 (`meeting`) 모듈**:
    - 회의 목록 및 회의록 상세 조회, 의제/결정사항/액션아이템 확인
    - 회의 생성 및 수정 폼 (`MeetingFormScreen`)
* **1-2. 업무 (`work`) 모듈**:
    - 내 업무/전체 업무 목록 조회 및 실시간 워크스페이스 필터 반응
    - 업무 상세 보기 및 진척률 (`done_ratio`) 수정, 댓글/파일 확인
    - 업무 생성 및 수정 폼 (`IssueFormScreen`)
* **1-3. 전역 상태 & 필터 동기화**:
    - `selectedProjectProvider` 변경 시 회의 및 업무 목록 즉시 재조회 연동 완료
* **1-4. 전사 라운지 & 온보딩 모듈**:
    - 하이엔드 럭셔리 브랜드 캠페인 레이아웃 (기업 목적, 사명 2035, 5대 핵심 가치관, 조직도, 사규집)
    - 온보딩 4단계 로드맵, 체크리스트, FAQ 아코디언 완료

---

### Phase 2: 프로젝트별 핵심 사업 모듈 (IBS Global) [다음 진행 대상]

* **2-1. 프로젝트 선택 (Project Selector) 동기화**:
    - `type == '2'` (부동산 개발 / 시행) 프로젝트만 선별하여 프로젝트 탭 연동
* **2-2. 5대 핵심 사업 모듈 카드 접근 UI (radius = 0)**:
    - 📄 **계약 관리 (`Contract`)**: 분양 계약 내역, 계약자 상세 정보, 승계/해지
    - 💳 **대금 수납 관리 (`Payment`)**: 차수별 납부 내역, 수납 등록 및 미납금 현황
    - 💰 **자금 / 재무 관리 (`Ledger`)**: 프로젝트 계좌 거래 이력 및 캐시플로우
    - 📂 **문서 / 소송 관리 (`Docs`)**: 프로젝트 일반 문서, 소송 사건 이력
    - ⚙️ **프로젝트 설정 (`Settings`)**: 프로젝트 기본 정보, 차수/유닛 배치 현황, 예산
* **2-3. 계약 관리 (`Contract`) 모듈 구현 [다음 작업]**:
    - 프로젝트별 분양/계약 목록 조회 API 연동 (`/api/v1/contracts/?project=<id>`)
    - 계약 상세 보기 화면 및 동호수 배치/유닛 정보 연동

---

### Phase 3: 실시간 워크스페이스 메신저 & 전자결재/협업 고도화

#### 3-1. 실시간 워크스페이스 메신저 (Real-Time Messenger System) [Phase 3 진행 예정]
* **백엔드 인프라 (Django Channels + Redis 7)**:
  - Django ASGI 환경 및 WebSocket 라우팅 구성 (`channels`, `daphne`)
  - Redis 7 (`ibs-redis`) 인메모리 Pub/Sub 채널 레이어 연동
  - 데이터 모델 설계:
    - `ChatRoom`: 워크스페이스 공용 채널(Group) / 1:1 다이렉트 메시지(DM) / 부서·현장 소그룹
    - `ChatMessage`: 발신자, 텍스트 본문, 파일/이미지 첨부, 답장(Reply), 업무/회의 링크 카드
    - `ChatReadReceipt`: 멤버별 읽음 위치(Last Read Message ID) 및 안 읽은 메시지 카운트
* **Flutter 모바일 메신저 클라이언트**:
  - `web_socket_channel` + Riverpod 기반 실시간 메시지 스트림 관리
  - 1:1 DM 및 워크스페이스 단체 대화방 UI (카카오톡/슬랙 스타일)
  - ⚡ 0.1초 실시간 수발신 & 카카오톡 스타일 읽음 카운트 (숫자 1 제거)
  - ✍️ 상대방 입력 중(Typing indicator) 표시
  - 📋 **IBS 특화 기능**: 채팅창 내 업무(Issue 번호)/회의록/도면 링크 입력 시 리치 프리뷰 카드 자동 렌더링
  - 📷 카메라 촬영 현장 사진 및 PDF 설계 도면 즉시 전송

#### 3-2. 모바일 전자결재 (Mobile Approval Core) [완료 ✅]
* **17종 전 양식 모바일 기안 및 상세 뷰 지원**:
  - 기안자 보직/겸직 선택 및 실시간 결재선 미리보기 위젯 연동
  - 금액 입력 시 전결 규정(`ApprovalPolicyRule`)에 따른 실시간 결재선 반영
* **4대 탭 관리**: 미결함(미결 배지), 기안함, 결재문서함(승인/공람), 전체문서함(관리자 전용)
* **원터치 모바일 승인/반려/의견 등록 및 회수 바텀시트**
* **WeasyPrint PDF 네이티브 출력 및 외부 공유 (`SharePlus`)**

#### 3-3. 전사 실시간 알림 (FCM Push Notifications) [Phase 3 진행 예정]
* Firebase Cloud Messaging (FCM) 기반 백그라운드 푸시 알림
* 새 채팅 메시지, 업무 할당/댓글, 결재 요청 즉시 스마트폰 푸시 전달

## 🔔 6. 모바일 푸시 알림 및 배지 시스템 아키텍처 (FCM Push & Badge Architecture)

IBS 모바일 앱은 **이동 중에도 지체 없이 업무를 인지하고 결재/회의/업무를 즉시 처리**할 수 있도록 엔드투엔드 실시간 푸시 알림 및 런처 배지 동기화 파이프라인을 갖추고 있습니다.

### 🏗️ 1) 푸시 알림 기술 스택 및 구조
* **안드로이드 공식 알림 채널**: `ibs_high_importance_channel` (Importance Max, Sound, Vibration, 런처 배지 허용)
* **포그라운드 & 백그라운드 완벽 대응**:
  * 포그라운드(앱 실행 중): `flutter_local_notifications` 헤드업 팝업 배너 및 상태바 알림 생성 ➔ OS 앱 아이콘 배지 실시간 갱신
  * 백그라운드 / 앱 종료: `@pragma('vm:entry-point') firebaseMessagingBackgroundHandler` 글로벌 최상위 수신 및 OS 시스템 트레이 등록
* **앱 아이콘 배지 동기화**: `unreadNotificationCount` + `pendingApprovalCount` 합산 실시간 런처 배지 반영
* **백엔드 발송 엔진**: Django Celery 비동기 워커 + Firebase Admin SDK (`_utils/push_service.py`)

---

### 📋 2) 현재 구현된 알림 전송 케이스 전수 목록 (Trigger Matrix)

| 도메인 | 트리거 이벤트 (발생 시점) | 수신 대상자 | 알림 타이틀 예시 | 알림 내용 및 동작 | 백엔드 태스크 |
|:---|:---|:---|:---|:---|:---|
| **전자결재** | **기안 상신 (임시저장 ➔ 상신)** | 1단계 결재자 전원 (`step.approvers`) | `[결재 요청] {문서유형}` | `{기안자명}님이 결재를 요청했습니다: {문서제목}` | `notify_approvers_task` |
| **전자결재** | **중간 단계 결재 승인 (다음 단계 진행)** | 다음 단계 결재자 전원 (`next_step.approvers`) | `[결재 요청] {문서유형}` | `{기안자명}님이 결재를 요청했습니다: {문서제목}` | `notify_approvers_task` |
| **전자결재** | **결재 최종 승인 완료** | 기안자 (`drafter`) | `[결재 완료] {문서유형}` | `"{문서제목}" 결재가 최종 승인되었습니다.` | `notify_drafter_task` |
| **전자결재** | **결재 최종 승인 (공람)** | 참조자 전원 (`observers`) | `[결재 공람] {문서유형}` | `"{문서제목}" 결재가 최종 승인되어 공람되었습니다.` | `notify_drafter_task` |
| **전자결재** | **결재 반려** | 기안자 (`drafter`) | `[결재 반려] {문서유형}` | `"{문서제목}" 결재가 반려되었습니다. (사유: {반려사유})` | `notify_drafter_task` |
| **전자결재** | **결재 의견 등록** | 기안자 (`drafter`) | `[결재 의견 등록] {문서유형}` | `"{문서제목}" 결재에 새로운 의견이 등록되었습니다.` | `notify_drafter_task` |
| **업무 (Issue)** | **신규 업무 생성 (담당자 지정)** | 지정된 담당자 (`assigned_to`) | `[업무 할당] {워크스페이스}` | `[#{업무번호}] {업무제목}` (프로필 자동 모니터링 연동) | `send_issue_mail_task` |
| **업무 (Issue)** | **신규 업무 생성 (담당자 미지정)** | 생성자 본인 (`creator`) | `[새 업무] {워크스페이스}` | `[#{업무번호}] {업무제목}` (프로필 자동 모니터링 연동) | `send_issue_mail_task` |
| **업무 (Issue)** | **지켜보는 업무 상태 변경** | 해당 업무의 모든 지켜보는 사람 (`watchers`) | `[업무 진행] {워크스페이스}` | `[#{업무번호}] 상태가 "{상태명}"(으)로 변경되었습니다.` | `send_issue_mail_task` |
| **업무 (Issue)** | **지켜보는 업무 담당자 변경** | 해당 업무의 모든 지켜보는 사람 (`watchers`) | `[담당자 변경] {워크스페이스}` | `[#{업무번호}] 담당자가 "{새담당자}"(으)로 변경되었습니다.` | `send_issue_mail_task` |
| **회의록 (Meeting)** | **신규 회의록 등록** | 작성자 + 지정된 참석자 전원 (`attendees`) | `[회의 등록] {워크스페이스}` | `새 회의록이 등록되었습니다: "{회의제목}"` | `send_meeting_mail_task` |
| **회의록 (Meeting)** | **회의록 내용 확정 (Confirm)** | 작성자 + 지정된 참석자 전원 (`attendees`) | `[회의 확정] {워크스페이스}` | `회의록이 확정되었습니다: "{회의제목}"` | `send_meeting_mail_task` |
| **공지 / 게시판** | 중요 공지 및 게시물 등록 | 워크스페이스 참여 멤버 (피드 동기화 완료 / 푸시 확장 대상) | `[공지] {워크스페이스}` | 채널 피드 실시간 스트림 반영 중 (필요 시 FCM 발송 확장 연동) | - |

---

### 🧪 3) 푸시 알림 파이프라인 자동 진단 및 테스트 방법
* **백엔드 관리 명령 점검**:
  ```bash
  # 1. Firebase Admin SDK 및 등록 기기 점검
  dkce web python manage.py test_fcm_push --check-only
  # 2. 특정 사용자에게 즉시 테스트 푸시 발송
  dkce web python manage.py test_fcm_push --user=<username>
  ```
* **백엔드 단위 자동화 테스트**:
  ```bash
  dkce web python manage.py test approval.tests.test_push_notifications
  ```
* **모바일 클라이언트 자가 진단**:
  * `FcmService.showTestLocalNotification()` 호출 시 시스템 채널 권한 및 런처 배지 즉각 자가 점검 가능

---

## 💻 7. 다른 PC (집/사무실)에서 이어 개발할 때 가이드

집이나 다른 PC에서 레포지토리를 받아 작업을 재개할 때 다음 순서로 실행하세요.

1. **최최신 코드 가져오기**
   ```bash
   git pull origin develop
   ```

2. **Android Studio에서 프로젝트 열기**
    - Android Studio 실행 -> `Open` 클릭
    - `C:\Users\<사용자계정>\Git\ibs\app\flutter` (또는 Mac 경로) 선택

3. **패키지 동기화 (의존성 로드)**
    - Android Studio 터미널 (또는 VS Code / PowerShell)에서 실행:
      ```bash
      cd app/flutter
      flutter pub get
      ```

4. **앱 실행 테스트**
    - 안드로이드 에뮬레이터 또는 실기기 연결 후 `flutter run` (또는 Android Studio 상단 재생 버튼 ▶️) 실행

---

## 📦 8. 파이어베이스 비공개 무선 배포 가이드 (Firebase App Distribution)

사내 직원 (10명 이내) 및 비공개 테스트용으로 구글/애플 스토어 등록 및 심사 없이 iOS (아이폰) 및 안드로이드 기기에 무선으로 앱을 바로 설치·배포하는 방법입니다.

### 🤖 1) 안드로이드 (Android) 파이어베이스 배포

1. **설치 파일 (APK) 빌드**:
   ```bash
   cd app/flutter
   flutter build apk --release
   ```
   *생성 파일 경로*: `build/app/outputs/flutter-apk/app-release.apk`

2. **파이어베이스 업로드**:
    - [Firebase Console](https://console.firebase.google.com) 접속 ➔ 프로젝트 선택
    - 좌측 메뉴 `Release & Monitor` ➔ **`App Distribution`** 선택
    - 생성된 `app-release.apk` 파일 드래그 & 드롭 업로드
    - 사내 직원 이메일 주소 목록 (예: `test@company.com`) 입력 후 **`발송`** 클릭

3. **테스터 설치 방법**:
    - 수신된 이메일에서 `[앱 다운로드]` 버튼 탭 ➔ 스마트폰에 즉시 설치 완료!

---

### 📱 2) 아이폰 (iOS / 아이폰 13 프로 등) 무료 무선/케이블 개발자 배포

유료 개발자 계정 결제 없이, 본인의 무료 애플 계정으로 아이폰 13 프로에 앱을 설치하는 4단계 순서입니다:

#### 1단계: Xcode에 무료 애플 계정 등록
1. 맥북에서 Xcode 앱 실행
2. 상단 메뉴 Xcode ➔ Settings (또는 Preferences) ➔ Accounts 탭 클릭
3. 좌측 하단 + 버튼 ➔ Apple ID 선택 후 본인 애플 계정 로그인

#### 2단계: 자동 서명 (Signing) 설정
1. 맥북 터미널에서 Xcode 프로젝트 열기:
   ```bash
   cd app/flutter/ios && open Runner.xcworkspace
   ```
2. Xcode 좌측 상단 Runner 파일 클릭 ➔ 중앙 Signing & Capabilities 탭 클릭
3. Automatically manage signing 체크박스 켜기
4. Team 드롭다운에서 방금 추가한 개인 팀 (Personal Team) 선택!

#### 3단계: 아이폰 13 프로에 네이티브 앱 설치
1. 아이폰 13 프로를 맥북과 같은 와이파이 (또는 케이블) 연결
2. Xcode 상단 기기 선택란에서 [Austin의 iPhone 13 Pro] 선택
3. Xcode 좌측 상단 ▶️ 재생 (Run) 버튼 클릭!

#### 4단계: 아이폰에서 신뢰 승인 (최초 1회)
• 아이폰 13 프로에 앱이 설치된 후 실행할 때 "신뢰할 수 없는 개발자" 팝업이 뜨면:
• 아이폰 설정 ➔ 일반 ➔ VPN 및 기기 관리 ➔ 본인 이메일 터치 ➔ [신뢰] 클릭!

---

### 🔑 3) 멀티 PC (집/사무실) 개발 환경 시크릿 동기화 가이드

Django(`app/django/.env`) 방식과 동일하게 Flutter 앱도 `app/flutter/env` (템플릿)과 `app/flutter/.env` (실제 시크릿 - `.gitignore` 대상) 구조로 시크릿을 관리합니다.

1. **최초/다른 PC에서 코드 받은 후 세팅**:
   ```bash
   cd app/flutter
   # 1. 템플릿 복사
   cp env .env
   # 2. .env 파일 내 GOOGLE_SERVICES_JSON_BASE64 및 GOOGLE_SERVICE_INFO_PLIST_BASE64 채우기
   
   # 3. 자동 복원 스크립트 실행 (1초 완료)
   python setup_env.py
   ```
   *`setup_env.py` 실행 시 `.env` 내용을 바탕으로 `android/app/google-services.json` 과 `ios/Runner/GoogleService-Info.plist` 파일이 자동 생성됩니다.*

---

*마지막 업데이트: 2026-08-21 (전자결재 17종 전 양식 모바일 기안 및 상세 뷰 구현 완료, Freezed 모델 역직렬화 방어, 다크 모드 탭 가시성 개선 반영)*