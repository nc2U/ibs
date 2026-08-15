import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants/app_colors.dart';
import '../constants/app_text_styles.dart';
import '../providers/project_provider.dart';
import '../../features/issue/providers/issue_provider.dart';
import '../../features/meeting/providers/meeting_provider.dart';
import '../../features/project/providers/project_provider.dart';

/// 선택 바텀시트
/// - onlyRealEstate: false (Work Core) -> 워크스페이스 선택 (모든 타입)
/// - onlyRealEstate: true (IBS Global) -> 프로젝트 선택 (type == '2' 부동산 개발만)
void showProjectSelectorBottomSheet(BuildContext context,
    {bool onlyRealEstate = false}) {
  showModalBottomSheet(
    context: context,
    backgroundColor: AppColors.bgCard,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (ctx) => _ProjectSelectorContent(onlyRealEstate: onlyRealEstate),
  );
}

class _ProjectSelectorContent extends ConsumerWidget {
  final bool onlyRealEstate;
  const _ProjectSelectorContent({required this.onlyRealEstate});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedProject = ref.watch(selectedProjectProvider);
    final projectsAsync = ref.watch(
        onlyRealEstate ? realEstateProjectsProvider : activeWorkspaceListProvider);

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
          child: Text(
            onlyRealEstate ? '프로젝트 선택' : '워크스페이스 선택',
            style: AppTextStyles.titleMd,
          ),
        ),
        const Divider(color: AppColors.border, height: 16),

        // ── 목록 ────────────────────────────────────────────────────────────────
        Expanded(
          child: projectsAsync.when(
            loading: () => const Center(
              child: CircularProgressIndicator(color: AppColors.accentWork),
            ),
            error: (e, _) => Center(
              child: Text('목록을 불러올 수 없습니다: $e',
                  style: AppTextStyles.bodyMuted),
            ),
            data: (projects) {
              if (projects.isEmpty) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Text(
                      onlyRealEstate
                          ? '소속된 부동산 개발 프로젝트가 없습니다.\n(관리자에게 프로젝트 멤버 등록을 요청해 주세요)'
                          : '등록된 워크스페이스가 없습니다.',
                      textAlign: TextAlign.center,
                      style: AppTextStyles.bodyMuted.copyWith(height: 1.4),
                    ),
                  ),
                );
              }

              return ListView(
                padding: const EdgeInsets.symmetric(vertical: 4),
                children: [
                  // Option: 전체 워크스페이스 (워크스페이스 선택시에만 노출)
                  if (!onlyRealEstate) ...[
                    _ProjectTile(
                      title: '🏢 전체 워크스페이스',
                      isSelected: selectedProject == null,
                      onTap: () {
                        selectProject(ref, null);
                        _refreshProviders(ref);
                        Navigator.pop(context);
                      },
                    ),
                    const Divider(color: AppColors.border, height: 1),
                  ],

                  // Option: 항목들 (계층 구조 indentedLabel 적용)
                  ...projects.map(
                    (p) => _ProjectTile(
                      title: p.indentedLabel,
                      subtitle: p.type == '2' ? '부동산개발 · ${p.slug}' : p.slug,
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
