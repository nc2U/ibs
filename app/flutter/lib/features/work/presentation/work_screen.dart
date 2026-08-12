import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/widgets/project_selector_bottom_sheet.dart';
import '../../issue/presentation/issue_list_screen.dart';
import '../../meeting/presentation/meeting_list_screen.dart';

/// 업무 관리 탭 메인 화면 (프로젝트 셀렉터 + 회의 목록 / 업무 목록 탭 전환 + 생성 FAB)
class WorkScreen extends ConsumerWidget {
  final int initialIndex;
  const WorkScreen({super.key, this.initialIndex = 0});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projectName = ref.watch(selectedProjectNameProvider);

    return DefaultTabController(
      length: 2,
      initialIndex: initialIndex,
      child: Scaffold(
        backgroundColor: AppColors.bgPrimary,
        body: Column(
          children: [
            // ── 프로젝트 선택 바 ─────────────────────────────────────
            InkWell(
              onTap: () => showProjectSelectorBottomSheet(context),
              child: Container(
                color: AppColors.bgSurface,
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  children: [
                    const Icon(Icons.business_center_rounded,
                        size: 16, color: AppColors.accentProject),
                    const SizedBox(width: 8),
                    Text(
                      '프로젝트:',
                      style: AppTextStyles.caption
                          .copyWith(color: AppColors.textMuted),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        projectName,
                        style: AppTextStyles.titleSm
                            .copyWith(color: AppColors.accentProject),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppColors.accentProject.withAlpha(25),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(
                            color: AppColors.accentProject.withAlpha(60)),
                      ),
                      child: Row(
                        children: [
                          Text('프로젝트 변경',
                              style: AppTextStyles.label
                                  .copyWith(color: AppColors.accentProject)),
                          const Icon(Icons.keyboard_arrow_down_rounded,
                              size: 16, color: AppColors.accentProject),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const Divider(color: AppColors.border, height: 1),

            // ── 상단 탭바 (회의 목록 | 업무 목록) ───────────────────────────
            Container(
              color: AppColors.bgSurface,
              child: TabBar(
                indicatorColor: AppColors.accentWork,
                indicatorWeight: 3,
                labelColor: AppColors.accentWork,
                unselectedLabelColor: AppColors.textMuted,
                labelStyle: AppTextStyles.titleSm,
                unselectedLabelStyle: AppTextStyles.bodyMd,
                tabs: const [
                  Tab(text: '회의 목록'),
                  Tab(text: '업무 목록'),
                ],
              ),
            ),
            const Expanded(
              child: TabBarView(
                children: [
                  MeetingListScreen(),
                  IssueListScreen(),
                ],
              ),
            ),
          ],
        ),
        floatingActionButton: Builder(
          builder: (ctx) {
            return SizedBox(
              height: 40,
              child: FloatingActionButton.extended(
                elevation: 3,
                highlightElevation: 6,
                backgroundColor: const Color(0xFF3565A6),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                extendedPadding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 0),
                icon: const Icon(Icons.add_rounded,
                    size: 18, color: Colors.white),
                label: Builder(
                  builder: (tabCtx) {
                    final controller = DefaultTabController.of(tabCtx);
                    return ListenableBuilder(
                      listenable: controller,
                      builder: (context, child) {
                        return Text(
                          controller.index == 0 ? '회의 등록' : '업무 등록',
                          style: AppTextStyles.bodyMd.copyWith(
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        );
                      },
                    );
                  },
                ),
                onPressed: () {
                  final controller = DefaultTabController.of(ctx);
                  if (controller.index == 0) {
                    context.push('/work/meetings/new');
                  } else {
                    context.push('/work/issues/new');
                  }
                },
              ),
            );
          },
        ),
      ),
    );
  }
}
