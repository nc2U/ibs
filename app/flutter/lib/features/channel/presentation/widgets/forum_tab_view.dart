import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../../providers/forum_provider.dart';
import 'post_card.dart';
import 'post_detail_sheet.dart';

/// 사내 게시판 탭 뷰 (게시판 칩바 + 카테고리 칩바 + 검색 + 게시글 피드)
class ForumTabView extends ConsumerStatefulWidget {
  const ForumTabView({super.key});

  @override
  ConsumerState<ForumTabView> createState() => _ForumTabViewState();
}

class _ForumTabViewState extends ConsumerState<ForumTabView> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      ref.read(postListProvider.notifier).loadMore();
    }
  }

  void _onSearch(String query) {
    ref.read(postSearchProvider.notifier).state = query.trim();
  }

  @override
  Widget build(BuildContext context) {
    final canRead = ref.can(Perm.forumRead);
    if (!canRead) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24.0),
          child: ErrorView.empty(
            message: '게시판을 조회할 권한이 없습니다.',
            subMessage: '관리자에게 [게시판 열람] 권한(forum.read)을 요청해 주세요.',
          ),
        ),
      );
    }

    final forumsAsync = ref.watch(forumListProvider);
    final selectedForumId = ref.watch(selectedForumIdProvider);
    final categoriesAsync = ref.watch(categoryListProvider);
    final selectedCategoryId = ref.watch(selectedCategoryIdProvider);
    final postListAsync = ref.watch(postListProvider);
    final selectedProject = ref.watch(selectedProjectProvider);

    final isForumDisabled =
        selectedProject != null && (selectedProject.module?.forum == false);

    if (isForumDisabled) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: ErrorView.empty(
            message: '게시판 모듈이 없는 워크스페이스입니다.',
            subMessage: '[${selectedProject.name}] 워크스페이스는 게시판 기능을 사용하지 않습니다.',
            icon: Icons.speaker_notes_off_outlined,
          ),
        ),
      );
    }

    return forumsAsync.when(
      data: (forums) {
        if (forums.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(32.0),
              child: ErrorView.empty(
                message: '개설된 게시판이 없습니다.',
                subMessage: selectedProject != null
                    ? '[${selectedProject.name}] 워크스페이스에 아직 생성된 게시판이 없습니다.\n게시판 개설 및 카테고리 관리는 PC 웹(워크스페이스 설정)에서 진행해 주세요.'
                    : '등록된 게시판이 없습니다.\nPC 웹(워크스페이스 설정)에서 새 게시판을 개설해 주세요.',
                icon: Icons.dashboard_customize_outlined,
              ),
            ),
          );
        }

        return Column(
          children: [
            // ── 1. 검색 바 (최상단 고정) ──────────────────────────────────
            Container(
              color: context.colors.bgSurface,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: TextField(
                controller: _searchController,
                onSubmitted: _onSearch,
                textInputAction: TextInputAction.search,
                style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
                decoration: InputDecoration(
                  hintText: '게시글 제목, 내용, 작성자 검색',
                  hintStyle: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                  prefixIcon: Icon(Icons.search_rounded,
                      size: 18, color: context.colors.textMuted),
                  suffixIcon: _searchController.text.isNotEmpty
                      ? IconButton(
                          icon: Icon(Icons.clear_rounded,
                              size: 16, color: context.colors.textMuted),
                          onPressed: () {
                            _searchController.clear();
                            _onSearch('');
                          },
                        )
                      : null,
                  filled: true,
                  fillColor: context.colors.bgCard,
                  isDense: true,
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.zero,
                    borderSide: BorderSide(color: context.colors.border),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.zero,
                    borderSide: BorderSide(color: context.colors.border),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.zero,
                    borderSide: BorderSide(color: context.colors.accentChannel),
                  ),
                ),
              ),
            ),
            Divider(color: context.colors.border, height: 1),

            // ── 2. 게시판 선택 칩 바 (가로 스크롤 레일, 100% Full Width) ────────
            Container(
              width: double.infinity,
              color: context.colors.bgSurface,
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.start,
                  children: [
                    // '전체글' 칩
                    Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: FilterChip(
                        label: const Text('전체글'),
                        selected: selectedForumId == null,
                        showCheckmark: false,
                        shape: const RoundedRectangleBorder(
                            borderRadius: BorderRadius.zero),
                        backgroundColor: context.colors.bgCard,
                        selectedColor: context.colors.accentChannel.withAlpha(30),
                        labelStyle: TextStyle(
                          color: selectedForumId == null
                              ? context.colors.accentChannel
                              : context.colors.textSecond,
                          fontWeight: selectedForumId == null
                              ? FontWeight.bold
                              : FontWeight.normal,
                          fontSize: 12,
                        ),
                        side: BorderSide(
                          color: selectedForumId == null
                              ? context.colors.accentChannel
                              : context.colors.border,
                        ),
                        onSelected: (_) {
                          ref.read(selectedForumIdProvider.notifier).state =
                              null;
                          ref.read(selectedCategoryIdProvider.notifier).state =
                              null;
                        },
                      ),
                    ),
                    // 개별 게시판 칩들
                    ...forums.map((forum) {
                      final isSelected = selectedForumId == forum.pk;
                      return Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: FilterChip(
                          label: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(forum.name),
                              if (forum.postCount > 0) ...[
                                const SizedBox(width: 4),
                                Text(
                                  '${forum.postCount}',
                                  style: TextStyle(
                                    color: isSelected
                                        ? context.colors.accentChannel
                                        : context.colors.textMuted,
                                    fontSize: 11,
                                  ),
                                ),
                              ],
                            ],
                          ),
                          selected: isSelected,
                          showCheckmark: false,
                          shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero),
                          backgroundColor: context.colors.bgCard,
                          selectedColor: context.colors.accentChannel.withAlpha(30),
                          labelStyle: TextStyle(
                            color: isSelected
                                ? context.colors.accentChannel
                                : context.colors.textSecond,
                            fontWeight: isSelected
                                ? FontWeight.bold
                                : FontWeight.normal,
                            fontSize: 12,
                          ),
                          side: BorderSide(
                            color: isSelected
                                ? context.colors.accentChannel
                                : context.colors.border,
                          ),
                          onSelected: (_) {
                            ref.read(selectedForumIdProvider.notifier).state =
                                forum.pk;
                            ref.read(selectedCategoryIdProvider.notifier).state =
                                null;
                          },
                        ),
                      );
                    }),
                  ],
                ),
              ),
            ),

            // ── 3. 서브 카테고리 칩 바 (게시판 선택 시 노출, 가로 스크롤 레일) ────
            if (selectedForumId != null)
              categoriesAsync.maybeWhen(
                data: (categories) {
                  if (categories.isEmpty) return const SizedBox.shrink();
                  return Container(
                    width: double.infinity,
                    color: context.colors.bgSurface,
                    padding: const EdgeInsets.only(bottom: 8),
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.start,
                        children: [
                          Padding(
                            padding: const EdgeInsets.only(right: 6),
                            child: ChoiceChip(
                              label: const Text('카테고리 전체'),
                              selected: selectedCategoryId == null,
                              shape: const RoundedRectangleBorder(
                                  borderRadius: BorderRadius.zero),
                              backgroundColor: context.colors.bgCard,
                              selectedColor: context.colors.accentProject.withAlpha(30),
                              labelStyle: TextStyle(
                                color: selectedCategoryId == null
                                    ? context.colors.accentProject
                                    : context.colors.textSecond,
                                fontSize: 11,
                                fontWeight: selectedCategoryId == null
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                              ),
                              side: BorderSide(
                                color: selectedCategoryId == null
                                    ? context.colors.accentProject
                                    : context.colors.border,
                              ),
                              onSelected: (_) {
                                ref
                                    .read(selectedCategoryIdProvider.notifier)
                                    .state = null;
                              },
                            ),
                          ),
                          ...categories.map((cat) {
                            final isCatSelected = selectedCategoryId == cat.pk;
                            return Padding(
                              padding: const EdgeInsets.only(right: 6),
                              child: ChoiceChip(
                                label: Text(cat.name),
                                selected: isCatSelected,
                                shape: const RoundedRectangleBorder(
                                    borderRadius: BorderRadius.zero),
                                backgroundColor: context.colors.bgCard,
                                selectedColor: context.colors.accentProject.withAlpha(30),
                                labelStyle: TextStyle(
                                  color: isCatSelected
                                      ? context.colors.accentProject
                                      : context.colors.textSecond,
                                  fontSize: 11,
                                  fontWeight: isCatSelected
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                ),
                                side: BorderSide(
                                  color: isCatSelected
                                      ? context.colors.accentProject
                                      : context.colors.border,
                                ),
                                onSelected: (_) {
                                  ref
                                      .read(selectedCategoryIdProvider.notifier)
                                      .state = cat.pk;
                                },
                              ),
                            );
                          }),
                        ],
                      ),
                    ),
                  );
                },
                orElse: () => const SizedBox.shrink(),
              ),

            Divider(color: context.colors.border, height: 1),

            // ── 4. 게시글 피드 목록 ───────────────────────────────────────
            Expanded(
              child: postListAsync.when(
                data: (data) {
                  if (data.results.isEmpty) {
                    final hasSearch = _searchController.text.trim().isNotEmpty;
                    final isForumFiltered = selectedForumId != null;

                    return ErrorView.empty(
                      message: hasSearch
                          ? '검색 결과와 일치하는 게시글이 없습니다.'
                          : (isForumFiltered
                              ? '선택한 게시판에 등록된 게시글이 없습니다.'
                              : '등록된 게시글이 없습니다.'),
                      subMessage: hasSearch
                          ? '다른 검색어로 다시 시도해 보세요.'
                          : (selectedProject != null
                              ? '[${selectedProject.name}] 워크스페이스의 첫 게시글을 작성해 보세요.'
                              : null),
                      icon: Icons.forum_outlined,
                    );
                  }

                  return RefreshIndicator(
                    onRefresh: () => ref.read(postListProvider.notifier).refresh(),
                    child: ListView.separated(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(16),
                      itemCount: data.results.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 10),
                      itemBuilder: (ctx, index) {
                        final post = data.results[index];
                        return PostCard(
                          post: post,
                          showWorkspaceBadge: selectedProject == null,
                          onTap: () {
                            showModalBottomSheet(
                              context: context,
                              isScrollControlled: true,
                              backgroundColor: Colors.transparent,
                              builder: (bCtx) => PostDetailSheet(post: post),
                            );
                          },
                        );
                      },
                    ),
                  );
                },
                loading: () => const LoadingShimmer(),
                error: (err, stack) => ErrorView(
                  message: '$err',
                  onRetry: () => ref.read(postListProvider.notifier).refresh(),
                ),
              ),
            ),
          ],
        );
      },
      loading: () => const LoadingShimmer(),
      error: (err, stack) => ErrorView(
        message: '$err',
        onRetry: () => ref.invalidate(forumListProvider),
      ),
    );
  }
}
