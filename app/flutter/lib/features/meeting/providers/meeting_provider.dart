import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/models/common_models.dart';
import '../data/meeting_repository.dart';
import '../data/models/meeting_model.dart';

// ── 필터 상태 ──────────────────────────────────────────────────────────────────

final meetingFilterProvider = StateProvider<MeetingFilterModel>((ref) {
  return const MeetingFilterModel();
});

// ── 회의 목록 (페이지네이션) ───────────────────────────────────────────────────

class MeetingListState {
  final List<MeetingModel> items;
  final int totalCount;
  final int currentPage;
  final bool hasMore;
  final bool isLoadingMore;

  const MeetingListState({
    required this.items,
    required this.totalCount,
    required this.currentPage,
    required this.hasMore,
    this.isLoadingMore = false,
  });

  MeetingListState copyWith({
    List<MeetingModel>? items,
    int? totalCount,
    int? currentPage,
    bool? hasMore,
    bool? isLoadingMore,
  }) {
    return MeetingListState(
      items: items ?? this.items,
      totalCount: totalCount ?? this.totalCount,
      currentPage: currentPage ?? this.currentPage,
      hasMore: hasMore ?? this.hasMore,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
    );
  }
}

class MeetingListNotifier extends AsyncNotifier<MeetingListState> {
  @override
  Future<MeetingListState> build() async {
    final filter = ref.watch(meetingFilterProvider);
    final resp = await ref.read(meetingRepositoryProvider).fetchMeetings(
          filter.copyWith(page: 1),
        );
    return MeetingListState(
      items: resp.results,
      totalCount: resp.count,
      currentPage: 1,
      hasMore: resp.next != null,
    );
  }

  Future<void> loadMore() async {
    final current = state.valueOrNull;
    if (current == null || !current.hasMore || current.isLoadingMore) return;

    state = AsyncData(current.copyWith(isLoadingMore: true));

    final filter = ref.read(meetingFilterProvider);
    try {
      final nextPage = current.currentPage + 1;
      final resp = await ref
          .read(meetingRepositoryProvider)
          .fetchMeetings(filter.copyWith(page: nextPage));

      // 응답 대기 중 필터가 바뀌어 목록이 재구성되었다면 오래된 응답은 폐기
      if (ref.read(meetingFilterProvider) != filter) return;

      state = AsyncData(current.copyWith(
        items: [...current.items, ...resp.results],
        currentPage: nextPage,
        hasMore: resp.next != null,
        isLoadingMore: false,
      ));
    } catch (_) {
      if (ref.read(meetingFilterProvider) != filter) return;
      // 스크롤 리스너에서 await 없이 호출되므로 예외를 전파하지 않고 로딩 상태만 해제
      state = AsyncData(current.copyWith(isLoadingMore: false));
    }
  }

  /// 기존 목록을 유지한 채 새로 조회 (RefreshIndicator/shimmer 깜빡임 방지)
  Future<void> refresh() async {
    final filter = ref.read(meetingFilterProvider);
    final result = await AsyncValue.guard(() async {
      final resp = await ref
          .read(meetingRepositoryProvider)
          .fetchMeetings(filter.copyWith(page: 1));
      return MeetingListState(
        items: resp.results,
        totalCount: resp.count,
        currentPage: 1,
        hasMore: resp.next != null,
      );
    });
    if (ref.read(meetingFilterProvider) != filter) return;
    // 갱신 실패 시 기존 데이터를 유지
    if (result.hasError && state.hasValue) return;
    state = result;
  }
}

final meetingListProvider =
    AsyncNotifierProvider<MeetingListNotifier, MeetingListState>(
  MeetingListNotifier.new,
);

// ── 회의 상세 ──────────────────────────────────────────────────────────────────

class MeetingDetailNotifier
    extends AutoDisposeFamilyAsyncNotifier<MeetingModel, int> {
  @override
  Future<MeetingModel> build(int id) async {
    return ref.read(meetingRepositoryProvider).fetchMeetingDetail(id);
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
        () => ref.read(meetingRepositoryProvider).fetchMeetingDetail(arg));
  }

  /// 회의 확정/확정취소 토글
  Future<bool> toggleConfirm() async {
    final isConfirmed = await ref.read(meetingRepositoryProvider).toggleConfirm(arg);
    final current = state.valueOrNull;
    if (current != null) {
      state = AsyncData(current.copyWith(isConfirmed: isConfirmed));
    }
    // 회의 목록도 갱신
    ref.invalidate(meetingListProvider);
    return isConfirmed;
  }
}

final meetingDetailProvider = AsyncNotifierProvider.autoDispose
    .family<MeetingDetailNotifier, MeetingModel, int>(
  MeetingDetailNotifier.new,
);

// ── 카테고리 & 멤버 프로바이더 ──────────────────────────────────────────────────

final meetingCategoriesProvider =
    FutureProvider.autoDispose.family<List<MeetingCategoryModel>, int?>((ref, projectPk) async {
  return ref.read(meetingRepositoryProvider).fetchCategories(projectPk: projectPk);
});

final meetingMembersProvider =
    FutureProvider.autoDispose.family<List<SimpleUserModel>, int?>((ref, projectPk) async {
  return ref.read(meetingRepositoryProvider).fetchMembers(projectPk: projectPk);
});
