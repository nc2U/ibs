import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/constants/permissions.dart';
import '../../../core/providers/permission_provider.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/widgets/error_view.dart';
import '../../../core/widgets/loading_shimmer.dart';
import '../data/models/issue_model.dart';
import '../providers/issue_provider.dart';
import 'widgets/done_ratio_bottom_sheet.dart';
import 'widgets/issue_card.dart';

/// 업무 목록 화면
/// - 상단 필터 칩: 내 업무 / 전체 / 완료 포함
/// - 프로젝트 선택 시 자동 project 필터 적용
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
        // 내 업무 중 진행 중인 업무 (assigned_to=me, status__closed=false)
        filter = IssueFilterModel(
          assignedTo: 'me',
          statusClosed: false,
          projectSlug: project?.slug,
          ordering: '-updated',
        );
        break;
      case _FilterMode.inProgress:
        // 전체 업무 중 진행 중인 업무 (status__closed=false)
        filter = IssueFilterModel(
          statusClosed: false,
          projectSlug: project?.slug,
          ordering: '-updated',
        );
        break;
      case _FilterMode.completed:
        // 전체 업무 중 완료된 업무 (status__closed=true)
        filter = IssueFilterModel(
          statusClosed: true,
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
    ref.listen(selectedProjectProvider, (previous, next) {
      _applyFilter();
    });

    final canRead = ref.can(Perm.issueRead);
    if (!canRead) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24.0),
          child: ErrorView.empty(
            message: '업무 목록을 조회할 권한이 없습니다.',
            subMessage: '관리자에게 [업무 열람] 권한을 요청해 주세요.',
          ),
        ),
      );
    }

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
                label: '진행 중',
                selected: _filterMode == _FilterMode.inProgress,
                onTap: () => _onFilterChanged(_FilterMode.inProgress),
              ),
              const SizedBox(width: 8),
              _FilterChip(
                label: '완료됨',
                selected: _filterMode == _FilterMode.completed,
                onTap: () => _onFilterChanged(_FilterMode.completed),
              ),
            ],
          ),
        ),

        // ── 업무 목록 ────────────────────────────────────────────────────────────
        Expanded(
          child: issueState.when(
            loading: () => const LoadingShimmer(),
            error: (e, _) => ErrorView.network(
              subMessage: e.toString(),
              onRetry: () => ref.invalidate(issueListProvider),
            ),
            data: (state) {
              if (state.items.isEmpty) {
                final emptyMsg = _filterMode == _FilterMode.mine
                    ? '진행 중인 내 업무가 없습니다.'
                    : (_filterMode == _FilterMode.inProgress
                        ? '진행 중인 업무가 없습니다.'
                        : '완료된 업무가 없습니다.');
                return ErrorView.empty(
                  message: emptyMsg,
                  subMessage: '프로젝트를 선택하거나 필터를 변경해 보세요.',
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
                      onTap: () => context.push(
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
enum _FilterMode { mine, inProgress, completed }

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
