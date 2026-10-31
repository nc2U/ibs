import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/docs_context_provider.dart';
import '../data/docs_repository.dart';
import '../data/models/docs_model.dart';

/// 카테고리 목록 프로바이더 (현재 선택된 docType에 맞춰 자동 연동)
final docCategoriesProvider = FutureProvider<List<DocCategoryModel>>((ref) async {
  final docType = ref.watch(docTypeFilterProvider);
  return ref.watch(docCategoriesByTypeProvider(docType).future);
});

/// 문서 구분별 카테고리 목록 프로바이더 (폼 내부에서 docType 전환 시 즉시 연동)
final docCategoriesByTypeProvider = FutureProvider.family<List<DocCategoryModel>, String?>((ref, docType) async {
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

/// 문서 추가 페이지 로딩 실패 상태 StateProvider
final docsLoadMoreFailedProvider = StateProvider<bool>((ref) => false);

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
    Future.microtask(() {
      ref.read(docsLoadMoreFailedProvider.notifier).state = false;
    });
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
    ref.read(docsLoadMoreFailedProvider.notifier).state = false;
    final prev = state.value;
    try {
      final updated = await build();
      state = AsyncValue.data(updated);
    } catch (e, st) {
      if (prev != null) {
        state = AsyncValue.data(prev);
      } else {
        state = AsyncValue.error(e, st);
      }
    }
  }

  Future<void> loadNextPage() async {
    final currentData = state.value;
    if (currentData == null || currentData.next == null || _isLoadingMore) return;

    _isLoadingMore = true;
    ref.read(docsLoadingMoreProvider.notifier).state = true;
    ref.read(docsLoadMoreFailedProvider.notifier).state = false;

    final repo = ref.read(docsRepositoryProvider);
    final initialProjectId = ref.read(docsContextProvider).project?.pk;
    final initialSearch = ref.read(docsSearchProvider);
    final initialDocType = ref.read(docTypeFilterProvider);
    final initialCategory = ref.read(docCategoryFilterProvider);

    _currentPage++;
    try {
      final nextPageData = await repo.fetchDocuments(
        issueProject: initialProjectId,
        docType: initialDocType,
        category: initialCategory,
        search: initialSearch,
        page: _currentPage,
      );

      // 경쟁 상태 방지: 비동기 대기 중 필터/검색어가 바뀌었으면 폐기
      final currentProjectId = ref.read(docsContextProvider).project?.pk;
      final currentSearch = ref.read(docsSearchProvider);
      final currentDocType = ref.read(docTypeFilterProvider);
      final currentCategory = ref.read(docCategoryFilterProvider);

      if (initialProjectId != currentProjectId ||
          initialSearch != currentSearch ||
          initialDocType != currentDocType ||
          initialCategory != currentCategory) {
        return;
      }

      final activeData = state.value ?? currentData;
      state = AsyncValue.data(
        DocumentListResponseModel(
          count: nextPageData.count,
          next: nextPageData.next,
          previous: nextPageData.previous,
          results: [...activeData.results, ...nextPageData.results],
        ),
      );
    } catch (_) {
      _currentPage--;
      ref.read(docsLoadMoreFailedProvider.notifier).state = true;
    } finally {
      _isLoadingMore = false;
      ref.read(docsLoadingMoreProvider.notifier).state = false;
    }
  }
}
