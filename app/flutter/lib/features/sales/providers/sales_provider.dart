import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/models/sales_models.dart';
import '../data/sales_repository.dart';

/// ── 필터 상태 프로바이더 ──────────────────────────────────────
enum SalesMappingStatusFilter { all, mapped, unmapped, approved, pending }

final salesMappingStatusFilterProvider =
    StateProvider<SalesMappingStatusFilter>((ref) => SalesMappingStatusFilter.all);

final salesTeamFilterProvider = StateProvider<int?>((ref) => null);

final salesPersonFilterProvider = StateProvider<int?>((ref) => null);

final salesSearchQueryProvider = StateProvider<String>((ref) => '');

/// ── 참조 데이터 비동기 프로바이더 ─────────────────────────────

/// 영업 팀 목록 프로바이더
final salesTeamsProvider = FutureProvider<List<SalesTeamModel>>((ref) async {

  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchSalesTeams(selectedProject.realProjectId);
});

/// 영업 인력 (상담사) 목록 프로바이더
final salesPersonsProvider = FutureProvider<List<SalesPersonModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchSalesPersons(projectId: selectedProject.realProjectId);
});

/// 수수료 정책 목록 프로바이더
final salesPoliciesProvider = FutureProvider<List<CommissionPolicyModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchCommissionPolicies(selectedProject.realProjectId);
});

/// 프로젝트 전체 계약 목록 프로바이더 (/api/v1/simple-contract/)
final simpleContractsProvider = FutureProvider<List<SimpleContractOption>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchSimpleContracts(selectedProject.realProjectId);
});

/// 계약별 영업 매핑 데이터 프로바이더 (/api/v1/sales-contract-agent/)
final rawContractSalesAgentsProvider =
    FutureProvider<List<ContractSalesAgentModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchContractSalesAgents(
    projectId: selectedProject.realProjectId,
  );
});

/// ── 실적 KPI 요약 지표 모델 & 프로바이더 ───────────────────────
class SalesPerformanceSummary {
  final int totalContracts;
  final int mappedCount;
  final int unmappedCount;
  final int mappingRate;
  final int mgmCount;
  final String? topAgentName;
  final String? topAgentTeam;
  final int topAgentCount;

  const SalesPerformanceSummary({
    this.totalContracts = 0,
    this.mappedCount = 0,
    this.unmappedCount = 0,
    this.mappingRate = 0,
    this.mgmCount = 0,
    this.topAgentName,
    this.topAgentTeam,
    this.topAgentCount = 0,
  });
}

/// 실시간 실적 KPI 집계 프로바이더
final salesPerformanceSummaryProvider = Provider<SalesPerformanceSummary>((ref) {
  final contractsAsync = ref.watch(simpleContractsProvider);
  final mappingsAsync = ref.watch(rawContractSalesAgentsProvider);

  final contracts = contractsAsync.valueOrNull ?? [];
  final mappings = mappingsAsync.valueOrNull ?? [];

  final total = contracts.length;
  final mapped = mappings.length;
  final unmapped = total > mapped ? total - mapped : 0;
  final rate = total > 0 ? ((mapped / total) * 100).round() : 0;
  final mgm = mappings.where((m) => m.mgmName != null && m.mgmName!.trim().isNotEmpty).length;

  // 최다 실적 상담사 계산
  String? topName;
  String? topTeam;
  int topCount = 0;

  if (mappings.isNotEmpty) {
    final counts = <String, Map<String, dynamic>>{};
    for (final m in mappings) {
      final name = m.salesPersonName ?? '미정';
      if (!counts.containsKey(name)) {
        counts[name] = {'name': name, 'team': m.teamName ?? '', 'count': 0};
      }
      counts[name]!['count'] = (counts[name]!['count'] as int) + 1;
    }

    final sorted = counts.values.toList()
      ..sort((a, b) => (b['count'] as int).compareTo(a['count'] as int));

    if (sorted.isNotEmpty) {
      topName = sorted.first['name'] as String;
      topTeam = sorted.first['team'] as String;
      topCount = sorted.first['count'] as int;
    }
  }

  return SalesPerformanceSummary(
    totalContracts: total,
    mappedCount: mapped,
    unmappedCount: unmapped,
    mappingRate: rate,
    mgmCount: mgm,
    topAgentName: topName,
    topAgentTeam: topTeam,
    topAgentCount: topCount,
  );
});

/// ── 전체 계약 + 매핑 통합 목록 프로바이더 ─────────────────────────
final combinedContractPerformanceProvider =
    Provider<AsyncValue<List<CombinedContractPerformanceItem>>>((ref) {
  final contractsAsync = ref.watch(simpleContractsProvider);
  final mappingsAsync = ref.watch(rawContractSalesAgentsProvider);

  if (contractsAsync.isLoading || mappingsAsync.isLoading) {
    return const AsyncValue.loading();
  }

  if (contractsAsync.hasError) {
    return AsyncValue.error(contractsAsync.error!, contractsAsync.stackTrace!);
  }
  if (mappingsAsync.hasError) {
    return AsyncValue.error(mappingsAsync.error!, mappingsAsync.stackTrace!);
  }

  final contracts = contractsAsync.valueOrNull ?? [];
  final mappings = mappingsAsync.valueOrNull ?? [];

  // contractId -> mapping Map
  final mappingMap = <int, ContractSalesAgentModel>{};
  for (final m in mappings) {
    mappingMap[m.contract] = m;
  }

  final combined = contracts.map((c) {
    return CombinedContractPerformanceItem(
      contractId: c.value,
      contractLabel: c.label,
      mapping: mappingMap[c.value],
    );
  }).toList();

  return AsyncValue.data(combined);
});

/// ── 필터링된 최종 실적 목록 프로바이더 ─────────────────────────────
final filteredContractPerformanceProvider =
    Provider<List<CombinedContractPerformanceItem>>((ref) {
  final combinedAsync = ref.watch(combinedContractPerformanceProvider);
  final items = combinedAsync.valueOrNull ?? [];

  final statusFilter = ref.watch(salesMappingStatusFilterProvider);
  final teamFilter = ref.watch(salesTeamFilterProvider);
  final personFilter = ref.watch(salesPersonFilterProvider);
  final query = ref.watch(salesSearchQueryProvider).trim().toLowerCase();

  return items.where((item) {
    // 1. 매핑 및 정산 승인 상태 필터
    if (statusFilter == SalesMappingStatusFilter.mapped && !item.isMapped) {
      return false;
    }
    if (statusFilter == SalesMappingStatusFilter.unmapped && item.isMapped) {
      return false;
    }
    if (statusFilter == SalesMappingStatusFilter.approved) {
      if (!item.isMapped || !item.isSettlementApproved) return false;
    }
    if (statusFilter == SalesMappingStatusFilter.pending) {
      if (!item.isMapped || item.isSettlementApproved) return false;
    }

    // 2. 팀 필터
    if (teamFilter != null && item.mapping?.team != teamFilter) {
      return false;
    }

    // 3. 상담사 필터
    if (personFilter != null && item.mapping?.salesPerson != personFilter) {
      return false;
    }

    // 4. 검색어 필터
    if (query.isNotEmpty) {
      final labelMatch = item.contractLabel.toLowerCase().contains(query);
      final personMatch = item.salesPersonName?.toLowerCase().contains(query) ?? false;
      final mgmMatch = item.mgmName?.toLowerCase().contains(query) ?? false;
      if (!labelMatch && !personMatch && !mgmMatch) return false;
    }

    return true;
  }).toList();
});

// ═════════════════════════════════════════════════════════════════
// 🏢 영업 조직 (Organization) 관련 프로바이더
// ═════════════════════════════════════════════════════════════════

/// 분양 대행사 목록 프로바이더 (/api/v1/sales-agency/)
final salesAgenciesProvider = FutureProvider<List<SalesAgencyModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchSalesAgencies(selectedProject.realProjectId);
});

/// ── 영업 조직(인력 명부) 필터 프로바이더 ────────────────────────
final orgAgencyFilterProvider = StateProvider<int?>((ref) => null);
final orgTeamFilterProvider = StateProvider<int?>((ref) => null);
final orgDutyFilterProvider = StateProvider<String>((ref) => ''); // '': 전체
final orgStatusFilterProvider = StateProvider<String>((ref) => '1'); // '1': 재직 우선
final orgSearchQueryProvider = StateProvider<String>((ref) => '');

/// ── 영업 조직 요약 지표 모델 & 프로바이더 ───────────────────────
class SalesOrganizationSummary {
  final int agencyCount;
  final int directAgencyCount;
  final int teamCount;
  final int totalPersons;
  final int activePersons;

  const SalesOrganizationSummary({
    this.agencyCount = 0,
    this.directAgencyCount = 0,
    this.teamCount = 0,
    this.totalPersons = 0,
    this.activePersons = 0,
  });
}

final salesOrganizationSummaryProvider = Provider<SalesOrganizationSummary>((ref) {
  final agencies = ref.watch(salesAgenciesProvider).valueOrNull ?? [];
  final teams = ref.watch(salesTeamsProvider).valueOrNull ?? [];
  final persons = ref.watch(salesPersonsProvider).valueOrNull ?? [];

  final directCount = agencies.where((a) => a.isDirectManaged).length;
  final activeCount = persons.where((p) => p.status == '1').length;

  return SalesOrganizationSummary(
    agencyCount: agencies.length,
    directAgencyCount: directCount,
    teamCount: teams.length,
    totalPersons: persons.length,
    activePersons: activeCount,
  );
});

/// ── 필터링된 영업 인력 목록 프로바이더 ───────────────────────────
final filteredOrgPersonsProvider = Provider<List<SalesPersonModel>>((ref) {
  final personsAsync = ref.watch(salesPersonsProvider);
  final persons = personsAsync.valueOrNull ?? [];
  final teams = ref.watch(salesTeamsProvider).valueOrNull ?? [];

  final agencyFilter = ref.watch(orgAgencyFilterProvider);
  final teamFilter = ref.watch(orgTeamFilterProvider);
  final dutyFilter = ref.watch(orgDutyFilterProvider);
  final statusFilter = ref.watch(orgStatusFilterProvider);
  final query = ref.watch(orgSearchQueryProvider).trim().toLowerCase();

  return persons.where((p) {
    // 1. 대행사 필터
    if (agencyFilter != null) {
      final team = teams.where((t) => t.id == p.team).firstOrNull;
      if (team == null || team.agency != agencyFilter) return false;
    }

    // 2. 팀 필터
    if (teamFilter != null && p.team != teamFilter) {
      return false;
    }

    // 3. 직책 필터
    if (dutyFilter.isNotEmpty && p.duty != dutyFilter) {
      return false;
    }

    // 4. 상태 필터
    if (statusFilter.isNotEmpty && p.status != statusFilter) {
      return false;
    }

    // 5. 검색어 필터
    if (query.isNotEmpty) {
      final matchName = p.name.toLowerCase().contains(query);
      final matchPhone = p.phone?.toLowerCase().contains(query) ?? false;
      final matchAccount = p.accountHolder?.toLowerCase().contains(query) ?? false;
      final matchTeam = p.teamName?.toLowerCase().contains(query) ?? false;
      if (!matchName && !matchPhone && !matchAccount && !matchTeam) return false;
    }

    return true;
  }).toList();
});

// ═════════════════════════════════════════════════════════════════
// 📋 수수료 정책 (Commission Policy) 관련 프로바이더
// ═════════════════════════════════════════════════════════════════

/// 공급 차수 목록 프로바이더 (/api/v1/order-group/)
final orderGroupsProvider = FutureProvider<List<OrderGroupOption>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchOrderGroups(selectedProject.realProjectId);
});

/// 유니트 타입 목록 프로바이더 (/api/v1/type/)
final unitTypesProvider = FutureProvider<List<UnitTypeOption>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchUnitTypes(selectedProject.realProjectId);
});

/// ── 수수료 정책 필터 프로바이더 ──────────────────────────────────
final policyOrderGroupFilterProvider = StateProvider<int?>((ref) => null);
final policyUnitTypeFilterProvider = StateProvider<int?>((ref) => null);
final policyActiveFilterProvider = StateProvider<String>((ref) => 'true'); // 'true': 활성, '': 전체, 'false': 비활성
final policySearchQueryProvider = StateProvider<String>((ref) => '');

/// ── 수수료 정책 요약 지표 모델 & 프로바이더 ───────────────────────
class SalesPolicySummary {
  final int totalCount;
  final int activeCount;
  final int maxFee;
  final int coveredTypesCount;

  const SalesPolicySummary({
    this.totalCount = 0,
    this.activeCount = 0,
    this.maxFee = 0,
    this.coveredTypesCount = 0,
  });
}

final salesPolicySummaryProvider = Provider<SalesPolicySummary>((ref) {
  final policies = ref.watch(salesPoliciesProvider).valueOrNull ?? [];
  final activePolicies = policies.where((p) => p.isActive).toList();

  int maxFee = 0;
  final coveredTypes = <int>{};
  for (final p in policies) {
    if (p.totalFee > maxFee) {
      maxFee = p.totalFee;
    }
    if (p.unitType != null) {
      coveredTypes.add(p.unitType!);
    }
  }

  return SalesPolicySummary(
    totalCount: policies.length,
    activeCount: activePolicies.length,
    maxFee: maxFee,
    coveredTypesCount: coveredTypes.length,
  );
});

/// ── 필터링된 수수료 정책 목록 프로바이더 ───────────────────────────
final filteredSalesPoliciesProvider = Provider<List<CommissionPolicyModel>>((ref) {
  final policies = ref.watch(salesPoliciesProvider).valueOrNull ?? [];
  final orderGroupFilter = ref.watch(policyOrderGroupFilterProvider);
  final unitTypeFilter = ref.watch(policyUnitTypeFilterProvider);
  final activeFilter = ref.watch(policyActiveFilterProvider);
  final query = ref.watch(policySearchQueryProvider).trim().toLowerCase();

  return policies.where((p) {
    // 1. 차수 필터
    if (orderGroupFilter != null && p.orderGroup != orderGroupFilter) {
      return false;
    }

    // 2. 유니트 타입 필터
    if (unitTypeFilter != null && p.unitType != unitTypeFilter) {
      return false;
    }

    // 3. 활성화 상태 필터
    if (activeFilter.isNotEmpty) {
      final reqActive = activeFilter == 'true';
      if (p.isActive != reqActive) return false;
    }

    // 4. 검색어 필터
    if (query.isNotEmpty) {
      final nameMatch = p.name.toLowerCase().contains(query);
      final typeMatch = p.unitTypeName?.toLowerCase().contains(query) ?? false;
      final ogMatch = p.orderGroupName?.toLowerCase().contains(query) ?? false;
      if (!nameMatch && !typeMatch && !ogMatch) return false;
    }

    return true;
  }).toList();
});

// ═════════════════════════════════════════════════════════════════
// 💰 수수료 정산 (Settlement) 관련 프로바이더
// ═════════════════════════════════════════════════════════════════

/// 수수료 정산 회차 목록 프로바이더 (/api/v1/sales-settlement-period/)
final settlementPeriodsProvider =
    FutureProvider<List<SettlementPeriodModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchSettlementPeriods(selectedProject.realProjectId);
});

/// 현재 선택된 정산 회차 ID 프로바이더 (null이면 최신 회차 자동 선택)
final selectedPeriodIdProvider = StateProvider<int?>((ref) => null);

/// 현재 선택된 정산 회차 객체 프로바이더
final currentSettlementPeriodProvider = Provider<SettlementPeriodModel?>((ref) {
  final periods = ref.watch(settlementPeriodsProvider).valueOrNull ?? [];
  final selectedId = ref.watch(selectedPeriodIdProvider);

  if (periods.isEmpty) return null;
  if (selectedId != null) {
    return periods.where((p) => p.id == selectedId).firstOrNull ?? periods.first;
  }
  return periods.first;
});

/// 선택된 회차의 개인별 수수료 지급 명세 목록 프로바이더 (/api/v1/sales-payout/)
final commissionPayoutsProvider =
    FutureProvider<List<CommissionPayoutModel>>((ref) async {
  final currentPeriod = ref.watch(currentSettlementPeriodProvider);
  if (currentPeriod == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchCommissionPayouts(periodId: currentPeriod.id);
});

/// 선택된 회차의 대행사 수수료 지급 명세 목록 프로바이더 (/api/v1/sales-agency-payout/)
final agencyPayoutsProvider =
    FutureProvider<List<AgencyPayoutModel>>((ref) async {
  final currentPeriod = ref.watch(currentSettlementPeriodProvider);
  if (currentPeriod == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchAgencyPayouts(periodId: currentPeriod.id);
});

/// ── 수수료 정산 명세 필터 프로바이더 ──────────────────────────────
final settlementSearchQueryProvider = StateProvider<String>((ref) => '');
final settlementDutyFilterProvider = StateProvider<String>((ref) => '');
final settlementPayStatusFilterProvider = StateProvider<String>((ref) => '');

/// ── 필터링된 개인별 수수료 지급 명세 목록 프로바이더 ─────────────────
final filteredCommissionPayoutsProvider =
    Provider<List<CommissionPayoutModel>>((ref) {
  final payouts = ref.watch(commissionPayoutsProvider).valueOrNull ?? [];
  final query = ref.watch(settlementSearchQueryProvider).trim().toLowerCase();
  final dutyFilter = ref.watch(settlementDutyFilterProvider);
  final statusFilter = ref.watch(settlementPayStatusFilterProvider);

  return payouts.where((p) {
    // 1. 지급 상태 필터
    if (statusFilter.isNotEmpty && p.payStatus != statusFilter) {
      return false;
    }

    // 2. 직책 필터 (dutyDisplay 검사)
    if (dutyFilter.isNotEmpty && p.dutyDisplay != dutyFilter) {
      return false;
    }

    // 3. 검색어 필터 (성명, 소속팀, 계좌주)
    if (query.isNotEmpty) {
      final nameMatch = p.salesPersonName?.toLowerCase().contains(query) ?? false;
      final teamMatch = p.teamName?.toLowerCase().contains(query) ?? false;
      final holderMatch = p.accountHolder?.toLowerCase().contains(query) ?? false;
      if (!nameMatch && !teamMatch && !holderMatch) return false;
    }

    return true;
  }).toList();
});

// ═════════════════════════════════════════════════════════════════
// 💳 수수료 지급 (Payout & Banking Transfer) 관련 프로바이더
// ═════════════════════════════════════════════════════════════════

/// 지급 관리 전용 선택 회차 ID 프로바이더 (null이면 정산확정/지급완료 회차 우선 선택)
final payoutTabPeriodIdProvider = StateProvider<int?>((ref) => null);

/// 지급 관리 전용 현재 선택 회차 프로바이더
final currentPayoutPeriodProvider = Provider<SettlementPeriodModel?>((ref) {
  final periods = ref.watch(settlementPeriodsProvider).valueOrNull ?? [];
  final selectedId = ref.watch(payoutTabPeriodIdProvider);

  if (periods.isEmpty) return null;
  if (selectedId != null) {
    return periods.where((p) => p.id == selectedId).firstOrNull ?? periods.first;
  }
  // 기본 선택: 확정('2') 또는 완료('3') 상태인 최신 회차 우선 선택
  final confirmedOrDone = periods.where((p) => p.isConfirmed || p.isCompleted).firstOrNull;
  return confirmedOrDone ?? periods.first;
});

/// 지급 관리 탭의 개인별 수수료 지급 명세 목록 프로바이더
final payoutTabPayoutsProvider =
    FutureProvider<List<CommissionPayoutModel>>((ref) async {
  final currentPeriod = ref.watch(currentPayoutPeriodProvider);
  if (currentPeriod == null) return [];

  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchCommissionPayouts(periodId: currentPeriod.id);
});

/// ── 지급 관리 필터 및 검색 프로바이더 ─────────────────────────────
final payoutTabSearchQueryProvider = StateProvider<String>((ref) => '');
final payoutTabStatusFilterProvider = StateProvider<String>((ref) => '');

/// ── 다중 선택된 지급 명세 ID 세트 프로바이더 ───────────────────────
final payoutTabSelectedIdsProvider = StateProvider<Set<int>>((ref) => {});

/// ── 지급 진행 요약 모델 및 프로바이더 ───────────────────────────
class PayoutStatusSummaryModel {
  final int totalCount;
  final int totalNetAmount;
  final int paidCount;
  final int paidNetAmount;
  final int unpaidCount;
  final int unpaidNetAmount;
  final int completionRate;
  final int totalTaxAmount;

  const PayoutStatusSummaryModel({
    this.totalCount = 0,
    this.totalNetAmount = 0,
    this.paidCount = 0,
    this.paidNetAmount = 0,
    this.unpaidCount = 0,
    this.unpaidNetAmount = 0,
    this.completionRate = 0,
    this.totalTaxAmount = 0,
  });
}

final payoutTabSummaryProvider = Provider<PayoutStatusSummaryModel>((ref) {
  final payouts = ref.watch(payoutTabPayoutsProvider).valueOrNull ?? [];
  if (payouts.isEmpty) return const PayoutStatusSummaryModel();

  final totalCount = payouts.length;
  final totalNetAmount = payouts.fold<int>(0, (sum, p) => sum + p.netAmount);
  final totalTaxAmount = payouts.fold<int>(0, (sum, p) => sum + p.totalTax);

  final paidItems = payouts.where((p) => p.payStatus == '3').toList();
  final paidCount = paidItems.length;
  final paidNetAmount = paidItems.fold<int>(0, (sum, p) => sum + p.netAmount);

  final unpaidCount = totalCount - paidCount;
  final unpaidNetAmount = totalNetAmount > paidNetAmount ? totalNetAmount - paidNetAmount : 0;
  final completionRate = totalNetAmount > 0 ? ((paidNetAmount / totalNetAmount) * 100).round() : 0;

  return PayoutStatusSummaryModel(
    totalCount: totalCount,
    totalNetAmount: totalNetAmount,
    paidCount: paidCount,
    paidNetAmount: paidNetAmount,
    unpaidCount: unpaidCount,
    unpaidNetAmount: unpaidNetAmount,
    completionRate: completionRate,
    totalTaxAmount: totalTaxAmount,
  );
});

/// ── 필터링된 지급 명세 목록 프로바이더 ───────────────────────────
final payoutTabFilteredListProvider =
    Provider<List<CommissionPayoutModel>>((ref) {
  final payouts = ref.watch(payoutTabPayoutsProvider).valueOrNull ?? [];
  final query = ref.watch(payoutTabSearchQueryProvider).trim().toLowerCase();
  final statusFilter = ref.watch(payoutTabStatusFilterProvider);

  return payouts.where((p) {
    // 1. 지급 상태 필터
    if (statusFilter.isNotEmpty && p.payStatus != statusFilter) {
      return false;
    }

    // 2. 통합 검색 필터 (성명, 소속팀, 계좌번호, 예금주, 은행명)
    if (query.isNotEmpty) {
      final nameMatch = p.salesPersonName?.toLowerCase().contains(query) ?? false;
      final teamMatch = p.teamName?.toLowerCase().contains(query) ?? false;
      final holderMatch = p.accountHolder?.toLowerCase().contains(query) ?? false;
      final bankMatch = p.bankName?.toLowerCase().contains(query) ?? false;
      final accountMatch = p.accountNumber?.replaceAll('-', '').contains(query.replaceAll('-', '')) ?? false;

      if (!nameMatch && !teamMatch && !holderMatch && !bankMatch && !accountMatch) {
        return false;
      }
    }

    return true;
  }).toList();
});

// ═════════════════════════════════════════════════════════════════
// 📂 영업 인력 제출 서류 (Sales Person Document) 프로바이더
// ═════════════════════════════════════════════════════════════════

/// 영업 인력별 제출 증빙 서류 목록 프로바이더 (/api/v1/sales-person-document/)
final salesPersonDocumentsProvider =
    FutureProvider.family<List<SalesPersonDocumentModel>, int>((ref, personId) async {
  final repository = ref.watch(salesRepositoryProvider);
  return repository.fetchSalesPersonDocuments(salesPersonId: personId);
});
