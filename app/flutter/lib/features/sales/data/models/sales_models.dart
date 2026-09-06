/// 분양 대행 관리 (Sales Agency) 데이터 모델
library;

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
      value: json['value'] as int? ?? 0,
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
      id: json['id'] as int? ?? 0,
      project: json['project'] as int? ?? 0,
      name: json['name'] as String? ?? '',
      isDirectManaged: json['is_direct_managed'] as bool? ?? false,
      businessNumber: json['business_number'] as String?,
      ceoName: json['ceo_name'] as String?,
      phone: json['phone'] as String?,
      order: json['order'] as int? ?? 1,
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
      id: json['id'] as int? ?? 0,
      agency: json['agency'] as int? ?? 0,
      agencyName: json['agency_name'] as String?,
      parent: json['parent'] as int?,
      parentName: json['parent_name'] as String?,
      name: json['name'] as String? ?? '',
      order: json['order'] as int? ?? 1,
      isActive: json['is_active'] as bool? ?? true,
      membersCount: json['members_count'] as int? ?? 0,
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
  });

  factory SalesPersonModel.fromJson(Map<String, dynamic> json) {
    return SalesPersonModel(
      id: json['id'] as int? ?? 0,
      team: json['team'] as int? ?? 0,
      teamName: json['team_name'] as String?,
      agencyName: json['agency_name'] as String?,
      user: json['user'] as int?,
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
      id: json['id'] as int? ?? 0,
      project: json['project'] as int? ?? 0,
      orderGroup: json['order_group'] as int?,
      orderGroupName: json['order_group_name'] as String?,
      unitType: json['unit_type'] as int?,
      unitTypeName: json['unit_type_name'] as String?,
      name: json['name'] as String? ?? '',
      agentFee: json['agent_fee'] as int? ?? 0,
      leaderFee: json['leader_fee'] as int? ?? 0,
      directorFee: json['director_fee'] as int? ?? 0,
      agencyFee: json['agency_fee'] as int? ?? 0,
      payCondition: json['pay_condition'] as String? ?? '1',
      payConditionDisplay: json['pay_condition_display'] as String?,
      startDate: json['start_date'] as String? ?? '',
      endDate: json['end_date'] as String?,
    );
  }

  int get totalFee => agentFee + leaderFee + directorFee + agencyFee;
}

/// 차수 (OrderGroup) 간략 옵션 모델
class OrderGroupOption {
  final int id;
  final String name;

  const OrderGroupOption({required this.id, required this.name});

  factory OrderGroupOption.fromJson(Map<String, dynamic> json) {
    return OrderGroupOption(
      id: json['pk'] as int? ?? json['id'] as int? ?? 0,
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
      id: json['pk'] as int? ?? json['id'] as int? ?? 0,
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
    this.createdAt,
    this.updatedAt,
  });

  factory ContractSalesAgentModel.fromJson(Map<String, dynamic> json) {
    return ContractSalesAgentModel(
      id: json['id'] as int? ?? 0,
      contract: json['contract'] as int? ?? 0,
      contractSerial: json['contract_serial'] as String?,
      contractorName: json['contractor_name'] as String?,
      orderGroupName: json['order_group_name'] as String?,
      unitTypeName: json['unit_type_name'] as String?,
      unitInfo: json['unit_info'] as String?,
      salesPerson: json['sales_person'] as int?,
      salesPersonName: json['sales_person_name'] as String?,
      team: json['team'] as int?,
      teamName: json['team_name'] as String?,
      policy: json['policy'] as int?,
      policyName: json['policy_name'] as String?,
      contractDate: json['contract_date'] as String?,
      mgmName: json['mgm_name'] as String?,
      mgmPhone: json['mgm_phone'] as String?,
      mgmFee: json['mgm_fee'] as int? ?? 0,
      note: json['note'] as String?,
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
  String? get salesPersonName => mapping?.salesPersonName;
  String? get teamName => mapping?.teamName;
  String? get policyName => mapping?.policyName;
  String? get contractDate => mapping?.contractDate;
  String? get mgmName => mapping?.mgmName;
  String? get mgmPhone => mapping?.mgmPhone;
  int get mgmFee => mapping?.mgmFee ?? 0;
  String? get note => mapping?.note;
}
