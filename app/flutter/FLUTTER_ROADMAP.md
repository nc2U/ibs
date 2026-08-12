# IBS Flutter 모바일 앱 개발 로드맵 & 가이드

이 문서는 IBS 시스템의 Flutter 기반 모바일 앱 개발 진행 상황, 로드맵, 그리고 타 컴퓨터(집/사무실)에서 이어 개발하기 위한 가이드를 제공합니다.

---

## 📌 1. 프로젝트 정보
* **위치**: `app/flutter`
* **Package Name**: `mobile_ibs`
* **App Display Name**: IBS (건설 종합 관리)
* **주요 개발 환경**: Flutter 3.44.x, Dart 3.12.x, Android Studio / PyCharm

---

## 🟢 2. 현재 진행 상황 (Current Status)

- [x] **Step 0**: `app/flutter` 디렉토리에 Flutter 프로젝트 생성 (`mobile_ibs`)
- [x] **Step 0-1**: 핵심 패키지 설치 완료 (`dio`, `flutter_riverpod`, `flutter_secure_storage`, `go_router`)
- [ ] **Step 1**: 폴더 구조 세팅 및 Dio 기반 JWT API 클라이언트 작성
- [ ] **Step 2**: 로그인 화면 구현 & JWT 토큰 발급/저장 기능 구현
- [ ] **Step 3**: App Router (`go_router`) 및 로그인 인증 가드 연동
- [ ] **Step 4**: 메인 현장(Project) 선택 및 업무/회의 요약 대시보드 화면 구현
- [ ] **Step 5**: 업무(`work`) 관리 기능 모바일 화면 구현
- [ ] **Step 6**: 회의(`meeting`) 및 의제/결정사항 조회 화면 구현

---

## 💻 3. 다른 PC(집/사무실)에서 이어 개발할 때 가이드

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
   - 안드로이드 에뮬레이터 또는 실기기 연결 후 `flutter run` 실행

---

## 🗺️ 4. 단계별 개발 로드맵 (Detailed Roadmap)

### Phase 1: 기반 아키텍처 및 인증 (Auth)
* **1-1. 폴더 구조 생성**: `core/`, `features/` 중심의 Feature-First 클린 아키텍처
* **1-2. JWT API Client 구현**: Django `apiV1/jwt/create/`, `apiV1/jwt/refresh/` 대응
  - `Dio` Interceptor를 활용하여 401 Unauthorized 발생 시 자동으로 토큰 재발급(Refresh) 처리
* **1-3. 로그인 화면 (Login Screen)**: 이메일/아이디 & 비밀번호 입력 폼 및 로그인 상태 관리

### Phase 2: 메인 화면 및 프로젝트 선택
* **2-1. 라우팅 설정 (`go_router`)**: 로그인 여부에 따른 화면 전환 (Auth Guard)
* **2-2. 현장(Project) 셀렉터**: 로그인 유저가 참여 중인 프로젝트 목록 조회 및 선택
* **2-3. 메인 하단 네비게이션**: [홈/대시보드], [업무], [회의], [설정] 탭 구성

### Phase 3: 핵심 현장 기능 모바일 구현
* **3-1. 업무 (Issue) 관리**:
  - 내게 할당된 업무 목록 조회 / 필터링
  - 업무 상세 보기 및 진척률(`done_ratio`) 수정
  - 현장 사진 촬영 후 업무 첨부 파일 업로드
* **3-2. 회의 (Meeting) 관리**:
  - 회의 목록 및 회의록 상세 조회
  - 결정 사항(`decisions`) 및 액션 아이템 확인

---

## 💡 5. Vue 3 vs Flutter 개념 비교 (참고용)

| 개념 | Vue 3 (현재 `app/vue`) | Flutter (신규 `app/flutter`) |
| :--- | :--- | :--- |
| **언어** | TypeScript | Dart |
| **라우팅** | Vue Router (`router/index.ts`) | `go_router` (`core/router/app_router.dart`) |
| **상태 관리** | Pinia (`stores/...`) | `Riverpod` (`providers/...`) |
| **HTTP 클라이언트** | `axios` | `dio` |
| **보안 저장소** | `localStorage` / `sessionStorage` | `flutter_secure_storage` |
| **UI 태그/위젯** | `<v-card>`, `<v-btn>` (Vuetify) | `Card()`, `ElevatedButton()` (Material) |

---

*마지막 업데이트: 2026-08-12*
