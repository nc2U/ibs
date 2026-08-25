import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/contract_repository.dart';
import '../data/models/contract_models.dart';

/// 검색어 상태 프로바이더
final contractSearchQueryProvider = StateProvider<String>((ref) => '');

/// 계약 상태 필터 프로바이더 ('all', '2'(계약유지), '3'(변경/승계진행), '4'(해약))
final contractStatusFilterProvider = StateProvider<String>((ref) => 'all');

/// 프로젝트별 계약 집계 현황 프로바이더
final contractAggregateProvider =
    FutureProvider<ContractAggregateModel>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) {
    return ContractAggregateModel(
      totalUnits: 0,
      subsNum: 0,
      contsNum: 0,
      nonContsNum: 0,
    );
  }

  final repository = ref.watch(contractRepositoryProvider);
  return repository.fetchContractAggregate(selectedProject.pk);
});

/// 프로젝트별 계약 목록 프로바이더
final contractListProvider =
    FutureProvider<List<ContractItemModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final search = ref.watch(contractSearchQueryProvider);
  final statusFilter = ref.watch(contractStatusFilterProvider);
  final repository = ref.watch(contractRepositoryProvider);

  String? queryStatus;
  if (statusFilter != 'all') {
    queryStatus = statusFilter;
  }

  return repository.fetchContracts(
    projectId: selectedProject.pk,
    search: search,
    status: queryStatus,
  );
});
