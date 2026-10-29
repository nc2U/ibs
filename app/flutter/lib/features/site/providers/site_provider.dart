import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/project_provider.dart';
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

/// 사용동의 필터 상태 프로바이더 (null: 전체, true: 동의완료, false: 미동의)
final siteUseConsentFilterProvider = StateProvider<bool?>((ref) => null);

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

  // 프로젝트 환지방식 여부 확인 및 종합 집계 병렬 조회
  final results = await Future.wait<dynamic>([
    repository.dio
        .get('/api/v1/project/${selectedProject.realProjectId}/')
        .then<bool>((res) => res.data is Map && res.data['is_returned_area'] == true)
        .catchError((_) => false),
    repository.fetchSiteAggregate(selectedProject.realProjectId),
  ]);

  final isReturned = results[0] as bool;
  final aggregate = results[1] as SiteAggregateModel;

  return SiteAggregateModel(
    totalSitesCount: aggregate.totalSitesCount,
    totalOfficialArea: aggregate.totalOfficialArea,
    totalReturnedArea: aggregate.totalReturnedArea,
    isReturnedArea: isReturned,
    totalOwnersCount: aggregate.totalOwnersCount,
    totalContractsCount: aggregate.totalContractsCount,
    totalContractedArea: aggregate.totalContractedArea,
    totalPrice: aggregate.totalPrice,
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
  final int? projectId;
  final String searchQuery;

  SiteListNotifier(
    this.ref, {
    required this.projectId,
    required this.searchQuery,
  }) : super(const SitePaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    if (projectId == null) {
      state = const SitePaginationState();
      return;
    }

    state = state.copyWith(isLoading: true, page: 1, error: null);

    try {
      final repository = ref.read(siteRepositoryProvider);
      final items = await repository.fetchSites(
        projectId: projectId!,
        search: searchQuery,
        page: 1,
      );

      if (!mounted) return;
      state = state.copyWith(
        items: items,
        page: 1,
        isLoading: false,
        hasMore: items.length >= 15,
      );
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoading || state.isFetchingNextPage || !state.hasMore) return;
    if (projectId == null) return;

    state = state.copyWith(isFetchingNextPage: true);
    final nextPage = state.page + 1;

    try {
      final repository = ref.read(siteRepositoryProvider);
      final nextItems = await repository.fetchSites(
        projectId: projectId!,
        search: searchQuery,
        page: nextPage,
      );

      if (!mounted) return;
      state = state.copyWith(
        items: [...state.items, ...nextItems],
        page: nextPage,
        isFetchingNextPage: false,
        hasMore: nextItems.length >= 15,
      );
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(isFetchingNextPage: false, hasMore: true);
    }
  }
}

final siteListProvider =
    StateNotifierProvider.autoDispose<SiteListNotifier, SitePaginationState<SiteItemModel>>((ref) {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  final searchQuery = ref.watch(siteSearchQueryProvider);
  return SiteListNotifier(
    ref,
    projectId: selectedProject?.realProjectId,
    searchQuery: searchQuery,
  );
});

/// 👤 2. 소유자별 토지 목록 Notifier
class SiteOwnerListNotifier extends StateNotifier<SitePaginationState<SiteOwnerItemModel>> {
  final Ref ref;
  final int? projectId;
  final String searchQuery;
  final String ownSort;
  final bool? useConsent;

  SiteOwnerListNotifier(
    this.ref, {
    required this.projectId,
    required this.searchQuery,
    required this.ownSort,
    required this.useConsent,
  }) : super(const SitePaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    if (projectId == null) {
      state = const SitePaginationState();
      return;
    }

    state = state.copyWith(isLoading: true, page: 1, error: null);

    try {
      final repository = ref.read(siteRepositoryProvider);
      final items = await repository.fetchSiteOwners(
        projectId: projectId!,
        search: searchQuery,
        ownSort: ownSort,
        useConsent: useConsent,
        page: 1,
      );

      if (!mounted) return;
      state = state.copyWith(
        items: items,
        page: 1,
        isLoading: false,
        hasMore: items.length >= 15,
      );
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoading || state.isFetchingNextPage || !state.hasMore) return;
    if (projectId == null) return;

    state = state.copyWith(isFetchingNextPage: true);
    final nextPage = state.page + 1;

    try {
      final repository = ref.read(siteRepositoryProvider);
      final nextItems = await repository.fetchSiteOwners(
        projectId: projectId!,
        search: searchQuery,
        ownSort: ownSort,
        useConsent: useConsent,
        page: nextPage,
      );

      if (!mounted) return;
      state = state.copyWith(
        items: [...state.items, ...nextItems],
        page: nextPage,
        isFetchingNextPage: false,
        hasMore: nextItems.length >= 15,
      );
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(isFetchingNextPage: false, hasMore: true);
    }
  }
}

final siteOwnerListProvider =
    StateNotifierProvider.autoDispose<SiteOwnerListNotifier, SitePaginationState<SiteOwnerItemModel>>((ref) {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  final searchQuery = ref.watch(siteSearchQueryProvider);
  final ownSort = ref.watch(siteOwnSortFilterProvider);
  final useConsent = ref.watch(siteUseConsentFilterProvider);
  return SiteOwnerListNotifier(
    ref,
    projectId: selectedProject?.realProjectId,
    searchQuery: searchQuery,
    ownSort: ownSort,
    useConsent: useConsent,
  );
});

/// 📑 3. 사업부지 매입계약 목록 Notifier
class SiteContractListNotifier extends StateNotifier<SitePaginationState<SiteContractItemModel>> {
  final Ref ref;
  final int? projectId;
  final String searchQuery;
  final String ownSort;

  SiteContractListNotifier(
    this.ref, {
    required this.projectId,
    required this.searchQuery,
    required this.ownSort,
  }) : super(const SitePaginationState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    if (projectId == null) {
      state = const SitePaginationState();
      return;
    }

    state = state.copyWith(isLoading: true, page: 1, error: null);

    try {
      final repository = ref.read(siteRepositoryProvider);
      final items = await repository.fetchSiteContracts(
        projectId: projectId!,
        search: searchQuery,
        ownSort: ownSort,
        page: 1,
      );

      if (!mounted) return;
      state = state.copyWith(
        items: items,
        page: 1,
        isLoading: false,
        hasMore: items.length >= 15,
      );
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoading || state.isFetchingNextPage || !state.hasMore) return;
    if (projectId == null) return;

    state = state.copyWith(isFetchingNextPage: true);
    final nextPage = state.page + 1;

    try {
      final repository = ref.read(siteRepositoryProvider);
      final nextItems = await repository.fetchSiteContracts(
        projectId: projectId!,
        search: searchQuery,
        ownSort: ownSort,
        page: nextPage,
      );

      if (!mounted) return;
      state = state.copyWith(
        items: [...state.items, ...nextItems],
        page: nextPage,
        isFetchingNextPage: false,
        hasMore: nextItems.length >= 15,
      );
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(isFetchingNextPage: false, hasMore: true);
    }
  }
}

final siteContractListProvider =
    StateNotifierProvider.autoDispose<SiteContractListNotifier, SitePaginationState<SiteContractItemModel>>((ref) {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  final searchQuery = ref.watch(siteSearchQueryProvider);
  final ownSort = ref.watch(siteOwnSortFilterProvider);
  return SiteContractListNotifier(
    ref,
    projectId: selectedProject?.realProjectId,
    searchQuery: searchQuery,
    ownSort: ownSort,
  );
});
