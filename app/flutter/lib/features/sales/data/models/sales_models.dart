/// 분양 대행 관리 (Sales Agency) 데이터 모델
library;

int _parseInt(dynamic val, [int fallback = 0]) {
  if (val == null) return fallback;
  if (val is int) return val;
  if (val is num) return val.toInt();
  if (val is String) {
    return int.tryParse(val) ?? double.tryParse(val)?.toInt() ?? fallback;
  }
  return fallback;
}

int? _tryParseInt(dynamic val) {
  if (val == null) return null;
  if (val is int) return val;
  if (val is num) return val.toInt();
  if (val is String) {
    return int.tryParse(val) ?? double.tryParse(val)?.toInt();
  }
  return null;
}

/// 간단 계약 선택지 모델
class SimpleContractOption {
  final int value;
  final String label;

  const SimpleContractOption({
    required this.value,
    required this.label,
  });

  factory SimpleContractOption.fromJson(Map<String, dynamic> json) {
    return SimpleContractOption(
      value: _parseInt(json['value']),
      label: json['label'] as String? ?? '',
    );
  }
}

/// 분양 대행사 모델
class SalesAgencyModel {
  final int id;
  final int project;
  final String name;
  final bool isDirectManaged;
  final String? businessNumber;
  final String? ceoName;
  final String? phone;
  final int order;
  final bool isActive;

  const SalesAgencyModel({
    required this.id,
    required this.project,
    required this.name,
    this.isDirectManaged = false,
    this.businessNumber,
    this.ceoName,
    this.phone,
    this.order = 1,
    this.isActive = true,
  });

  factory SalesAgencyModel.fromJson(Map<String, dynamic> json) {
    return SalesAgencyModel(
      id: _parseInt(json['id']),
      project: _parseInt(json['project']),
      name: json['name'] as String? ?? '',
      isDirectManaged: json['is_direct_managed'] as bool? ?? false,
      businessNumber: json['business_number'] as String?,
      ceoName: json['ceo_name'] as String?,
      phone: json['phone'] as String?,
      order: _parseInt(json['order'], 1),
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}

/// 영업 조직 (본부/팀) 모델
class SalesTeamModel {
  final int id;
  final int agency;
  final String? agencyName;
  final int? parent;
  final String? parentName;
  final String name;
  final int order;
  final bool isActive;
  final int membersCount;

  const SalesTeamModel({
    required this.id,
    required this.agency,
    this.agencyName,
    this.parent,
    this.parentName,
    required this.name,
    this.order = 1,
    this.isActive = true,
    this.membersCount = 0,
  });

  factory SalesTeamModel.fromJson(Map<String, dynamic> json) {
    return SalesTeamModel(
      id: _parseInt(json['id']),
      agency: _parseInt(json['agency']),
      agencyName: json['agency_name'] as String?,
      parent: _tryParseInt(json['parent']),
      parentName: json['parent_name'] as String?,
      name: json['name'] as String? ?? '',
      order: _parseInt(json['order'], 1),
      isActive: json['is_active'] as bool? ?? true,
      membersCount: _parseInt(json['members_count']),
    );
  }
}

/// 영업 인력 (상담사/팀장/본부장) 모델
class SalesPersonModel {
  final int id;
  final int team;
  final String? teamName;
  final String? agencyName;
  final int? user;
  final String name;
  final String duty; // 1: 상담사, 2: 팀장, 3: 본부장, 4: 총괄본부장
  final String? dutyDisplay;
  final String status; // 1: 위촉(재직), 2: 해촉(퇴사)
  final String? statusDisplay;
  final String? phone;
  final String? idNumber;
  final String taxType; // 1: 3.3% 프리랜서, 2: 4대보험, 3: 기타
  final String? taxTypeDisplay;
  final String? bankName;
  final String? accountNumber;
  final String? accountHolder;
  final String? joinDate;
  final String? quitDate;
  final String? notes;
  final int documentsCount;
  final List<SalesPersonDocumentModel> documents;

  const SalesPersonModel({
    required this.id,
    required this.team,
    this.teamName,
    this.agencyName,
    this.user,
    required this.name,
    this.duty = '1',
    this.dutyDisplay,
    this.status = '1',
    this.statusDisplay,
    this.phone,
    this.idNumber,
    this.taxType = '1',
    this.taxTypeDisplay,
    this.bankName,
    this.accountNumber,
    this.accountHolder,
    this.joinDate,
    this.quitDate,
    this.notes,
    this.documentsCount = 0,
    this.documents = const [],
  });

  factory SalesPersonModel.fromJson(Map<String, dynamic> json) {
    final docsList = (json['documents'] as List<dynamic>?)
            ?.map((d) => SalesPersonDocumentModel.fromJson(d as Map<String, dynamic>))
            .toList() ??
        [];

    return SalesPersonModel(
      id: _parseInt(json['id']),
      team: _parseInt(json['team']),
      teamName: json['team_name'] as String?,
      agencyName: json['agency_name'] as String?,
      user: _tryParseInt(json['user']),
      name: json['name'] as String? ?? '',
      duty: json['duty'] as String? ?? '1',
      dutyDisplay: json['duty_display'] as String?,
      status: json['status'] as String? ?? '1',
      statusDisplay: json['status_display'] as String?,
      phone: json['phone'] as String?,
      idNumber: json['id_number'] as String?,
      taxType: json['tax_type'] as String? ?? '1',
      taxTypeDisplay: json['tax_type_display'] as String?,
      bankName: json['bank_name'] as String?,
      accountNumber: json['account_number'] as String?,
      accountHolder: json['account_holder'] as String?,
      joinDate: json['join_date'] as String?,
      quitDate: json['quit_date'] as String?,
      notes: json['notes'] as String?,
      documentsCount: _parseInt(json['documents_count'], docsList.length),
      documents: docsList,
    );
  }
}

/// 영업 인력 제출 증빙 서류 모델
class SalesPersonDocumentModel {
  final int id;
  final int salesPerson;
  final String? salesPersonName;
  final String docType; // 1: 등본, 2: 통장, 3: 신분증, 4: 위촉계약서, 5: 각종 서약서/각서, 9: 기타
  final String? docTypeDisplay;
  final String title;
  final String? file;
  final String? fileName;
  final String? fileType;
  final int? fileSize;
  final bool isVerified;
  final String? verifiedAt;
  final int? verifiedBy;
  final String? verifiedByName;
  final int? uploader;
  final String? uploaderName;
  final String? createdAt;
  final String? updatedAt;

  const SalesPersonDocumentModel({
    required this.id,
    required this.salesPerson,
    this.salesPersonName,
    this.docType = '1',
    this.docTypeDisplay,
    required this.title,
    this.file,
    this.fileName,
    this.fileType,
    this.fileSize,
    this.isVerified = false,
    this.verifiedAt,
    this.verifiedBy,
    this.verifiedByName,
    this.uploader,
    this.uploaderName,
    this.createdAt,
    this.updatedAt,
  });

  factory SalesPersonDocumentModel.fromJson(Map<String, dynamic> json) {
    return SalesPersonDocumentModel(
      id: _parseInt(json['id']),
      salesPerson: _parseInt(json['sales_person']),
      salesPersonName: json['sales_person_name'] as String?,
      docType: json['doc_type'] as String? ?? '1',
      docTypeDisplay: json['doc_type_display'] as String?,
      title: json['title'] as String? ?? '',
      file: json['file'] as String?,
      fileName: json['file_name'] as String?,
      fileType: json['file_type'] as String?,
      fileSize: _tryParseInt(json['file_size']),
      isVerified: json['is_verified'] as bool? ?? false,
      verifiedAt: json['verified_at'] as String?,
      verifiedBy: _tryParseInt(json['verified_by']),
      verifiedByName: json['verified_by_name'] as String?,
      uploader: _tryParseInt(json['uploader']),
      uploaderName: json['uploader_name'] as String?,
      createdAt: json['created_at'] as String?,
      updatedAt: json['updated_at'] as String?,
    );
  }
}

/// 수수료 정책 모델
class CommissionPolicyModel {
  final int id;
  final int project;
  final int? orderGroup;
  final String? orderGroupName;
  final int? unitType;
  final String? unitTypeName;
  final String name;
  final int agentFee;
  final int leaderFee;
  final int directorFee;
  final int agencyFee;
  final String payCondition;
  final String? payConditionDisplay;
  final String startDate;
  final String? endDate;
  final bool isActive;

  const CommissionPolicyModel({
    required this.id,
    required this.project,
    this.orderGroup,
    this.orderGroupName,
    this.unitType,
    this.unitTypeName,
    required this.name,
    this.agentFee = 0,
    this.leaderFee = 0,
    this.directorFee = 0,
    this.agencyFee = 0,
    this.payCondition = '1',
    this.payConditionDisplay,
    required this.startDate,
    this.endDate,
    this.isActive = true,
  });

  factory CommissionPolicyModel.fromJson(Map<String, dynamic> json) {
    return CommissionPolicyModel(
      id: _parseInt(json['id']),
      project: _parseInt(json['project']),
      orderGroup: _tryParseInt(json['order_group']),
      orderGroupName: json['order_group_name'] as String?,
      unitType: _tryParseInt(json['unit_type']),
      unitTypeName: json['unit_type_name'] as String?,
      name: json['name'] as String? ?? '',
      agentFee: _parseInt(json['agent_fee']),
      leaderFee: _parseInt(json['leader_fee']),
      directorFee: _parseInt(json['director_fee']),
      agencyFee: _parseInt(json['agency_fee']),
      payCondition: json['pay_condition'] as String? ?? '1',
      payConditionDisplay: json['pay_condition_display'] as String?,
      startDate: json['start_date'] as String? ?? '',
      endDate: json['end_date'] as String?,
    );
  }

  int get totalFee => agentFee + leaderFee + directorFee + agencyFee;
  int get vatAmount => (totalFee * 0.1).floor();
  int get totalBillingAmount => totalFee + vatAmount;
}

/// 차수 (OrderGroup) 간략 옵션 모델
class OrderGroupOption {
  final int id;
  final String name;

  const OrderGroupOption({required this.id, required this.name});

  factory OrderGroupOption.fromJson(Map<String, dynamic> json) {
    return OrderGroupOption(
      id: _parseInt(json['pk'] ?? json['id']),
      name: json['name'] as String? ?? '',
    );
  }
}

/// 유니트 타입 (UnitType) 간략 옵션 모델
class UnitTypeOption {
  final int id;
  final String name;
  final String? color;

  const UnitTypeOption({required this.id, required this.name, this.color});

  factory UnitTypeOption.fromJson(Map<String, dynamic> json) {
    return UnitTypeOption(
      id: _parseInt(json['pk'] ?? json['id']),
      name: json['name'] as String? ?? '',
      color: json['color'] as String?,
    );
  }
}

/// 계약 영업 담당자 매핑 모델
class ContractSalesAgentModel {
  final int id;
  final int contract;
  final String? contractSerial;
  final String? contractorName;
  final String? orderGroupName;
  final String? unitTypeName;
  final String? unitInfo;
  final int? agency;
  final String? agencyName;
  final bool isDirectManaged;
  final int? salesPerson;
  final String? salesPersonName;
  final int? team;
  final String? teamName;
  final int? policy;
  final String? policyName;
  final String? contractDate;
  final String? mgmName;
  final String? mgmPhone;
  final int mgmFee;
  final String? note;
  final bool isSettlementApproved;
  final String? approvalNote;
  final bool isSettled;
  final String? settledPeriodTitle;
  final String? createdAt;
  final String? updatedAt;

  const ContractSalesAgentModel({
    required this.id,
    required this.contract,
    this.contractSerial,
    this.contractorName,
    this.orderGroupName,
    this.unitTypeName,
    this.unitInfo,
    this.agency,
    this.agencyName,
    this.isDirectManaged = true,
    this.salesPerson,
    this.salesPersonName,
    this.team,
    this.teamName,
    this.policy,
    this.policyName,
    this.contractDate,
    this.mgmName,
    this.mgmPhone,
    this.mgmFee = 0,
    this.note,
    this.isSettlementApproved = true,
    this.approvalNote,
    this.isSettled = false,
    this.settledPeriodTitle,
    this.createdAt,
    this.updatedAt,
  });

  factory ContractSalesAgentModel.fromJson(Map<String, dynamic> json) {
    return ContractSalesAgentModel(
      id: _parseInt(json['id']),
      contract: _parseInt(json['contract']),
      contractSerial: json['contract_serial'] as String?,
      contractorName: json['contractor_name'] as String?,
      orderGroupName: json['order_group_name'] as String?,
      unitTypeName: json['unit_type_name'] as String?,
      unitInfo: json['unit_info'] as String?,
      agency: _tryParseInt(json['agency']),
      agencyName: json['agency_name'] as String?,
      isDirectManaged: json['is_direct_managed'] as bool? ?? true,
      salesPerson: _tryParseInt(json['sales_person']),
      salesPersonName: json['sales_person_name'] as String?,
      team: _tryParseInt(json['team']),
      teamName: json['team_name'] as String?,
      policy: _tryParseInt(json['policy']),
      policyName: json['policy_name'] as String?,
      contractDate: json['contract_date'] as String?,
      mgmName: json['mgm_name'] as String?,
      mgmPhone: json['mgm_phone'] as String?,
      mgmFee: _parseInt(json['mgm_fee']),
      note: json['note'] as String?,
      isSettlementApproved: json['is_settlement_approved'] as bool? ?? true,
      approvalNote: json['approval_note'] as String?,
      isSettled: json['is_settled'] as bool? ?? false,
      settledPeriodTitle: json['settled_period_title'] as String?,
      createdAt: json['created_at'] as String?,
      updatedAt: json['updated_at'] as String?,
    );
  }
}

/// 전체 계약과 영업 매핑 정보를 결합한 통합 아이템 모델
class CombinedContractPerformanceItem {
  final int contractId;
  final String contractLabel;
  final ContractSalesAgentModel? mapping;

  const CombinedContractPerformanceItem({
    required this.contractId,
    required this.contractLabel,
    this.mapping,
  });

  bool get isMapped => mapping != null;
  int? get agency => mapping?.agency;
  String? get agencyName => mapping?.agencyName;
  bool get isDirectManaged => mapping?.isDirectManaged ?? true;
  String? get salesPersonName => mapping?.salesPersonName;
  String? get teamName => mapping?.teamName;
  String? get policyName => mapping?.policyName;
  String? get contractDate => mapping?.contractDate;
  String? get mgmName => mapping?.mgmName;
  String? get mgmPhone => mapping?.mgmPhone;
  int get mgmFee => mapping?.mgmFee ?? 0;
  String? get note => mapping?.note;
  bool get isSettlementApproved => mapping?.isSettlementApproved ?? true;
  String? get approvalNote => mapping?.approvalNote;
  bool get isSettled => mapping?.isSettled ?? false;
  String? get settledPeriodTitle => mapping?.settledPeriodTitle;
}


/// 수수료 지급 상세 계약 건별 내역 모델
class PayoutContractDetailModel {
  final int id;
  final int payout;
  final int contract;
  final String? contractSerial;
  final String? contractorName;
  final String roleType; // agent, leader, director, mgm
  final String? roleTypeDisplay;
  final int unitFee;

  const PayoutContractDetailModel({
    required this.id,
    required this.payout,
    required this.contract,
    this.contractSerial,
    this.contractorName,
    this.roleType = 'agent',
    this.roleTypeDisplay,
    this.unitFee = 0,
  });

  factory PayoutContractDetailModel.fromJson(Map<String, dynamic> json) {
    return PayoutContractDetailModel(
      id: _parseInt(json['id']),
      payout: _parseInt(json['payout']),
      contract: _parseInt(json['contract']),
      contractSerial: json['contract_serial'] as String?,
      contractorName: json['contractor_name'] as String?,
      roleType: json['role_type'] as String? ?? 'agent',
      roleTypeDisplay: json['role_type_display'] as String?,
      unitFee: _parseInt(json['unit_fee']),
    );
  }
}

/// 개인별 수수료 정산 및 지급 내역 모델
class CommissionPayoutModel {
  final int id;
  final int period;
  final int salesPerson;
  final String? salesPersonName;
  final String? dutyDisplay;
  final String? teamName;
  final int basePay;
  final int contractCount;
  final int commissionAmount;
  final int bonusAmount;
  final int deductionAmount;
  final int grossAmount;
  final int incomeTax;
  final int localIncomeTax;
  final int totalTax;
  final int netAmount;
  final String payStatus; // 1: 대기, 2: 승인, 3: 지급 완료, 4: 지급 보류
  final String? payStatusDisplay;
  final String? paidDate;
  final String? bankName;
  final String? accountNumber;
  final String? accountHolder;
  final String? note;
  final List<PayoutContractDetailModel> contractDetails;

  const CommissionPayoutModel({
    required this.id,
    required this.period,
    required this.salesPerson,
    this.salesPersonName,
    this.dutyDisplay,
    this.teamName,
    this.basePay = 0,
    this.contractCount = 0,
    this.commissionAmount = 0,
    this.bonusAmount = 0,
    this.deductionAmount = 0,
    this.grossAmount = 0,
    this.incomeTax = 0,
    this.localIncomeTax = 0,
    this.totalTax = 0,
    this.netAmount = 0,
    this.payStatus = '1',
    this.payStatusDisplay,
    this.paidDate,
    this.bankName,
    this.accountNumber,
    this.accountHolder,
    this.note,
    this.contractDetails = const [],
  });

  factory CommissionPayoutModel.fromJson(Map<String, dynamic> json) {
    final detailsList = (json['contract_details'] as List<dynamic>?)
            ?.map((d) => PayoutContractDetailModel.fromJson(d as Map<String, dynamic>))
            .toList() ??
        [];

    return CommissionPayoutModel(
      id: _parseInt(json['id']),
      period: _parseInt(json['period']),
      salesPerson: _parseInt(json['sales_person']),
      salesPersonName: json['sales_person_name'] as String?,
      dutyDisplay: json['duty_display'] as String?,
      teamName: json['team_name'] as String?,
      basePay: _parseInt(json['base_pay']),
      contractCount: _parseInt(json['contract_count']),
      commissionAmount: _parseInt(json['commission_amount']),
      bonusAmount: _parseInt(json['bonus_amount']),
      deductionAmount: _parseInt(json['deduction_amount']),
      grossAmount: _parseInt(json['gross_amount']),
      incomeTax: _parseInt(json['income_tax']),
      localIncomeTax: _parseInt(json['local_income_tax']),
      totalTax: _parseInt(json['total_tax']),
      netAmount: _parseInt(json['net_amount']),
      payStatus: json['pay_status'] as String? ?? '1',
      payStatusDisplay: json['pay_status_display'] as String?,
      paidDate: json['paid_date'] as String?,
      bankName: json['bank_name'] as String?,
      accountNumber: json['account_number'] as String?,
      accountHolder: json['account_holder'] as String?,
      note: json['note'] as String?,
      contractDetails: detailsList,
    );
  }
}

/// 수수료 정산 회차 모델
class SettlementPeriodModel {
  final int id;
  final int project;
  final String title;
  final String startDate;
  final String endDate;
  final String? payoutDate;
  final String status; // 1: 정산 작성 중, 2: 정산 확정, 3: 지급 완료
  final String? statusDisplay;
  final int totalContracts;
  final int totalGrossAmount;
  final int totalTaxAmount;
  final int totalNetAmount;
  final int agencyFeeTotal;
  final int billingSupplyPrice;
  final int billingVat;
  final int billingTotalAmount;
  final int payoutCount;
  final int agencyPayoutCount;
  final int? createdBy;
  final String? createdAt;
  final String? updatedAt;

  const SettlementPeriodModel({
    required this.id,
    required this.project,
    required this.title,
    required this.startDate,
    required this.endDate,
    this.payoutDate,
    this.status = '1',
    this.statusDisplay,
    this.totalContracts = 0,
    this.totalGrossAmount = 0,
    this.totalTaxAmount = 0,
    this.totalNetAmount = 0,
    this.agencyFeeTotal = 0,
    this.billingSupplyPrice = 0,
    this.billingVat = 0,
    this.billingTotalAmount = 0,
    this.payoutCount = 0,
    this.agencyPayoutCount = 0,
    this.createdBy,
    this.createdAt,
    this.updatedAt,
  });

  bool get isDraft => status == '1';
  bool get isConfirmed => status == '2';
  bool get isCompleted => status == '3';

  factory SettlementPeriodModel.fromJson(Map<String, dynamic> json) {
    final gross = _parseInt(json['total_gross_amount']);
    final agencyFee = _parseInt(json['agency_fee_total']);
    final supply = json['billing_supply_price'] != null
        ? _parseInt(json['billing_supply_price'])
        : (gross + agencyFee);
    final vat = json['billing_vat'] != null
        ? _parseInt(json['billing_vat'])
        : (supply * 0.1).floor();
    final totalBilling = json['billing_total_amount'] != null
        ? _parseInt(json['billing_total_amount'])
        : (supply + vat);

    return SettlementPeriodModel(
      id: _parseInt(json['id']),
      project: _parseInt(json['project']),
      title: json['title'] as String? ?? '',
      startDate: json['start_date'] as String? ?? '',
      endDate: json['end_date'] as String? ?? '',
      payoutDate: json['payout_date'] as String?,
      status: json['status'] as String? ?? '1',
      statusDisplay: json['status_display'] as String?,
      totalContracts: _parseInt(json['total_contracts']),
      totalGrossAmount: gross,
      totalTaxAmount: _parseInt(json['total_tax_amount']),
      totalNetAmount: _parseInt(json['total_net_amount']),
      agencyFeeTotal: agencyFee,
      billingSupplyPrice: supply,
      billingVat: vat,
      billingTotalAmount: totalBilling,
      payoutCount: _parseInt(json['payout_count']),
      agencyPayoutCount: _parseInt(json['agency_payout_count']),
      createdBy: _tryParseInt(json['created_by']),
      createdAt: json['created_at'] as String?,
      updatedAt: json['updated_at'] as String?,
    );
  }
}

/// 대행사 수수료 지급/청구 명세 모델
class AgencyPayoutModel {
  final int id;
  final int period;
  final int agency;
  final String? agencyName;
  final bool isDirectManaged;
  final int contractCount;
  final int agencyFeeSum;
  final int unallocatedFee;
  final int vatAmount;
  final int totalAmount;
  final String payStatus;
  final String? payStatusDisplay;
  final String? paidDate;
  final String? businessNumber;
  final String? bankName;
  final String? accountNumber;
  final String? accountHolder;
  final String? note;

  const AgencyPayoutModel({
    required this.id,
    required this.period,
    required this.agency,
    this.agencyName,
    this.isDirectManaged = false,
    this.contractCount = 0,
    this.agencyFeeSum = 0,
    this.unallocatedFee = 0,
    this.vatAmount = 0,
    this.totalAmount = 0,
    this.payStatus = '1',
    this.payStatusDisplay,
    this.paidDate,
    this.businessNumber,
    this.bankName,
    this.accountNumber,
    this.accountHolder,
    this.note,
  });

  factory AgencyPayoutModel.fromJson(Map<String, dynamic> json) {
    return AgencyPayoutModel(
      id: _parseInt(json['id']),
      period: _parseInt(json['period']),
      agency: _parseInt(json['agency']),
      agencyName: json['agency_name'] as String?,
      isDirectManaged: json['is_direct_managed'] as bool? ?? false,
      contractCount: _parseInt(json['contract_count']),
      agencyFeeSum: _parseInt(json['agency_fee_sum']),
      unallocatedFee: _parseInt(json['unallocated_fee']),
      vatAmount: _parseInt(json['vat_amount']),
      totalAmount: _parseInt(json['total_amount']),
      payStatus: json['pay_status'] as String? ?? '1',
      payStatusDisplay: json['pay_status_display'] as String?,
      paidDate: json['paid_date'] as String?,
      businessNumber: json['business_number'] as String?,
      bankName: json['bank_name'] as String?,
      accountNumber: json['account_number'] as String?,
      accountHolder: json['account_holder'] as String?,
      note: json['note'] as String?,
    );
  }
}

/// 영업 조직 건강성 경고 항목
class OrgHealthWarning {
  final String type;
  final String severity; // error, warning
  final String? agency;
  final String? team;
  final String? unitType;
  final String message;

  const OrgHealthWarning({
    required this.type,
    required this.severity,
    this.agency,
    this.team,
    this.unitType,
    required this.message,
  });

  factory OrgHealthWarning.fromJson(Map<String, dynamic> json) {
    return OrgHealthWarning(
      type: json['type'] as String? ?? '',
      severity: json['severity'] as String? ?? 'warning',
      agency: json['agency'] as String?,
      team: json['team'] as String?,
      unitType: json['unit_type'] as String?,
      message: json['message'] as String? ?? '',
    );
  }

  bool get isError => severity == 'error';
}

/// 영업 조직 건강성 진단 결과 모델
class OrgHealthCheckResult {
  final bool isHealthy;
  final int errorCount;
  final int warningCount;
  final List<OrgHealthWarning> items;

  const OrgHealthCheckResult({
    required this.isHealthy,
    required this.errorCount,
    required this.warningCount,
    required this.items,
  });

  factory OrgHealthCheckResult.fromJson(Map<String, dynamic> json) {
    final list = (json['items'] as List<dynamic>?)
            ?.map((e) => OrgHealthWarning.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [];

    return OrgHealthCheckResult(
      isHealthy: json['is_healthy'] as bool? ?? true,
      errorCount: _parseInt(json['error_count']),
      warningCount: _parseInt(json['warning_count']),
      items: list,
    );
  }
}

/// 수수료 환수(Clawback) 모델
class CommissionClawbackModel {
  final int id;
  final int contract;
  final String? contractSerial;
  final int salesPerson;
  final String? salesPersonName;
  final int amount;
  final String reason;
  final bool isSettled;
  final int? settledPayout;
  final String? createdAt;

  const CommissionClawbackModel({
    required this.id,
    required this.contract,
    this.contractSerial,
    required this.salesPerson,
    this.salesPersonName,
    this.amount = 0,
    this.reason = '',
    this.isSettled = false,
    this.settledPayout,
    this.createdAt,
  });

  factory CommissionClawbackModel.fromJson(Map<String, dynamic> json) {
    return CommissionClawbackModel(
      id: _parseInt(json['id']),
      contract: _parseInt(json['contract']),
      contractSerial: json['contract_serial'] as String?,
      salesPerson: _parseInt(json['sales_person']),
      salesPersonName: json['sales_person_name'] as String?,
      amount: _parseInt(json['amount']),
      reason: json['reason'] as String? ?? '',
      isSettled: json['is_settled'] as bool? ?? false,
      settledPayout: _tryParseInt(json['settled_payout']),
      createdAt: json['created_at'] as String?,
    );
  }
}


