import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/constants/permissions.dart';
import '../../../core/providers/permission_provider.dart';
import '../../../core/providers/share_payload_provider.dart';
import '../../../core/router/app_router.dart';
import '../../docs/presentation/widgets/document_form_sheet.dart';

/// ShellRoute 메인 래퍼
/// - 하단 탭바를 모든 탭에서 유지 (홈 / 업무 / 프로젝트 / 채널)
/// - AppBar 우측: 알림 아이콘 + 아바타(내 설정 진입)
class MainShell extends ConsumerWidget {
  final Widget child;
  const MainShell({super.key, required this.child});

  static const _tabs = [
    _TabItem(route: AppRoutes.home,     icon: Icons.grid_view_rounded,       label: '홈'),
    _TabItem(route: AppRoutes.work,     icon: Icons.assignment_rounded,       label: '업무'),
    _TabItem(route: AppRoutes.project,  icon: Icons.business_center_rounded,  label: '프로젝트'),
    _TabItem(route: AppRoutes.approval, icon: Icons.draw_rounded,             label: '전자결재'),
    _TabItem(route: AppRoutes.channel,  icon: Icons.campaign_rounded,         label: '채널'),
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

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentIdx = _currentIndex(context);

    // 외부 앱에서 공유된 파일/링크가 있을 때 문서 등록 모달 자동 팝업 (docs.create 권한 검증)
    ref.listen<SharePayload?>(pendingSharePayloadProvider, (prev, next) {
      if (next != null && next.isNotEmpty) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!context.mounted) return;
          if (!ref.can(Perm.docsCreate)) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content:
                    Text('문서 등록 권한(docs.create)이 없어 공유된 문서를 등록할 수 없습니다.'),
                backgroundColor: AppColors.error,
              ),
            );
            ref.read(pendingSharePayloadProvider.notifier).clear();
            return;
          }
          showModalBottomSheet(
            context: context,
            isScrollControlled: true,
            useRootNavigator: true,
            backgroundColor: Colors.transparent,
            builder: (ctx) => DocumentFormSheet(
              initialFiles: next.files,
              initialLinks: next.links,
              initialTitle: next.defaultTitle,
            ),
          );
          ref.read(pendingSharePayloadProvider.notifier).clear();
        });
      }
    });

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
            Text('IBS 웍스', style: AppTextStyles.titleMd),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded,
                size: 24, color: AppColors.textMuted),
            tooltip: '알림',
            onPressed: () {},
          ),
          GestureDetector(
            onTap: () => context.push(AppRoutes.profile),
            child: Padding(
              padding: const EdgeInsets.only(left: 4, right: 16),
              child: CircleAvatar(
                radius: 15,
                backgroundColor: AppColors.accentWork.withAlpha(45),
                child: Text(
                  'A',
                  style: TextStyle(
                    color: AppColors.accentWork,
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
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
        selectedLabelStyle:
            const TextStyle(fontWeight: FontWeight.bold, fontSize: 11),
        unselectedLabelStyle: const TextStyle(fontSize: 11),
        elevation: 12,
        items: _tabs
            .map((t) => BottomNavigationBarItem(
                  icon: Icon(t.icon),
                  label: t.label,
                ))
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
