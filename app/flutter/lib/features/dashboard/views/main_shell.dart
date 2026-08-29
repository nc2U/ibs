import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/constants/permissions.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/notification_provider.dart';
import '../../../core/providers/permission_provider.dart';
import '../../../core/providers/share_payload_provider.dart';
import '../../../core/router/app_router.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../../core/providers/badge_provider.dart';
import '../../../core/providers/dio_provider.dart';
import '../../../core/services/fcm_service.dart';
import '../../../core/services/sse_notification_service.dart';
import '../../../core/widgets/notification_sheet.dart';
import '../../../core/widgets/user_avatar.dart';
import '../../approval/providers/approval_providers.dart';
import '../../chat/providers/chat_provider.dart';
import '../../docs/presentation/widgets/document_form_sheet.dart';

import 'dart:async';

/// ShellRoute 메인 래퍼
/// - 하단 탭바를 모든 탭에서 유지 (홈 / 업무 / 프로젝트 / 채널)
/// - AppBar 우측: 알림 아이콘 + 아바타(내 설정 진입)
/// - 앱 라이프사이클 및 30초 주기 알림/뱃지 자동 동기화
class MainShell extends ConsumerStatefulWidget {
  final Widget child;
  const MainShell({super.key, required this.child});

  @override
  ConsumerState<MainShell> createState() => _MainShellState();
}

class _MainShellState extends ConsumerState<MainShell> {
  static const _tabs = [
    _TabItem(route: AppRoutes.home,     icon: Icons.grid_view_rounded,       label: '홈'),
    _TabItem(route: AppRoutes.work,     icon: Icons.assignment_rounded,       label: '업무'),
    _TabItem(route: AppRoutes.project,  icon: Icons.business_center_rounded,  label: '프로젝트'),
    _TabItem(route: AppRoutes.approval, icon: Icons.draw_rounded,             label: '전자결재'),
    _TabItem(route: AppRoutes.channel,  icon: Icons.campaign_rounded,         label: '채널'),
  ];

  Timer? _syncTimer;
  late final AppLifecycleListener _lifecycleListener;

  @override
  void initState() {
    super.initState();
    // 1. 앱 포그라운드 복귀 시 알림 & 결재 대기 즉시 동기화
    _lifecycleListener = AppLifecycleListener(
      onResume: _syncData,
      onShow: _syncData,
    );

    // 2. 앱 실행 중 15초 주기 자동 동기화
    _syncTimer = Timer.periodic(const Duration(seconds: 15), (_) {
      _syncData();
    });
  }

  void _syncData() {
    if (!mounted) return;
    ref.read(notificationListProvider.notifier).fetchNotifications();
    ref.invalidate(pendingApprovalsProvider);
  }

  @override
  void dispose() {
    _syncTimer?.cancel();
    _lifecycleListener.dispose();
    super.dispose();
  }

  int _currentIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    for (var i = 0; i < _tabs.length; i++) {
      if (location.startsWith(_tabs[i].route)) return i;
    }
    return 0;
  }

  void _onTabTap(BuildContext context, int index) {
    if (index == 3) {
      // 전자결재 탭 진입 시 대기 목록 즉시 갱신
      ref.invalidate(pendingApprovalsProvider);
    }
    context.go(_tabs[index].route);
  }

  @override
  Widget build(BuildContext context) {
    final currentIdx = _currentIndex(context);

    // 앱 아이콘 알림 뱃지 자동 동기화 (미확인 알림 + 미결 결재)
    final totalBadgeCount = ref.watch(totalAppBadgeCountProvider);
    final pendingCount = ref.watch(pendingApprovalCountProvider);

    // 실시간 SSE 알림 스트림 연결 유지 (웹과 동일한 0.1초 즉시 동기화)
    ref.watch(sseNotificationServiceProvider);

    // FCM 푸시 알림 서비스 초기화 (로그인된 세션)
    final dio = ref.watch(dioProvider);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      FcmService.initialize(dio);
    });

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
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        backgroundColor: context.colors.bgPrimary,
        foregroundColor: context.colors.textPrimary,
        elevation: 0,
        titleSpacing: 16,
        title: Row(
          children: [
            SvgPicture.asset(
              context.isDarkMode
                  ? 'assets/images/sygnet.svg'
                  : 'assets/images/sygnet_light.svg',
              width: 26,
              height: 26,
            ),
            const SizedBox(width: 10),
            Text(
              'IBS 워크스페이스',
              style: AppTextStyles.titleMd.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        actions: [
          // ── 💬 실시간 메신저 바로가기 및 미확인 메시지 배지 ───────────────────
          Consumer(
            builder: (ctx, ref, _) {
              final unreadChatCount = ref.watch(totalUnreadChatCountProvider).valueOrNull ?? 0;
              return Stack(
                alignment: Alignment.center,
                children: [
                  IconButton(
                    icon: Icon(
                      unreadChatCount > 0 ? Icons.chat_rounded : Icons.chat_outlined,
                      size: 22,
                      color: unreadChatCount > 0
                          ? context.colors.accentWork
                          : context.colors.textMuted,
                    ),
                    tooltip: '실시간 메신저',
                    onPressed: () {
                      ref.invalidate(chatRoomsProvider);
                      ref.invalidate(totalUnreadChatCountProvider);
                      context.push(AppRoutes.chat);
                    },
                  ),
                  if (unreadChatCount > 0)
                    Positioned(
                      top: 8,
                      right: 8,
                      child: Container(
                        padding: const EdgeInsets.all(3.5),
                        decoration: const BoxDecoration(
                          color: Colors.redAccent,
                          shape: BoxShape.circle,
                        ),
                        child: Text(
                          unreadChatCount > 99 ? '99+' : '$unreadChatCount',
                          style: const TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                            height: 1,
                          ),
                        ),
                      ),
                    ),
                ],
              );
            },
          ),

          // ── 🔔 알림 센터 ──────────────────────────────────────────
          Stack(
            alignment: Alignment.center,
            children: [
              IconButton(
                icon: Icon(
                  totalBadgeCount > 0
                      ? Icons.notifications_active_rounded
                      : Icons.notifications_none_rounded,
                  size: 23,
                  color: totalBadgeCount > 0
                      ? context.colors.accentWork
                      : context.colors.textMuted,
                ),
                tooltip: '알림 센터',
                onPressed: () {
                  ref.read(notificationListProvider.notifier).fetchNotifications();
                  ref.invalidate(pendingApprovalsProvider);
                  NotificationSheet.show(context);
                },
              ),
              if (totalBadgeCount > 0)
                Positioned(
                  top: 8,
                  right: 8,
                  child: Container(
                    padding: const EdgeInsets.all(3.5),
                    decoration: BoxDecoration(
                      color: context.colors.accentWork,
                      shape: BoxShape.circle,
                    ),
                    child: Text(
                      totalBadgeCount > 99 ? '99+' : '$totalBadgeCount',
                      style: const TextStyle(
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                        height: 1,
                      ),
                    ),
                  ),
                ),
            ],
          ),
          Consumer(
            builder: (ctx, ref, _) {
              final currentUser = ref.watch(currentUserProvider).valueOrNull;
              return GestureDetector(
                onTap: () => context.push(AppRoutes.profile),
                child: Padding(
                  padding: const EdgeInsets.only(left: 4, right: 16),
                  child: UserAvatar(
                    user: currentUser,
                    radius: 15,
                  ),
                ),
              );
            },
          ),
        ],
      ),
      body: widget.child,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: currentIdx,
        onTap: (i) => _onTabTap(context, i),
        type: BottomNavigationBarType.fixed,
        backgroundColor: context.colors.bgSurface,
        selectedItemColor: context.colors.accentWork,
        unselectedItemColor: context.colors.textDisabled,
        selectedLabelStyle:
            const TextStyle(fontWeight: FontWeight.bold, fontSize: 11),
        unselectedLabelStyle: const TextStyle(fontSize: 11),
        elevation: 8,
        items: _tabs.map((t) {
          Widget iconWidget = Icon(t.icon);
          if (t.route == AppRoutes.approval && pendingCount > 0) {
            iconWidget = Badge(
              label: Text('$pendingCount', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
              backgroundColor: context.colors.error,
              child: Icon(t.icon),
            );
          }
          return BottomNavigationBarItem(
            icon: iconWidget,
            label: t.label,
          );
        }).toList(),
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
