import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants/app_colors.dart';
import '../constants/app_text_styles.dart';
import '../providers/project_provider.dart';
import 'project_selector_bottom_sheet.dart';

/// 앱 공용 워크스페이스 / 프로젝트 선택 상단 바 위젯 (radius = 0)
/// - Work Core (업무 관리), Channel (공지/게시판), Project (프로젝트 관리) 공용
class WorkspaceSelectorBar extends ConsumerWidget {
  /// 부동산 개발 프로젝트(type == '2')만 필터링할지 여부 (IBS Global 전용)
  final bool onlyRealEstate;

  /// 우측 추가 위젯 (예: 업무 화면의 문서함 전환 버튼 등)
  final Widget? trailing;

  /// 프로젝트 선택 후 콜백
  final VoidCallback? onProjectChanged;

  const WorkspaceSelectorBar({
    super.key,
    this.onlyRealEstate = false,
    this.trailing,
    this.onProjectChanged,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedProject = ref.watch(selectedProjectProvider);
    final projectName = ref.watch(selectedProjectNameProvider);

    final displayName = onlyRealEstate
        ? (selectedProject?.name ?? '프로젝트를 선택하세요')
        : projectName;

    final badgeLabel = onlyRealEstate ? '프로젝트 변경' : '워크스페이스 변경';

    return InkWell(
      onTap: () {
        showProjectSelectorBottomSheet(
          context,
          onlyRealEstate: onlyRealEstate,
        );
        onProjectChanged?.call();
      },
      child: Container(
        color: AppColors.bgSurface,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Row(
          children: [
            const Icon(
              Icons.business_center_rounded,
              size: 18,
              color: AppColors.accentProject,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                displayName,
                style: AppTextStyles.titleSm.copyWith(
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.accentProject.withAlpha(20),
                borderRadius: BorderRadius.zero,
                border: Border.all(
                  color: AppColors.accentProject.withAlpha(60),
                  width: 0.8,
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    badgeLabel,
                    style: AppTextStyles.label.copyWith(
                      color: AppColors.accentProject,
                      fontSize: 11,
                    ),
                  ),
                  const SizedBox(width: 2),
                  const Icon(
                    Icons.keyboard_arrow_down_rounded,
                    size: 15,
                    color: AppColors.accentProject,
                  ),
                ],
              ),
            ),
            if (trailing != null) ...[
              const SizedBox(width: 8),
              trailing!,
            ],
          ],
        ),
      ),
    );
  }
}
