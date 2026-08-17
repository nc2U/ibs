import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/constants/permissions.dart';
import '../../../core/providers/permission_provider.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../../core/widgets/workspace_selector_bar.dart';
import '../providers/forum_provider.dart';
import 'widgets/company_intro_tab_view.dart';
import 'widgets/faq_support_tab_view.dart';
import 'widgets/forum_tab_view.dart';
import 'widgets/notice_form_sheet.dart';
import 'widgets/notice_list_view.dart';
import 'widgets/onboarding_tab_view.dart';
import 'widgets/post_form_sheet.dart';

/// 채널 / 라운지 메인 화면 (/channel)
///
/// ── 상단 초슬림 미니멀 캡슐 스위치 (Type B) ──────────────────────
/// 1️⃣ 메인 세그먼트: [ 💬 소통 피드 ] vs [ 🏢 전사 라운지 ]
/// 2️⃣ 서브 섹션:
///   - [소통]: 워크스페이스 셀렉터 바 + (공지사항 | 게시판)
///   - [라운지]: 워크스페이스 무관(전사 공통) + (회사소개 | 온보딩·가이드 | FAQ·기술지원)
class ChannelTab extends ConsumerStatefulWidget {
  final int initialSection; // 0: 소통 피드, 1: 전사 라운지 & 온보딩
  final int initialIndex;   // 서브 탭 인덱스
  const ChannelTab({
    super.key,
    this.initialSection = 0,
    this.initialIndex = 0,
  });

  @override
  ConsumerState<ChannelTab> createState() => _ChannelTabState();
}

class _ChannelTabState extends ConsumerState<ChannelTab>
    with TickerProviderStateMixin {
  late int _mainSection; // 0: 워크스페이스 소통, 1: 전사 라운지 & 온보딩

  late final TabController _commTabController;
  late final TabController _loungeTabController;

  @override
  void initState() {
    super.initState();
    _mainSection = widget.initialSection;
    final commInitIndex = (_mainSection == 0 && widget.initialIndex < 2)
        ? widget.initialIndex
        : 0;
    final loungeInitIndex = (_mainSection == 1 && widget.initialIndex < 3)
        ? widget.initialIndex
        : 0;

    _commTabController = TabController(
      length: 2,
      vsync: this,
      initialIndex: commInitIndex,
    );
    _commTabController.addListener(() {
      if (mounted) setState(() {});
    });

    _loungeTabController = TabController(
      length: 3,
      vsync: this,
      initialIndex: loungeInitIndex,
    );
    _loungeTabController.addListener(() {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _commTabController.dispose();
    _loungeTabController.dispose();
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
    final hasForums = (forumsAsync.valueOrNull?.isNotEmpty ?? false);

    final canManageNews = !isNewsDisabled && ref.can(Perm.newsManage);
    final canCreatePost = !isForumDisabled &&
        hasForums &&
        (ref.can(Perm.forumCreate) || ref.can(Perm.forumManage));

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: Column(
        children: [
          // ── 1. 초슬림 미니멀 캡슐 스위치 (Type B) ────────────────────────
          _buildCapsuleSwitch(),
          Divider(color: context.colors.border, height: 1),

          // ── 2. 본문 컨텐츠 (소통 ↔ 라운지 서브 탭 뷰) ────────────────────
          Expanded(
            child: _mainSection == 0
                ? _buildCommunicationSection()
                : _buildLoungeSection(),
          ),
        ],
      ),

      // ── 3. 플로팅 액션 버튼 (소통 모드일 때만 활성화) ─────────────────
      floatingActionButton: _mainSection == 0
          ? _buildFab(canManageNews, canCreatePost)
          : null,
    );
  }

  // 🎨 초슬림 미니멀 캡슐 스위치 (높이 34px, 전폭 대칭)
  Widget _buildCapsuleSwitch() {
    return Container(
      color: context.colors.bgCard,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Container(
        height: 36,
        padding: const EdgeInsets.all(3),
        decoration: BoxDecoration(
          color: context.colors.bgSurface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: context.colors.border, width: 0.8),
        ),
        child: Row(
          children: [
            _buildCapsuleItem(0, '소통 피드', Icons.forum_outlined),
            _buildCapsuleItem(1, '전사 라운지 & 온보딩', Icons.business_outlined),
          ],
        ),
      ),
    );
  }

  Widget _buildCapsuleItem(int index, String label, IconData icon) {
    final isSelected = _mainSection == index;
    return Expanded(
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () {
          if (_mainSection != index) setState(() => _mainSection = index);
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 160),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: isSelected ? context.colors.bgCard : Colors.transparent,
            borderRadius: BorderRadius.circular(15),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: Colors.black.withAlpha(15),
                      blurRadius: 2,
                      offset: const Offset(0, 1),
                    )
                  ]
                : null,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 14,
                color: isSelected
                    ? context.colors.accentWork
                    : context.colors.textMuted,
              ),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                  color: isSelected
                      ? context.colors.textPrimary
                      : context.colors.textMuted,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // 📢 1) 워크스페이스 소통 섹션 (워크스페이스 바 + 공지/게시판 2개 탭)
  Widget _buildCommunicationSection() {
    return Column(
      children: [
        // 워크스페이스 셀렉터 바 (공통 컴포넌트)
        const WorkspaceSelectorBar(),
        Divider(color: context.colors.border, height: 1),

        // 소통 서브 탭바
        Container(
          decoration: BoxDecoration(
            color: context.colors.bgSurface,
            border: Border(
              bottom: BorderSide(color: context.colors.border, width: 0.8),
            ),
          ),
          child: TabBar(
            controller: _commTabController,
            indicatorSize: TabBarIndicatorSize.tab,
            indicator: BoxDecoration(
              color: context.colors.bgCard,
              border: Border(
                bottom: BorderSide(
                  color: context.colors.accentWork,
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
                      color: _commTabController.index == 0
                          ? context.colors.accentWork
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
                      color: _commTabController.index == 1
                          ? context.colors.accentWork
                          : context.colors.textMuted,
                    ),
                    const SizedBox(width: 6),
                    const Text('게시판'),
                  ],
                ),
              ),
            ],
          ),
        ),

        // 소통 탭 본문
        Expanded(
          child: TabBarView(
            controller: _commTabController,
            children: const [
              NoticeListView(),
              ForumTabView(),
            ],
          ),
        ),
      ],
    );
  }

  // 🏢 2) 전사 라운지 & 온보딩 섹션 (회사소개 / 온보딩·가이드 / FAQ·기술지원 3개 서브 탭)
  Widget _buildLoungeSection() {
    // 탭별 시맨틱 포인트 컬러 (0: 청색, 1: 녹색, 2: 앰버색)
    final loungeAccentColor = _loungeTabController.index == 0
        ? context.colors.accentCorp // Corporate Blue
        : _loungeTabController.index == 1
            ? context.colors.accentProject // Emerald Green
            : context.colors.accentApproval; // Amber Gold

    return Column(
      children: [
        // 라운지 서브 탭바 (3개 서브 탭)
        Container(
          decoration: BoxDecoration(
            color: context.colors.bgSurface,
            border: Border(
              bottom: BorderSide(color: context.colors.border, width: 0.8),
            ),
          ),
          child: TabBar(
            controller: _loungeTabController,
            isScrollable: true,
            tabAlignment: TabAlignment.start,
            indicatorSize: TabBarIndicatorSize.tab,
            indicator: BoxDecoration(
              color: context.colors.bgCard,
              border: Border(
                bottom: BorderSide(
                  color: loungeAccentColor,
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
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.business_outlined,
                        size: 18,
                        color: _loungeTabController.index == 0
                            ? context.colors.accentCorp
                            : context.colors.textMuted,
                      ),
                      const SizedBox(width: 6),
                      const Text('회사소개'),
                    ],
                  ),
                ),
              ),
              Tab(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.school_outlined,
                        size: 18,
                        color: _loungeTabController.index == 1
                            ? context.colors.accentProject
                            : context.colors.textMuted,
                      ),
                      const SizedBox(width: 6),
                      const Text('온보딩·가이드'),
                    ],
                  ),
                ),
              ),
              Tab(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.help_outline_rounded,
                        size: 18,
                        color: _loungeTabController.index == 2
                            ? context.colors.accentApproval
                            : context.colors.textMuted,
                      ),
                      const SizedBox(width: 6),
                      const Text('FAQ·기술지원'),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),

        // 라운지 탭 본문 (3개 탭 뷰)
        Expanded(
          child: TabBarView(
            controller: _loungeTabController,
            children: const [
              CompanyIntroTabView(),
              OnboardingTabView(),
              FaqSupportTabView(),
            ],
          ),
        ),
      ],
    );
  }

  // ✏️ 플로팅 버튼 분기
  Widget? _buildFab(bool canManageNews, bool canCreatePost) {
    if (_commTabController.index == 0 && canManageNews) {
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
        backgroundColor: context.colors.accentWork,
        foregroundColor: Colors.white,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        icon: const Icon(Icons.add_rounded, size: 20),
        label: const Text(
          '공지 등록',
          style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 0.2),
        ),
      );
    } else if (_commTabController.index == 1 && canCreatePost) {
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
        backgroundColor: context.colors.accentWork,
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
