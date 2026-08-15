import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/project_provider.dart';
import '../data/models/notice_model.dart';
import '../data/notice_repository.dart';

/// 공지 검색어 StateProvider
final noticeSearchProvider = StateProvider<String>((ref) => '');

/// 공지사항 목록 Notifier
final noticeListProvider =
    AsyncNotifierProvider<NoticeListNotifier, NoticeListResponse>(
  NoticeListNotifier.new,
);

class NoticeListNotifier extends AsyncNotifier<NoticeListResponse> {
  int _currentPage = 1;

  @override
  Future<NoticeListResponse> build() async {
    final selectedProject = ref.watch(selectedProjectProvider);
    final search = ref.watch(noticeSearchProvider);
    final repo = ref.watch(noticeRepositoryProvider);

    _currentPage = 1;

    return repo.fetchNotices(
      project: selectedProject?.pk,
      search: search,
      page: _currentPage,
    );
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => build());
  }

  Future<void> loadMore() async {
    final current = state.value;
    if (current == null || current.next == null || state.isLoading) return;

    final selectedProject = ref.read(selectedProjectProvider);
    final search = ref.read(noticeSearchProvider);
    final repo = ref.read(noticeRepositoryProvider);

    try {
      final nextPage = _currentPage + 1;
      final response = await repo.fetchNotices(
        project: selectedProject?.pk,
        search: search,
        page: nextPage,
      );
      _currentPage = nextPage;
      state = AsyncValue.data(
        NoticeListResponse(
          count: response.count,
          next: response.next,
          previous: response.previous,
          results: [...current.results, ...response.results],
        ),
      );
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}

/// 공지사항 단건 상세 FutureProvider
final noticeDetailProvider =
    FutureProvider.family<NoticeModel, int>((ref, id) async {
  final repo = ref.watch(noticeRepositoryProvider);
  return repo.fetchNoticeDetail(id);
});
