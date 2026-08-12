import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../issue/presentation/issue_list_screen.dart';
import '../../meeting/presentation/meeting_list_screen.dart';

/// 업무 관리 탭 메인 화면 (회의 목록 / 업무 목록 탭 전환 + 생성 FAB)
class WorkScreen extends StatelessWidget {
  final int initialIndex;
  const WorkScreen({super.key, this.initialIndex = 0});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      initialIndex: initialIndex,
      child: Scaffold(
        backgroundColor: AppColors.bgPrimary,
        body: Column(
          children: [
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
            return FloatingActionButton.extended(
              backgroundColor: AppColors.accentWork,
              foregroundColor: Colors.white,
              icon: const Icon(Icons.add_rounded),
              label: Builder(
                builder: (tabCtx) {
                  final controller = DefaultTabController.of(tabCtx);
                  return ListenableBuilder(
                    listenable: controller,
                    builder: (context, child) {
                      return Text(
                        controller.index == 0 ? '회의 등록' : '업무 등록',
                        style: AppTextStyles.titleSm,
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
            );
          },
        ),
      ),
    );
  }
}
