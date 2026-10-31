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

    final filter = ref.read(issueFilterProvider);
    state = AsyncData(current.copyWith(isLoadingMore: true, loadMoreFailed: false));

    try {
      final nextPage = current.currentPage + 1;
      final resp = await ref
          .read(issueRepositoryProvider)
          .fetchIssues(filter.copyWith(page: nextPage));

      if (ref.read(issueFilterProvider) != filter) return;

      final latest = state.valueOrNull ?? current;
      state = AsyncData(latest.copyWith(
        items: [...latest.items, ...resp.results],
        currentPage: nextPage,
        hasMore: resp.next != null,
        isLoadingMore: false,
        loadMoreFailed: false,
      ));
    } catch (_) {
      if (ref.read(issueFilterProvider) != filter) return;
      final latest = state.valueOrNull ?? current;
      state = AsyncData(latest.copyWith(
        isLoadingMore: false,
        loadMoreFailed: true,
      ));
    }
  }

  /// 개별 업무 상태 즉시 갱신 (Optimistic / Local Update)
  void updateSingleIssue(IssueModel updated) {
    final current = state.valueOrNull;
    if (current == null) return;

    final updatedItems = current.items.map((i) {
      return i.pk == updated.pk ? updated : i;
    }).toList();

    state = AsyncData(current.copyWith(items: updatedItems));
  }

  /// 새로고침 (pull-to-refresh) - 화면 깜빡임 없이 기존 데이터 유지
  Future<void> refresh() async {
    final filter = ref.read(issueFilterProvider);
    try {
      final resp = await ref
          .read(issueRepositoryProvider)
          .fetchIssues(filter.copyWith(page: 1));

      if (ref.read(issueFilterProvider) != filter) return;

      state = AsyncData(IssueListState(
        items: resp.results,
        totalCount: resp.count,
        currentPage: 1,
        hasMore: resp.next != null,
        loadMoreFailed: false,
      ));
    } catch (e, st) {
      if (state.valueOrNull == null) {
        state = AsyncError(e, st);
      }
    }
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
  final bool loadMoreFailed;

  const IssueListState({
    required this.items,
    required this.totalCount,
    required this.currentPage,
    required this.hasMore,
    this.isLoadingMore = false,
    this.loadMoreFailed = false,
  });

  IssueListState copyWith({
    List<IssueModel>? items,
    int? totalCount,
    int? currentPage,
    bool? hasMore,
    bool? isLoadingMore,
    bool? loadMoreFailed,
  }) {
    return IssueListState(
      items: items ?? this.items,
      totalCount: totalCount ?? this.totalCount,
      currentPage: currentPage ?? this.currentPage,
      hasMore: hasMore ?? this.hasMore,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      loadMoreFailed: loadMoreFailed ?? this.loadMoreFailed,
    );
  }
}

// ── 업무 상세 ──────────────────────────────────────────────────────────────────

class IssueDetailNotifier
    extends AutoDisposeFamilyAsyncNotifier<IssueModel, int> {
  @override
  Future<IssueModel> build(int id) async {
    return ref.read(issueRepositoryProvider).fetchIssueDetail(id);
  }

  /// 진척률 업데이트 (Optimistic Update 및 상태 자동 연동 지원)
  Future<void> updateDoneRatio(int ratio) async {
    final detailIssue = state.valueOrNull;
    final listIssue = ref
        .read(issueListProvider)
        .valueOrNull
        ?.items
        .where((i) => i.pk == arg)
        .firstOrNull;
    final baseIssue = detailIssue ?? listIssue;
    final statuses = ref.read(issueStatusListProvider).valueOrNull;

    IssueStatusModel? nextStatus;
    int? nextStatusId;

    if (ratio == 100) {
      if (baseIssue == null || !baseIssue.status.closed) {
        nextStatus = statuses?.where((s) => s.closed).firstOrNull ??
            const IssueStatusModel(pk: 5, name: '완료', closed: true);
        nextStatusId = nextStatus.pk;
      }
    } else if (baseIssue != null) {
      if (baseIssue.status.closed) {
        nextStatus = statuses?.where((s) => s.pk == 2).firstOrNull ??
            statuses?.where((s) => !s.closed && s.pk != 1).firstOrNull ??
            const IssueStatusModel(pk: 2, name: '진행', closed: false);
        nextStatusId = nextStatus.pk;
      } else if (ratio > 0 && baseIssue.status.pk == 1) {
        nextStatus = statuses?.where((s) => s.pk == 2).firstOrNull ??
            statuses?.where((s) => !s.closed && s.pk != 1).firstOrNull ??
            const IssueStatusModel(pk: 2, name: '진행', closed: false);
        nextStatusId = nextStatus.pk;
      }
    }

    if (baseIssue != null) {
      final optimisticIssue = baseIssue.copyWith(
        doneRatio: ratio,
        status: nextStatus ?? baseIssue.status,
      );

      if (detailIssue != null) {
        state = AsyncData(optimisticIssue);
      }
      ref.read(issueListProvider.notifier).updateSingleIssue(optimisticIssue);

      try {
        final serverUpdated = await ref
            .read(issueRepositoryProvider)
            .updateDoneRatio(arg, ratio, statusId: nextStatusId);
        state = AsyncData(serverUpdated);
        ref.read(issueListProvider.notifier).updateSingleIssue(serverUpdated);
        if (baseIssue.status.closed != serverUpdated.status.closed) {
          ref.invalidate(issueListProvider);
        }
        ref.invalidate(issueLogProvider(arg));
      } catch (_) {
        // 실패 시 원래 값으로 롤백
        if (detailIssue != null) {
          state = AsyncData(detailIssue);
        }
        ref.read(issueListProvider.notifier).updateSingleIssue(baseIssue);
        rethrow;
      }
    } else {
      final serverUpdated = await ref
          .read(issueRepositoryProvider)
          .updateDoneRatio(arg, ratio, statusId: nextStatusId);
      state = AsyncData(serverUpdated);
      ref.invalidate(issueListProvider);
      ref.invalidate(issueLogProvider(arg));
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
    try {
      final updated =
          await ref.read(issueRepositoryProvider).fetchIssueDetail(arg);
      state = AsyncData(updated);
    } catch (e, st) {
      if (state.valueOrNull == null) {
        state = AsyncError(e, st);
      }
    }
  }
}

final issueDetailProvider = AsyncNotifierProvider.autoDispose
    .family<IssueDetailNotifier, IssueModel, int>(
  IssueDetailNotifier.new,
);

// ── 댓글 ───────────────────────────────────────────────────────────────────────

class IssueCommentNotifier
    extends AutoDisposeFamilyAsyncNotifier<List<IssueCommentModel>, int> {
  @override
  Future<List<IssueCommentModel>> build(int issueId) async {
    return ref.read(issueRepositoryProvider).fetchComments(issueId);
  }

  Future<void> addComment(String content, {bool isPrivate = false}) async {
    await ref
        .read(issueRepositoryProvider)
        .addComment(arg, content, isPrivate: isPrivate);
    // 댓글 추가 후 댓글 목록, 변경 로그, 상세 화면 동기화
    ref.invalidateSelf();
    ref.invalidate(issueLogProvider(arg));
    ref.invalidate(issueDetailProvider(arg));
  }
}

final issueCommentProvider = AsyncNotifierProvider.autoDispose
    .family<IssueCommentNotifier, List<IssueCommentModel>, int>(
  IssueCommentNotifier.new,
);

// ── 변경 로그 (IssueLog) ───────────────────────────────────────────────────────

class IssueLogNotifier
    extends AutoDisposeFamilyAsyncNotifier<List<IssueLogEntryModel>, int> {
  @override
  Future<List<IssueLogEntryModel>> build(int issueId) async {
    return ref.read(issueRepositoryProvider).fetchIssueLogs(issueId);
  }

  Future<void> refresh() async {
    try {
      final logs =
          await ref.read(issueRepositoryProvider).fetchIssueLogs(arg);
      state = AsyncData(logs);
    } catch (e, st) {
      if (state.valueOrNull == null) {
        state = AsyncError(e, st);
      }
    }
  }
}

final issueLogProvider = AsyncNotifierProvider.autoDispose
    .family<IssueLogNotifier, List<IssueLogEntryModel>, int>(
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

/// 특정 프로젝트의 상위 업무 후보 목록 조회 (필터 무관 전체 목록)
final projectIssuesProvider =
    FutureProvider.family<List<IssueModel>, String>((ref, projectSlug) async {
  if (projectSlug.isEmpty) return const [];
  final repo = ref.watch(issueRepositoryProvider);
  final res = await repo.fetchIssues(
    IssueFilterModel(
      projectSlug: projectSlug,
      pageSize: 100,
    ),
  );
  return res.results;
});
