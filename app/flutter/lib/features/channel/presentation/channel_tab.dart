import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/constants/permissions.dart';
import '../../../core/providers/permission_provider.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/widgets/project_selector_bottom_sheet.dart';
import '../providers/forum_provider.dart';
import 'widgets/forum_tab_view.dart';
import 'widgets/notice_form_sheet.dart';
import 'widgets/notice_list_view.dart';
import 'widgets/post_form_sheet.dart';

/// 채널 메인 화면 (/channel)
/// - 최상단: 워크스페이스 셀렉터 바
/// - 탭: 공지사항 | 게시판
/// - FAB: 공지 등록 (news.manage) / 글쓰기 (forum.create)
class ChannelTab extends ConsumerStatefulWidget {
  const ChannelTab({super.key});

  @override
  ConsumerState<ChannelTab> createState() => _ChannelTabState();
}

class _ChannelTabState extends ConsumerState<ChannelTab>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
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
    final canManageNews = ref.can(Perm.newsManage);
    final canCreatePost = ref.can(Perm.forumCreate) || ref.can(Perm.forumManage);

    return Scaffold(
      backgroundColor: AppColors.bgCard,
      body: Column(
        children: [
          // ── 1. 최상단 워크스페이스 셀렉터 바 ───────────────────────────
          InkWell(
            onTap: () => showProjectSelectorBottomSheet(context),
            child: Container(
              color: AppColors.bgSurface,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  const Icon(Icons.business_rounded,
                      size: 18, color: AppColors.accentProject),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '선택된 워크스페이스',
                          style: AppTextStyles.caption
                              .copyWith(color: AppColors.textMuted),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          selectedProject?.name ?? '🏢 전체 워크스페이스',
                          style: AppTextStyles.titleSm.copyWith(
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.accentProject.withAlpha(20),
                      borderRadius: BorderRadius.zero,
                      border: Border.all(
                          color: AppColors.accentProject.withAlpha(60)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('변경',
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

          // ── 2. 메인 탭바 (공지사항 | 게시판) ───────────────────────────
          Container(
            decoration: const BoxDecoration(
              color: AppColors.bgSurface,
              border: Border(
                bottom: BorderSide(color: AppColors.border, width: 0.8),
              ),
            ),
            child: TabBar(
              controller: _tabController,
              indicatorSize: TabBarIndicatorSize.tab,
              indicator: const BoxDecoration(
                color: AppColors.bgCard,
                border: Border(
                  bottom: BorderSide(
                    color: AppColors.accentWork,
                    width: 3.5,
                  ),
                ),
              ),
              labelColor: AppColors.accentWork,
              unselectedLabelColor: AppColors.textMuted,
              labelStyle: AppTextStyles.titleSm
                  .copyWith(fontWeight: FontWeight.w700),
              unselectedLabelStyle: AppTextStyles.bodyMd,
              dividerColor: Colors.transparent,
              tabs: const [
                Tab(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.campaign_rounded, size: 18),
                      SizedBox(width: 6),
                      Text('공지사항'),
                    ],
                  ),
                ),
                Tab(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.forum_outlined, size: 18),
                      SizedBox(width: 6),
                      Text('게시판'),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // ── 3. 탭 뷰 본문 ─────────────────────────────────────────────
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: const [
                NoticeListView(),
                ForumTabView(),
              ],
            ),
          ),
        ],
      ),

      // ── 4. 플로팅 액션 버튼 (탭별 권한에 따른 분기) ──────────────────
      floatingActionButton: () {
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
            backgroundColor: AppColors.accentWork,
            foregroundColor: Colors.white,
            shape: const RoundedRectangleBorder(
                borderRadius: BorderRadius.zero),
            icon: const Icon(Icons.add_rounded, size: 20),
            label: const Text(
              '공지 등록',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                letterSpacing: 0.2,
              ),
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
            backgroundColor: AppColors.accentWork,
            foregroundColor: Colors.white,
            shape: const RoundedRectangleBorder(
                borderRadius: BorderRadius.zero),
            icon: const Icon(Icons.edit_rounded, size: 20),
            label: const Text(
              '글쓰기',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                letterSpacing: 0.2,
              ),
            ),
          );
        }
        return null;
      }(),
    );
  }
}
