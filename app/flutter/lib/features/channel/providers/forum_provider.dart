import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/project_provider.dart';
import '../data/models/forum_model.dart';
import '../data/forum_repository.dart';

/// 현재 워크스페이스의 게시판 목록 프로바이더
final forumListProvider = FutureProvider<List<ForumModel>>((ref) async {
  final selectedProject = ref.watch(selectedProjectProvider);
  final repo = ref.watch(forumRepositoryProvider);
  return repo.fetchForums(
    projectId: selectedProject?.pk,
    projectSlug: selectedProject?.slug,
  );
});

/// 선택된 게시판 ID (null 이면 전체글)
final selectedForumIdProvider = StateProvider<int?>((ref) => null);

/// 현재 선택된 게시판의 카테고리 목록 프로바이더
final categoryListProvider = FutureProvider<List<PostCategoryModel>>((ref) async {
  final forumId = ref.watch(selectedForumIdProvider);
  if (forumId == null) return [];
  final repo = ref.watch(forumRepositoryProvider);
  return repo.fetchCategories(forumId);
});

/// 선택된 카테고리 ID (null 이면 전체)
final selectedCategoryIdProvider = StateProvider<int?>((ref) => null);

/// 게시글 검색어
final postSearchProvider = StateProvider<String>((ref) => '');

/// 게시글 목록 Notifier (페이징 + 필터링 + 무한 스크롤)
final postListProvider =
    AsyncNotifierProvider<PostListNotifier, PostListResponse>(
  PostListNotifier.new,
);

class PostListNotifier extends AsyncNotifier<PostListResponse> {
  int _currentPage = 1;

  @override
  Future<PostListResponse> build() async {
    final selectedProject = ref.watch(selectedProjectProvider);
    final selectedForumId = ref.watch(selectedForumIdProvider);
    final selectedCategoryId = ref.watch(selectedCategoryIdProvider);
    final search = ref.watch(postSearchProvider);
    final repo = ref.watch(forumRepositoryProvider);

    _currentPage = 1;

    return repo.fetchPosts(
      forumId: selectedForumId,
      categoryId: selectedCategoryId,
      projectId: selectedProject?.pk,
      projectSlug: selectedProject?.slug,
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
    final selectedForumId = ref.read(selectedForumIdProvider);
    final selectedCategoryId = ref.read(selectedCategoryIdProvider);
    final search = ref.read(postSearchProvider);
    final repo = ref.read(forumRepositoryProvider);

    try {
      final nextPage = _currentPage + 1;
      final response = await repo.fetchPosts(
        forumId: selectedForumId,
        categoryId: selectedCategoryId,
        projectId: selectedProject?.pk,
        projectSlug: selectedProject?.slug,
        search: search,
        page: nextPage,
      );
      _currentPage = nextPage;
      state = AsyncValue.data(
        PostListResponse(
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

/// 게시글 상세 프로바이더
final postDetailProvider =
    FutureProvider.family<PostModel, int>((ref, postId) async {
  final repo = ref.watch(forumRepositoryProvider);
  return repo.fetchPostDetail(postId);
});

/// 특정 게시글의 댓글 목록 프로바이더
final postCommentsProvider =
    FutureProvider.family<List<PostCommentModel>, int>((ref, postId) async {
  final repo = ref.watch(forumRepositoryProvider);
  return repo.fetchComments(postId: postId);
});

/// ── FAQ & 기술지원 전용 프로바이더 (본사 1번 포럼 연동) ────────────────────
const int kTechSupportForumId = 1;

/// FAQ 1번 포럼의 카테고리 목록
final faqCategoriesProvider = FutureProvider<List<PostCategoryModel>>((ref) async {
  final repo = ref.watch(forumRepositoryProvider);
  return repo.fetchCategories(kTechSupportForumId);
});

/// FAQ 1번 포럼의 is_faq=true 게시글 전체 목록
final faqPostsProvider = FutureProvider<List<PostModel>>((ref) async {
  final repo = ref.watch(forumRepositoryProvider);
  final response = await repo.fetchPosts(
    forumId: kTechSupportForumId,
    isFaq: true,
    page: 1,
  );
  return response.results;
});

/// FAQ 1번 포럼의 공지글 (이용 안내 등) 목록
final faqNoticesProvider = FutureProvider<List<PostModel>>((ref) async {
  final repo = ref.watch(forumRepositoryProvider);
  final response = await repo.fetchPosts(
    forumId: kTechSupportForumId,
    isNotice: true,
    page: 1,
  );
  return response.results;
});
