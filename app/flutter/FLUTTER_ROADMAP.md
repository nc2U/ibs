# IBS Flutter 모바일 앱 개발 로드맵 & 가이드

이 문서는 IBS 시스템의 Flutter 기반 모바일 앱 개발 진행 상황, 로드맵, 그리고 타 컴퓨터 (집/사무실)에서 이어 개발하기 위한 가이드를 제공합니다.

---

## 📌 1. 프로젝트 정보

* **위치**: `app/flutter`
* **Package Name**: `mobile_ibs`
* **App Display Name**: IBS워크스페이스
* **주요 개발 환경**: Flutter 3.44.x, Dart 3.12.x, Android Studio / PyCharm

---

## 🟢 2. 현재 진행 상황 (Current Status)

- [x] **Step 0**: `app/flutter` 디렉토리에 Flutter 프로젝트 생성 (`mobile_ibs`)
- [x] **Step 0-1**: 핵심 패키지 설치 완료 (`dio`, `flutter_riverpod`, `flutter_secure_storage`, `go_router`)
- [x] **Step 1**: Android Studio SDK 37 설정 & 에뮬레이터 세팅 및 첫 스마트폰 빌드 성공
- [x] **Step 2**: Feature-First 기반 폴더 구조 생성 (`core/`, `features/`)
- [x] **Step 3**: Dio API Client 및 보안 토큰 저장소(`flutter_secure_storage`) 작성
- [x] **Step 4**: 웹 자원 브랜드 동기화 (`IBS워크스페이스` 타이틀 및 `assets/images/logo.png` 적용)
- [x] **Step 5**: Django SimpleJWT (`/api/v1/token/`, Email 기반) 인증 연동 완료
- [x] **Step 6**: 모바일 로그인 화면(UI) 작성 및 실제 서버 계정 인증 성공
- [x] **Step 7**: 로그인 성공 시 메인 대시보드 리다이렉트 & 상단 로그아웃 폼 구축
- [x] **Step 8**: 모바일 메인 대시보드 레이아웃(현장 셀렉터, 퀵 메뉴, 하단 탭 바) 구현
- [ ] **Step 9**: Phase 1 - 업무/회의 모듈 백엔드 API 실제 데이터 동기화 (진행 예정)
- [ ] **Step 10**: Phase 2 - 현장별 계약/수납/입출금/문서 조회 모듈 연동 (진행 예정)
- [ ] **Step 11**: Phase 3 - 고객 정보 열람(납입/계약/상담) & 전자결재/푸시 알림 (진행 예정)

---

## 💻 3. 다른 PC (집/사무실)에서 이어 개발할 때 가이드

집이나 다른 PC에서 레포지토리를 받아 작업을 재개할 때 다음 순서로 실행하세요.

1. **최신 코드 가져오기**
   ```bash
   git pull origin develop
   ```

2. **Android Studio에서 프로젝트 열기**
   - Android Studio 실행 -> `Open` 클릭
   - `C:\Users\<사용자계정>\Git\ibs\app\flutter` 경로 선택

3. **패키지 동기화 (의존성 로드)**
   - Android Studio 터미널 (또는 VS Code / PowerShell)에서 실행:
     ```bash
     cd app/flutter
     flutter pub get
     ```

4. **앱 실행 테스트**
   - 안드로이드 에뮬레이터 또는 실기기 연결 후 `flutter run` (또는 Android Studio 상단 재생 버튼 ▶️) 실행

---

## 🗺️ 4. 단계별 개발 로드맵 (Detailed Roadmap)

### Phase 1: 업무관리 핵심 모듈 (입출력 및 진행 현황) [다음 진행 대상]
* **1-1. 회의록 (`meeting`) 모듈**:
  - 회의 목록 및 회의록 상세 조회
  - 의제(`agenda`), 결정 사항(`decisions`), 액션 아이템 확인
* **1-2. 업무 (`work`) 모듈**:
  - 내게 할당된 업무 목록 조회 / 필터링
  - 업무 상세 보기 및 진척률(`done_ratio`) 수정 및 댓글/이력 확인
  - 현장 사진 촬영 후 업무 첨부 파일 업로드

### Phase 2: 프로젝트별 핵심 사업 모듈
* **2-1. 현장 선택 (Project Selector) 동기화**:
  - 로그인 유저가 속한 실제 프로젝트 목록 API 동기화 및 탭 간 전역 상태 유지
* **2-2. 사업/재무 모듈 조회**:
  - 계약 (`contract`) 및 수납/입출금 (`ledger` / `payment`) 현황 요약 카드
  - 현장 문서 (`docs`) 및 첨부파일 미리보기/조회

### Phase 3: 고객 정보 열람 및 모바일 부가 서비스
* **3-1. 고객 (Customer) 정보 관리**:
  - 고객별 계약/납입/미납금 현황 조회
  - 고객 상담 기록 작성 및 고지 알림 기능
* **3-2. 모바일 전자 결재 & 알림**:
  - 결재 문서 작성, 결재 라인 지정, 원클릭 결재/반려
  - Firebase Cloud Messaging (FCM) 기반 실시간 모바일 푸시 알림

---

## 💡 5. Vue 3 vs Flutter 개념 비교 (참고용)

| 개념 | Vue 3 (현재 `app/vue`) | Flutter (신규 `app/flutter`) |
| :--- | :--- | :--- |
| **언어** | TypeScript | Dart |
| **라우팅** | Vue Router (`router/index.ts`) | `go_router` (`core/router/app_router.dart`) / `Navigator` |
| **상태 관리** | Pinia (`stores/...`) | `Riverpod` (`providers/...`) |
| **HTTP 클라이언트** | `axios` | `dio` |
| **보안 저장소** | `localStorage` / `sessionStorage` | `flutter_secure_storage` |
| **UI 태그/위젯** | `<v-card>`, `<v-btn>` (Vuetify) | `Card()`, `ElevatedButton()` (Material) |

---

*마지막 업데이트: 2026-08-12 (로그인/인증 & 메인 대시보드 리다이렉트 구현 완료)*
