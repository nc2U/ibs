import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/docs_context_provider.dart';
import '../data/docs_repository.dart';
import '../data/models/docs_model.dart';

/// 카테고리 목록 프로바이더 (현재 선택된 docType에 맞춰 자동 연동)
final docCategoriesProvider = FutureProvider<List<DocCategoryModel>>((ref) async {
  final docType = ref.watch(docTypeFilterProvider);
  final repo = ref.watch(docsRepositoryProvider);
  return repo.fetchCategories(docType: docType);
});

/// 소송 사건 목록 옵션 프로바이더 (프로젝트 ID별)
final suitCaseOptionsProvider = FutureProvider.family<List<SuitCaseOptionModel>, int?>((ref, issueProject) async {
  final repo = ref.watch(docsRepositoryProvider);
  return repo.fetchSuitCases(issueProject: issueProject);
});

/// 문서 검색어 StateProvider
final docsSearchProvider = StateProvider<String>((ref) => '');

/// 문서 유형 필터 StateProvider ('1': 일반문서, '2': 소송기록, 기본값 '1')
final docTypeFilterProvider = StateProvider<String?>((ref) => '1');

/// 문서 카테고리 필터 StateProvider (null: 전체)
final docCategoryFilterProvider = StateProvider<int?>((ref) => null);

/// 문서 추가 페이지 로딩 상태 StateProvider
final docsLoadingMoreProvider = StateProvider<bool>((ref) => false);

/// 문서 목록 Notifier
final docsListProvider = AsyncNotifierProvider<DocsListNotifier, DocumentListResponseModel>(
  DocsListNotifier.new,
);

class DocsListNotifier extends AsyncNotifier<DocumentListResponseModel> {
  int _currentPage = 1;
  bool _isLoadingMore = false;

  @override
  Future<DocumentListResponseModel> build() async {
    final ctx = ref.watch(docsContextProvider);
    final search = ref.watch(docsSearchProvider);
    final docType = ref.watch(docTypeFilterProvider);
    final category = ref.watch(docCategoryFilterProvider);
    final repo = ref.watch(docsRepositoryProvider);

    _currentPage = 1;
    _isLoadingMore = false;
    final issueProjectId = ctx.project?.pk;

    return repo.fetchDocuments(
      issueProject: issueProjectId,
      docType: docType,
      category: category,
      search: search,
      page: _currentPage,
    );
  }

  Future<void> refresh() async {
    _currentPage = 1;
    _isLoadingMore = false;
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => build());
  }

  Future<void> loadNextPage() async {
    final currentData = state.value;
    if (currentData == null || currentData.next == null || _isLoadingMore) return;

    _isLoadingMore = true;
    ref.read(docsLoadingMoreProvider.notifier).state = true;

    final repo = ref.read(docsRepositoryProvider);
    final ctx = ref.read(docsContextProvider);
    final search = ref.read(docsSearchProvider);
    final docType = ref.read(docTypeFilterProvider);
    final category = ref.read(docCategoryFilterProvider);

    _currentPage++;
    try {
      final nextPageData = await repo.fetchDocuments(
        issueProject: ctx.project?.pk,
        docType: docType,
        category: category,
        search: search,
        page: _currentPage,
      );

      state = AsyncValue.data(
        DocumentListResponseModel(
          count: nextPageData.count,
          next: nextPageData.next,
          previous: nextPageData.previous,
          results: [...currentData.results, ...nextPageData.results],
        ),
      );
    } catch (_) {
      _currentPage--;
    } finally {
      _isLoadingMore = false;
      ref.read(docsLoadingMoreProvider.notifier).state = false;
    }
  }
}
