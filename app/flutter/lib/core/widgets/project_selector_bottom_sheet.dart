import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants/app_colors.dart';
import '../constants/app_text_styles.dart';
import '../providers/project_provider.dart';
import '../../features/issue/providers/issue_provider.dart';
import '../../features/meeting/providers/meeting_provider.dart';
import '../../features/project/data/models/project_model.dart';
import '../../features/project/providers/project_provider.dart';

/// 프로젝트 선택 바텀시트
void showProjectSelectorBottomSheet(BuildContext context) {
  showModalBottomSheet(
    context: context,
    backgroundColor: AppColors.bgCard,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (ctx) => const _ProjectSelectorContent(),
  );
}

class _ProjectSelectorContent extends ConsumerWidget {
  const _ProjectSelectorContent();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedProject = ref.watch(selectedProjectProvider);
    final projectsAsync = ref.watch(projectListProvider);

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── 드래그 핸들 ──────────────────────────────────────────────────────────
        Center(
          child: Container(
            margin: const EdgeInsets.only(top: 8, bottom: 12),
            width: 36,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.textDisabled,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ),

        // ── 헤더 ────────────────────────────────────────────────────────────────
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          child: Text('프로젝트 선택', style: AppTextStyles.titleMd),
        ),
        const Divider(color: AppColors.border, height: 16),

        // ── 목록 ────────────────────────────────────────────────────────────────
        Expanded(
          child: projectsAsync.when(
            loading: () => const Center(
              child: CircularProgressIndicator(color: AppColors.accentWork),
            ),
            error: (e, _) => Center(
              child: Text('프로젝트 목록을 불러올 수 없습니다.',
                  style: AppTextStyles.bodyMuted),
            ),
            data: (projects) {
              return ListView(
                padding: const EdgeInsets.symmetric(vertical: 4),
                children: [
                  // Option: 전사 공통
                  _ProjectTile(
                    title: '🏢 전사 공통 (전체 프로젝트)',
                    isSelected: selectedProject == null,
                    onTap: () {
                      selectProject(ref, null);
                      _refreshProviders(ref);
                      Navigator.pop(context);
                    },
                  ),
                  const Divider(color: AppColors.border, height: 1),

                  // Option: 각 프로젝트들
                  ...projects.map(
                    (p) => _ProjectTile(
                      title: p.name,
                      subtitle: p.slug,
                      isSelected: selectedProject?.pk == p.pk,
                      onTap: () {
                        selectProject(ref, p);
                        _refreshProviders(ref);
                        Navigator.pop(context);
                      },
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }

  void _refreshProviders(WidgetRef ref) {
    // 선택된 프로젝트에 맞춰 issueList 및 meetingList 필터 업데이트 & 새로고침
    final project = ref.read(selectedProjectProvider);

    final issueFilter = ref.read(issueFilterProvider);
    ref.read(issueFilterProvider.notifier).state = issueFilter.copyWith(
      projectSlug: project?.slug,
      clearProjectSlug: project == null,
    );

    final meetingFilter = ref.read(meetingFilterProvider);
    ref.read(meetingFilterProvider.notifier).state = meetingFilter.copyWith(
      projectSlug: project?.slug,
      clearProjectSlug: project == null,
    );
  }
}

class _ProjectTile extends StatelessWidget {
  final String title;
  final String? subtitle;
  final bool isSelected;
  final VoidCallback onTap;

  const _ProjectTile({
    required this.title,
    this.subtitle,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(
        title,
        style: AppTextStyles.bodyMd.copyWith(
          color: isSelected ? AppColors.accentWork : AppColors.textPrimary,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        ),
      ),
      subtitle: subtitle != null
          ? Text(subtitle!, style: AppTextStyles.caption)
          : null,
      trailing: isSelected
          ? const Icon(Icons.check_circle_rounded,
              color: AppColors.accentWork, size: 20)
          : null,
      onTap: onTap,
    );
  }
}
