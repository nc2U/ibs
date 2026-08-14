import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';
import '../../features/auth/views/login_page.dart';
import '../../features/dashboard/views/main_shell.dart';
import '../../features/dashboard/views/home_tab.dart';
import '../../features/issue/presentation/issue_detail_screen.dart';

import '../../features/meeting/presentation/meeting_detail_screen.dart';
import '../../features/meeting/presentation/meeting_form_screen.dart';

import '../../features/work/presentation/work_screen.dart';
import '../../features/issue/presentation/issue_form_screen.dart';
import '../../features/project/presentation/project_screen.dart';
import '../../features/channel/presentation/channel_tab.dart';
import '../../features/profile/presentation/profile_screen.dart';
import '../../features/docs/presentation/docs_screen.dart';
import '../../features/search/presentation/search_results_screen.dart';

// ── Route 이름 상수 ─────────────────────────────────────────────────────────────
abstract class AppRoutes {
  static const login        = '/login';
  static const home         = '/home';
  static const work         = '/work';
  static const issues       = '/work/issues';
  static const issueDetail  = '/work/issues/:issueId';
  static const meetings     = '/work/meetings';
  static const meetingDetail = '/work/meetings/:meetingId';
  static const project      = '/project';
  static const approval     = '/approval';
  static const docs         = '/docs';
  static const search       = '/search';
  static const channel      = '/channel';
  static const profile      = '/profile';
}

// ── 라우터 프로바이더 ─────────────────────────────────────────────────────────
final appRouterProvider = Provider<GoRouter>((ref) {
  final isAuthenticated = ref.watch(isAuthenticatedProvider);

  return GoRouter(
    initialLocation: AppRoutes.home,
    debugLogDiagnostics: false,

    // ── 인증 가드 및 외부 파일 공유 딥링크 안전 처리 ─────────────────────────────
    redirect: (context, state) {
      final uri = state.uri;
      final path = uri.path;

      // 외부 앱(시놀로지 드라이브, 카카오톡 등)에서 파일 공유 시 들어오는 file:/// 또는 /private/... 딥링크 가로채기
      if (path.startsWith('/private') ||
          path.startsWith('/var') ||
          uri.scheme == 'file' ||
          uri.scheme.startsWith('sharemedia')) {
        return isAuthenticated ? AppRoutes.home : AppRoutes.login;
      }

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

      // 내 설정 (Shell 밖 — 독립 AppBar 보유)
      GoRoute(
        path: AppRoutes.profile,
        builder: (ctx, state) => const ProfileScreen(),
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
            builder: (ctx, state) => const WorkScreen(initialIndex: 0),
            routes: [
              GoRoute(
                path: 'issues',
                builder: (ctx, state) => const WorkScreen(initialIndex: 1),
                routes: [
                  GoRoute(
                    path: 'new',
                    builder: (ctx, state) {
                      final meetingIdStr = state.uri.queryParameters['meeting_id'];
                      final meetingId = meetingIdStr != null ? int.tryParse(meetingIdStr) : null;
                      final projectSlug = state.uri.queryParameters['project_slug'];

                      return IssueFormScreen(
                        initialMeetingId: meetingId,
                        initialProjectSlug: projectSlug,
                      );
                    },
                  ),
                  GoRoute(
                    path: ':issueId',
                    builder: (ctx, state) {
                      final id = int.tryParse(
                              state.pathParameters['issueId'] ?? '') ??
                          0;
                      return IssueDetailScreen(issueId: id);
                    },
                  ),
                ],
              ),
              GoRoute(
                path: 'meetings',
                builder: (ctx, state) => const WorkScreen(initialIndex: 0),
                routes: [
                  GoRoute(
                    path: 'new',
                    builder: (ctx, state) => const MeetingFormScreen(),
                  ),
                  GoRoute(
                    path: ':meetingId',
                    builder: (ctx, state) {
                      final id = int.tryParse(
                              state.pathParameters['meetingId'] ?? '') ??
                          0;
                      return MeetingDetailScreen(meetingId: id);
                    },
                  ),
                ],
              ),
            ],
          ),

          // 프로젝트 관리 탭
          GoRoute(
            path: AppRoutes.project,
            builder: (ctx, state) => const ProjectScreen(),
          ),

          // 채널 탭 (공지 + 게시판 + 공용문서)
          GoRoute(
            path: AppRoutes.channel,
            builder: (ctx, state) => const ChannelTab(),
          ),

          // 전자결재 (탭바 미표시, 홈 히어로카드에서 진입)
          GoRoute(
            path: AppRoutes.approval,
            builder: (ctx, state) =>
                const Center(child: Text('전자결재 (준비 중)')),
          ),

          // 공용 문서 화면
          GoRoute(
            path: AppRoutes.docs,
            builder: (ctx, state) => const DocsScreen(),
          ),

          // 통합 검색 화면 (하단 탭바 유지)
          GoRoute(
            path: AppRoutes.search,
            builder: (ctx, state) => const SearchResultsScreen(),
          ),
        ],
      ),
    ],

    errorBuilder: (ctx, state) => const MainShell(child: HomeTab()),
  );
});
