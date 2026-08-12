import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../issue/presentation/issue_list_screen.dart';
import '../../meeting/presentation/meeting_list_screen.dart';

/// 업무 관리 탭 메인 화면 (업무 목록 / 회의 목록 탭 전환)
class WorkScreen extends StatelessWidget {
  final int initialIndex;
  const WorkScreen({super.key, this.initialIndex = 0});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      initialIndex: initialIndex,
      child: Column(
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
                Tab(text: '업무 목록'),
                Tab(text: '회의 목록'),
              ],
            ),
          ),
          const Expanded(
            child: TabBarView(
              children: [
                IssueListScreen(),
                MeetingListScreen(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
