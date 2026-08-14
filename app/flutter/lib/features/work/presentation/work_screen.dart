import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/models/common_models.dart';
import '../../../../core/providers/docs_context_provider.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/router/app_router.dart';
import '../../../../core/widgets/project_selector_bottom_sheet.dart';
import '../../docs/presentation/docs_screen.dart';
import '../../issue/presentation/issue_list_screen.dart';
import '../../meeting/presentation/meeting_list_screen.dart';
import '../../project/providers/project_provider.dart';

/// 업무 관리 탭 메인 화면 (프로젝트 셀렉터 + 회의 목록 / 업무 목록 탭 전환 + 인라인 문서함 뷰 토글 + 생성 FAB)
class WorkScreen extends ConsumerStatefulWidget {
  final int initialIndex;
  const WorkScreen({super.key, this.initialIndex = 0});

  @override
  ConsumerState<WorkScreen> createState() => _WorkScreenState();
}

class _WorkScreenState extends ConsumerState<WorkScreen> {
  bool _isDocsView = false;
  static const _docsColor = Color(0xFF5E35B1);

  void _openDocsView() {
    final currentWs = ref.read(selectedProjectProvider);
    if (currentWs != null) {
      ref.read(docsContextProvider.notifier).state = DocsContext.workspace(
        SimpleProjectModel(
          pk: currentWs.pk,
          name: currentWs.name,
          slug: currentWs.slug,
        ),
      );
    } else {
      ref.read(docsContextProvider.notifier).state = DocsContext.all();
    }
    setState(() {
      _isDocsView = true;
    });
  }

  void _closeDocsView() {
    setState(() {
      _isDocsView = false;
    });
  }

  void _syncDocsContextIfNeeded() {
    if (_isDocsView) {
      final currentWs = ref.read(selectedProjectProvider);
      if (currentWs != null) {
        ref.read(docsContextProvider.notifier).state = DocsContext.workspace(
          SimpleProjectModel(
            pk: currentWs.pk,
            name: currentWs.name,
            slug: currentWs.slug,
          ),
        );
      } else {
        ref.read(docsContextProvider.notifier).state = DocsContext.all();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final projectName = ref.watch(selectedProjectNameProvider);

    return DefaultTabController(
      length: 2,
      initialIndex: widget.initialIndex,
      child: Scaffold(
        backgroundColor: AppColors.bgPrimary,
        body: Column(
          children: [
            // ── 워크스페이스 고정 선택 바 (문서함 뷰에서도 동일 유지) ─────────
            InkWell(
              onTap: () {
                showProjectSelectorBottomSheet(context);
                _syncDocsContextIfNeeded();
              },
              child: Container(
                color: AppColors.bgSurface,
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  children: [
                    const Icon(Icons.business_center_rounded,
                        size: 16, color: AppColors.accentProject),
                    const SizedBox(width: 8),
                    Text(
                      '워크스페이스:',
                      style: AppTextStyles.caption
                          .copyWith(color: AppColors.textMuted),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        projectName,
                        style: AppTextStyles.titleSm
                            .copyWith(color: AppColors.accentProject),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppColors.accentProject.withAlpha(25),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(
                            color: AppColors.accentProject.withAlpha(60)),
                      ),
                      child: Row(
                        children: [
                          Text('워크스페이스 변경',
                              style: AppTextStyles.label
                                  .copyWith(color: AppColors.accentProject)),
                          const Icon(Icons.keyboard_arrow_down_rounded,
                              size: 16, color: AppColors.accentProject),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),

                    // ── 문서함 ↔ 업무목록 스위칭 버튼 (고대비 시인성 개선) ──────
                    InkWell(
                      onTap: _isDocsView ? _closeDocsView : _openDocsView,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: _isDocsView
                              ? AppColors.accentWork.withAlpha(40)
                              : const Color(0xFF6A1B9A), // 선명한 솔리드 보라색
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(
                            color: _isDocsView
                                ? AppColors.accentWork
                                : const Color(0xFFAB47BC),
                            width: 1,
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              _isDocsView
                                  ? Icons.arrow_back_rounded
                                  : Icons.folder_shared_outlined,
                              size: 14,
                              color: _isDocsView
                                  ? AppColors.accentWork
                                  : Colors.white,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              _isDocsView ? '업무 목록' : '문서함',
                              style: AppTextStyles.label.copyWith(
                                color: _isDocsView
                                    ? AppColors.accentWork
                                    : Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const Divider(color: AppColors.border, height: 1),

            // ── 바디 영역 (문서함 뷰 VS 기본 업무/회의 탭 뷰) ────────────────────
            Expanded(
              child: _isDocsView
                  ? const DocsScreen()
                  : Column(
                      children: [
                        // ── 상단 탭바 (회의 목록 | 업무 목록) ───────────────
                        Container(
                          decoration: const BoxDecoration(
                            color: AppColors.bgSurface,
                            border: Border(
                              bottom: BorderSide(
                                  color: AppColors.border, width: 0.8),
                            ),
                          ),
                          child: TabBar(
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
                              Tab(text: '회의 목록'),
                              Tab(text: '업무 목록'),
                            ],
                          ),
                        ),
                        const Expanded(
                          child: TabBarView(
                            children: [
                              MeetingListScreen(),
                              IssueListScreen(),
                            ],
                          ),
                        ),
                      ],
                    ),
            ),
          ],
        ),

        // FAB (문서함 뷰일 때는 미표시)
        floatingActionButton: _isDocsView
            ? null
            : Builder(
                builder: (ctx) {
                  final controller = DefaultTabController.of(ctx);
                  return ListenableBuilder(
                    listenable: controller,
                    builder: (context, child) {
                      final selectedProject =
                          ref.watch(selectedProjectProvider);
                      final allProjects =
                          ref.watch(projectListProvider).valueOrNull ?? [];
                      final currentProj = selectedProject != null
                          ? allProjects
                              .where((p) => p.slug == selectedProject.slug)
                              .firstOrNull
                          : null;
                      final isMeetingModuleEnabled =
                          currentProj?.module?.meeting ?? true;

                      final isMeetingTab = controller.index == 0;
                      final canCreate = isMeetingTab
                          ? (ref.can(Perm.meetingCreate) &&
                              isMeetingModuleEnabled)
                          : ref.can(Perm.issueCreate);

                      if (!canCreate) return const SizedBox.shrink();

                      // 회의: 틸/청록 에메랄드 (#0D9488), 업무: 선명한 로열 블루 (#2563EB)
                      final fabColor = isMeetingTab
                          ? const Color(0xFF0D9488)
                          : const Color(0xFF2563EB);

                      return FloatingActionButton.extended(
                        elevation: 4,
                        highlightElevation: 8,
                        backgroundColor: fabColor,
                        foregroundColor: Colors.white,
                        shape: const RoundedRectangleBorder(
                          borderRadius: BorderRadius.zero,
                        ),
                        icon: const Icon(Icons.add_rounded,
                            size: 20, color: Colors.white),
                        label: Text(
                          isMeetingTab ? '회의 등록' : '업무 등록',
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                            letterSpacing: 0.2,
                          ),
                        ),
                        onPressed: () {
                          if (isMeetingTab) {
                            context.go('/work/meetings/new');
                          } else {
                            context.go('/work/issues/new');
                          }
                        },
                      );
                    },
                  );
                },
              ),
      ),
    );
  }
}
