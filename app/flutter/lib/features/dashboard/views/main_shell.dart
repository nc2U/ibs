import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/notification_provider.dart';
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
import '../../todo/presentation/providers/todo_provider.dart';
import '../widgets/push_permission_prompt_modal.dart';

/// ShellRoute 메인 래퍼
/// - 하단 탭바를 모든 탭에서 유지 (홈 / 업무 / 프로젝트 / 채널)
/// - AppBar 우측: 알림 아이콘 + 아바타(내 설정 진입)
/// - 앱 라이프사이클 및 스마트 60초 주기 동기화 (백그라운드 진입 시 타이머 정지)
/// - 안드로이드 뒤로가기(PopScope) 탭 복귀 UX 지원
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
  bool _fcmInitialized = false;
  DateTime? _lastBackPressTime;
  DateTime? _lastSyncTime;

  @override
  void initState() {
    super.initState();
    // 1. 앱 포그라운드/백그라운드 라이프사이클 감지 (중복 호출 방지를 위해 onResume / onPause 단일화)
    _lifecycleListener = AppLifecycleListener(
      onResume: () {
        if (!mounted) return;
        ref.read(sseNotificationServiceProvider).start();
        _syncData();
        _startSyncTimer();
      },
      onPause: () {
        _stopSyncTimer();
        if (mounted) {
          ref.read(sseNotificationServiceProvider).stop();
        }
      },
    );

    // 2. 스마트 주기적 자동 동기화 시작 (SSE/WebSocket이 메인이므로 60초 간격)
    _startSyncTimer();

    // 3. 앱 콜드 스타트 즉시 동기화 및 FCM 푸시 알림 세션 1회 안전 초기화
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _syncData();
      _initFcmOnce();
    });
  }

  Future<void> _initFcmOnce() async {
    if (_fcmInitialized || !mounted) return;
    _fcmInitialized = true;
    final dio = ref.read(dioProvider);

    // 1. 기존 FCM 백그라운드 리스너 등 기본 초기화
    await FcmService.initialize(dio);

    // 2. 최초 진입 시 푸시 알림 수신 동의 모달 안내 여부 확인
    final hasPrompted = await FcmService.hasPromptedPushPermission();
    if (!hasPrompted && mounted) {
      // 최초 권한 안내 바텀시트 모달 표시
      final bool? accepted = await PushPermissionPromptModal.show(context);
      await FcmService.markPushPromptShown();

      if (accepted == true && mounted) {
        // 사용자가 '알림 받기'를 선택한 경우 권한 요청 및 서버 등록 진행
        await FcmService.setPushEnabled(dio, true);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('푸시 알림이 활성화되었습니다.'),
              behavior: SnackBarBehavior.floating,
              duration: Duration(seconds: 2),
            ),
          );
        }
      }
    }
  }

  void _startSyncTimer() {
    _syncTimer?.cancel();
    _syncTimer = Timer.periodic(const Duration(seconds: 60), (_) {
      _syncData();
    });
  }

  void _stopSyncTimer() {
    _syncTimer?.cancel();
    _syncTimer = null;
  }

  void _syncData() {
    if (!mounted) return;
    final isAuthenticated = ref.read(isAuthenticatedProvider);
    if (!isAuthenticated) return;

    final now = DateTime.now();
    if (_lastSyncTime != null &&
        now.difference(_lastSyncTime!) < const Duration(seconds: 2)) {
      return;
    }
    _lastSyncTime = now;

    ref.read(notificationListProvider.notifier).fetchNotifications();
    ref.invalidate(pendingApprovalsProvider);
    ref.invalidate(totalUnreadChatCountProvider);
    ref.invalidate(chatRoomsProvider);
    ref.read(todoListProvider.notifier).refresh();
  }

  @override
  void dispose() {
    _stopSyncTimer();
    _lifecycleListener.dispose();
    super.dispose();
  }

  /// 현재 라우트가 5대 하단 탭 중 어디에 속하는지 반환 (비탭 보조 화면인 경우 null)
  int? _matchedTabIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    for (var i = 0; i < _tabs.length; i++) {
      if (location.startsWith(_tabs[i].route)) return i;
    }
    return null;
  }

  void _onTabTap(BuildContext context, int index) {
    if (index == 3) {
      // 전자결재 탭 진입 시 대기 목록 즉시 갱신
      ref.invalidate(pendingApprovalsProvider);
    }
    context.go(_tabs[index].route);
  }

  void _handlePopInvoked(bool didPop) {
    if (didPop) return;

    // 1. push로 진입한 하위 페이지(상세, 검색, 채팅, 할일 등)가 스택에 있으면 먼저 pop 수행
    if (context.canPop()) {
      context.pop();
      return;
    }

    // 2. 스택이 비어있으나 현재 위치가 홈(/home) 루트가 아닌 경우:
    //    - 탭의 하위 상세 경로(예: 딥링크로 진입한 /work/issues/123)이면 해당 탭 루트로 이동
    //    - 그 외 다른 탭 루트 또는 보조 화면(/chat, /todo, /search, /docs)이면 홈 탭으로 복귀
    final location = GoRouterState.of(context).matchedLocation;
    final matchedIdx = _matchedTabIndex(context);
    if (matchedIdx != null && location != _tabs[matchedIdx].route) {
      context.go(_tabs[matchedIdx].route);
      return;
    }
    if (location != AppRoutes.home) {
      context.go(AppRoutes.home);
      return;
    }

    // 3. 홈 탭(/home) 루트일 때: 2초 내에 두 번 누르면 앱 종료
    final now = DateTime.now();
    if (_lastBackPressTime == null ||
        now.difference(_lastBackPressTime!) > const Duration(seconds: 2)) {
      _lastBackPressTime = now;
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('뒤로가기 버튼을 한 번 더 누르면 앱이 종료됩니다.'),
          duration: Duration(seconds: 2),
        ),
      );
    } else {
      SystemNavigator.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final matchedIdx = _matchedTabIndex(context);
    final currentIdx = matchedIdx ?? 0;
    final isOnMainTab = matchedIdx != null;

    // 모바일 OS 앱 아이콘 알림 뱃지 자동 동기화 (미확인 알림 + 미결 결재)
    ref.watch(totalAppBadgeCountProvider);
    final pendingCount = ref.watch(pendingApprovalCountProvider);

    // 실시간 SSE 알림 스트림 연결 유지 (웹과 동일한 0.1초 즉시 동기화)
    ref.watch(sseNotificationServiceProvider);

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) => _handlePopInvoked(didPop),
      child: Scaffold(
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
                        final location =
                            GoRouterState.of(context).matchedLocation;
                        if (!location.startsWith(AppRoutes.chat)) {
                          context.push(AppRoutes.chat);
                        }
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

            // ── 📝 할일 관리 바로가기 및 미완료 할일 배지 ─────────────────────
            Consumer(
              builder: (ctx, ref, _) {
                final pendingTodoCount = ref.watch(pendingTodoCountProvider);
                return Stack(
                  alignment: Alignment.center,
                  children: [
                    IconButton(
                      icon: Icon(
                        pendingTodoCount > 0
                            ? Icons.checklist_rounded
                            : Icons.check_box_outlined,
                        size: 22,
                        color: pendingTodoCount > 0
                            ? context.colors.accentWork
                            : context.colors.textMuted,
                      ),
                      tooltip: '할일 관리',
                      onPressed: () {
                        ref.read(todoListProvider.notifier).refresh();
                        final location =
                            GoRouterState.of(context).matchedLocation;
                        if (location != AppRoutes.todo) {
                          context.push(AppRoutes.todo);
                        }
                      },
                    ),
                    if (pendingTodoCount > 0)
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
                            pendingTodoCount > 99 ? '99+' : '$pendingTodoCount',
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

            // ── 🔔 알림 센터 (순수 미확인 알림 건수 독립 표출) ──────────────────
            Consumer(
              builder: (ctx, ref, _) {
                final unreadNotifCount = ref.watch(unreadNotificationCountProvider);
                return Stack(
                  alignment: Alignment.center,
                  children: [
                    IconButton(
                      icon: Icon(
                        unreadNotifCount > 0
                            ? Icons.notifications_active_rounded
                            : Icons.notifications_none_rounded,
                        size: 23,
                        color: unreadNotifCount > 0
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
                    if (unreadNotifCount > 0)
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
                            unreadNotifCount > 99 ? '99+' : '$unreadNotifCount',
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
            Consumer(
              builder: (ctx, ref, _) {
                final currentUser = ref.watch(currentUserProvider).valueOrNull;
                return Padding(
                  padding: const EdgeInsets.only(left: 4, right: 12),
                  child: InkResponse(
                    onTap: () => context.push(AppRoutes.profile),
                    radius: 20,
                    child: Padding(
                      padding: const EdgeInsets.all(4.0),
                      child: UserAvatar(
                        user: currentUser,
                        radius: 15,
                      ),
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
          selectedItemColor: isOnMainTab
              ? context.colors.accentWork
              : context.colors.textDisabled,
          unselectedItemColor: context.colors.textDisabled,
          selectedLabelStyle: TextStyle(
            fontWeight: isOnMainTab ? FontWeight.bold : FontWeight.normal,
            fontSize: 11,
          ),
          unselectedLabelStyle: const TextStyle(fontSize: 11),
          elevation: 8,
          items: _tabs.map((t) {
            Widget iconWidget = Icon(t.icon);
            if (t.route == AppRoutes.approval && pendingCount > 0) {
              final badgeLabel = pendingCount > 99 ? '99+' : '$pendingCount';
              iconWidget = Badge(
                label: Text(badgeLabel, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
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
