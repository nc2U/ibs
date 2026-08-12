import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/router/app_router.dart';
import '../../../core/widgets/project_selector_bottom_sheet.dart';

/// ShellRoute 메인 래퍼
/// - 하단 탭바를 모든 탭에서 유지
/// - AppBar에 현재 선택된 프로젝트명 항상 노출
class MainShell extends ConsumerWidget {
  final Widget child;
  const MainShell({super.key, required this.child});

  static const _tabs = [
    _TabItem(route: AppRoutes.home,     icon: Icons.grid_view_rounded,        label: '홈'),
    _TabItem(route: AppRoutes.work,     icon: Icons.assignment_rounded,        label: '업무관리'),
    _TabItem(route: AppRoutes.project,  icon: Icons.business_center_rounded,   label: '프로젝트'),
    _TabItem(route: AppRoutes.approval, icon: Icons.draw_rounded,              label: '전자결재'),
    _TabItem(route: AppRoutes.docs,     icon: Icons.folder_shared_rounded,     label: '공용문서'),
  ];

  int _currentIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    for (var i = 0; i < _tabs.length; i++) {
      if (location.startsWith(_tabs[i].route)) return i;
    }
    return 0;
  }

  void _onTabTap(BuildContext context, int index) {
    context.go(_tabs[index].route);
  }

  Future<void> _handleLogout(BuildContext context, WidgetRef ref) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: Text('로그아웃', style: AppTextStyles.titleLg),
        content: Text('IBS 워크스페이스에서\n로그아웃 하시겠습니까?', style: AppTextStyles.bodySecond),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: AppTextStyles.bodyMuted),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text('로그아웃'),
          ),
        ],
      ),
    );
    if (confirm == true) {
      await ref.read(authProvider.notifier).logout();
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projectName = ref.watch(selectedProjectNameProvider);
    final currentIdx = _currentIndex(context);

    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      appBar: AppBar(
        backgroundColor: AppColors.bgPrimary,
        foregroundColor: AppColors.textPrimary,
        elevation: 0,
        titleSpacing: 16,
        title: Row(
          children: [
            SvgPicture.asset('assets/images/sygnet.svg', width: 26, height: 26),
            const SizedBox(width: 10),
            InkWell(
              onTap: () => showProjectSelectorBottomSheet(context),
              borderRadius: BorderRadius.circular(4),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('IBS 워크스페이스', style: AppTextStyles.titleMd),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(projectName,
                            style: AppTextStyles.caption
                                .copyWith(color: AppColors.accentWork)),
                        const SizedBox(width: 2),
                        const Icon(Icons.arrow_drop_down_rounded,
                            size: 16, color: AppColors.accentWork),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded, size: 24, color: AppColors.textMuted),
            tooltip: '알림',
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.logout_rounded, size: 22, color: AppColors.textMuted),
            tooltip: '로그아웃',
            onPressed: () => _handleLogout(context, ref),
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: child,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: currentIdx,
        onTap: (i) => _onTabTap(context, i),
        type: BottomNavigationBarType.fixed,
        backgroundColor: AppColors.bgSurface,
        selectedItemColor: AppColors.accentWork,
        unselectedItemColor: AppColors.textDisabled,
        selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11),
        unselectedLabelStyle: const TextStyle(fontSize: 11),
        elevation: 12,
        items: _tabs
            .map((t) => BottomNavigationBarItem(icon: Icon(t.icon), label: t.label))
            .toList(),
      ),
    );
  }
}

class _TabItem {
  final String route;
  final IconData icon;
  final String label;
  const _TabItem({required this.route, required this.icon, required this.label});
}
