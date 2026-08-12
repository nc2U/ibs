import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/widgets/error_view.dart';
import '../../../core/widgets/loading_shimmer.dart';
import '../data/models/issue_model.dart';
import '../providers/issue_provider.dart';
import 'widgets/done_ratio_bottom_sheet.dart';
import 'widgets/issue_card.dart';

/// 업무 목록 화면
/// - 상단 필터 칩: 내 업무 / 전체 / 완료 포함
/// - 현장 선택 시 자동 project 필터 적용
/// - 무한 스크롤 페이지네이션
class IssueListScreen extends ConsumerStatefulWidget {
  const IssueListScreen({super.key});

  @override
  ConsumerState<IssueListScreen> createState() => _IssueListScreenState();
}

class _IssueListScreenState extends ConsumerState<IssueListScreen> {
  final ScrollController _scrollController = ScrollController();
  _FilterMode _filterMode = _FilterMode.mine;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    // 초기 필터 적용
    WidgetsBinding.instance.addPostFrameCallback((_) => _applyFilter());
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      ref.read(issueListProvider.notifier).loadMore();
    }
  }

  void _applyFilter() {
    final project = ref.read(selectedProjectProvider);
    IssueFilterModel filter;

    switch (_filterMode) {
      case _FilterMode.mine:
        // 내 업무 + 미완료 (closed 상태 제외)
        filter = IssueFilterModel(
          projectSlug: project?.slug,
          ordering: '-updated',
        );
        break;
      case _FilterMode.all:
        filter = IssueFilterModel(
          projectSlug: project?.slug,
          ordering: '-updated',
        );
        break;
      case _FilterMode.withClosed:
        filter = IssueFilterModel(
          projectSlug: project?.slug,
          ordering: '-updated',
        );
        break;
    }

    ref.read(issueFilterProvider.notifier).state = filter;
  }

  void _onFilterChanged(_FilterMode mode) {
    setState(() => _filterMode = mode);
    _applyFilter();
  }

  @override
  Widget build(BuildContext context) {
    final issueState = ref.watch(issueListProvider);

    return Column(
      children: [
        // ── 필터 칩 바 ──────────────────────────────────────────────────────────
        Container(
          color: AppColors.bgSurface,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(
            children: [
              _FilterChip(
                label: '내 업무',
                selected: _filterMode == _FilterMode.mine,
                onTap: () => _onFilterChanged(_FilterMode.mine),
              ),
              const SizedBox(width: 8),
              _FilterChip(
                label: '전체 업무',
                selected: _filterMode == _FilterMode.all,
                onTap: () => _onFilterChanged(_FilterMode.all),
              ),
              const SizedBox(width: 8),
              _FilterChip(
                label: '완료 포함',
                selected: _filterMode == _FilterMode.withClosed,
                onTap: () => _onFilterChanged(_FilterMode.withClosed),
              ),
            ],
          ),
        ),

        // ── 업무 목록 ────────────────────────────────────────────────────────────
        Expanded(
          child: issueState.when(
            loading: () => const LoadingShimmer(),
            error: (e, _) => ErrorView.network(
              onRetry: () => ref.invalidate(issueListProvider),
            ),
            data: (state) {
              if (state.items.isEmpty) {
                return const ErrorView.empty(
                  message: '할당된 업무가 없습니다.',
                  subMessage: '현장을 선택하거나 필터를 변경해 보세요.',
                );
              }

              return RefreshIndicator(
                color: AppColors.accentWork,
                backgroundColor: AppColors.bgCard,
                onRefresh: () =>
                    ref.read(issueListProvider.notifier).refresh(),
                child: ListView.separated(
                  controller: _scrollController,
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 12),
                  itemCount:
                      state.items.length + (state.hasMore ? 1 : 0),
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (ctx, index) {
                    if (index >= state.items.length) {
                      return const Padding(
                        padding: EdgeInsets.symmetric(vertical: 16),
                        child: Center(
                          child: CircularProgressIndicator(
                              color: AppColors.accentWork),
                        ),
                      );
                    }
                    final issue = state.items[index];
                    return IssueCard(
                      issue: issue,
                      onTap: () => context.go(
                          '/work/issues/${issue.pk}'),
                      onDoneRatioTap: () =>
                          showDoneRatioBottomSheet(
                        context: context,
                        ref: ref,
                        issueId: issue.pk,
                        currentRatio: issue.doneRatio,
                      ),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

// ── 필터 모드 ──────────────────────────────────────────────────────────────────
enum _FilterMode { mine, all, withClosed }

// ── 필터 칩 위젯 ───────────────────────────────────────────────────────────────
class _FilterChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _FilterChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: selected
              ? AppColors.accentWork.withAlpha(40)
              : AppColors.bgCard,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: selected ? AppColors.accentWork : AppColors.border,
            width: selected ? 1.5 : 0.8,
          ),
        ),
        child: Text(
          label,
          style: AppTextStyles.label.copyWith(
            color: selected ? AppColors.accentWork : AppColors.textMuted,
          ),
        ),
      ),
    );
  }
}
