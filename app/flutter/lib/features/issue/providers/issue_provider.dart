import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/issue_repository.dart';
import '../data/models/issue_model.dart';

// ── 필터 상태 ──────────────────────────────────────────────────────────────────

/// 현재 적용된 필터 상태
final issueFilterProvider = StateProvider<IssueFilterModel>((ref) {
  return const IssueFilterModel();
});

// ── 업무 목록 (무한 스크롤) ────────────────────────────────────────────────────

class IssueListNotifier extends AsyncNotifier<IssueListState> {
  @override
  Future<IssueListState> build() async {
    final filter = ref.watch(issueFilterProvider);
    // 필터가 바뀌면 1페이지부터 다시 로드
    final resp = await ref.read(issueRepositoryProvider).fetchIssues(
          filter.copyWith(page: 1),
        );
    return IssueListState(
      items: resp.results,
      totalCount: resp.count,
      currentPage: 1,
      hasMore: resp.next != null,
    );
  }

  /// 다음 페이지 로드 (무한 스크롤)
  Future<void> loadMore() async {
    final current = state.valueOrNull;
    if (current == null || !current.hasMore || current.isLoadingMore) return;

    state = AsyncData(current.copyWith(isLoadingMore: true));

    try {
      final filter = ref.read(issueFilterProvider);
      final nextPage = current.currentPage + 1;
      final resp = await ref
          .read(issueRepositoryProvider)
          .fetchIssues(filter.copyWith(page: nextPage));

      state = AsyncData(current.copyWith(
        items: [...current.items, ...resp.results],
        currentPage: nextPage,
        hasMore: resp.next != null,
        isLoadingMore: false,
      ));
    } catch (e, st) {
      state = AsyncData(current.copyWith(isLoadingMore: false));
      // 오류 로깅 (필요 시 Sentry 연동)
      Error.throwWithStackTrace(e, st);
    }
  }

  /// 새로고침 (pull-to-refresh)
  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final filter = ref.read(issueFilterProvider);
      final resp = await ref
          .read(issueRepositoryProvider)
          .fetchIssues(filter.copyWith(page: 1));
      return IssueListState(
        items: resp.results,
        totalCount: resp.count,
        currentPage: 1,
        hasMore: resp.next != null,
      );
    });
  }
}

final issueListProvider =
    AsyncNotifierProvider<IssueListNotifier, IssueListState>(
  IssueListNotifier.new,
);

// ── 업무 목록 상태 모델 ────────────────────────────────────────────────────────

class IssueListState {
  final List<IssueModel> items;
  final int totalCount;
  final int currentPage;
  final bool hasMore;
  final bool isLoadingMore;

  const IssueListState({
    required this.items,
    required this.totalCount,
    required this.currentPage,
    required this.hasMore,
    this.isLoadingMore = false,
  });

  IssueListState copyWith({
    List<IssueModel>? items,
    int? totalCount,
    int? currentPage,
    bool? hasMore,
    bool? isLoadingMore,
  }) {
    return IssueListState(
      items: items ?? this.items,
      totalCount: totalCount ?? this.totalCount,
      currentPage: currentPage ?? this.currentPage,
      hasMore: hasMore ?? this.hasMore,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
    );
  }
}

// ── 업무 상세 ──────────────────────────────────────────────────────────────────

class IssueDetailNotifier
    extends FamilyAsyncNotifier<IssueModel, int> {
  @override
  Future<IssueModel> build(int id) async {
    return ref.read(issueRepositoryProvider).fetchIssueDetail(id);
  }

  /// 진척률 업데이트 (Optimistic Update)
  Future<void> updateDoneRatio(int ratio) async {
    final current = state.valueOrNull;
    if (current == null) return;

    // 즉시 UI 업데이트
    state = AsyncData(current.copyWith(doneRatio: ratio));

    try {
      await ref.read(issueRepositoryProvider).updateDoneRatio(current.pk, ratio);
    } catch (_) {
      // 실패 시 원래 값으로 롤백
      state = AsyncData(current);
      rethrow;
    }
  }

  /// 지켜보기 / 관심끄기 토글
  Future<void> toggleWatch() async {
    final current = state.valueOrNull;
    if (current == null) return;

    final updated =
        await ref.read(issueRepositoryProvider).toggleWatch(current.pk);
    state = AsyncData(updated);
  }

  /// 상세 새로고침
  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() =>
        ref.read(issueRepositoryProvider).fetchIssueDetail(arg));
  }
}

final issueDetailProvider =
    AsyncNotifierProviderFamily<IssueDetailNotifier, IssueModel, int>(
  IssueDetailNotifier.new,
);

// ── 댓글 ───────────────────────────────────────────────────────────────────────

class IssueCommentNotifier
    extends FamilyAsyncNotifier<List<IssueCommentModel>, int> {
  @override
  Future<List<IssueCommentModel>> build(int issueId) async {
    return ref.read(issueRepositoryProvider).fetchComments(issueId);
  }

  Future<void> addComment(String content, {bool isPrivate = false}) async {
    await ref
        .read(issueRepositoryProvider)
        .addComment(arg, content, isPrivate: isPrivate);
    // 댓글 추가 후 다시 로드
    ref.invalidateSelf();
  }
}

final issueCommentProvider =
    AsyncNotifierProviderFamily<IssueCommentNotifier, List<IssueCommentModel>, int>(
  IssueCommentNotifier.new,
);

// ── 변경 로그 (IssueLog) ───────────────────────────────────────────────────────

class IssueLogNotifier
    extends FamilyAsyncNotifier<List<IssueLogEntryModel>, int> {
  @override
  Future<List<IssueLogEntryModel>> build(int issueId) async {
    return ref.read(issueRepositoryProvider).fetchIssueLogs(issueId);
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
        () => ref.read(issueRepositoryProvider).fetchIssueLogs(arg));
  }
}

final issueLogProvider =
    AsyncNotifierProviderFamily<IssueLogNotifier, List<IssueLogEntryModel>, int>(
  IssueLogNotifier.new,
);

// ── 전역 공용 상태 / 우선순위 목록 프로바이더 ───────────────────────────────────

final issueStatusListProvider =
    FutureProvider<List<IssueStatusModel>>((ref) async {
  return ref.watch(issueRepositoryProvider).fetchStatuses();
});

final issuePriorityListProvider =
    FutureProvider<List<IssuePriorityModel>>((ref) async {
  return ref.watch(issueRepositoryProvider).fetchPriorities();
});
