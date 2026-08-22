import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/router/app_router.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../providers/approval_providers.dart';
import 'widgets/approval_doc_card.dart';

class ApprovalMainScreen extends ConsumerStatefulWidget {
  final int initialTabIndex;

  const ApprovalMainScreen({
    super.key,
    this.initialTabIndex = 0,
  });

  @override
  ConsumerState<ApprovalMainScreen> createState() => _ApprovalMainScreenState();
}

class _ApprovalMainScreenState extends ConsumerState<ApprovalMainScreen>
    with TickerProviderStateMixin {
  late TabController _tabController;
  int _completedSubTab = 0; // 0: 승인완료, 1: 참조/공람
  bool _lastIsSuperuser = false;

  @override
  void initState() {
    super.initState();
    _lastIsSuperuser = false;
    _initTabController(false);
  }

  void _initTabController(bool isSuperuser) {
    _lastIsSuperuser = isSuperuser;
    final tabCount = isSuperuser ? 4 : 3;
    final initialIdx = widget.initialTabIndex < tabCount ? widget.initialTabIndex : 0;
    _tabController = TabController(length: tabCount, vsync: this, initialIndex: initialIdx);
    _tabController.addListener(() {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _goDetail(int docId) async {
    await context.push('${AppRoutes.approval}/$docId');
    if (mounted) {
      ref.invalidate(pendingApprovalsProvider);
      ref.invalidate(draftedApprovalsProvider);
      ref.invalidate(approvedApprovalsProvider);
      ref.invalidate(observedApprovalsProvider);
      ref.invalidate(allApprovalsProvider);
    }
  }

  void _goDraft() {
    context.push('${AppRoutes.approval}/draft');
  }

  @override
  Widget build(BuildContext context) {
    final pendingCount = ref.watch(pendingApprovalCountProvider);
    final user = ref.watch(currentUserProvider).valueOrNull;
    final isSuperuser = user?.isSuperuser ?? false;

    if (isSuperuser != _lastIsSuperuser) {
      _tabController.dispose();
      _initTabController(isSuperuser);
    }

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
<<<<<<< HEAD
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            // ── 상단 고정 헤더 바 (업무 탭의 워크스페이스 바와 동일한 색상/구분선 패턴) ──
            Container(
              color: context.colors.bgSurface,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  Icon(
                    Icons.draw_rounded,
                    size: 18,
                    color: context.colors.accentApproval,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '전자결재',
                    style: AppTextStyles.titleSm.copyWith(
                      fontWeight: FontWeight.w700,
                      color: context.colors.textPrimary,
                    ),
                  ),
                ],
              ),
            ),
            Divider(color: context.colors.border, height: 1),

            // ── 상단 탭바 (대기함 | 기안함 | 문서함 | [전체]) ───────────────
            Container(
              decoration: BoxDecoration(
                color: context.colors.bgSurface,
                border: Border(
                  bottom: BorderSide(
                    color: context.colors.border,
                    width: 0.8,
                  ),
                ),
              ),
              child: TabBar(
                controller: _tabController,
                isScrollable: false,
                indicatorSize: TabBarIndicatorSize.tab,
                indicator: BoxDecoration(
                  color: context.colors.bgCard,
                  border: Border(
                    bottom: BorderSide(
                      color: context.colors.accentApproval,
                      width: 3.0,
                    ),
                  ),
                ),
                labelColor: context.colors.textPrimary,
                unselectedLabelColor: context.colors.textMuted,
                labelStyle: AppTextStyles.titleSm.copyWith(fontWeight: FontWeight.w700),
                unselectedLabelStyle: AppTextStyles.bodyMd,
                dividerColor: Colors.transparent,
                tabs: [
                  Tab(
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text('대기함'),
                        if (pendingCount > 0) ...[
                          const SizedBox(width: 4),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                            decoration: BoxDecoration(
                              color: context.colors.error,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              '$pendingCount',
                              style: const TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w800,
                                color: Colors.white,
                              ),
=======
      appBar: AppBar(
        title: Text(
          '전자결재',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.w800,
            color: context.colors.textPrimary,
          ),
        ),
        centerTitle: false,
        backgroundColor: context.colors.bgCard,
        elevation: 0,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(44),
          child: Container(
            decoration: BoxDecoration(
              color: context.colors.bgSurface,
              border: Border(
                bottom: BorderSide(color: context.colors.border, width: 0.8),
              ),
            ),
            child: TabBar(
              controller: _tabController,
              isScrollable: false,
              indicatorSize: TabBarIndicatorSize.tab,
              indicator: BoxDecoration(
                color: context.colors.bgCard,
                border: Border(
                  bottom: BorderSide(
                    color: context.colors.accentApproval,
                    width: 3.0,
                  ),
                ),
              ),
              labelColor: context.colors.textPrimary,
              unselectedLabelColor: context.colors.textMuted,
              labelStyle: AppTextStyles.titleSm.copyWith(fontWeight: FontWeight.w700),
              unselectedLabelStyle: AppTextStyles.bodyMd,
              dividerColor: Colors.transparent,
              tabs: [
                Tab(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text('대기함'),
                      if (pendingCount > 0) ...[
                        const SizedBox(width: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                          decoration: BoxDecoration(
                            color: context.colors.error,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            '$pendingCount',
                            style: const TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                              color: Colors.white,
>>>>>>> f695059595 (approval ui update)
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
<<<<<<< HEAD
                  const Tab(text: '기안함'),
                  const Tab(text: '문서함'),
                  if (isSuperuser) const Tab(text: '전체'),
                ],
              ),
=======
                ),
                const Tab(text: '기안함'),
                const Tab(text: '문서함'),
                if (isSuperuser) const Tab(text: '전체'),
              ],
>>>>>>> f695059595 (approval ui update)
            ),

            // ── 탭 뷰 본문 ─────────────────────────────────────────────
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  // ── 0. 결재 대기함 ──────────────────────────────────────────
                  _buildPendingTab(),

                  // ── 1. 내 기안함 ──────────────────────────────────────────
                  _buildDraftedTab(),

                  // ── 2. 결재 문서함 (완료 / 참조) ───────────────────────────
                  _buildApprovedTab(),

                  // ── 3. 전체 문서함 (최고 관리자 전용) ────────────────────────
                  if (isSuperuser) _buildAllDocumentsTab(),
                ],
              ),
            ),
          ],
        ),
<<<<<<< HEAD
=======
        actions: [
          IconButton(
            icon: Icon(Icons.edit_document, color: context.colors.accentApproval),
            tooltip: '새 기안 작성',
            onPressed: _goDraft,
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // ── 0. 결재 대기함 ──────────────────────────────────────────
          _buildPendingTab(),

          // ── 1. 내 기안함 ──────────────────────────────────────────
          _buildDraftedTab(),

          // ── 2. 결재 문서함 (완료 / 참조) ───────────────────────────
          _buildApprovedTab(),

          // ── 3. 전체 문서함 (최고 관리자 전용) ────────────────────────
          if (isSuperuser) _buildAllDocumentsTab(),
        ],
>>>>>>> f695059595 (approval ui update)
      ),
      floatingActionButton: FloatingActionButton.extended(
        elevation: 4,
        highlightElevation: 8,
        backgroundColor: context.colors.accentApproval,
        foregroundColor: Colors.white,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.zero,
        ),
        icon: const Icon(Icons.add_rounded, size: 20, color: Colors.white),
        label: const Text(
          '기안 작성',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Colors.white,
            letterSpacing: 0.2,
          ),
        ),
        onPressed: _goDraft,
      ),
    );
  }

  // ── [Tab 0] 결재 대기함 ──────────────────────────────────────────────
  Widget _buildPendingTab() {
    final asyncList = ref.watch(pendingApprovalsProvider);

    return RefreshIndicator(
      onRefresh: () async => ref.refresh(pendingApprovalsProvider),
      color: context.colors.accentApproval,
      child: asyncList.when(
        data: (list) {
          if (list.isEmpty) {
            return const ErrorView.empty(
              message: '결재 대기 중인 문서가 없습니다.',
              subMessage: '새로운 결재 요청이 도착하면 여기에 표시됩니다.',
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(14),
            itemCount: list.length,
            itemBuilder: (ctx, i) => ApprovalDocCard(
              document: list[i],
              onTap: () => _goDetail(list[i].id),
            ),
          );
        },
        loading: () => const LoadingShimmer(),
        error: (err, _) => ErrorView(
          message: '결재 대기 목록을 불러오지 못했습니다.',
          subMessage: err.toString(),
          onRetry: () => ref.refresh(pendingApprovalsProvider),
        ),
      ),
    );
  }

  // ── [Tab 1] 내 기안함 ────────────────────────────────────────────────
  Widget _buildDraftedTab() {
    final asyncList = ref.watch(draftedApprovalsProvider);

    return RefreshIndicator(
      onRefresh: () async => ref.refresh(draftedApprovalsProvider),
      color: context.colors.accentApproval,
      child: asyncList.when(
        data: (list) {
          if (list.isEmpty) {
            return const ErrorView.empty(
              message: '내가 기안한 문서가 없습니다.',
              subMessage: '우측 하단 "새 기안" 버튼을 눌러 결재를 요청해 보세요.',
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(14),
            itemCount: list.length,
            itemBuilder: (ctx, i) => ApprovalDocCard(
              document: list[i],
              onTap: () => _goDetail(list[i].id),
            ),
          );
        },
        loading: () => const LoadingShimmer(),
        error: (err, _) => ErrorView(
          message: '기안 문서 목록을 불러오지 못했습니다.',
          subMessage: err.toString(),
          onRetry: () => ref.refresh(draftedApprovalsProvider),
        ),
      ),
    );
  }

  // ── [Tab 2] 결재 문서함 ──────────────────────────────────────────────
  Widget _buildApprovedTab() {
    final approvedAsync = ref.watch(approvedApprovalsProvider);
    final observedAsync = ref.watch(observedApprovalsProvider);

    final currentAsync = _completedSubTab == 0 ? approvedAsync : observedAsync;

    return Column(
      children: [
        // 서브 탭 필터 (완료 문서 vs 참조/공람 문서)
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            border: Border(bottom: BorderSide(color: context.colors.border, width: 0.6)),
          ),
          child: Row(
            children: [
              _buildSubPill(0, '결재 완료 문서', approvedAsync.valueOrNull?.length ?? 0),
              const SizedBox(width: 8),
              _buildSubPill(1, '참조 / 공람 문서', observedAsync.valueOrNull?.length ?? 0),
            ],
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(approvedApprovalsProvider);
              ref.invalidate(observedApprovalsProvider);
            },
            color: context.colors.accentApproval,
            child: currentAsync.when(
              data: (list) {
                if (list.isEmpty) {
                  return ErrorView.empty(
                    message: _completedSubTab == 0
                        ? '결재 완료된 문서가 없습니다.'
                        : '참조/공람된 문서가 없습니다.',
                  );
                }
                return ListView.builder(
                  padding: const EdgeInsets.all(14),
                  itemCount: list.length,
                  itemBuilder: (ctx, i) => ApprovalDocCard(
                    document: list[i],
                    onTap: () => _goDetail(list[i].id),
                  ),
                );
              },
              loading: () => const LoadingShimmer(),
              error: (err, _) => ErrorView(
                message: '문서 목록을 불러오지 못했습니다.',
                subMessage: err.toString(),
                onRetry: () {
                  ref.invalidate(approvedApprovalsProvider);
                  ref.invalidate(observedApprovalsProvider);
                },
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSubPill(int index, String label, int count) {
    final isSelected = _completedSubTab == index;
    return InkWell(
      onTap: () => setState(() => _completedSubTab = index),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: isSelected ? context.colors.accentApproval : context.colors.bgSurface,
          borderRadius: BorderRadius.zero,
          border: Border.all(
            color: isSelected ? context.colors.accentApproval : context.colors.border,
            width: 0.8,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                color: isSelected ? Colors.white : context.colors.textSecond,
              ),
            ),
            if (count > 0) ...[
              const SizedBox(width: 5),
              Text(
                '($count)',
                style: TextStyle(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w700,
                  color: isSelected ? Colors.white70 : context.colors.textMuted,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  // ── [Tab 3] 전체 문서함 (관리자) ──────────────────────────────────────
  Widget _buildAllDocumentsTab() {
    final asyncResponse = ref.watch(allApprovalsProvider);
    final filter = ref.watch(allApprovalsFilterProvider);

    return Column(
      children: [
        // 검색 & 상태 필터 바
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            border: Border(bottom: BorderSide(color: context.colors.border, width: 0.6)),
          ),
          child: Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 36,
                  child: TextField(
                    decoration: InputDecoration(
                      hintText: '문서번호, 제목, 기안자 검색...',
                      hintStyle: TextStyle(fontSize: 12, color: context.colors.textMuted),
                      prefixIcon: Icon(Icons.search, size: 18, color: context.colors.textMuted),
                      contentPadding: EdgeInsets.zero,
                      filled: true,
                      fillColor: context.colors.bgSurface,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.zero,
                        borderSide: BorderSide(color: context.colors.border, width: 0.6),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.zero,
                        borderSide: BorderSide(color: context.colors.border, width: 0.6),
                      ),
                    ),
                    onSubmitted: (val) {
                      ref.read(allApprovalsFilterProvider.notifier).state =
                          filter.copyWith(search: val.trim().isNotEmpty ? val.trim() : null, page: 1);
                    },
                  ),
                ),
              ),
              const SizedBox(width: 8),
              PopupMenuButton<String>(
                icon: Icon(Icons.filter_list_rounded, color: context.colors.textSecond, size: 20),
                tooltip: '상태 필터',
                onSelected: (val) {
                  ref.read(allApprovalsFilterProvider.notifier).state =
                      filter.copyWith(status: val == 'ALL' ? null : val, page: 1);
                },
                itemBuilder: (ctx) => [
                  const PopupMenuItem(value: 'ALL', child: Text('전체 상태')),
                  const PopupMenuItem(value: 'pending', child: Text('결재중')),
                  const PopupMenuItem(value: 'approved', child: Text('승인완료')),
                  const PopupMenuItem(value: 'rejected', child: Text('반려')),
                  const PopupMenuItem(value: 'draft', child: Text('임시저장')),
                ],
              ),
            ],
          ),
        ),

        // 목록 리스트
        Expanded(
          child: RefreshIndicator(
            onRefresh: () async => ref.refresh(allApprovalsProvider),
            color: context.colors.accentApproval,
            child: asyncResponse.when(
              data: (resp) {
                if (resp.results.isEmpty) {
                  return const ErrorView.empty(message: '조회된 결재 문서가 없습니다.');
                }
                return ListView.builder(
                  padding: const EdgeInsets.all(14),
                  itemCount: resp.results.length,
                  itemBuilder: (ctx, i) => ApprovalDocCard(
                    document: resp.results[i],
                    onTap: () => _goDetail(resp.results[i].id),
                  ),
                );
              },
              loading: () => const LoadingShimmer(),
              error: (err, _) => ErrorView(
                message: '전사 결재 문서를 불러오지 못했습니다.',
                subMessage: err.toString(),
                onRetry: () => ref.refresh(allApprovalsProvider),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
