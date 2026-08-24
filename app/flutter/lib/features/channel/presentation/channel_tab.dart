import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/constants/permissions.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/permission_provider.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../../core/widgets/workspace_selector_bar.dart';
import '../providers/forum_provider.dart';
import 'widgets/corporate_lounge_view.dart';
import 'widgets/forum_tab_view.dart';
import 'widgets/notice_form_sheet.dart';
import 'widgets/notice_list_view.dart';
import 'widgets/post_form_sheet.dart';

/// 채널 메인 화면 (/channel)
///
/// ── 상단 구조 일원화 ──────────────────────────────────────────
/// 1️⃣ 최상단: [ WorkspaceSelectorBar ] (다른 모든 탭과 일관된 UI 계층)
/// 2️⃣ 3단 메인 탭바: [ 📢 공지사항 | 💬 게시판 | 🏢 전사 라운지 ]
///   - [공지사항]: 선택된 워크스페이스 공지 목록
///   - [게시판]: 선택된 워크스페이스 소통 게시판
///   - [전사 라운지]: 전사 공통 브랜드북, 조직도, 온보딩 가이드, FAQ
class ChannelTab extends ConsumerStatefulWidget {
  final int initialIndex; // 0: 공지사항, 1: 게시판, 2: 전사 라운지

  const ChannelTab({
    super.key,
    int? initialSection,
    int initialIndex = 0,
  }) : initialIndex = (initialSection == 1 ? 2 : initialIndex);

  @override
  ConsumerState<ChannelTab> createState() => _ChannelTabState();
}

class _ChannelTabState extends ConsumerState<ChannelTab>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    final initIdx = (widget.initialIndex >= 0 && widget.initialIndex < 3)
        ? widget.initialIndex
        : 0;

    _tabController = TabController(
      length: 3,
      vsync: this,
      initialIndex: initIdx,
    );
    _tabController.addListener(() {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final selectedProject = ref.watch(selectedProjectProvider);
    final isNewsDisabled =
        selectedProject != null && (selectedProject.module?.news == false);
    final isForumDisabled =
        selectedProject != null && (selectedProject.module?.forum == false);

    final forumsAsync = ref.watch(forumListProvider);
    final forums = forumsAsync.valueOrNull ?? [];
    final hasForums = forums.isNotEmpty;

    final activeForumId = ref.watch(selectedForumIdProvider);
    final activeForum = forums.where((f) => f.pk == activeForumId).firstOrNull ??
        forums.firstOrNull;
    final currentUser = ref.watch(currentUserProvider).valueOrNull;
    final isSuper = currentUser?.isSuperuser ?? false;
    final isForumMgr = isSuper ||
        (activeForum?.manager.contains(currentUser?.pk ?? -1) ?? false);

    final canManageNews = !isNewsDisabled && ref.can(Perm.newsManage);
    final canCreatePost = !isForumDisabled &&
        hasForums &&
        (ref.can(Perm.forumCreate) || ref.can(Perm.forumManage)) &&
        ((activeForum?.managerOnly ?? false) ? isForumMgr : true);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: Column(
        children: [
          // ── 1. 최상단 워크스페이스 셀렉터 바 (타 메뉴와 100% 일관성) ─────────
          const WorkspaceSelectorBar(),
          Divider(color: context.colors.border, height: 1),

          // ── 2. 심플 & 직관적인 3개 탭바 ─────────────────────────────────
          Container(
            decoration: BoxDecoration(
              color: context.colors.bgSurface,
              border: Border(
                bottom: BorderSide(color: context.colors.border, width: 0.8),
              ),
            ),
            child: TabBar(
              controller: _tabController,
              indicatorSize: TabBarIndicatorSize.tab,
              indicator: BoxDecoration(
                color: context.colors.bgCard,
                border: Border(
                  bottom: BorderSide(
                    color: _tabController.index == 2
                        ? context.colors.accentCorp
                        : context.colors.accentChannel,
                    width: 3.0,
                  ),
                ),
              ),
              labelColor: context.colors.textPrimary,
              unselectedLabelColor: context.colors.textMuted,
              labelStyle:
                  AppTextStyles.titleSm.copyWith(fontWeight: FontWeight.w700),
              unselectedLabelStyle: AppTextStyles.bodyMd,
              dividerColor: Colors.transparent,
              tabs: [
                Tab(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.campaign_rounded,
                        size: 18,
                        color: _tabController.index == 0
                            ? context.colors.accentChannel
                            : context.colors.textMuted,
                      ),
                      const SizedBox(width: 6),
                      const Text('공지사항'),
                    ],
                  ),
                ),
                Tab(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.forum_outlined,
                        size: 18,
                        color: _tabController.index == 1
                            ? context.colors.accentChannel
                            : context.colors.textMuted,
                      ),
                      const SizedBox(width: 6),
                      const Text('게시판'),
                    ],
                  ),
                ),
                Tab(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.business_outlined,
                        size: 18,
                        color: _tabController.index == 2
                            ? context.colors.accentCorp
                            : context.colors.textMuted,
                      ),
                      const SizedBox(width: 6),
                      const Text('전사 라운지'),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // ── 3. 본문 탭 컨텐츠 ──────────────────────────────────────────
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: const [
                NoticeListView(),
                ForumTabView(),
                CorporateLoungeView(),
              ],
            ),
          ),
        ],
      ),

      // ── 4. 플로팅 액션 버튼 (공지 / 게시판 모드일 때만 활성화) ────────────
      floatingActionButton: _buildFab(canManageNews, canCreatePost),
    );
  }

  // ✏️ 플로팅 버튼 분기
  Widget? _buildFab(bool canManageNews, bool canCreatePost) {
    if (_tabController.index == 0 && canManageNews) {
      return FloatingActionButton.extended(
        onPressed: () {
          showModalBottomSheet(
            context: context,
            isScrollControlled: true,
            backgroundColor: Colors.transparent,
            builder: (ctx) => const NoticeFormSheet(),
          );
        },
        elevation: 4,
        highlightElevation: 8,
        backgroundColor: context.colors.accentChannel,
        foregroundColor: Colors.white,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        icon: const Icon(Icons.add_rounded, size: 20),
        label: const Text(
          '공지 등록',
          style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 0.2),
        ),
      );
    } else if (_tabController.index == 1 && canCreatePost) {
      return FloatingActionButton.extended(
        onPressed: () {
          final activeForumId = ref.read(selectedForumIdProvider);
          showModalBottomSheet(
            context: context,
            isScrollControlled: true,
            backgroundColor: Colors.transparent,
            builder: (ctx) => PostFormSheet(initialForumId: activeForumId),
          );
        },
        elevation: 4,
        highlightElevation: 8,
        backgroundColor: context.colors.accentChannel,
        foregroundColor: Colors.white,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        icon: const Icon(Icons.edit_rounded, size: 20),
        label: const Text(
          '글쓰기',
          style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 0.2),
        ),
      );
    }
    return null;
  }
}
