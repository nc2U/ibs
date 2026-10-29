import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/constants/permissions.dart';
import '../../../core/models/common_models.dart';
import '../../../core/providers/docs_context_provider.dart';
import '../../../core/providers/permission_provider.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../../core/widgets/workspace_selector_bar.dart';
import '../../docs/presentation/docs_screen.dart';
import '../../issue/presentation/issue_list_screen.dart';
import '../../meeting/presentation/meeting_list_screen.dart';
import '../../project/providers/project_provider.dart';

/// 업무 관리 탭 메인 화면 (워크스페이스 셀렉터 + 회의 목록 / 업무 목록 탭 전환 + 인라인 문서함 뷰 토글 + 생성 FAB)
class WorkScreen extends ConsumerStatefulWidget {
  final int initialIndex;
  const WorkScreen({super.key, this.initialIndex = 0});

  @override
  ConsumerState<WorkScreen> createState() => _WorkScreenState();
}

class _WorkScreenState extends ConsumerState<WorkScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late int _currentTabIndex;
  bool _isDocsView = false;

  @override
  void initState() {
    super.initState();
    _currentTabIndex = widget.initialIndex.clamp(0, 1);
    _tabController = TabController(
      length: 2,
      vsync: this,
      initialIndex: _currentTabIndex,
    );
    _tabController.addListener(_onTabChanged);
  }

  @override
  void didUpdateWidget(covariant WorkScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialIndex != widget.initialIndex) {
      final targetIndex = widget.initialIndex.clamp(0, 1);
      if (_isDocsView) {
        _isDocsView = false;
      }
      if (_tabController.index != targetIndex) {
        _currentTabIndex = targetIndex;
        _tabController.animateTo(targetIndex);
      }
    }
  }

  void _onTabChanged() {
    if (_tabController.index != _currentTabIndex) {
      setState(() {
        _currentTabIndex = _tabController.index;
      });
    }
  }

  @override
  void dispose() {
    _tabController.removeListener(_onTabChanged);
    _tabController.dispose();
    super.dispose();
  }

  void _openDocsView() {
    final currentWs = ref.read(selectedWorkspaceProvider);
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

  @override
  Widget build(BuildContext context) {
    // ── 🔄 워크스페이스 변경 감지 리스너: 문서함 뷰(_isDocsView) 활성 상태에서 워크스페이스가 변경되면 문서 컨텍스트 즉시 동기화 ──
    ref.listen(selectedWorkspaceProvider, (previous, next) {
      if (_isDocsView) {
        if (next != null) {
          final isDocEnabled = next.module?.document ?? true;
          if (!isDocEnabled) {
            _closeDocsView();
            return;
          }
          ref.read(docsContextProvider.notifier).state = DocsContext.workspace(
            SimpleProjectModel(
              pk: next.pk,
              name: next.name,
              slug: next.slug,
            ),
          );
        } else {
          ref.read(docsContextProvider.notifier).state = DocsContext.all();
        }
      }
    });

    final selectedWs = ref.watch(selectedWorkspaceProvider);
    final allProjects = ref.watch(projectListProvider).valueOrNull ?? [];
    final currentProj = selectedWs != null
        ? allProjects.where((p) => p.slug == selectedWs.slug).firstOrNull
        : null;
    final activeModule = selectedWs?.module ?? currentProj?.module;

    final isMeetingModuleEnabled = activeModule?.meeting ?? true;
    final isIssueModuleEnabled = activeModule?.issue ?? true;
    final isDocsModuleEnabled = activeModule?.document ?? true;

    final canShowDocsToggle = _isDocsView ||
        (isDocsModuleEnabled &&
            ref.can(Perm.docsRead, projectSlug: selectedWs?.slug));

    final isMeetingTab = _currentTabIndex == 0;
    final canCreate = isMeetingTab
        ? (ref.can(Perm.meetingCreate, projectSlug: selectedWs?.slug) &&
            isMeetingModuleEnabled)
        : (ref.can(Perm.issueCreate, projectSlug: selectedWs?.slug) &&
            isIssueModuleEnabled);

    return PopScope(
      canPop: !_isDocsView,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop && _isDocsView) {
          _closeDocsView();
        }
      },
      child: Scaffold(
        backgroundColor: context.colors.bgPrimary,
        body: Column(
          children: [
            // ── 워크스페이스 고정 선택 바 (공용 컴포넌트) ─────────────────────
            WorkspaceSelectorBar(
              trailing: canShowDocsToggle
                  ? InkWell(
                      onTap: _isDocsView ? _closeDocsView : _openDocsView,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: _isDocsView
                              ? context.colors.accentWork.withAlpha(30)
                              : const Color(0xFF6A1B9A),
                          borderRadius: BorderRadius.zero,
                          border: Border.all(
                            color: _isDocsView
                                ? context.colors.accentWork
                                : const Color(0xFFAB47BC),
                            width: 0.8,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              _isDocsView
                                  ? Icons.arrow_back_rounded
                                  : Icons.folder_shared_outlined,
                              size: 13,
                              color: _isDocsView
                                  ? context.colors.accentWork
                                  : Colors.white,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              _isDocsView
                                  ? (isMeetingTab ? '회의 목록' : '업무 목록')
                                  : '문서함',
                              style: AppTextStyles.label.copyWith(
                                color: _isDocsView
                                    ? context.colors.accentWork
                                    : Colors.white,
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                      ),
                    )
                  : null,
            ),
            Divider(color: context.colors.border, height: 1),

            // ── 바디 영역 (문서함 뷰 VS 기본 업무/회의 탭 뷰) ────────────────────
            Expanded(
              child: _isDocsView
                  ? const DocsScreen(isEmbedded: true)
                  : Column(
                      children: [
                        // ── 상단 탭바 (회의 목록 | 업무 목록) ───────────────
                        Container(
                          decoration: BoxDecoration(
                            color: context.colors.bgSurface,
                            border: Border(
                              bottom: BorderSide(
                                  color: context.colors.border, width: 0.8),
                            ),
                          ),
                          child: TabBar(
                            controller: _tabController,
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
                        Expanded(
                          child: TabBarView(
                            controller: _tabController,
                            children: const [
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

        // FAB (문서함 뷰일 때 또는 생성 권한/모듈이 없을 때는 미표시)
        floatingActionButton: (_isDocsView || !canCreate)
            ? null
            : FloatingActionButton.extended(
                elevation: 4,
                highlightElevation: 8,
                // 회의: 틸/청록 에메랄드 (#0D9488), 업무: 업무 테마색 (context.colors.accentWork)
                backgroundColor: isMeetingTab
                    ? const Color(0xFF0D9488)
                    : context.colors.accentWork,
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
                    context.push('/work/meetings/new');
                  } else {
                    final wsSlug = selectedWs?.slug;
                    context.push(wsSlug != null
                        ? '/work/issues/new?project_slug=$wsSlug'
                        : '/work/issues/new');
                  }
                },
              ),
      ),
    );
  }
}
