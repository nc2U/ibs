import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/auth_provider.dart';
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

/// 검색어 상태 프로바이더 (프로젝트 전환 시 자동 초기화)
final contractSearchQueryProvider = StateProvider<String>((ref) {
  ref.watch(selectedRealEstateProjectProvider.select((p) => p?.realProjectId));
  return '';
});

/// 프로젝트별 계약 집계 현황 프로바이더
final contractAggregateProvider =
    FutureProvider<ContractAggregateModel>((ref) async {
  ref.watch(authSessionVersionProvider);
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
  final bool isNextPageError;

  const ContractPaginationState({
    this.items = const [],
    this.page = 1,
    this.isLoading = false,
    this.isFetchingNextPage = false,
    this.hasMore = true,
    this.error,
    this.isNextPageError = false,
  });

  ContractPaginationState<T> copyWith({
    List<T>? items,
    int? page,
    bool? isLoading,
    bool? isFetchingNextPage,
    bool? hasMore,
    String? error,
    bool? isNextPageError,
  }) {
    return ContractPaginationState<T>(
      items: items ?? this.items,
      page: page ?? this.page,
      isLoading: isLoading ?? this.isLoading,
      isFetchingNextPage: isFetchingNextPage ?? this.isFetchingNextPage,
      hasMore: hasMore ?? this.hasMore,
      error: error,
      isNextPageError: isNextPageError ?? this.isNextPageError,
    );
  }
}

/// 1. 유효 계약 목록 무한 스크롤 Notifier
class ValidContractListNotifier extends StateNotifier<ContractPaginationState<ContractItemModel>> {
  final Ref ref;
  int _generation = 0;

  ValidContractListNotifier(this.ref) : super(const ContractPaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      _generation++;
      if (!mounted) return;
      state = const ContractPaginationState(items: [], hasMore: false);
      return;
    }

    final gen = ++_generation;
    state = state.copyWith(
      isLoading: true,
      isFetchingNextPage: false,
      page: 1,
      items: [],
      hasMore: true,
      error: null,
      isNextPageError: false,
    );

    final search = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final result = await repository.fetchContracts(
        projectId: selectedProject.realProjectId,
        search: search,
        page: 1,
        limit: 10,
      );
      if (!mounted || gen != _generation) return;

      state = state.copyWith(
        isLoading: false,
        items: result.items,
        page: 1,
        hasMore: result.hasMore,
        isNextPageError: false,
      );
    } catch (e) {
      if (!mounted || gen != _generation) return;
      state = state.copyWith(
        isLoading: false,
        error: ContractRepository.extractErrorMessage(e, '계약 목록을 불러오지 못했습니다.'),
        isNextPageError: false,
      );
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoading || state.isFetchingNextPage || !state.hasMore) return;

    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) return;

    final gen = _generation;
    state = state.copyWith(isFetchingNextPage: true, isNextPageError: false);

    final initialProjectId = selectedProject.realProjectId;
    final targetPage = state.page + 1;
    final initialSearch = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final result = await repository.fetchContracts(
        projectId: initialProjectId,
        search: initialSearch,
        page: targetPage,
        limit: 10,
      );

      // 경쟁 상태 방지: 비동기 대기 중 프로젝트 또는 검색어가 변경되었거나 페이지가 리셋되었으면 결과 폐기
      final currentProject = ref.read(selectedRealEstateProjectProvider);
      final currentSearch = ref.read(contractSearchQueryProvider);
      if (!mounted ||
          gen != _generation ||
          currentProject?.realProjectId != initialProjectId ||
          currentSearch != initialSearch ||
          state.page + 1 != targetPage) {
        return;
      }

      state = state.copyWith(
        isFetchingNextPage: false,
        isNextPageError: false,
        items: [...state.items, ...result.items],
        page: targetPage,
        hasMore: result.hasMore,
      );
    } catch (e) {
      if (!mounted || gen != _generation) return;
      state = state.copyWith(
        isFetchingNextPage: false,
        isNextPageError: true,
      );
    }
  }
}

/// 2. 권리의무 승계 무한 스크롤 Notifier
class SuccessionListNotifier extends StateNotifier<ContractPaginationState<SuccessionItemModel>> {
  final Ref ref;
  int _generation = 0;

  SuccessionListNotifier(this.ref) : super(const ContractPaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      _generation++;
      if (!mounted) return;
      state = const ContractPaginationState(items: [], hasMore: false);
      return;
    }

    final gen = ++_generation;
    state = state.copyWith(
      isLoading: true,
      isFetchingNextPage: false,
      page: 1,
      items: [],
      hasMore: true,
      error: null,
      isNextPageError: false,
    );

    final search = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final result = await repository.fetchSuccessions(
        projectId: selectedProject.realProjectId,
        search: search,
        page: 1,
        limit: 10,
      );
      if (!mounted || gen != _generation) return;

      state = state.copyWith(
        isLoading: false,
        items: result.items,
        page: 1,
        hasMore: result.hasMore,
        isNextPageError: false,
      );
    } catch (e) {
      if (!mounted || gen != _generation) return;
      state = state.copyWith(
        isLoading: false,
        error: ContractRepository.extractErrorMessage(e, '권리의무 승계 목록을 불러오지 못했습니다.'),
        isNextPageError: false,
      );
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoading || state.isFetchingNextPage || !state.hasMore) return;

    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) return;

    final gen = _generation;
    state = state.copyWith(isFetchingNextPage: true, isNextPageError: false);

    final initialProjectId = selectedProject.realProjectId;
    final targetPage = state.page + 1;
    final initialSearch = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final result = await repository.fetchSuccessions(
        projectId: initialProjectId,
        search: initialSearch,
        page: targetPage,
        limit: 10,
      );

      // 경쟁 상태 방지
      final currentProject = ref.read(selectedRealEstateProjectProvider);
      final currentSearch = ref.read(contractSearchQueryProvider);
      if (!mounted ||
          gen != _generation ||
          currentProject?.realProjectId != initialProjectId ||
          currentSearch != initialSearch ||
          state.page + 1 != targetPage) {
        return;
      }

      state = state.copyWith(
        isFetchingNextPage: false,
        isNextPageError: false,
        items: [...state.items, ...result.items],
        page: targetPage,
        hasMore: result.hasMore,
      );
    } catch (e) {
      if (!mounted || gen != _generation) return;
      state = state.copyWith(
        isFetchingNextPage: false,
        isNextPageError: true,
      );
    }
  }
}

/// 3. 계약 해약/해지 무한 스크롤 Notifier
class ContractorReleaseListNotifier extends StateNotifier<ContractPaginationState<ContractorReleaseItemModel>> {
  final Ref ref;
  int _generation = 0;

  ContractorReleaseListNotifier(this.ref) : super(const ContractPaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      _generation++;
      if (!mounted) return;
      state = const ContractPaginationState(items: [], hasMore: false);
      return;
    }

    final gen = ++_generation;
    state = state.copyWith(
      isLoading: true,
      isFetchingNextPage: false,
      page: 1,
      items: [],
      hasMore: true,
      error: null,
      isNextPageError: false,
    );

    final search = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final result = await repository.fetchReleases(
        projectId: selectedProject.realProjectId,
        search: search,
        page: 1,
        limit: 10,
      );
      if (!mounted || gen != _generation) return;

      state = state.copyWith(
        isLoading: false,
        items: result.items,
        page: 1,
        hasMore: result.hasMore,
        isNextPageError: false,
      );
    } catch (e) {
      if (!mounted || gen != _generation) return;
      state = state.copyWith(
        isLoading: false,
        error: ContractRepository.extractErrorMessage(e, '계약 해약 목록을 불러오지 못했습니다.'),
        isNextPageError: false,
      );
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoading || state.isFetchingNextPage || !state.hasMore) return;

    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) return;

    final gen = _generation;
    state = state.copyWith(isFetchingNextPage: true, isNextPageError: false);

    final initialProjectId = selectedProject.realProjectId;
    final targetPage = state.page + 1;
    final initialSearch = ref.read(contractSearchQueryProvider);
    final repository = ref.read(contractRepositoryProvider);

    try {
      final result = await repository.fetchReleases(
        projectId: initialProjectId,
        search: initialSearch,
        page: targetPage,
        limit: 10,
      );

      // 경쟁 상태 방지
      final currentProject = ref.read(selectedRealEstateProjectProvider);
      final currentSearch = ref.read(contractSearchQueryProvider);
      if (!mounted ||
          gen != _generation ||
          currentProject?.realProjectId != initialProjectId ||
          currentSearch != initialSearch ||
          state.page + 1 != targetPage) {
        return;
      }

      state = state.copyWith(
        isFetchingNextPage: false,
        isNextPageError: false,
        items: [...state.items, ...result.items],
        page: targetPage,
        hasMore: result.hasMore,
      );
    } catch (e) {
      if (!mounted || gen != _generation) return;
      state = state.copyWith(
        isFetchingNextPage: false,
        isNextPageError: true,
      );
    }
  }
}

/// 유효 계약 목록 프로바이더 (StateNotifierProvider)
final validContractListProvider =
    StateNotifierProvider<ValidContractListNotifier, ContractPaginationState<ContractItemModel>>((ref) {
  ref.watch(authSessionVersionProvider);
  return ValidContractListNotifier(ref);
});

/// 권리의무 승계 목록 프로바이더 (StateNotifierProvider)
final successionListProvider =
    StateNotifierProvider<SuccessionListNotifier, ContractPaginationState<SuccessionItemModel>>((ref) {
  ref.watch(authSessionVersionProvider);
  return SuccessionListNotifier(ref);
});

/// 계약 해약/해지 목록 프로바이더 (StateNotifierProvider)
final contractorReleaseListProvider =
    StateNotifierProvider<ContractorReleaseListNotifier, ContractPaginationState<ContractorReleaseItemModel>>((ref) {
  ref.watch(authSessionVersionProvider);
  return ContractorReleaseListNotifier(ref);
});

/// 계약자별 민원 및 상담 이력 목록 프로바이더 (Family)
final contractorConsultationLogsProvider =
    FutureProvider.family<List<ContractorConsultationLogModel>, int>((ref, contractorId) async {
  ref.watch(authSessionVersionProvider);
  final repository = ref.watch(contractRepositoryProvider);
  return repository.fetchConsultationLogs(contractorId: contractorId);
});

/// 계약자별 주소 변경 이력 목록 프로바이더 (Family)
final contractorAddressHistoryProvider =
    FutureProvider.family<List<ContractorAddressModel>, int>((ref, contractorId) async {
  ref.watch(authSessionVersionProvider);
  final repository = ref.watch(contractRepositoryProvider);
  return repository.fetchAddressHistory(contractorId: contractorId);
});

/// 🏢 프로젝트별 동 목록 프로바이더
final buildingUnitsProvider = FutureProvider.autoDispose<List<BuildingUnitModel>>((ref) async {
  ref.watch(authSessionVersionProvider);
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];
  final repository = ref.watch(contractRepositoryProvider);
  return repository.fetchBuildingUnits(selectedProject.realProjectId);
});

/// 🎨 프로젝트별 유닛 타입 목록 프로바이더
final unitTypesProvider = FutureProvider.autoDispose<List<UnitTypeItemModel>>((ref) async {
  ref.watch(authSessionVersionProvider);
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];
  final repository = ref.watch(contractRepositoryProvider);
  return repository.fetchUnitTypes(selectedProject.realProjectId);
});

/// 🔲 동호수 배치도 선택된 동 ID 상태 프로바이더 (프로젝트 전환 시 자동 초기화)
final selectedBuildingUnitIdProvider = StateProvider<int?>((ref) {
  ref.watch(selectedRealEstateProjectProvider.select((p) => p?.realProjectId));
  return null;
});

/// 🔲 프로젝트별 전체 동호수 배치 목록 프로바이더 (선택된 동 기준)
final allHouseUnitsProvider = FutureProvider.autoDispose<List<LayoutHouseUnitModel>>((ref) async {
  ref.watch(authSessionVersionProvider);
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];
  final buildingId = ref.watch(selectedBuildingUnitIdProvider);
  final repository = ref.watch(contractRepositoryProvider);
  return repository.fetchAllHouseUnits(selectedProject.realProjectId, buildingUnitId: buildingId);
});

