import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/contract_repository.dart';
import '../data/models/contract_models.dart';

/// 3대 서브 탭 구분 enum (계약 목록, 권리의무 승계, 계약 해약)
enum ContractSubTab {
  contracts,   // 📋 유효 계약 목록
  successions, // 🔄 권리의무 승계
  releases,    // 🚫 계약 해약 관리
}

/// 현재 선택된 서브 탭 프로바이더
final contractCurrentSubTabProvider =
    StateProvider<ContractSubTab>((ref) => ContractSubTab.contracts);

/// 검색어 상태 프로바이더
final contractSearchQueryProvider = StateProvider<String>((ref) => '');

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

/// 유효 계약 목록 프로바이더 (is_active=true, is_contract=true)
final validContractListProvider =
    FutureProvider<List<ContractItemModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final search = ref.watch(contractSearchQueryProvider);
  final repository = ref.watch(contractRepositoryProvider);

  return repository.fetchContracts(
    projectId: selectedProject.pk,
    search: search,
  );
});

/// 권리의무 승계 목록 프로바이더
final successionListProvider =
    FutureProvider<List<SuccessionItemModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final search = ref.watch(contractSearchQueryProvider);
  final repository = ref.watch(contractRepositoryProvider);

  return repository.fetchSuccessions(
    projectId: selectedProject.pk,
    search: search,
  );
});

/// 계약 해약/해지 목록 프로바이더
final contractorReleaseListProvider =
    FutureProvider<List<ContractorReleaseItemModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final search = ref.watch(contractSearchQueryProvider);
  final repository = ref.watch(contractRepositoryProvider);

  return repository.fetchReleases(
    projectId: selectedProject.pk,
    search: search,
  );
});
