import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/models/site_models.dart';
import '../data/site_repository.dart';

/// 3대 서브 탭 구분 enum (지번별 토지, 소유자별 토지, 사업부지 매입계약)
enum SiteSubTab {
  sites,     // 📌 1. 지번별 토지 조서
  owners,    // 👤 2. 소유자별 토지 조서
  contracts, // 📑 3. 사업부지 매입계약
}

/// 현재 선택된 서브 탭 프로바이더
final siteCurrentSubTabProvider =
    StateProvider<SiteSubTab>((ref) => SiteSubTab.sites);

/// 통합 검색어 상태 프로바이더
final siteSearchQueryProvider = StateProvider<String>((ref) => '');

/// 소유구분 필터 상태 프로바이더 ('': 전체, '1': 개인, '2': 법인, '3': 국공유지)
final siteOwnSortFilterProvider = StateProvider<String>((ref) => '');

/// 📊 부지 종합 집계 프로바이더
final siteOverallAggregateProvider =
    FutureProvider<SiteAggregateModel>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) {
    return SiteAggregateModel(
      totalSitesCount: 0,
      totalOfficialArea: 0.0,
      totalReturnedArea: 0.0,
      isReturnedArea: false,
      totalOwnersCount: 0,
      totalContractsCount: 0,
      totalContractedArea: 0.0,
      totalPrice: 0,
    );
  }

  final repository = ref.watch(siteRepositoryProvider);
  
  // 프로젝트 단건 조회로 is_returned_area(환지방식 여부) 확인
  bool isReturned = false;
  try {
    final response = await repository.dio.get('/api/v1/project/${selectedProject.realProjectId}/');
    if (response.data is Map && response.data['is_returned_area'] == true) {
      isReturned = true;
    }
  } catch (_) {}

  return repository.fetchSiteAggregate(
    selectedProject.realProjectId,
    isReturnedArea: isReturned,
  );
});

/// ── 공통 무한 스크롤 상태 모델 ───────────────────────────
class SitePaginationState<T> {
  final List<T> items;
  final int page;
  final bool isLoading;
  final bool isFetchingNextPage;
  final bool hasMore;
  final String? error;

  const SitePaginationState({
    this.items = const [],
    this.page = 1,
    this.isLoading = false,
    this.isFetchingNextPage = false,
    this.hasMore = true,
    this.error,
  });

  SitePaginationState<T> copyWith({
    List<T>? items,
    int? page,
    bool? isLoading,
    bool? isFetchingNextPage,
    bool? hasMore,
    String? error,
  }) {
    return SitePaginationState<T>(
      items: items ?? this.items,
      page: page ?? this.page,
      isLoading: isLoading ?? this.isLoading,
      isFetchingNextPage: isFetchingNextPage ?? this.isFetchingNextPage,
      hasMore: hasMore ?? this.hasMore,
      error: error,
    );
  }
}

/// 📌 1. 지번별 토지 목록 Notifier
class SiteListNotifier extends StateNotifier<SitePaginationState<SiteItemModel>> {
  final Ref ref;

  SiteListNotifier(this.ref) : super(const SitePaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      state = const SitePaginationState();
      return;
    }

    state = state.copyWith(isLoading: true, page: 1, error: null);
    final query = ref.read(siteSearchQueryProvider);

    try {
      final repository = ref.read(siteRepositoryProvider);
      final items = await repository.fetchSites(
        projectId: selectedProject.realProjectId,
        search: query,
        page: 1,
      );

      state = state.copyWith(
        items: items,
        page: 1,
        isLoading: false,
        hasMore: items.length >= 15,
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
    final query = ref.read(siteSearchQueryProvider);

    try {
      final repository = ref.read(siteRepositoryProvider);
      final nextItems = await repository.fetchSites(
        projectId: selectedProject.realProjectId,
        search: query,
        page: nextPage,
      );

      state = state.copyWith(
        items: [...state.items, ...nextItems],
        page: nextPage,
        isFetchingNextPage: false,
        hasMore: nextItems.length >= 15,
      );
    } catch (e) {
      state = state.copyWith(isFetchingNextPage: false);
    }
  }
}

final siteListProvider =
    StateNotifierProvider.autoDispose<SiteListNotifier, SitePaginationState<SiteItemModel>>((ref) {
  return SiteListNotifier(ref);
});

/// 👤 2. 소유자별 토지 목록 Notifier
class SiteOwnerListNotifier extends StateNotifier<SitePaginationState<SiteOwnerItemModel>> {
  final Ref ref;

  SiteOwnerListNotifier(this.ref) : super(const SitePaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      state = const SitePaginationState();
      return;
    }

    state = state.copyWith(isLoading: true, page: 1, error: null);
    final query = ref.read(siteSearchQueryProvider);
    final ownSort = ref.read(siteOwnSortFilterProvider);

    try {
      final repository = ref.read(siteRepositoryProvider);
      final items = await repository.fetchSiteOwners(
        projectId: selectedProject.realProjectId,
        search: query,
        ownSort: ownSort,
        page: 1,
      );

      state = state.copyWith(
        items: items,
        page: 1,
        isLoading: false,
        hasMore: items.length >= 15,
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
    final query = ref.read(siteSearchQueryProvider);
    final ownSort = ref.read(siteOwnSortFilterProvider);

    try {
      final repository = ref.read(siteRepositoryProvider);
      final nextItems = await repository.fetchSiteOwners(
        projectId: selectedProject.realProjectId,
        search: query,
        ownSort: ownSort,
        page: nextPage,
      );

      state = state.copyWith(
        items: [...state.items, ...nextItems],
        page: nextPage,
        isFetchingNextPage: false,
        hasMore: nextItems.length >= 15,
      );
    } catch (e) {
      state = state.copyWith(isFetchingNextPage: false);
    }
  }
}

final siteOwnerListProvider =
    StateNotifierProvider.autoDispose<SiteOwnerListNotifier, SitePaginationState<SiteOwnerItemModel>>((ref) {
  return SiteOwnerListNotifier(ref);
});

/// 📑 3. 사업부지 매입계약 목록 Notifier
class SiteContractListNotifier extends StateNotifier<SitePaginationState<SiteContractItemModel>> {
  final Ref ref;

  SiteContractListNotifier(this.ref) : super(const SitePaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      state = const SitePaginationState();
      return;
    }

    state = state.copyWith(isLoading: true, page: 1, error: null);
    final query = ref.read(siteSearchQueryProvider);
    final ownSort = ref.read(siteOwnSortFilterProvider);

    try {
      final repository = ref.read(siteRepositoryProvider);
      final items = await repository.fetchSiteContracts(
        projectId: selectedProject.realProjectId,
        search: query,
        ownSort: ownSort,
        page: 1,
      );

      state = state.copyWith(
        items: items,
        page: 1,
        isLoading: false,
        hasMore: items.length >= 15,
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
    final query = ref.read(siteSearchQueryProvider);
    final ownSort = ref.read(siteOwnSortFilterProvider);

    try {
      final repository = ref.read(siteRepositoryProvider);
      final nextItems = await repository.fetchSiteContracts(
        projectId: selectedProject.realProjectId,
        search: query,
        ownSort: ownSort,
        page: nextPage,
      );

      state = state.copyWith(
        items: [...state.items, ...nextItems],
        page: nextPage,
        isFetchingNextPage: false,
        hasMore: nextItems.length >= 15,
      );
    } catch (e) {
      state = state.copyWith(isFetchingNextPage: false);
    }
  }
}

final siteContractListProvider =
    StateNotifierProvider.autoDispose<SiteContractListNotifier, SitePaginationState<SiteContractItemModel>>((ref) {
  return SiteContractListNotifier(ref);
});
