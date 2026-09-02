import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/contract_repository.dart';
import '../data/models/contract_models.dart';

/// 4대 서브 탭 구분 enum (계약 목록, 동호수 배치도, 권리의무 승계, 계약 해약)
enum ContractSubTab {
  contracts,   // 📋 유효 계약 목록
  unitMatrix,  // 🏢 동호수 배치도 (매트릭스 뷰)
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
  return repository.fetchContractAggregate(selectedProject.realProjectId);
});

/// ── 무한 스크롤 (Pagination) 상태 모델 ───────────────────────────
class ContractPaginationState<T> {
  final List<T> items;
  final int page;
  final bool isLoading;
  final bool isFetchingNextPage;
  final bool hasMore;
  final String? error;

  const ContractPaginationState({
    this.items = const [],
    this.page = 1,
    this.isLoading = false,
    this.isFetchingNextPage = false,
    this.hasMore = true,
    this.error,
  });

  ContractPaginationState<T> copyWith({
    List<T>? items,
    int? page,
    bool? isLoading,
    bool? isFetchingNextPage,
    bool? hasMore,
    String? error,
  }) {
    return ContractPaginationState<T>(
      items: items ?? this.items,
      page: page ?? this.page,
      isLoading: isLoading ?? this.isLoading,
      isFetchingNextPage: isFetchingNextPage ?? this.isFetchingNextPage,
      hasMore: hasMore ?? this.hasMore,
      error: error,
    );
  }
}

/// 1. 유효 계약 목록 무한 스크롤 Notifier
class ValidContractListNotifier extends StateNotifier<ContractPaginationState<ContractItemModel>> {
  final Ref ref;

  ValidContractListNotifier(this.ref) : super(const ContractPaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      state = const ContractPaginationState(items: [], hasMore: false);
      return;
    }

    state = state.copyWith(isLoading: true, page: 1, items: [], hasMore: true, error: null);

    final search = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final items = await repository.fetchContracts(
        projectId: selectedProject.realProjectId,
        search: search,
        page: 1,
        limit: 10,
      );

      state = state.copyWith(
        isLoading: false,
        items: items,
        page: 1,
        hasMore: items.length >= 10,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoading || state.isFetchingNextPage || !state.hasMore) return;

    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) return;

    state = state.copyWith(isFetchingNextPage: true);

    final nextPage = state.page + 1;
    final search = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final newItems = await repository.fetchContracts(
        projectId: selectedProject.realProjectId,
        search: search,
        page: nextPage,
        limit: 10,
      );

      state = state.copyWith(
        isFetchingNextPage: false,
        items: [...state.items, ...newItems],
        page: nextPage,
        hasMore: newItems.length >= 10,
      );
    } catch (e) {
      state = state.copyWith(isFetchingNextPage: false);
    }
  }
}

/// 2. 권리의무 승계 무한 스크롤 Notifier
class SuccessionListNotifier extends StateNotifier<ContractPaginationState<SuccessionItemModel>> {
  final Ref ref;

  SuccessionListNotifier(this.ref) : super(const ContractPaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      state = const ContractPaginationState(items: [], hasMore: false);
      return;
    }

    state = state.copyWith(isLoading: true, page: 1, items: [], hasMore: true, error: null);

    final search = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final items = await repository.fetchSuccessions(
        projectId: selectedProject.realProjectId,
        search: search,
        page: 1,
        limit: 10,
      );

      state = state.copyWith(
        isLoading: false,
        items: items,
        page: 1,
        hasMore: items.length >= 10,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoading || state.isFetchingNextPage || !state.hasMore) return;

    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) return;

    state = state.copyWith(isFetchingNextPage: true);

    final nextPage = state.page + 1;
    final search = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final newItems = await repository.fetchSuccessions(
        projectId: selectedProject.realProjectId,
        search: search,
        page: nextPage,
        limit: 10,
      );

      state = state.copyWith(
        isFetchingNextPage: false,
        items: [...state.items, ...newItems],
        page: nextPage,
        hasMore: newItems.length >= 10,
      );
    } catch (e) {
      state = state.copyWith(isFetchingNextPage: false);
    }
  }
}

/// 3. 계약 해약/해지 무한 스크롤 Notifier
class ContractorReleaseListNotifier extends StateNotifier<ContractPaginationState<ContractorReleaseItemModel>> {
  final Ref ref;

  ContractorReleaseListNotifier(this.ref) : super(const ContractPaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      state = const ContractPaginationState(items: [], hasMore: false);
      return;
    }

    state = state.copyWith(isLoading: true, page: 1, items: [], hasMore: true, error: null);

    final search = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final items = await repository.fetchReleases(
        projectId: selectedProject.realProjectId,
        search: search,
        page: 1,
        limit: 10,
      );

      state = state.copyWith(
        isLoading: false,
        items: items,
        page: 1,
        hasMore: items.length >= 10,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoading || state.isFetchingNextPage || !state.hasMore) return;

    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) return;

    state = state.copyWith(isFetchingNextPage: true);

    final nextPage = state.page + 1;
    final search = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final newItems = await repository.fetchReleases(
        projectId: selectedProject.realProjectId,
        search: search,
        page: nextPage,
        limit: 10,
      );

      state = state.copyWith(
        isFetchingNextPage: false,
        items: [...state.items, ...newItems],
        page: nextPage,
        hasMore: newItems.length >= 10,
      );
    } catch (e) {
      state = state.copyWith(isFetchingNextPage: false);
    }
  }
}

/// 유효 계약 목록 프로바이더 (StateNotifierProvider)
final validContractListProvider =
    StateNotifierProvider<ValidContractListNotifier, ContractPaginationState<ContractItemModel>>(
        (ref) => ValidContractListNotifier(ref));

/// 권리의무 승계 목록 프로바이더 (StateNotifierProvider)
final successionListProvider =
    StateNotifierProvider<SuccessionListNotifier, ContractPaginationState<SuccessionItemModel>>(
        (ref) => SuccessionListNotifier(ref));

/// 계약 해약/해지 목록 프로바이더 (StateNotifierProvider)
final contractorReleaseListProvider =
    StateNotifierProvider<ContractorReleaseListNotifier, ContractPaginationState<ContractorReleaseItemModel>>(
        (ref) => ContractorReleaseListNotifier(ref));

/// 계약자별 민원 및 상담 이력 목록 프로바이더 (Family)
final contractorConsultationLogsProvider =
    FutureProvider.family<List<ContractorConsultationLogModel>, int>((ref, contractorId) async {
  final repository = ref.watch(contractRepositoryProvider);
  return repository.fetchConsultationLogs(contractorId: contractorId);
});

/// 계약자별 주소 변경 이력 목록 프로바이더 (Family)
final contractorAddressHistoryProvider =
    FutureProvider.family<List<ContractorAddressModel>, int>((ref, contractorId) async {
  final repository = ref.watch(contractRepositoryProvider);
  return repository.fetchAddressHistory(contractorId: contractorId);
});

/// 🏢 프로젝트별 동 목록 프로바이더
final buildingUnitsProvider = FutureProvider<List<BuildingUnitModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];
  final repository = ref.watch(contractRepositoryProvider);
  return repository.fetchBuildingUnits(selectedProject.realProjectId);
});

/// 🎨 프로젝트별 유닛 타입 목록 프로바이더
final unitTypesProvider = FutureProvider<List<UnitTypeItemModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];
  final repository = ref.watch(contractRepositoryProvider);
  return repository.fetchUnitTypes(selectedProject.realProjectId);
});

/// 🔲 동호수 배치도 선택된 동 ID 상태 프로바이더
final selectedBuildingUnitIdProvider = StateProvider<int?>((ref) => null);

/// 🔲 프로젝트별 전체 동호수 배치 목록 프로바이더 (선택된 동 기준)
final allHouseUnitsProvider = FutureProvider<List<LayoutHouseUnitModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];
  final buildingId = ref.watch(selectedBuildingUnitIdProvider);
  final repository = ref.watch(contractRepositoryProvider);
  return repository.fetchAllHouseUnits(selectedProject.realProjectId, buildingUnitId: buildingId);
});

