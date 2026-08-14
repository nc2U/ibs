import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../data/models/meeting_model.dart';
import '../providers/meeting_provider.dart';
import 'widgets/meeting_card.dart';

/// 회의 목록 화면
class MeetingListScreen extends ConsumerStatefulWidget {
  const MeetingListScreen({super.key});

  @override
  ConsumerState<MeetingListScreen> createState() => _MeetingListScreenState();
}

class _MeetingListScreenState extends ConsumerState<MeetingListScreen> {
  final ScrollController _scrollController = ScrollController();
  _FilterMode _filterMode = _FilterMode.all;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
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
      ref.read(meetingListProvider.notifier).loadMore();
    }
  }

  void _applyFilter() {
    final project = ref.read(selectedProjectProvider);
    String? statusParam;
    switch (_filterMode) {
      case _FilterMode.active:
        statusParam = '1';
        break;
      case _FilterMode.closed:
        statusParam = '2';
        break;
      case _FilterMode.all:
        statusParam = null;
        break;
    }

    ref.read(meetingFilterProvider.notifier).state = MeetingFilterModel(
      projectSlug: project?.slug,
      status: statusParam,
      ordering: '-meeting_date',
    );
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

    final canRead = ref.can(Perm.meetingRead);
    if (!canRead) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24.0),
          child: ErrorView.empty(
            message: '회의 목록을 조회할 권한이 없습니다.',
            subMessage: '관리자에게 [회의 열람] 권한을 요청해 주세요.',
          ),
        ),
      );
    }

    final meetingState = ref.watch(meetingListProvider);

    return Column(
      children: [
        // ── 필터 칩 바 ──────────────────────────────────────────────────────────
        Container(
          color: AppColors.bgSurface,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(
            children: [
              _FilterChip(
                label: '전체 회의',
                selected: _filterMode == _FilterMode.all,
                onTap: () => _onFilterChanged(_FilterMode.all),
              ),
              const SizedBox(width: 8),
              _FilterChip(
                label: '진행/예정',
                selected: _filterMode == _FilterMode.active,
                onTap: () => _onFilterChanged(_FilterMode.active),
              ),
              const SizedBox(width: 8),
              _FilterChip(
                label: '종료',
                selected: _filterMode == _FilterMode.closed,
                onTap: () => _onFilterChanged(_FilterMode.closed),
              ),
            ],
          ),
        ),

        // ── 회의 목록 ────────────────────────────────────────────────────────────
        Expanded(
          child: meetingState.when(
            loading: () => const LoadingShimmer(),
            error: (e, _) => ErrorView.network(
              subMessage: e.toString(),
              onRetry: () => ref.invalidate(meetingListProvider),
            ),
            data: (state) {
              if (state.items.isEmpty) {
                return const ErrorView.empty(
                  message: '등록된 회의가 없습니다.',
                  subMessage: '프로젝트를 선택하거나 필터를 변경해 보세요.',
                );
              }

              return RefreshIndicator(
                color: AppColors.accentWork,
                backgroundColor: AppColors.bgCard,
                onRefresh: () =>
                    ref.read(meetingListProvider.notifier).refresh(),
                child: ListView.separated(
                  controller: _scrollController,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  itemCount: state.items.length + (state.hasMore ? 1 : 0),
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
                    final meeting = state.items[index];
                    return MeetingCard(
                      meeting: meeting,
                      onTap: () => context.push('/work/meetings/${meeting.pk}'),
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

enum _FilterMode { all, active, closed }

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
