import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../../providers/notice_provider.dart';
import 'notice_card.dart';
import 'notice_detail_sheet.dart';

/// 공지사항 탭 뷰 (검색 + 목록 + 페이징 + 권한 제어)
class NoticeListView extends ConsumerStatefulWidget {
  const NoticeListView({super.key});

  @override
  ConsumerState<NoticeListView> createState() => _NoticeListViewState();
}

class _NoticeListViewState extends ConsumerState<NoticeListView> {
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
      ref.read(noticeListProvider.notifier).loadMore();
    }
  }

  void _onSearch(String query) {
    ref.read(noticeSearchProvider.notifier).state = query.trim();
  }

  @override
  Widget build(BuildContext context) {
    final canRead = ref.can(Perm.newsRead);
    if (!canRead) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24.0),
          child: ErrorView.empty(
            message: '공지사항을 조회할 권한이 없습니다.',
            subMessage: '관리자에게 [공지사항 열람] 권한(news.read)을 요청해 주세요.',
          ),
        ),
      );
    }

    final noticeListAsync = ref.watch(noticeListProvider);
    final selectedProject = ref.watch(selectedProjectProvider);

    return Column(
      children: [
        // ── 1. 검색 바 ───────────────────────────────────────────────
        Container(
          color: context.colors.bgSurface,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: TextField(
            controller: _searchController,
            onSubmitted: _onSearch,
            textInputAction: TextInputAction.search,
            style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
            decoration: InputDecoration(
              hintText: '공지 제목, 요약, 본문 내용 검색',
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

        // ── 2. 공지 목록 본문 ─────────────────────────────────────────
        Expanded(
          child: noticeListAsync.when(
            data: (data) {
              if (data.results.isEmpty) {
                return const ErrorView(
                  message: '등록된 공지사항이 없습니다.',
                  icon: Icons.campaign_outlined,
                );
              }

              return RefreshIndicator(
                onRefresh: () =>
                    ref.read(noticeListProvider.notifier).refresh(),
                child: ListView.separated(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: data.results.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (ctx, index) {
                    final notice = data.results[index];
                    return NoticeCard(
                      notice: notice,
                      showWorkspaceBadge: selectedProject == null,
                      onTap: () {
                        if (!ref.can(Perm.newsRead)) return;
                        showModalBottomSheet(
                          context: context,
                          isScrollControlled: true,
                          backgroundColor: Colors.transparent,
                          builder: (bCtx) =>
                              NoticeDetailSheet(notice: notice),
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
              onRetry: () => ref.read(noticeListProvider.notifier).refresh(),
            ),
          ),
        ),
      ],
    );
  }
}
