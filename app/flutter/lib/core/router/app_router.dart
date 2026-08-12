import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';
import '../../features/auth/views/login_page.dart';
import '../../features/dashboard/views/main_shell.dart';
import '../../features/dashboard/views/home_tab.dart';
import '../../features/issue/presentation/issue_list_screen.dart';
import '../../features/issue/presentation/issue_detail_screen.dart';

// ── Route 이름 상수 ─────────────────────────────────────────────────────────────
abstract class AppRoutes {
  static const login     = '/login';
  static const home      = '/home';
  static const work      = '/work';
  static const issues    = '/work/issues';
  static const issueDetail = '/work/issues/:issueId';
  static const meetings  = '/work/meetings';
  static const meetingDetail = '/work/meetings/:meetingId';
  static const project   = '/project';
  static const approval  = '/approval';
  static const docs      = '/docs';
}

// ── 라우터 프로바이더 ─────────────────────────────────────────────────────────
final appRouterProvider = Provider<GoRouter>((ref) {
  final isAuthenticated = ref.watch(isAuthenticatedProvider);

  return GoRouter(
    initialLocation: AppRoutes.home,
    debugLogDiagnostics: false,

    // ── 인증 가드 ────────────────────────────────────────────────────────────
    redirect: (context, state) {
      final onLogin = state.matchedLocation == AppRoutes.login;
      if (!isAuthenticated && !onLogin) return AppRoutes.login;
      if (isAuthenticated && onLogin) return AppRoutes.home;
      return null;
    },

    routes: [
      // 로그인 (Shell 밖)
      GoRoute(
        path: AppRoutes.login,
        builder: (ctx, state) => const LoginPage(),
      ),

      // ── ShellRoute: 하단 탭바 유지 ─────────────────────────────────────────
      ShellRoute(
        builder: (ctx, state, child) => MainShell(child: child),
        routes: [
          // 홈
          GoRoute(
            path: AppRoutes.home,
            builder: (ctx, state) => const HomeTab(),
          ),

          // 업무 관리 탭
          GoRoute(
            path: AppRoutes.work,
            builder: (ctx, state) => const IssueListScreen(),
            routes: [
              GoRoute(
                path: 'issues',
                builder: (ctx, state) => const IssueListScreen(),
                routes: [
                  GoRoute(
                    path: ':issueId',
                    builder: (ctx, state) {
                      final id = int.tryParse(state.pathParameters['issueId'] ?? '') ?? 0;
                      return IssueDetailScreen(issueId: id);
                    },
                  ),
                ],
              ),
              GoRoute(
                path: 'meetings',
                builder: (ctx, state) => const Center(child: Text('회의 목록')),
                routes: [
                  GoRoute(
                    path: ':meetingId',
                    builder: (ctx, state) {
                      final id = int.tryParse(state.pathParameters['meetingId'] ?? '');
                      return Center(child: Text('회의 상세 #$id'));
                    },
                  ),
                ],
              ),
            ],
          ),

          // 프로젝트 관리 탭
          GoRoute(
            path: AppRoutes.project,
            builder: (ctx, state) => const Center(child: Text('프로젝트 관리')),
          ),

          // 전자결재 탭 (Phase 3)
          GoRoute(
            path: AppRoutes.approval,
            builder: (ctx, state) => const Center(child: Text('전자결재 (준비 중)')),
          ),

          // 공용 문서 탭
          GoRoute(
            path: AppRoutes.docs,
            builder: (ctx, state) => const Center(child: Text('공용 문서')),
          ),
        ],
      ),
    ],

    errorBuilder: (ctx, state) => Scaffold(
      backgroundColor: const Color(0xFF202336),
      body: Center(
        child: Text(
          '페이지를 찾을 수 없습니다.\n${state.error}',
          style: const TextStyle(color: Colors.white70),
          textAlign: TextAlign.center,
        ),
      ),
    ),
  );
});
