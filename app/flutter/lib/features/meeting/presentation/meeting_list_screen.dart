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
import '../../project/providers/project_provider.dart';
import '../data/models/meeting_model.dart';
import '../providers/meeting_provider.dart';
import 'widgets/meeting_card.dart';
import 'widgets/meeting_pdf_helper.dart';

/// 회의 목록 화면
class MeetingListScreen extends ConsumerStatefulWidget {
  const MeetingListScreen({super.key});

  @override
  ConsumerState<MeetingListScreen> createState() => _MeetingListScreenState();
}

class _MeetingListScreenState extends ConsumerState<MeetingListScreen> {
  final ScrollController _scrollController = ScrollController();
  _MeetingFilterMode _filterMode = _MeetingFilterMode.all;

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
      case _MeetingFilterMode.prepared:
        statusParam = '1';
        break;
      case _MeetingFilterMode.closed:
        statusParam = '2';
        break;
      case _MeetingFilterMode.cancelled:
        statusParam = '3';
        break;
      case _MeetingFilterMode.all:
        statusParam = null;
        break;
    }

    ref.read(meetingFilterProvider.notifier).state = MeetingFilterModel(
      projectSlug: project?.slug,
      status: statusParam,
      ordering: '-meeting_date',
    );
  }

  void _onFilterChanged(_MeetingFilterMode mode) {
    setState(() => _filterMode = mode);
    _applyFilter();
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(selectedProjectProvider, (previous, next) {
      _applyFilter();
    });

    final selectedProject = ref.watch(selectedProjectProvider);
    if (selectedProject != null) {
      final allProjects = ref.watch(projectListProvider).valueOrNull ?? [];
      final currentProj = allProjects
          .where((p) => p.slug == selectedProject.slug)
          .firstOrNull;
      final isMeetingModuleEnabled = currentProj?.module?.meeting ?? true;

      if (!isMeetingModuleEnabled) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: ErrorView.empty(
              message: '회의록 모듈이 비활성화되어 있습니다.',
              subMessage:
                  '${selectedProject.name} 워크스페이스는 회의록 기능을 사용하지 않습니다.',
            ),
          ),
        );
      }
    }

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
        // ── 필터 칩 바 (1: 준비, 2: 종료, 3: 취소) ──────────────────────────────
        Container(
          color: AppColors.bgSurface,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(
            children: [
              _FilterChip(
                label: '전체',
                selected: _filterMode == _MeetingFilterMode.all,
                onTap: () => _onFilterChanged(_MeetingFilterMode.all),
              ),
              const SizedBox(width: 8),
              _FilterChip(
                label: '준비',
                selected: _filterMode == _MeetingFilterMode.prepared,
                onTap: () => _onFilterChanged(_MeetingFilterMode.prepared),
              ),
              const SizedBox(width: 8),
              _FilterChip(
                label: '종료',
                selected: _filterMode == _MeetingFilterMode.closed,
                onTap: () => _onFilterChanged(_MeetingFilterMode.closed),
              ),
              const SizedBox(width: 8),
              _FilterChip(
                label: '취소',
                selected: _filterMode == _MeetingFilterMode.cancelled,
                onTap: () => _onFilterChanged(_MeetingFilterMode.cancelled),
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
                      onExportPdf: () => exportMeetingPdf(context, ref, meeting),
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

enum _MeetingFilterMode { all, prepared, closed, cancelled }

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
