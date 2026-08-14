import 'package:flutter_riverpod/flutter_riverpod.dart';
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

    try {
      final filter = ref.read(meetingFilterProvider);
      final nextPage = current.currentPage + 1;
      final resp = await ref
          .read(meetingRepositoryProvider)
          .fetchMeetings(filter.copyWith(page: nextPage));

      state = AsyncData(current.copyWith(
        items: [...current.items, ...resp.results],
        currentPage: nextPage,
        hasMore: resp.next != null,
        isLoadingMore: false,
      ));
    } catch (e, st) {
      state = AsyncData(current.copyWith(isLoadingMore: false));
      Error.throwWithStackTrace(e, st);
    }
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final filter = ref.read(meetingFilterProvider);
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
  }
}

final meetingListProvider =
    AsyncNotifierProvider<MeetingListNotifier, MeetingListState>(
  MeetingListNotifier.new,
);

// ── 회의 상세 ──────────────────────────────────────────────────────────────────

class MeetingDetailNotifier
    extends FamilyAsyncNotifier<MeetingModel, int> {
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
    ref.read(meetingListProvider.notifier).refresh();
    return isConfirmed;
  }
}

final meetingDetailProvider =
    AsyncNotifierProviderFamily<MeetingDetailNotifier, MeetingModel, int>(
  MeetingDetailNotifier.new,
);
