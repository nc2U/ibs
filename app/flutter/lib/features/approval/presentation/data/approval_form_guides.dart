class ApprovalFormGuide {
  final String title;
  final String category;
  final String summary;
  final List<String> tips;
  final List<String> requiredAttachments;
  final String? exampleTitle;
  final String? exampleContent;

  const ApprovalFormGuide({
    required this.title,
    required this.category,
    required this.summary,
    required this.tips,
    required this.requiredAttachments,
    this.exampleTitle,
    this.exampleContent,
  });
}

const defaultGuide = ApprovalFormGuide(
  title: '일반 기안 문서',
  category: '공통',
  summary: '표준 결재 양식에 따라 문서를 작성합니다.',
  tips: [
    '결재 요청 목적과 주요 내용을 육하원칙에 따라 명확하게 기재하세요.',
    '관련 증빙 서류나 참고 자료가 있다면 첨부파일로 등록해 주세요.',
    '결재선 미리보기를 통해 전결권자를 사전에 확인하시기 바랍니다.',
  ],
  requiredAttachments: ['관련 참고 자료 및 품의 증빙 서류 (선택)'],
  exampleTitle: '[품의] 업무 추진의 건',
);

final Map<String, ApprovalFormGuide> approvalFormGuides = {
  'LEAVE': const ApprovalFormGuide(
    title: '휴가 / 연차 신청서',
    category: '인사/근태',
    summary: '연차, 반차, 경조휴가, 병가 등 근태 휴가를 신청하는 공통 양식입니다.',
    tips: [
      '휴가 시작일 최소 1~2일 전 사전 상신을 원칙으로 합니다.',
      '연속 2일 이상의 휴가인 경우 업무 대행자와의 사전 업무 인수인계가 필수입니다.',
      '오전/오후 반차의 경우 일수를 0.5일로 선택하세요.',
      '경조휴가는 사규에 따른 경조사별 부여 일수를 사전에 확인하시기 바랍니다.',
    ],
    requiredAttachments: [
      '경조휴가: 청첩장, 부고장, 가족관계증명서 등 증빙 사본',
      '병가/공가: 진단서 또는 소견서 (연속 3일 이상 시 필수)',
      '예비군/민방위: 훈련 소집 통지서 또는 교육 이수증',
    ],
    exampleTitle: '[연차] 정기 하계 휴가 신청의 건',
    exampleContent: '하계 휴가 계획에 따라 연차 휴가를 신청합니다. 부재 중 긴급 업무는 대행자에게 인계 완료하였습니다.',
  ),
  'LEAVE_APPLICATION': const ApprovalFormGuide(
    title: '휴가 / 연차 신청서',
    category: '인사/근태',
    summary: '연차, 반차, 경조휴가, 병가 등 근태 휴가를 신청하는 공통 양식입니다.',
    tips: [
      '휴가 시작일 최소 1~2일 전 사전 상신을 원칙으로 합니다.',
      '연속 2일 이상의 휴가인 경우 업무 대행자와의 사전 인수인계가 필수입니다.',
    ],
    requiredAttachments: [
      '경조휴가: 청첩장, 부고장 등 증빙 사본',
      '병가: 진단서 (3일 이상 연속 시)',
    ],
    exampleTitle: '[연차] 정기 연차 휴가 신청의 건',
  ),
  'EXPENSE': const ApprovalFormGuide(
    title: '지출결의서',
    category: '회계/자금',
    summary: '법인카드 결제 건 또는 계좌 이체 지급을 결의하는 회계 양식입니다.',
    tips: [
      '법인카드 사용 건은 사용일로부터 3영업일 이내 상신이 원칙입니다.',
      '접대비/식대 50만원 이상 지출 시 참석자 전원 명단 기재가 필수입니다.',
      '계좌 이체 지급 건은 지급 요청일 최소 2영업일 전에 상신 완료되어야 합니다.',
    ],
    requiredAttachments: [
      '신용카드 매출전표 (법인카드 영수증)',
      '전자세금계산서 또는 계산서 (계좌이체 건)',
      '거래명세서 또는 품목별 상세 영수증',
      '신규 거래처: 사업자등록증 및 통장 사본',
    ],
    exampleTitle: '[지출결의] 부서 전략 세미나 다과비 지출의 건',
    exampleContent: '부서 정기 세미나 진행에 따른 참석자 식음료 비용을 결의합니다.',
  ),
  'EXPENSE_REPORT': const ApprovalFormGuide(
    title: '지출결의서',
    category: '회계/자금',
    summary: '법인카드 결제 건 또는 계좌 이체 지급을 결의하는 회계 양식입니다.',
    tips: [
      '법인카드 사용 건은 사용일로부터 3영업일 이내 상신이 원칙입니다.',
      '증빙 영수증(카드전표, 계산서)을 반드시 첨부하세요.',
    ],
    requiredAttachments: [
      '카드 매출전표 또는 세금계산서',
      '거래명세표',
      '입금 통장 사본 (계좌이체 시)',
    ],
    exampleTitle: '[지출결의] 사무용품 정기 구매 대금 지급의 건',
  ),
  'PURCHASE': const ApprovalFormGuide(
    title: '구매품의서',
    category: '회계/자금',
    summary: '비품, 소모품, IT 장비 및 자재 구매를 사전에 품의하는 양식입니다.',
    tips: [
      '추정 금액 100만원 이상 구매 건은 2개사 이상의 비교견적서를 첨부해야 합니다.',
      '단일 품목 500만원 초과 시 구매 부서와 사전 협의를 권장합니다.',
    ],
    requiredAttachments: [
      '비교견적서 (2개사 이상 견적 비교표)',
      '제품 사양서(카탈로그) 또는 품목 명세서',
    ],
    exampleTitle: '[구매품의] 개발팀 신규 개발용 고성능 모니터 구매의 건',
  ),
  'PURCHASE_ORDER': const ApprovalFormGuide(
    title: '구매품의서',
    category: '회계/자금',
    summary: '비품, 소모품, IT 장비 및 자재 구매를 사전에 품의하는 양식입니다.',
    tips: [
      '추정 금액 100만원 이상 구매 건은 2개사 이상의 비교견적서를 첨부해야 합니다.',
    ],
    requiredAttachments: ['비교견적서 (2개사 이상)', '제품 사양서'],
    exampleTitle: '[구매품의] 사무용 PC 및 주변기기 구매의 건',
  ),
  'GENERAL': const ApprovalFormGuide(
    title: '업무품의서 (일반)',
    category: '일반품의',
    summary: '부서별 일반 업무 추진, 제도 개선, 프로젝트 안건 등을 상신하는 공통 품의 양식입니다.',
    tips: [
      '배경 및 필요성, 세부 추진 계획, 소요 예산, 기대 효과를 체계적으로 정리하세요.',
      '예산이 수반되는 안건은 관련 계정 과목 및 세부 산출 내역을 명시하세요.',
    ],
    requiredAttachments: [
      '사업 계획서 또는 세부 실행 방안 보고서',
      '소요 예산 산출 근거표',
    ],
    exampleTitle: '[품의] 2026년도 사내 업무 생산성 도구 도입의 건',
  ),
  'BIZ_APPROVAL': const ApprovalFormGuide(
    title: '업무품의서 (일반)',
    category: '일반품의',
    summary: '부서별 일반 업무 추진, 제도 개선, 프로젝트 안건 등을 상신하는 공통 품의 양식입니다.',
    tips: [
      '추진 배경과 세부 계획, 기대 효과를 육하원칙에 따라 기재하세요.',
    ],
    requiredAttachments: ['세부 계획서', '예산 산출 내역'],
    exampleTitle: '[품의] 신규 프로젝트 착수 및 예산 승인의 건',
  ),
  'BIZ': const ApprovalFormGuide(
    title: '업무품의서 (일반)',
    category: '일반품의',
    summary: '부서별 일반 업무 추진, 제도 개선, 프로젝트 안건 등을 상신하는 공통 품의 양식입니다.',
    tips: [
      '추진 목적과 기대 효과를 명확하게 기재하세요.',
    ],
    requiredAttachments: ['관련 계획서 사본'],
    exampleTitle: '[품의] 상반기 업무 추진 계획의 건',
  ),
  'BUSINESS_TRIP': const ApprovalFormGuide(
    title: '출장신청서',
    category: '인사/근태',
    summary: '국내외 업무 출장을 사전에 신청하고 여비를 산정하는 양식입니다.',
    tips: [
      '출장 출발 최소 3일 전 사전 상신을 원칙으로 합니다.',
      '방문처 담당자, 미팅 목적, 구체적인 일정을 명시하세요.',
      '교통비 및 숙박비는 회사 여비 규정에 부합하는지 사전 검토하세요.',
    ],
    requiredAttachments: [
      '출장 일정표 또는 방문 기관 초청장/공문',
      '교통편(항공/KTX) 예약 확인서 (예약 건)',
    ],
    exampleTitle: '[출장] 신규 분양 사업지 현장 실사 및 인허가 협의 출장의 건',
  ),
  'TRIP': const ApprovalFormGuide(
    title: '출장신청서',
    category: '인사/근태',
    summary: '국내외 업무 출장을 사전에 신청하는 양식입니다.',
    tips: [
      '출장 목적과 방문처, 이동 수단을 구체적으로 기재하세요.',
    ],
    requiredAttachments: ['출장 일정표', '방문처 관련 서류'],
    exampleTitle: '[출장] 현장 사업지 점검 출장 신청의 건',
  ),
  'CONTRACT': const ApprovalFormGuide(
    title: '계약체결 품의서',
    category: '법무/계약',
    summary: '신규 계약 체결 전 계약 조건, 법적 위험성, 대금 지급 조건을 품의하는 양식입니다.',
    tips: [
      '계약 상대방의 신용도 및 대표자 명의를 사업자등록증과 대조 확인하세요.',
      '특약 사항이나 위약벌 조항이 있는 경우 법무 검토 여부를 명시하세요.',
    ],
    requiredAttachments: [
      '계약서 초안 (Final Draft)',
      '계약 상대방 사업자등록증 및 법인인감증명서 사본',
      '비교 견적서 또는 수의계약 사유서',
    ],
    exampleTitle: '[계약체결] 2026년도 사옥 시설관리 용역 계약 체결의 건',
  ),
  'OFFICIAL_LETTER': const ApprovalFormGuide(
    title: '공문 발신 품의서',
    category: '공문/대외',
    summary: '관공서, 금융기관, 협력업체 등에 대외 발송하는 공문서의 직인 날인 및 발송을 승인받는 양식입니다.',
    tips: [
      '수신처와 발송 명의(대표이사 직인 등)가 정확한지 확인하세요.',
      '공문 시행일자 및 회신 기한을 명시하세요.',
    ],
    requiredAttachments: [
      '발송 대상 공문 전문 (직인 날인 전 최종본)',
      '수신 기관 관련 근거 문서 또는 접수 공문 사본',
    ],
    exampleTitle: '[공문발신] 사업계획승인 신청 관련 보완서류 제출의 건',
  ),
};

ApprovalFormGuide getApprovalGuide(String? formKey, String? code) {
  final k = (formKey ?? '').toUpperCase();
  if (approvalFormGuides.containsKey(k)) return approvalFormGuides[k]!;
  final c = (code ?? '').toUpperCase();
  if (approvalFormGuides.containsKey(c)) return approvalFormGuides[c]!;
  return defaultGuide;
}
