import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/models/sales_models.dart';
import '../data/sales_repository.dart';

/// ── 필터 상태 프로바이더 ──────────────────────────────────────
enum SalesMappingStatusFilter { all, mapped, unmapped }

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
    // 1. 매핑 상태 필터
    if (statusFilter == SalesMappingStatusFilter.mapped && !item.isMapped) {
      return false;
    }
    if (statusFilter == SalesMappingStatusFilter.unmapped && item.isMapped) {
      return false;
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
