# Ledger 앱 문서

Cash 앱에서 Ledger 앱으로의 장기 리팩토링 프로젝트 관련 문서들입니다.

## 📚 문서 목록

### [01. 리팩토링 마스터 플랜](01_refactoring_master_plan.md)
- 전체 프로젝트 개요 및 목표
- 현재 Cash 앱 문제점 분석
- Ledger 앱 목표 아키텍처
- 단계별 리팩토링 로드맵
- 성공 지표 및 KPI

### [02. 아키텍처 설계 가이드](02_architecture_design.md)
- 도메인 주도 설계 원칙
- 모델 구조 상세 설계
- 도메인별 모델 분리 방안
- 서비스 레이어 패턴
- 성능 최적화 전략
- 보안 및 권한 관리

### [03. 데이터 이관 가이드](03_data_migration_guide.md)
- 단계별 이관 프로세스
- 데이터 품질 검증 방법
- 실시간 동기화 구현
- 양방향 동기화 전략
- 점진적 전환 방법
- 롤백 및 위험 관리

## 🎯 프로젝트 목표

### 기술적 목표
- **단일 책임 원칙 준수**: 각 모델이 하나의 관심사만 담당
- **확장성 확보**: 새로운 거래 유형과 비즈니스 로직을 쉽게 추가
- **성능 최적화**: 기존 성능 수준 이상 유지
- **코드 품질 향상**: 테스트 용이성 및 유지보수성 개선

### 비즈니스 목표
- **무중단 서비스**: 운영 중단 없는 점진적 전환
- **데이터 무결성**: 100% 데이터 정확성 보장
- **사용자 경험**: 기존 사용성 유지 및 개선
- **개발 생산성**: 신규 기능 개발 속도 50% 향상

## 🏗️ 아키텍처 개요

### 기존 구조 (Cash 앱)
```
CashBook (단일 모델)
├── 은행거래 정보
├── 회계분류 정보
├── 증빙 정보
├── 관리 정보
└── 메타데이터

ProjectCashBook (단일 모델)
├── 은행거래 정보
├── 회계분류 정보
├── 계약 정보
├── 회차 정보
└── 메타데이터
```

### 목표 구조 (Ledger 앱)
```
Banking Domain
├── BankTransaction (추상)
├── CompanyBankTransaction
└── ProjectBankTransaction

Accounting Domain
├── AccountingEntry (추상)
├── CompanyAccountingEntry
└── ProjectAccountingEntry

Contract Domain
├── ContractPayment
└── TransactionSplit

Service Layer
├── TransactionService
├── LedgerQueryService
└── BidirectionalSyncService
```

## 📋 이관 로드맵

### Phase 1: 모델 설계 (2-3주)
- [x] 아키텍처 설계 및 문서화
- [ ] 새로운 모델 구조 구현
- [ ] 기본 마이그레이션 생성
- [ ] 단위 테스트 작성

### Phase 2: API 개발 (3-4주)
- [ ] REST API 설계 및 구현
- [ ] Serializer 및 ViewSet 개발
- [ ] 권한 시스템 적용
- [ ] API 문서 생성

### Phase 3: Frontend 개발 (4-5주)
- [ ] Vue 컴포넌트 개발
- [ ] 상태 관리 구현
- [ ] UI/UX 최적화
- [ ] E2E 테스트 작성

### Phase 4: 데이터 이관 (2-3주)
- [ ] 읽기 전용 이관
- [ ] 실시간 동기화
- [ ] 양방향 동기화
- [ ] 데이터 검증

### Phase 5: 시스템 전환 (1-2주)
- [ ] 점진적 사용자 전환
- [ ] Cash 앱 비활성화
- [ ] 데이터 아카이브
- [ ] 최종 정리

## 🔧 개발 환경 설정

### 필수 도구
```bash
# Python 패키지 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
python manage.py makemigrations ledger
python manage.py migrate

# 테스트 실행
python manage.py test ledger
```

### 개발 가이드라인
- **코딩 스타일**: PEP 8 준수
- **테스트 커버리지**: 90% 이상 유지
- **문서화**: 모든 공개 API 문서화 필수
- **코드 리뷰**: PR 시 최소 2명 승인

## 🔍 모니터링 및 검증

### 데이터 무결성 검증
```bash
# 이관 결과 검증
python manage.py validate_migration

# 데이터 일관성 확인
python manage.py check_data_consistency

# 성능 벤치마크
python manage.py benchmark_performance
```

### 실시간 모니터링
- **동기화 지연**: < 1초 목표
- **오류율**: < 0.1% 유지
- **응답시간**: < 500ms 목표
- **처리량**: 기존 대비 100% 이상

## 📞 연락처

### 개발팀
- **백엔드**: [Django/Python 개발자]
- **프론트엔드**: [Vue.js 개발자]
- **DevOps**: [인프라 엔지니어]

### 문의 및 지원
- **이슈 리포트**: GitHub Issues 활용
- **기술 문의**: Slack #ledger-migration 채널
- **긴급 상황**: 온콜 담당자 연락

## 📝 변경 로그

### v1.0 (2025-01-20)
- 초기 문서 작성
- 마스터 플랜 수립
- 아키텍처 설계 완료
- 데이터 이관 가이드 작성

### 향후 계획
- API 설계 명세서 작성
- 테스트 전략 문서 작성
- 운영 가이드 작성
- 개발자 가이드 작성

---

**문서 관리**:
- **작성자**: 개발팀
- **최종 검토**: 아키텍트
- **승인**: 프로젝트 매니저
- **다음 리뷰**: 매주 월요일