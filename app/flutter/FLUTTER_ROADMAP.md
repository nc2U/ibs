# IBS Flutter 모바일 앱 개발 로드맵 & 가이드

이 문서는 IBS 시스템의 Flutter 기반 모바일 앱 개발 진행 상황, 로드맵, 그리고 타 컴퓨터 (집/사무실)에서 이어 개발하기 위한 가이드를 제공합니다.

---

## 📌 1. 프로젝트 정보

* **위치**: `app/flutter`
* **Package Name**: `mobile_ibs`
* **App Display Name**: IBS워크스페이스
* **주요 개발 환경**: Flutter 3.x, Dart 3.9.x+, Android Studio / PyCharm
* **핵심 패키지**:
    * 상태관리: `flutter_riverpod` + `riverpod_annotation` (코드 생성)
    * 라우팅: `go_router` (ShellRoute 기반 하단탭 유지)
    * 네트워킹: `dio` (AuthInterceptor 토큰 자동 갱신)
    * 보안저장소: `flutter_secure_storage`
    * 모델: `freezed` + `json_serializable` (코드 생성)
    * UI: `google_fonts` (Noto Sans KR), `shimmer`, `cached_network_image`
    * 기타: `image_picker`, `hive_flutter`, `flutter_svg`

---

## 🏛️ 2. 도메인 용어 체계 (Domain Terminology Architecture)

| 구분 | 백엔드 모델 | 비즈니스 도메인 범위 | 웹(Vue) & 모바일(Flutter) 용어 |
| :--- | :--- | :--- | :--- |
| **Work Core** | `work.IssueProject` | 본사관리(1) / 부동산개발(2) / 기타(3) 통합 협업 공간 | **`워크스페이스` (Workspace)** |
| **IBS Global** | `project.IssueProject` (`type='2'`) | 분양, 수납, 입출금, 소송문서 등 부동산 개발 전용 사업지 | **`프로젝트` (Project)** |

* **'현장' 용어 사용 엄금**: 코드베이스 및 UI에서 '현장'이라는 용어 대신 '워크스페이스' 또는 '프로젝트'를 명확히 구분하여 사용합니다.
* **워크스페이스 (`work_core`)**: 업무(Issue), 회의록(Meeting), 로드맵, 공지사항 등 본사/프로젝트 전반의 협업 공간.
* **프로젝트 (`ibs_global`)**: 부동산 개발(`type='2'`)에 한정되어 계약(Contract), 수납(Payment), 재무(Ledger), 소송/공용문서(Docs), 설정(Settings)을 관리하는 사업지.

---

## 📱 3. 모바일 앱 메인 카테고리 구조

```text
 📱 IBS워크스페이스 (Mobile App Structure)
  ├── 1️⃣ [업무 관리] (Work Core)
  │    ├── 🏢 워크스페이스 선택 (Workspace Selector)
  │    ├── 📅 회의록 목록, 의제 & 결정사항/액션아이템 (Meeting)
  │    ├── 📋 할당 업무 목록, 진척률 및 댓글 (Issue)
  │    └── ✏️ 회의록 & 업무 신규 생성 및 수정 폼 (Meeting / Issue CRUD)
  │
  ├── 2️⃣ [프로젝트 관리] (Project Core) *radius = 0 직각 미니멀 디자인
  │    ├── 🏗️ 프로젝트 선택 (Project Selector - type='2' 전용) & 개요
  │    ├── 📄 계약 관리 (Contract)
  │    ├── 💳 대금 수납 관리 (Payment)
  │    ├── 💰 자금 / 재무 관리 (Ledger)
  │    ├── 📂 문서 / 소송 관리 (Docs)
  │    └── ⚙️ 프로젝트 설정 (Settings)
  │
  ├── 3️⃣ [전자 결재] (Approval Core) *웹/백엔드 우선 적용 후 개발
  │    ├── 🔴 미결함 (내가 승인/반려할 결재)
  │    ├── 📤 기안함 (내가 올린 지출결의/계약승인서)
  │    ├── ✍️ 모바일 서명 & 1초 결재 승인/반려
  │    └── 🔔 실시간 PUSH 알림
  │
  └── 4️⃣ [전사 정보 공유 & 온보딩] (Corporate & Onboarding) *웹/백엔드 우선 적용 후 개발
       ├── 🎯 회사 비전, 미션, OKR 목표 달성률 & CEO 메시지/오늘의 한마디
       └── 🔰 신입사원 온보딩 가이드 & 사내 FAQ
```

---

## 🟢 4. 현재 진행 상황 (Current Status)

- [x] **Step 0**: `app/flutter` 디렉토리에 Flutter 프로젝트 생성 (`mobile_ibs`)
- [x] **Step 0-1**: 핵심 패키지 설치 완료 (`dio`, `flutter_riverpod`, `flutter_secure_storage`, `go_router`)
- [x] **Step 1**: Android Studio SDK 37 설정 & 에뮬레이터 세팅 및 첫 스마트폰 빌드 성공
- [x] **Step 2**: Feature-First 기반 폴더 구조 생성 (`core/`, `features/`)
- [x] **Step 3**: Dio API Client 및 보안 토큰 저장소(`flutter_secure_storage`) 작성
- [x] **Step 4**: 웹 자원 브랜드 동기화 (`IBS워크스페이스` 타이틀 및 `assets/images/logo.png` 적용)
- [x] **Step 5**: Django SimpleJWT (`/api/v1/token/`, Email 기반) 인증 연동 완료
- [x] **Step 6**: 모바일 로그인 화면(UI) 작성 및 실제 서버 계정 인증 성공
- [x] **Step 7**: 로그인 성공 시 메인 대시보드 리다이렉트 & 상단 로그아웃 폼 구축
- [x] **Step 8**: 모바일 메인 대시보드 레이아웃 (워크스페이스 셀렉터, 퀵 메뉴, 하단 탭 바) 구현
- [x] **Step 9**: Phase 1 - 업무/회의 모듈 (Issue / Meeting) API 연동, CRUD 폼, 실시간 필터 동기화 구현 완료
- [x] **Step 9-1**: 도메인 용어 체계 정립 (`work_core: 워크스페이스` vs `ibs_global: 프로젝트`) 및 Vue 3 웹 & Flutter 모바일 100% 동기화
- [x] **Step 9-2**: `ProjectScreen` (프로젝트 탭) 5대 핵심 모듈 카드 리팩토링 (계약/수납/자금/문서/설정, `radius = 0` 직각 스타일 적용)
- [ ] **Step 10**: Phase 2 - 프로젝트별 계약 관리 (`Contract`) 및 수납/입출금 상세 조회 모듈 연동 (다음 진행 예정)
- [ ] **Step 11**: Phase 3 - 전자결재 / 전사 정보 확장 모듈 (진행 예정)

---

## 💻 5. 다른 PC (집/사무실)에서 이어 개발할 때 가이드

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

## 🗺️ 6. 단계별 개발 로드맵 (Detailed Roadmap)

### Phase 1: 업무관리 핵심 모듈 (입출력 및 진행 현황) [완료]
* **1-1. 회의록 (`meeting`) 모듈**:
  - 회의 목록 및 회의록 상세 조회, 의제/결정사항/액션아이템 확인
  - 회의 생성 및 수정 폼 (`MeetingFormScreen`)
* **1-2. 업무 (`work`) 모듈**:
  - 내 업무/전체 업무 목록 조회 및 실시간 워크스페이스 필터 반응
  - 업무 상세 보기 및 진척률(`done_ratio`) 수정, 댓글/파일 확인
  - 업무 생성 및 수정 폼 (`IssueFormScreen`)
* **1-3. 전역 상태 & 필터 동기화**:
  - `selectedProjectProvider` 변경 시 회의 및 업무 목록 즉시 재조회 연동 완료

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
  - 프로젝트별 분양/계약 목록 조회 API 연동
  - 계약 상세 보기 화면 및 동호수 배치 현황 연결

### Phase 3: 전자결재 & 전사 정보 확장 모듈
> ⚠️ **원칙**: 아래 기능들은 Django 백엔드 및 Vue 웹 애플리케이션에 먼저 모델/기능을 완성 및 검증한 후 모바일 앱으로 확충합니다.
* **3-1. 고객 (Customer) 정보 관리**:
  - 고객별 계약/납입/미납금 현황 조회
  - 고객 상담 기록 작성 및 고지 알림 기능
* **3-2. 전사 비전 & 온보딩 시스템**:
  - 회사 비전/미션/OKR 및 경영진 메시지 공유
  - 신입사원 온보딩 가이드, 체크리스트, 사내 FAQ, 디렉토리
* **3-3. 모바일 전자 결재 & 알림**:
  - 결재 문서 작성, 결재 라인 지정, 원클릭 결재/반려
  - Firebase Cloud Messaging (FCM) 기반 실시간 모바일 푸시 알림

---

## 💡 7. Vue 3 vs Flutter 개념 비교 (참고용)

| 개념 | Vue 3 (현재 `app/vue`) | Flutter (신규 `app/flutter`) |
| :--- | :--- | :--- |
| **언어** | TypeScript | Dart |
| **라우팅** | Vue Router (`router/index.ts`) | `go_router` (`core/router/app_router.dart`) / `Navigator` |
| **상태 관리** | Pinia (`stores/...`) | `Riverpod` (`providers/...`) |
| **HTTP 클라이언트** | `axios` | `dio` |
| **보안 저장소** | `localStorage` / `sessionStorage` | `flutter_secure_storage` |
| **UI 태그/위젯** | `<v-card>`, `<v-btn>` (Vuetify) | `Card()`, `ElevatedButton()` (Material) |

---

## 📦 8. 파이어베이스 비공개 무선 배포 가이드 (Firebase App Distribution)

사내 직원(10명 이내) 및 비공개 테스트용으로 구글/애플 스토어 등록 및 심사 없이 iOS(아이폰) 및 안드로이드 기기에 무선으로 앱을 바로 설치·배포하는 방법입니다.

### 🤖 1) 안드로이드 (Android) 파이어베이스 배포

1. **설치 파일(APK) 빌드**:
   ```bash
   cd app/flutter
   flutter build apk --release
   ```
   *생성 파일 경로*: `build/app/outputs/flutter-apk/app-release.apk`

2. **파이어베이스 업로드**:
   - [Firebase Console](https://console.firebase.google.com) 접속 ➔ 프로젝트 선택
   - 좌측 메뉴 `Release & Monitor` ➔ **`App Distribution`** 선택
   - 생성된 `app-release.apk` 파일 드래그 & 드롭 업로드
   - 사내 직원 이메일 주소 목록(예: `test@company.com`) 입력 후 **`발송`** 클릭

3. **테스터 설치 방법**:
   - 수신된 이메일에서 `[앱 다운로드]` 버튼 탭 ➔ 스마트폰에 즉시 설치 완료!

---

### 📱 2) 아이폰 (iOS / 아이폰 13 프로 등) 파이어베이스 배포

아이폰의 경우 애플 보안 정책에 따라 테스터 기기의 UDID 등록 및 Ad-Hoc 프로비저닝 프로필이 연결된 IPA 빌드가 필요합니다.

1. **테스트 아이폰 UDID 추출**:
   - 아이폰 사파리(Safari) 브라우저로 **[udid.io](https://www.udid.io)** 접속
   - `Tap to find UDID` 탭 ➔ 아이폰 고유 UDID 복사

2. **애플 개발자 계정 (developer.apple.com) 등록**:
   - `Certificates, Identifiers & Profiles` ➔ `Devices`에 복사한 UDID 추가
   - Ad-Hoc 프로비저닝 프로필(Provisioning Profile) 생성/갱신

3. **IPA 파일 빌드**:
   ```bash
   cd app/flutter
   flutter build ipa --release --export-options-plist=ios/ExportOptions.plist
   ```
   *생성 파일 경로*: `build/ios/ipa/mobile_ibs.ipa`

4. **파이어베이스 업로드 및 배포**:
   - [Firebase Console](https://console.firebase.google.com) ➔ `App Distribution`
   - `.ipa` 파일 드래그 & 드롭 업로드 ➔ 사내 직원 이메일로 발송

---

### ⚡ 3) 외부 연동용 서버 URL 주입 빌드 방식

배포 시 백엔드 운영/개발 서버 URL을 동적으로 전달하려면 `--dart-define` 옵션을 추가하여 빌드합니다.

```bash
# 안드로이드 운영 서버 주소 주입 빌드
flutter build apk --release --dart-define=BASE_URL=https://api.ibs.company.com

# iOS 운영 서버 주소 주입 빌드
flutter build ipa --release --dart-define=BASE_URL=https://api.ibs.company.com --export-options-plist=ios/ExportOptions.plist
```

---

*마지막 업데이트: 2026-08-14 (파이어베이스 안드로이드/아이폰 비공개 배포 가이드 및 --dart-define 서버 주소 주입 연동 완료)*
