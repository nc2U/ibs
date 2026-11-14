# 백엔드 도메인 상세 아키텍처

백엔드의 주요 비즈니스 도메인별 데이터 흐름, 권한, 프론트엔드 연동 규약을 정리합니다. (`apiV1/permissions/permission_guide.md` 및 `.agents/artifacts/`도 함께 참고하십시오.)

---

## 핵심 아키텍처 개념

이 시스템은 건설 프로젝트의 전 생애주기 데이터를 **'워크스페이스 & 프로젝트 기반의 협업 환경'**으로 통합하여 관리하는 것을 목표로 합니다.

* **데이터 무결성 및 이력 관리**: 모든 비즈니스 활동은 변경 이력(`log`)과 권한 체계를 통해 관리되며, 단순히 현재 상태뿐만 아니라 진행 과정을 투명하게 공개합니다.
* **결합된 도메인 관리**: 독립적인 도메인(계약, 수납, 문서 등)이 프로젝트라는 공통 분모를 통해 하나의 맥락으로 연결되어 작동합니다.

---

## 업무 관리 시스템 (`work` 앱)

부동산 시행 및 개발 프로세스를 '업무(`Issue`)'와 '회의(`Meeting`)' 단위로 관리하는 핵심 도메인입니다.

### 1. 데이터 모델 및 비즈니스 흐름

* **워크스페이스 (`IssueProject`) 및 회의 (`Meeting`) 중심 협업**: 워크스페이스는 최상위 관리 단위이며, 회의는 워크스페이스 내 의사결정을 자산화하는 핵심 도구입니다. 단순 회의 기록 작성을 넘어 의제(`agenda`), 결정 사항(`decisions`), 후속 조치(`action_items`)를 자산화합니다. 외부인 참석자는 `other_attendees` 텍스트 필드로 기록합니다.
* **회의와 업무의 유기적 매핑**: `Issue` 모델은 `meeting`을 외래키(`null=True, blank=True`)로 참조합니다. 회의 중 생성된 액션 아이템은 관련 업무(`Issue`)로 자동/수동 할당되어 진척률(`done_ratio`)과 완료율이 실시간 모니터링됩니다.
* **통합 이력 추적**: `ActivityLogEntry`를 통해 워크스페이스 내 전체 활동을 로깅하며, `IssueLogEntry`를 활용해 업무의 상태 변경 정보와 텍스트 차이점(`diff`)을 보관하여 변경 이력을 투명하게 관리합니다.

### 2. 백엔드 API & 권한 통제

* **액션 기반 권한 매핑**: 각 ViewSet에는 `@property`로 `required_permission`을 정의하여 DRF 액션별 권한 코드(예: `meeting.read`, `issue.create`)를 명시합니다. 이 코드는 `apiV1/permissions/work_perms.py`의 `ProjectPermission` / `MeetingPermission` 등 커스텀 권한 클래스에서 요청 유저의 역할(`Role`)과 비교 검증됩니다.
* **행 단위 데이터 보안 (Row-Level Security)**: 권한 검증과 별개로 목록 조회(`list`) 시 권한 없는 워크스페이스의 데이터 유출을 막기 위해, `get_queryset()` 메서드에서 슈퍼유저/`work_manager`가 아닐 경우 **"공개 워크스페이스이거나, 사용자가 속한 워크스페이스이거나, 작성자/담당자(또는 회의 참석자)인 데이터"**로만 필터링해야 합니다.
* **Eager Loading 최적화**: N+1 쿼리 문제를 원천 차단하기 위해 `select_related` 및 `prefetch_related`를 통해 관계 테이블을 미리 로딩해야 합니다.

### 3. 프론트엔드 Pinia & 타입 연동

* **상태 동기화**: Pinia 스토어(`useIssue`, `useMeeting` 등)에서 CRUD 완료 시, 연관된 타 스토어(`useLogging`, `useWork` 등)의 액션을 재조회하여 화면의 일관성을 맞춥니다. 파일이 첨부된 폼을 전송할 때는 `multipart/form-data` 헤더를 설정합니다.
* **타입 안전성**: 프론트엔드 `app/vue/src/store/types/work_*.ts` 파일 내 인터페이스는 백엔드 Serializer가 반환하는 필드 및 Nullable 옵션과 일치하도록 일원화합니다.

---

## 분양 대행 관리 시스템 (`sales` 앱)

부동산 개발 프로젝트(`type='2'`)에서 발생하는 분양 대행 조직, 계약 실적 매핑, 수수료 정책, 정산 회차 및 지급/환수를 총괄하는 도메인입니다.

### 1. 비즈니스 모델 및 흐름

* **영업 조직 관리 (`SalesAgency`, `SalesTeam`, `SalesPerson`)**: 직영 사업부(`is_direct_managed=True`)와 외주 대행사(`is_direct_managed=False`)를 구분하여 관리하며, 인력별 직책(`duty`: 1-상담사, 2-팀장, 3-본부장, 4-임원, 5-지원직)과 재직 상태(`status`: 1-재직, 2-퇴사)를 관리합니다.
* **계약 실적 매핑 (`ContractSalesAgent`)**: 분양 계약(`contract.Contract`)과 영업 인력 또는 외주 대행사의 1:1 매핑 정보를 관리합니다. MGM/중개사 소개 수수료 연계 정보 및 수수료 정산 대상 포함 여부(`is_settlement_approved`)를 지정합니다.
* **수수료 정책 (`CommissionPolicy`)**: 차수/타입별 건당 직급별 인센티브(상담사, 팀장, 본부장, 대행사) 기준표를 정의하며, 공급가(VAT 별도) 및 시행사 청구액(VAT 10% 포함)을 자동으로 계산합니다.
* **정산 회차 및 산출 (`SettlementPeriod`, `CommissionPayout`, `AgencyPayout`)**:
  * 지정 기간 내 체결된 승인 계약 건을 집계하며 타 회차 기정산 건은 자동 제외합니다.
  * 소속 팀에 팀장 부재 시 상위 본부장에게 합산 배정되거나 대행사 이익(`unallocated_fee`)으로 자동 귀속됩니다.
  * 개인별 지급 명세(`CommissionPayout`)는 인센티브, 기본급/일비, 공제/환수액을 반영한 뒤 원천징수 세액 3.3%(사업소득세 3% + 지방소득세 0.3%)를 공제한 세후 실지급액을 산출합니다.
  * 계약 해지 시 발생하는 환수 건(`CommissionClawback`)은 차기 정산 시 자동으로 차감 상계됩니다.
* **지급 관리**: 정산 확정(`status='2'`) 후 회차별/개인별/대행사별 지급 상태(1-미지급, 2-지급 준비, 3-지급 완료)를 갱신 및 관리합니다.

### 2. 백엔드 & 프론트엔드 연동 규칙

* **권한 통제**: `sales.read`(조회), `sales.settle`(정산 실행/확정), `sales.payout`(지급 처리), `sales.policy`(정책 관리), `sales.manage`(조직 및 매핑 관리) 권한 체계를 엄격히 준수합니다.
* **상태 일관성**: 정산 실행(`generatePayouts`) 및 확정(`confirmSettlement`) 시 연관된 대장(개인별 명세, 대행사 명세, 환수 대장)의 상태를 동기화하여 재조회합니다.
