import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../providers/ledger_provider.dart';
import 'widgets/account_balance_card.dart';
import 'widgets/cashflow_mini_chart_card.dart';
import 'widgets/transaction_detail_sheet.dart';
import 'widgets/transaction_item_card.dart';

/// 🪙 회계 자금 관리 (Ledger) 메인 화면
class LedgerScreen extends ConsumerStatefulWidget {
  final VoidCallback onBackToMain;

  const LedgerScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  ConsumerState<LedgerScreen> createState() => _LedgerScreenState();
}

class _LedgerScreenState extends ConsumerState<LedgerScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _transactionsScrollController = ScrollController();
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    _transactionsScrollController.addListener(_onTransactionsScroll);

    // ── 화면 진입 시 현재 선택된 프로젝트 기준으로 최신 데이터 동기화 ──
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        ref.invalidate(ledgerOverallAggregateProvider);
        ref.invalidate(projectBankAccountsProvider);
        ref.invalidate(ledgerBalanceByAccountProvider);
        ref.read(projectTransactionsProvider.notifier).fetchInitial();
      }
    });
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _searchController.dispose();
    _transactionsScrollController.dispose();
    super.dispose();
  }

  void _onTransactionsScroll() {
    if (_transactionsScrollController.position.pixels >=
        _transactionsScrollController.position.maxScrollExtent - 200) {
      if (ref.read(ledgerCurrentSubTabProvider) == LedgerSubTab.transactions) {
        ref.read(projectTransactionsProvider.notifier).fetchNextPage();
      }
    }
  }

  void _onSearchChanged(String value) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 350), () {
      if (!mounted) return;
      ref.read(ledgerSearchQueryProvider.notifier).state = value;
      ref.read(projectTransactionsProvider.notifier).fetchInitial();
    });
  }

  void _onClearSearch() {
    _debounceTimer?.cancel();
    _searchController.clear();
    ref.read(ledgerSearchQueryProvider.notifier).state = '';
    ref.read(projectTransactionsProvider.notifier).fetchInitial();
  }

  void _applyDatePreset(LedgerDatePreset preset) {
    final now = DateTime.now();
    String? from;
    String? to;

    switch (preset) {
      case LedgerDatePreset.all:
        from = null;
        to = null;
        break;
      case LedgerDatePreset.today:
        final dateStr = DateFormat('yyyy-MM-dd').format(now);
        from = dateStr;
        to = dateStr;
        break;
      case LedgerDatePreset.thisMonth:
        from = DateFormat('yyyy-MM-01').format(now);
        final lastDay = DateTime(now.year, now.month + 1, 0);
        to = DateFormat('yyyy-MM-dd').format(lastDay);
        break;
      case LedgerDatePreset.lastMonth:
        final firstDayOfLastMonth = DateTime(now.year, now.month - 1, 1);
        from = DateFormat('yyyy-MM-01').format(firstDayOfLastMonth);
        final lastDayOfLastMonth = DateTime(now.year, now.month, 0);
        to = DateFormat('yyyy-MM-dd').format(lastDayOfLastMonth);
        break;
      case LedgerDatePreset.last3Months:
        final threeMonthsAgo = DateTime(now.year, now.month - 2, 1);
        from = DateFormat('yyyy-MM-01').format(threeMonthsAgo);
        final lastDayOfThisMonth = DateTime(now.year, now.month + 1, 0);
        to = DateFormat('yyyy-MM-dd').format(lastDayOfThisMonth);
        break;
      case LedgerDatePreset.thisYear:
        from = '${now.year}-01-01';
        to = '${now.year}-12-31';
        break;
      case LedgerDatePreset.custom:
        return;
    }

    ref.read(ledgerDatePresetProvider.notifier).state = preset;
    ref.read(ledgerFromDateFilterProvider.notifier).state = from;
    ref.read(ledgerToDateFilterProvider.notifier).state = to;
    ref.read(projectTransactionsProvider.notifier).fetchInitial();
  }

  Future<void> _pickDateRange() async {
    final now = DateTime.now();
    final currentFrom = ref.read(ledgerFromDateFilterProvider);
    final currentTo = ref.read(ledgerToDateFilterProvider);

    DateTime initialStart = now;
    DateTime initialEnd = now;
    if (currentFrom != null) {
      try {
        initialStart = DateTime.parse(currentFrom);
      } catch (_) {}
    }
    if (currentTo != null) {
      try {
        initialEnd = DateTime.parse(currentTo);
      } catch (_) {}
    }

    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2010),
      lastDate: DateTime(2035),
      initialDateRange: DateTimeRange(start: initialStart, end: initialEnd),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: ColorScheme.dark(
              primary: context.colors.accentProject,
              onPrimary: Colors.white,
              surface: context.colors.bgCard,
              onSurface: context.colors.textPrimary,
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      final fromStr = DateFormat('yyyy-MM-dd').format(picked.start);
      final toStr = DateFormat('yyyy-MM-dd').format(picked.end);

      ref.read(ledgerDatePresetProvider.notifier).state = LedgerDatePreset.custom;
      ref.read(ledgerFromDateFilterProvider.notifier).state = fromStr;
      ref.read(ledgerToDateFilterProvider.notifier).state = toStr;
      ref.read(projectTransactionsProvider.notifier).fetchInitial();
    }
  }

  @override
  Widget build(BuildContext context) {
    // ── 🔄 프로젝트 변경 감지 리스너: 프로젝트가 변경되면 출납 내역 및 자금 집계, 계좌 목록을 즉시 자동 갱신 ──
    ref.listen(selectedRealEstateProjectProvider, (previous, next) {
      if (previous?.realProjectId != next?.realProjectId) {
        ref.invalidate(ledgerOverallAggregateProvider);
        ref.invalidate(projectBankAccountsProvider);
        ref.invalidate(ledgerBalanceByAccountProvider);
        ref.read(ledgerSelectedBankAccFilterProvider.notifier).state = null;
        ref.read(projectTransactionsProvider.notifier).fetchInitial();
      }
    });

    final selectedProject = ref.watch(selectedRealEstateProjectProvider);
    final aggregateAsync = ref.watch(ledgerOverallAggregateProvider);
    final currentTab = ref.watch(ledgerCurrentSubTabProvider);
    final bankAccountsAsync = ref.watch(projectBankAccountsProvider);
    final sortFilter = ref.watch(ledgerSortFilterProvider);
    final selectedBankAcc = ref.watch(ledgerSelectedBankAccFilterProvider);
    final datePreset = ref.watch(ledgerDatePresetProvider);
    final fromDate = ref.watch(ledgerFromDateFilterProvider);
    final toDate = ref.watch(ledgerToDateFilterProvider);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: Column(
        children: [
          // ── 1. 회계 자금 헤더 배너 (고정) ─────────────────────────────────────────
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            child: Row(
              children: [
                IconButton(
                  onPressed: widget.onBackToMain,
                  icon: const Icon(Icons.arrow_back_rounded, size: 20),
                  tooltip: '메인으로 돌아가기',
                  color: context.colors.textPrimary,
                  padding: const EdgeInsets.all(4),
                  constraints: const BoxConstraints(),
                ),
                const SizedBox(width: 8),
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: const Color(0xFFF59E0B).withAlpha(30),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.account_balance_wallet_outlined,
                      size: 20, color: Color(0xFFF59E0B)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Text(
                            '회계 자금 관리',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 5, vertical: 1.5),
                            decoration: BoxDecoration(
                              color: const Color(0xFFF59E0B).withAlpha(20),
                              border: Border.all(
                                  color: const Color(0xFFF59E0B).withAlpha(120),
                                  width: 0.8),
                              borderRadius: BorderRadius.circular(2),
                            ),
                            child: const Text(
                              'LEDGER',
                              style: TextStyle(
                                fontSize: 9.5,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFFF59E0B),
                                letterSpacing: 0.6,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        selectedProject?.name ?? '선택된 프로젝트 없음',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () {
                    ref.invalidate(ledgerOverallAggregateProvider);
                    ref.invalidate(ledgerBalanceByAccountProvider);
                    ref.invalidate(projectBankAccountsProvider);
                    ref.read(projectTransactionsProvider.notifier).fetchInitial();
                  },
                  icon: const Icon(Icons.refresh_rounded, size: 18),
                  tooltip: '새로고침',
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  color: context.colors.textSecond,
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 아래부터 스크롤 가능한 본문 영역 (CustomScrollView) ───────────────
          if (selectedProject == null)
            Expanded(
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.business_center_outlined,
                      size: 48,
                      color: context.colors.textDisabled,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '선택된 프로젝트가 없습니다.',
                      style: AppTextStyles.titleSm.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '상단에서 부동산 개발 프로젝트를 먼저 선택해 주세요.',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
            )
          else
            Expanded(
              child: RefreshIndicator(
                color: context.colors.accentProject,
                onRefresh: () async {
                  ref.invalidate(ledgerOverallAggregateProvider);
                  ref.invalidate(ledgerBalanceByAccountProvider);
                  ref.invalidate(projectBankAccountsProvider);
                  ref.read(projectTransactionsProvider.notifier).fetchInitial();
                },
                child: CustomScrollView(
                controller: _transactionsScrollController,
                physics: const AlwaysScrollableScrollPhysics(),
                slivers: [
                  // A. KPI 대시보드 및 캐시플로우 미니 차트 (스크롤 연동)
                  SliverToBoxAdapter(
                    child: aggregateAsync.when(
                      loading: () => const SizedBox(
                        height: 64,
                        child: Center(
                          child: SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2)),
                        ),
                      ),
                      error: (_, __) => const SizedBox.shrink(),
                      data: (aggregate) {
                        if (aggregate == null) return const SizedBox.shrink();
                        return Container(
                          color: context.colors.bgCard,
                          padding: const EdgeInsets.symmetric(
                              horizontal: 14, vertical: 8),
                          child: Row(
                            children: [
                              _KpiItem(
                                label: '총 잔고액',
                                value: _formatToBillion(aggregate.totalBalance),
                                color: const Color(0xFF38BDF8),
                              ),
                              _divider(),
                              _KpiItem(
                                label: '당월 입금',
                                value: _formatToBillion(aggregate.monthIncome),
                                color: const Color(0xFF10B981),
                              ),
                              _divider(),
                              _KpiItem(
                                label: '당월 지출',
                                value: _formatToBillion(aggregate.monthExpense),
                                color: const Color(0xFFEF4444),
                              ),
                              _divider(),
                              _KpiItem(
                                label: '당월 수지차',
                                value: _formatToBillion(aggregate.monthBalance),
                                color: aggregate.monthBalance >= 0
                                    ? const Color(0xFF10B981)
                                    : const Color(0xFFEF4444),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                  const SliverToBoxAdapter(
                    child: Divider(height: 1),
                  ),
                  const SliverToBoxAdapter(
                    child: CashflowMiniChartCard(),
                  ),
                  const SliverToBoxAdapter(
                    child: Divider(height: 1),
                  ),

                  // B. 3대 서브 탭 바 (상단 고정 Sticky Header)
                  SliverPersistentHeader(
                    pinned: true,
                    delegate: _PinnedHeaderDelegate(
                      height: 52.0,
                      child: Container(
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          border: Border(
                            bottom: BorderSide(
                              color: context.colors.border,
                              width: 0.8,
                            ),
                          ),
                        ),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 7),
                        child: Row(
                          children: [
                            _SubTabButton(
                              title: '출납 내역',
                              icon: Icons.receipt_outlined,
                              isSelected:
                                  currentTab == LedgerSubTab.transactions,
                              onTap: () {
                                ref
                                    .read(ledgerCurrentSubTabProvider.notifier)
                                    .state = LedgerSubTab.transactions;
                              },
                            ),
                            const SizedBox(width: 6),
                            _SubTabButton(
                              title: '계좌별 잔액',
                              icon: Icons.account_balance_outlined,
                              isSelected:
                                  currentTab == LedgerSubTab.balanceStatus,
                              onTap: () {
                                ref
                                    .read(ledgerCurrentSubTabProvider.notifier)
                                    .state = LedgerSubTab.balanceStatus;
                              },
                            ),
                            const SizedBox(width: 6),
                            _SubTabButton(
                              title: '전도금 정산',
                              icon: Icons.business_center_outlined,
                              isSelected: currentTab == LedgerSubTab.imprest,
                              onTap: () {
                                ref
                                    .read(ledgerCurrentSubTabProvider.notifier)
                                    .state = LedgerSubTab.imprest;
                              },
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  // C. 검색 & 기간/계좌 필터 바 (출납내역 탭에서 활성화)
                  if (currentTab == LedgerSubTab.transactions) ...[
                    SliverToBoxAdapter(
                      child: Container(
                        color: context.colors.bgCard,
                        padding: const EdgeInsets.symmetric(
                            horizontal: 14, vertical: 8),
                        child: Column(
                          children: [
                            // 1) 통합 검색창
                            Container(
                              height: 38,
                              decoration: BoxDecoration(
                                color: context.colors.bgSurface,
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(
                                    color: context.colors.border, width: 0.8),
                              ),
                              child: TextField(
                                controller: _searchController,
                                onChanged: _onSearchChanged,
                                style: AppTextStyles.bodySecond.copyWith(
                                  color: context.colors.textPrimary,
                                  fontSize: 13,
                                ),
                                decoration: InputDecoration(
                                  isDense: true,
                                  hintText: '적요, 거래처, 계정과목, 메모 검색...',
                                  hintStyle: AppTextStyles.bodySecond.copyWith(
                                    color: context.colors.textMuted,
                                    fontSize: 12.5,
                                  ),
                                  prefixIcon: Icon(
                                    Icons.search_rounded,
                                    size: 18,
                                    color: context.colors.textMuted,
                                  ),
                                  suffixIcon: _searchController.text.isNotEmpty
                                      ? IconButton(
                                          icon: const Icon(
                                              Icons.clear_rounded,
                                              size: 16),
                                          color: context.colors.textMuted,
                                          onPressed: _onClearSearch,
                                        )
                                      : null,
                                  border: InputBorder.none,
                                  contentPadding:
                                      const EdgeInsets.symmetric(vertical: 9),
                                ),
                              ),
                            ),
                            const SizedBox(height: 8),

                            // 2) 기간 선택 바
                            SingleChildScrollView(
                              scrollDirection: Axis.horizontal,
                              child: Row(
                                children: [
                                  _DatePresetChip(
                                    label: '전체기간',
                                    isSelected:
                                        datePreset == LedgerDatePreset.all,
                                    onTap: () =>
                                        _applyDatePreset(LedgerDatePreset.all),
                                  ),
                                  const SizedBox(width: 4),
                                  _DatePresetChip(
                                    label: '오늘',
                                    isSelected:
                                        datePreset == LedgerDatePreset.today,
                                    onTap: () => _applyDatePreset(
                                        LedgerDatePreset.today),
                                  ),
                                  const SizedBox(width: 4),
                                  _DatePresetChip(
                                    label: '이번달',
                                    isSelected: datePreset ==
                                        LedgerDatePreset.thisMonth,
                                    onTap: () => _applyDatePreset(
                                        LedgerDatePreset.thisMonth),
                                  ),
                                  const SizedBox(width: 4),
                                  _DatePresetChip(
                                    label: '지난달',
                                    isSelected: datePreset ==
                                        LedgerDatePreset.lastMonth,
                                    onTap: () => _applyDatePreset(
                                        LedgerDatePreset.lastMonth),
                                  ),
                                  const SizedBox(width: 4),
                                  _DatePresetChip(
                                    label: '최근3개월',
                                    isSelected: datePreset ==
                                        LedgerDatePreset.last3Months,
                                    onTap: () => _applyDatePreset(
                                        LedgerDatePreset.last3Months),
                                  ),
                                  const SizedBox(width: 4),
                                  _DatePresetChip(
                                    label: '올해',
                                    isSelected:
                                        datePreset == LedgerDatePreset.thisYear,
                                    onTap: () => _applyDatePreset(
                                        LedgerDatePreset.thisYear),
                                  ),
                                  const SizedBox(width: 6),

                                  // 달력 직접 지정 버튼
                                  InkWell(
                                    onTap: _pickDateRange,
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 7, vertical: 3.5),
                                      decoration: BoxDecoration(
                                        color: datePreset ==
                                                LedgerDatePreset.custom
                                            ? context.colors.accentProject
                                                .withAlpha(25)
                                            : context.colors.bgSurface,
                                        borderRadius: BorderRadius.circular(4),
                                        border: Border.all(
                                          color: datePreset ==
                                                  LedgerDatePreset.custom
                                              ? context.colors.accentProject
                                              : context.colors.border,
                                          width: datePreset ==
                                                  LedgerDatePreset.custom
                                              ? 1
                                              : 0.8,
                                        ),
                                      ),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Icon(
                                            Icons.calendar_month_outlined,
                                            size: 12,
                                            color: datePreset ==
                                                    LedgerDatePreset.custom
                                                ? context.colors.accentProject
                                                : context.colors.textMuted,
                                          ),
                                          const SizedBox(width: 4),
                                          Text(
                                            datePreset ==
                                                        LedgerDatePreset
                                                            .custom &&
                                                    fromDate != null &&
                                                    toDate != null
                                                ? '${fromDate.substring(5)} ~ ${toDate.substring(5)}'
                                                : '직접선택',
                                            style: TextStyle(
                                              fontSize: 10.5,
                                              fontWeight: datePreset ==
                                                      LedgerDatePreset.custom
                                                  ? FontWeight.bold
                                                  : FontWeight.normal,
                                              color: datePreset ==
                                                      LedgerDatePreset.custom
                                                  ? context.colors.accentProject
                                                  : context.colors.textSecond,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 8),

                            // 3) 거래구분 빠른 필터 칩 & 계좌 선택 드롭다운
                            Row(
                              children: [
                                _FilterChipButton(
                                  label: '전체',
                                  isSelected: sortFilter == '',
                                  onTap: () {
                                    ref
                                        .read(
                                            ledgerSortFilterProvider.notifier)
                                        .state = '';
                                    ref
                                        .read(projectTransactionsProvider
                                            .notifier)
                                        .fetchInitial();
                                  },
                                ),
                                const SizedBox(width: 4),
                                _FilterChipButton(
                                  label: '수입(+)',
                                  isSelected: sortFilter == '1',
                                  color: const Color(0xFF10B981),
                                  onTap: () {
                                    ref
                                        .read(
                                            ledgerSortFilterProvider.notifier)
                                        .state = '1';
                                    ref
                                        .read(projectTransactionsProvider
                                            .notifier)
                                        .fetchInitial();
                                  },
                                ),
                                const SizedBox(width: 4),
                                _FilterChipButton(
                                  label: '지출(-)',
                                  isSelected: sortFilter == '2',
                                  color: const Color(0xFFEF4444),
                                  onTap: () {
                                    ref
                                        .read(
                                            ledgerSortFilterProvider.notifier)
                                        .state = '2';
                                    ref
                                        .read(projectTransactionsProvider
                                            .notifier)
                                        .fetchInitial();
                                  },
                                ),
                                const SizedBox(width: 4),
                                _FilterChipButton(
                                  label: '대체',
                                  isSelected: sortFilter == '3',
                                  color: const Color(0xFF38BDF8),
                                  onTap: () {
                                    ref
                                        .read(
                                            ledgerSortFilterProvider.notifier)
                                        .state = '3';
                                    ref
                                        .read(projectTransactionsProvider
                                            .notifier)
                                        .fetchInitial();
                                  },
                                ),
                                const Spacer(),

                                // 계좌 선택 드롭다운
                                bankAccountsAsync.when(
                                  data: (banks) {
                                    if (banks.isEmpty) {
                                      return const SizedBox.shrink();
                                    }
                                    final selectedAlias = selectedBankAcc == null
                                        ? '계좌 전체'
                                        : banks
                                            .firstWhere(
                                                (b) => b.pk == selectedBankAcc,
                                                orElse: () => banks.first)
                                            .aliasName;

                                    return PopupMenuButton<int>(
                                      initialValue: selectedBankAcc ?? 0,
                                      tooltip: selectedAlias,
                                      onSelected: (val) {
                                        ref
                                            .read(
                                                ledgerSelectedBankAccFilterProvider
                                                    .notifier)
                                            .state = val == 0 ? null : val;
                                        ref
                                            .read(projectTransactionsProvider
                                                .notifier)
                                            .fetchInitial();
                                      },
                                      child: Container(
                                        constraints:
                                            const BoxConstraints(maxWidth: 130),
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 8, vertical: 4),
                                        decoration: BoxDecoration(
                                          color: selectedBankAcc != null
                                              ? context.colors.accentProject
                                                  .withAlpha(20)
                                              : context.colors.bgSurface,
                                          borderRadius: BorderRadius.circular(4),
                                          border: Border.all(
                                            color: selectedBankAcc != null
                                                ? context.colors.accentProject
                                                : context.colors.border,
                                            width: 0.8,
                                          ),
                                        ),
                                        child: Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Icon(
                                              Icons.account_balance_outlined,
                                              size: 13,
                                              color: selectedBankAcc != null
                                                  ? context.colors.accentProject
                                                  : context.colors.textMuted,
                                            ),
                                            const SizedBox(width: 4),
                                            Flexible(
                                              child: Text(
                                                selectedAlias,
                                                style: TextStyle(
                                                  fontSize: 11,
                                                  fontWeight:
                                                      selectedBankAcc != null
                                                          ? FontWeight.bold
                                                          : FontWeight.normal,
                                                  color: selectedBankAcc != null
                                                      ? context
                                                          .colors.accentProject
                                                      : context
                                                          .colors.textPrimary,
                                                ),
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                            ),
                                            const SizedBox(width: 2),
                                            Icon(Icons.arrow_drop_down,
                                                size: 14,
                                                color: context.colors.textMuted),
                                          ],
                                        ),
                                      ),
                                      itemBuilder: (ctx) => [
                                        const PopupMenuItem<int>(
                                          value: 0,
                                          child: Text('전체 계좌',
                                              style: TextStyle(fontSize: 12)),
                                        ),
                                        ...banks.map(
                                          (b) => PopupMenuItem<int>(
                                            value: b.pk,
                                            child: Text(b.aliasName,
                                                style: const TextStyle(
                                                    fontSize: 12)),
                                          ),
                                        ),
                                      ],
                                    );
                                  },
                                  loading: () => const SizedBox.shrink(),
                                  error: (_, __) => const SizedBox.shrink(),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SliverToBoxAdapter(
                      child: Divider(height: 1),
                    ),
                  ],

                  // D. 탭별 맞춤 리스트 (Slivers)
                  Builder(
                    builder: (context) {
                      switch (currentTab) {
                        case LedgerSubTab.transactions:
                          return _buildTransactionsSliver();
                        case LedgerSubTab.balanceStatus:
                          return _buildBalanceStatusSliver();
                        case LedgerSubTab.imprest:
                          return _buildImprestSliver();
                      }
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 💳 1. 출납 전표 목록 Sliver 뷰
  Widget _buildTransactionsSliver() {
    final state = ref.watch(projectTransactionsProvider);

    if (state.isLoading) {
      return const _SliverLoadingView();
    }

    if (state.error != null && state.items.isEmpty) {
      return _SliverErrorView(message: '데이터 로드 실패: ${state.error}');
    }

    if (state.items.isEmpty) {
      return const _SliverEmptyView(
        icon: Icons.search_off_rounded,
        message: '조회된 출납 거래 내역이 없습니다.',
      );
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      sliver: SliverList(
        delegate: SliverChildBuilderDelegate(
          (ctx, index) {
            if (index == state.items.length) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 14),
                child: Center(
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              );
            }

            final item = state.items[index];
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: TransactionItemCard(
                item: item,
                onTap: () => TransactionDetailSheet.show(
                  context,
                  item: item,
                  onNoteEdited: () => ref
                      .read(projectTransactionsProvider.notifier)
                      .fetchInitial(),
                ),
              ),
            );
          },
          childCount: itemCount,
        ),
      ),
    );
  }

  /// 🏦 2. 계좌별 잔액 현황 Sliver 뷰
  Widget _buildBalanceStatusSliver() {
    final balancesAsync = ref.watch(ledgerBalanceByAccountProvider);

    return balancesAsync.when(
      loading: () => const _SliverLoadingView(),
      error: (err, _) => _SliverErrorView(message: '잔액 데이터 로드 실패: $err'),
      data: (items) {
        if (items.isEmpty) {
          return const _SliverEmptyView(
            icon: Icons.account_balance_outlined,
            message: '등록된 프로젝트 계좌 정보가 없습니다.',
          );
        }

        return SliverPadding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          sliver: SliverList(
            delegate: SliverChildBuilderDelegate(
              (ctx, index) {
                final acc = items[index];
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: AccountBalanceCard(item: acc),
                );
              },
              childCount: items.length,
            ),
          ),
        );
      },
    );
  }

  /// 💼 3. 프로젝트 전도금/운영비 Sliver 뷰
  Widget _buildImprestSliver() {
    final imprestAsync = ref.watch(ledgerImprestAccountsProvider);

    return imprestAsync.when(
      loading: () => const _SliverLoadingView(),
      error: (err, _) => _SliverErrorView(message: '전도금 로드 실패: $err'),
      data: (imprestItems) {
        if (imprestItems.isEmpty) {
          return const _SliverEmptyView(
            icon: Icons.business_center_outlined,
            message: '프로젝트 전도금(운영비) 전용 계좌 내역이 없습니다.',
          );
        }

        return SliverPadding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          sliver: SliverList(
            delegate: SliverChildBuilderDelegate(
              (ctx, index) {
                final acc = imprestItems[index];
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: AccountBalanceCard(item: acc, isImprest: true),
                );
              },
              childCount: imprestItems.length,
            ),
          ),
        );
      },
    );
  }

  String _formatToBillion(int amount) {
    if (amount == 0) return '0원';
    final isNegative = amount < 0;
    final absAmount = amount.abs();
    final double billion = absAmount / 100000000;
    final prefix = isNegative ? '-' : '';

    if (billion >= 10000) {
      final double trillion = billion / 10000;
      return '$prefix${trillion.toStringAsFixed(1)}조원';
    }
    return '$prefix${billion.toStringAsFixed(1)}억원';
  }

  Widget _divider() {
    return Container(
      width: 1,
      height: 24,
      color: context.colors.border,
      margin: const EdgeInsets.symmetric(horizontal: 4),
    );
  }
}

class _SliverLoadingView extends StatelessWidget {
  const _SliverLoadingView();

  @override
  Widget build(BuildContext context) {
    return SliverFillRemaining(
      hasScrollBody: false,
      child: Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: context.colors.accentProject,
        ),
      ),
    );
  }
}

class _SliverErrorView extends StatelessWidget {
  final String message;
  const _SliverErrorView({required this.message});

  @override
  Widget build(BuildContext context) {
    return SliverFillRemaining(
      hasScrollBody: false,
      child: Center(
        child: Text(
          message,
          style: TextStyle(color: context.colors.error),
        ),
      ),
    );
  }
}

class _SliverEmptyView extends StatelessWidget {
  final IconData icon;
  final String message;
  const _SliverEmptyView({required this.icon, required this.message});

  @override
  Widget build(BuildContext context) {
    return SliverFillRemaining(
      hasScrollBody: false,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 40, color: context.colors.textDisabled),
            const SizedBox(height: 12),
            Text(
              message,
              style: AppTextStyles.bodySecond
                  .copyWith(color: context.colors.textMuted),
            ),
          ],
        ),
      ),
    );
  }
}

class _FilterChipButton extends StatelessWidget {
  final String label;
  final bool isSelected;
  final Color? color;
  final VoidCallback onTap;

  const _FilterChipButton({
    required this.label,
    required this.isSelected,
    this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final activeColor = color ?? context.colors.accentProject;
    return Material(
      color: isSelected ? activeColor.withAlpha(25) : context.colors.bgSurface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(4),
        side: BorderSide(
          color: isSelected ? activeColor : context.colors.border,
          width: isSelected ? 1 : 0.8,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(4),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              color: isSelected ? activeColor : context.colors.textSecond,
            ),
          ),
        ),
      ),
    );
  }
}

class _SubTabButton extends StatelessWidget {
  final String title;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  const _SubTabButton({
    required this.title,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Material(
        color: isSelected
            ? context.colors.accentProject.withAlpha(25)
            : context.colors.bgCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(6),
          side: BorderSide(
            color: isSelected
                ? context.colors.accentProject
                : context.colors.border,
            width: isSelected ? 1.2 : 0.8,
          ),
        ),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(6),
          child: Container(
            height: 38,
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  icon,
                  size: 14,
                  color: isSelected
                      ? context.colors.accentProject
                      : context.colors.textSecond,
                ),
                const SizedBox(width: 4),
                Flexible(
                  child: Text(
                    title,
                    style: AppTextStyles.caption.copyWith(
                      color: isSelected
                          ? context.colors.accentProject
                          : context.colors.textSecond,
                      fontWeight:
                          isSelected ? FontWeight.bold : FontWeight.normal,
                      fontSize: 12,
                      height: 1.15,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _KpiItem extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _KpiItem({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(label,
              style: AppTextStyles.caption
                  .copyWith(color: context.colors.textMuted, fontSize: 10.5)),
          const SizedBox(height: 2),
          Text(
            value,
            style: AppTextStyles.titleSm.copyWith(
              color: color,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

class _DatePresetChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _DatePresetChip({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: isSelected
          ? context.colors.accentProject.withAlpha(25)
          : context.colors.bgSurface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(4),
        side: BorderSide(
          color: isSelected
              ? context.colors.accentProject
              : context.colors.border,
          width: isSelected ? 1 : 0.8,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(4),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3.5),
          child: Text(
            label,
            style: TextStyle(
              fontSize: 10.5,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              color: isSelected
                  ? context.colors.accentProject
                  : context.colors.textSecond,
            ),
          ),
        ),
      ),
    );
  }
}

class _PinnedHeaderDelegate extends SliverPersistentHeaderDelegate {
  final Widget child;
  final double height;

  _PinnedHeaderDelegate({required this.child, required this.height});

  @override
  double get minExtent => height;

  @override
  double get maxExtent => height;

  @override
  Widget build(
      BuildContext context, double shrinkOffset, bool overlapsContent) {
    return SizedBox.expand(child: child);
  }

  @override
  bool shouldRebuild(covariant _PinnedHeaderDelegate oldDelegate) {
    return height != oldDelegate.height || child != oldDelegate.child;
  }
}
