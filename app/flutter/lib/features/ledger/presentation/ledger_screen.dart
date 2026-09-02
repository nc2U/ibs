import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../contract/data/contract_repository.dart';
import '../../contract/data/models/contract_models.dart';
import '../../contract/providers/contract_provider.dart';
import '../../payment/providers/payment_provider.dart';
import '../../project/presentation/project_screen.dart';
import '../data/ledger_repository.dart';
import '../data/models/ledger_models.dart';
import '../providers/ledger_provider.dart';
import 'widgets/cashflow_mini_chart_card.dart';

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
      ref.read(projectTransactionsProvider.notifier).fetchNextPage();
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
        final lastDay = DateTime(now.year, now.month + 1, 0).day;
        to = DateFormat('yyyy-MM-').format(now) + lastDay.toString().padLeft(2, '0');
        break;
      case LedgerDatePreset.lastMonth:
        final lastMonth = DateTime(now.year, now.month - 1, 1);
        from = DateFormat('yyyy-MM-01').format(lastMonth);
        final lastDay = DateTime(lastMonth.year, lastMonth.month + 1, 0).day;
        to = DateFormat('yyyy-MM-').format(lastMonth) + lastDay.toString().padLeft(2, '0');
        break;
      case LedgerDatePreset.last3Months:
        final threeMonthsAgo = DateTime(now.year, now.month - 2, 1);
        from = DateFormat('yyyy-MM-01').format(threeMonthsAgo);
        final lastDay = DateTime(now.year, now.month + 1, 0).day;
        to = DateFormat('yyyy-MM-').format(now) + lastDay.toString().padLeft(2, '0');
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

  /// ✏️ 적요 및 현장 메모 빠른 수정 다이얼로그
  void _showEditNoteDialog(ProjectTransactionItemModel item) {
    final contentCtrl = TextEditingController(text: item.content ?? '');
    final noteCtrl = TextEditingController(text: item.note ?? '');

    showDialog(
      context: context,
      builder: (dialogCtx) {
        return AlertDialog(
          backgroundColor: context.colors.bgCard,
          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
          title: Row(
            children: [
              const Icon(Icons.edit_note_rounded,
                  color: Color(0xFFF59E0B), size: 22),
              const SizedBox(width: 8),
              Text(
                '적요 및 메모 수정',
                style: AppTextStyles.titleSm.copyWith(
                  color: context.colors.textPrimary,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '거래일자: ${item.dealDate} | 계좌: ${item.bankAccountName ?? ''}',
                  style: AppTextStyles.caption
                      .copyWith(color: context.colors.textMuted),
                ),
                const SizedBox(height: 14),

                // 적요 입력
                Text(
                  '적요 (거래 내용)',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                TextField(
                  controller: contentCtrl,
                  style: AppTextStyles.bodySecond
                      .copyWith(color: context.colors.textPrimary),
                  decoration: InputDecoration(
                    isDense: true,
                    hintText: '적요를 입력하세요',
                    hintStyle: AppTextStyles.caption
                        .copyWith(color: context.colors.textMuted),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.zero,
                      borderSide: BorderSide(color: context.colors.border),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 8),
                  ),
                ),
                const SizedBox(height: 14),

                // 비고/메모 입력
                Text(
                  '비고 / 현장 메모 (담당자 메모)',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                TextField(
                  controller: noteCtrl,
                  maxLines: 3,
                  style: AppTextStyles.bodySecond
                      .copyWith(color: context.colors.textPrimary),
                  decoration: InputDecoration(
                    isDense: true,
                    hintText: '현장 지출 사유나 비고 메모를 입력하세요',
                    hintStyle: AppTextStyles.caption
                        .copyWith(color: context.colors.textMuted),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.zero,
                      borderSide: BorderSide(color: context.colors.border),
                    ),
                    contentPadding: const EdgeInsets.all(10),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogCtx),
              child: Text('취소',
                  style: TextStyle(color: context.colors.textSecond)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: context.colors.accentProject,
                foregroundColor: Colors.white,
                shape: const RoundedRectangleBorder(
                    borderRadius: BorderRadius.zero),
              ),
              onPressed: () async {
                Navigator.pop(dialogCtx);
                final repo = ref.read(ledgerRepositoryProvider);
                final success = await repo.updateTransactionNoteAndContent(
                  pk: item.pk,
                  content: contentCtrl.text.trim(),
                  note: noteCtrl.text.trim(),
                );

                if (mounted) {
                  if (success) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('전표 적요 및 메모가 저장되었습니다.'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                    ref
                        .read(projectTransactionsProvider.notifier)
                        .fetchInitial();
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: const Text('저장에 실패했습니다. 권한을 확인해주세요.'),
                        backgroundColor: context.colors.error,
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  }
                }
              },
              child: const Text('저장하기'),
            ),
          ],
        );
      },
    );
  }

  void _showTransactionDetailBottomSheet(ProjectTransactionItemModel item) {
    final numFormat = NumberFormat('#,###');

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) {
        return SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: item.sortColor.withAlpha(25),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        item.isIncome
                            ? Icons.arrow_downward_rounded
                            : (item.isExpense
                                ? Icons.arrow_upward_rounded
                                : Icons.swap_horiz_rounded),
                        size: 20,
                        color: item.sortColor,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item.content ?? '거래 전표 상세',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          Text(
                            '거래일시: ${item.dealDate}',
                            style: AppTextStyles.caption
                                .copyWith(color: context.colors.textMuted),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, size: 18),
                      onPressed: () => Navigator.pop(ctx),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 14),

                // 상세 내용
                _DetailRow(
                  label: '거래 구분',
                  value: item.sortName ?? '출납',
                  isHighlight: true,
                  color: item.sortColor,
                ),
                _DetailRow(
                  label: '거래 금액',
                  value: '${item.sortSign}${numFormat.format(item.amount)}원',
                  isHighlight: true,
                  color: item.sortColor,
                ),
                _DetailRow(
                  label: '거래 계좌',
                  value: item.bankAccountName ?? '프로젝트 전용계좌',
                ),
                if (item.trader != null && item.trader!.isNotEmpty)
                  _DetailRow(label: '거래처 / 입금자', value: item.trader!),
                if (item.accountName != null && item.accountName!.isNotEmpty)
                  _DetailRow(label: '대표 계정과목', value: item.accountName!),
                if (item.note != null && item.note!.isNotEmpty)
                  _DetailRow(label: '비고 / 메모', value: item.note!),

                // 복식분개 항목이 있는 경우
                if (item.accountingEntries.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text(
                    '📑 회계 분개 상세 (${item.accountingEntries.length}건)',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textMuted,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.all(8),
                    color: context.colors.bgSurface,
                    child: Column(
                      children: item.accountingEntries.map((e) {
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 2),
                          child: Row(
                            children: [
                              Text(
                                e.accountName ?? '계정',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textPrimary,
                                ),
                              ),
                              if (e.trader != null && e.trader!.isNotEmpty) ...[
                                const SizedBox(width: 6),
                                Text(
                                  '(${e.trader})',
                                  style: AppTextStyles.caption.copyWith(
                                    color: context.colors.textMuted,
                                    fontSize: 11,
                                  ),
                                ),
                              ],
                              const Spacer(),
                              Text(
                                '${numFormat.format(e.amount)}원',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textPrimary,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],

                const SizedBox(height: 14),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 10),

                // 하단 스마트 액션 버튼들
                Column(
                  children: [
                    Row(
                      children: [
                        // 1. 적요 및 현장 메모 빠른 수정 버튼
                        Expanded(
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFFF59E0B),
                              foregroundColor: Colors.white,
                              shape: const RoundedRectangleBorder(
                                  borderRadius: BorderRadius.zero),
                              padding: const EdgeInsets.symmetric(vertical: 10),
                            ),
                            onPressed: () {
                              Navigator.pop(ctx);
                              _showEditNoteDialog(item);
                            },
                            icon: const Icon(Icons.edit_note_rounded, size: 17),
                            label: const Text('적요/메모 수정',
                                style: TextStyle(
                                    fontSize: 12.5,
                                    fontWeight: FontWeight.bold)),
                          ),
                        ),
                        const SizedBox(width: 8),

                        // 2. 전표 복사 버튼
                        Expanded(
                          child: OutlinedButton.icon(
                            style: OutlinedButton.styleFrom(
                              foregroundColor: context.colors.textPrimary,
                              side: BorderSide(color: context.colors.border),
                              shape: const RoundedRectangleBorder(
                                  borderRadius: BorderRadius.zero),
                              padding: const EdgeInsets.symmetric(vertical: 10),
                            ),
                            onPressed: () {
                              Navigator.pop(ctx);
                              Clipboard.setData(ClipboardData(
                                  text:
                                      '${item.dealDate} [${item.sortName}] ${item.content} ${numFormat.format(item.amount)}원'));
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('전표 정보가 복사되었습니다.'),
                                  behavior: SnackBarBehavior.floating,
                                ),
                              );
                            },
                            icon: const Icon(Icons.copy_rounded, size: 16),
                            label: const Text('전표 복사',
                                style: TextStyle(fontSize: 12.5)),
                          ),
                        ),
                      ],
                    ),

                    // 3. 순수 분양대금(분담금, is_payment=true) 수납건인 경우에만: 계약건 납부목록 전체보기 연동
                    if (item.paymentContractEntry != null) ...[
                      const SizedBox(height: 8),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: const Color(0xFF0D9488),
                            side: const BorderSide(
                                color: Color(0xFF0D9488), width: 0.9),
                            shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.zero),
                            padding: const EdgeInsets.symmetric(vertical: 10),
                          ),
                          onPressed: () async {
                            Navigator.pop(ctx);
                            final contractEntry = item.paymentContractEntry!;

                            // 1. 해당 계약건 Provider에 세팅 (메모리 탐색 또는 API 단건 조회)
                            final contractsState = ref.read(validContractListProvider);
                            ContractItemModel? targetContract;
                            for (final c in contractsState.items) {
                              if (c.pk == contractEntry.contractId) {
                                targetContract = c;
                                break;
                              }
                            }

                            if (targetContract == null && contractEntry.contractId != null) {
                              // 계약 목록이 아직 로드되지 않았거나 첫 페이지에 없는 경우 단건 API 조회
                              final contractRepo = ref.read(contractRepositoryProvider);
                              targetContract = await contractRepo.fetchContractDetail(contractEntry.contractId!);
                            }

                            if (targetContract != null) {
                              ref.read(selectedContractForPaymentProvider.notifier).state = targetContract;
                            }

                            // 2. 수납 관리 서브모듈로 즉시 전환 및 계약건별 탭 활성화
                            ref.read(paymentCurrentSubTabProvider.notifier).state =
                                PaymentSubTab.byContract;
                            ref.read(projectActiveModuleProvider.notifier).state =
                                ProjectActiveModule.payment;
                          },
                          icon: const Icon(Icons.receipt_long_outlined, size: 16),
                          label: Text(
                            '이 계약건(${item.paymentContractEntry!.contractDisplay ?? '계약자'}) 전체 납부내역 보기',
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
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
          // ── 1. 회계 자금 헤더 배너 ─────────────────────────────────────────
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: const Color(0xFFF59E0B).withAlpha(30),
                    borderRadius: BorderRadius.zero,
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
                            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                            decoration: BoxDecoration(
                              color: const Color(0xFFF59E0B).withAlpha(20),
                              border: Border.all(color: const Color(0xFFF59E0B).withAlpha(120), width: 0.8),
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
                        selectedProject?.name ?? '부동산 개발 프로젝트',
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

          // ── 2. KPI 대시보드 (자금 현황 요약 배너) ───────────────────────────
          aggregateAsync.when(
            loading: () => const SizedBox(
              height: 72,
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
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
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
          Divider(color: context.colors.border, height: 1),

          // ── 2-2. 최근 6개월 캐시플로우 미니 차트 (월별 입출금 추이 시각화) ──
          const CashflowMiniChartCard(),
          Divider(color: context.colors.border, height: 1),

          // ── 3. 3대 서브 탭 바 ──────────────────────────────────────────
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            child: Row(
              children: [
                _SubTabButton(
                  title: '출납 내역',
                  icon: Icons.receipt_outlined,
                  isSelected: currentTab == LedgerSubTab.transactions,
                  onTap: () {
                    ref.read(ledgerCurrentSubTabProvider.notifier).state =
                        LedgerSubTab.transactions;
                  },
                ),
                const SizedBox(width: 6),
                _SubTabButton(
                  title: '계좌별 잔액',
                  icon: Icons.account_balance_outlined,
                  isSelected: currentTab == LedgerSubTab.balanceStatus,
                  onTap: () {
                    ref.read(ledgerCurrentSubTabProvider.notifier).state =
                        LedgerSubTab.balanceStatus;
                  },
                ),
                const SizedBox(width: 6),
                _SubTabButton(
                  title: '전도금 정산',
                  icon: Icons.business_center_outlined,
                  isSelected: currentTab == LedgerSubTab.imprest,
                  onTap: () {
                    ref.read(ledgerCurrentSubTabProvider.notifier).state =
                        LedgerSubTab.imprest;
                  },
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 4. 검색 & 기간/계좌 필터 바 (출납내역 탭에서 활성화) ──────────────
          if (currentTab == LedgerSubTab.transactions) ...[
            Container(
              color: context.colors.bgCard,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              child: Column(
                children: [
                  // 1) 통합 검색창
                  Container(
                    height: 38,
                    decoration: BoxDecoration(
                      color: context.colors.bgSurface,
                      borderRadius: BorderRadius.zero,
                      border:
                          Border.all(color: context.colors.border, width: 0.8),
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
                                icon: const Icon(Icons.clear_rounded, size: 16),
                                color: context.colors.textMuted,
                                onPressed: _onClearSearch,
                              )
                            : null,
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(vertical: 9),
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),

                  // 2) 기간 선택 바 (프리셋 칩 + 직접 지정 달력)
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        _DatePresetChip(
                          label: '전체기간',
                          isSelected: datePreset == LedgerDatePreset.all,
                          onTap: () => _applyDatePreset(LedgerDatePreset.all),
                        ),
                        const SizedBox(width: 4),
                        _DatePresetChip(
                          label: '오늘',
                          isSelected: datePreset == LedgerDatePreset.today,
                          onTap: () => _applyDatePreset(LedgerDatePreset.today),
                        ),
                        const SizedBox(width: 4),
                        _DatePresetChip(
                          label: '이번달',
                          isSelected: datePreset == LedgerDatePreset.thisMonth,
                          onTap: () => _applyDatePreset(LedgerDatePreset.thisMonth),
                        ),
                        const SizedBox(width: 4),
                        _DatePresetChip(
                          label: '지난달',
                          isSelected: datePreset == LedgerDatePreset.lastMonth,
                          onTap: () => _applyDatePreset(LedgerDatePreset.lastMonth),
                        ),
                        const SizedBox(width: 4),
                        _DatePresetChip(
                          label: '최근3개월',
                          isSelected: datePreset == LedgerDatePreset.last3Months,
                          onTap: () => _applyDatePreset(LedgerDatePreset.last3Months),
                        ),
                        const SizedBox(width: 4),
                        _DatePresetChip(
                          label: '올해',
                          isSelected: datePreset == LedgerDatePreset.thisYear,
                          onTap: () => _applyDatePreset(LedgerDatePreset.thisYear),
                        ),
                        const SizedBox(width: 6),

                        // 달력 직접 지정 버튼
                        InkWell(
                          onTap: _pickDateRange,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3.5),
                            decoration: BoxDecoration(
                              color: datePreset == LedgerDatePreset.custom
                                  ? context.colors.accentProject.withAlpha(25)
                                  : context.colors.bgSurface,
                              border: Border.all(
                                color: datePreset == LedgerDatePreset.custom
                                    ? context.colors.accentProject
                                    : context.colors.border,
                                width: datePreset == LedgerDatePreset.custom ? 1 : 0.8,
                              ),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.calendar_month_outlined,
                                  size: 12,
                                  color: datePreset == LedgerDatePreset.custom
                                      ? context.colors.accentProject
                                      : context.colors.textMuted,
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  datePreset == LedgerDatePreset.custom && fromDate != null && toDate != null
                                      ? '${fromDate.substring(5)} ~ ${toDate.substring(5)}'
                                      : '직접선택',
                                  style: TextStyle(
                                    fontSize: 10.5,
                                    fontWeight: datePreset == LedgerDatePreset.custom ? FontWeight.bold : FontWeight.normal,
                                    color: datePreset == LedgerDatePreset.custom
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

                  // 3) 거래구분 빠른 필터 칩(전체/수입/지출/대체) & 계좌 선택 드롭다운
                  Row(
                    children: [
                      _FilterChipButton(
                        label: '전체',
                        isSelected: sortFilter == '',
                        onTap: () {
                          ref.read(ledgerSortFilterProvider.notifier).state = '';
                          ref.read(projectTransactionsProvider.notifier).fetchInitial();
                        },
                      ),
                      const SizedBox(width: 4),
                      _FilterChipButton(
                        label: '수입(+)',
                        isSelected: sortFilter == '1',
                        color: const Color(0xFF10B981),
                        onTap: () {
                          ref.read(ledgerSortFilterProvider.notifier).state = '1';
                          ref.read(projectTransactionsProvider.notifier).fetchInitial();
                        },
                      ),
                      const SizedBox(width: 4),
                      _FilterChipButton(
                        label: '지출(-)',
                        isSelected: sortFilter == '2',
                        color: const Color(0xFFEF4444),
                        onTap: () {
                          ref.read(ledgerSortFilterProvider.notifier).state = '2';
                          ref.read(projectTransactionsProvider.notifier).fetchInitial();
                        },
                      ),
                      const SizedBox(width: 4),
                      _FilterChipButton(
                        label: '대체',
                        isSelected: sortFilter == '3',
                        color: const Color(0xFF38BDF8),
                        onTap: () {
                          ref.read(ledgerSortFilterProvider.notifier).state = '3';
                          ref.read(projectTransactionsProvider.notifier).fetchInitial();
                        },
                      ),
                      const Spacer(),

                      // 계좌 선택 드롭다운 (고정 폭 및 말줄임표 처리로 오버플로우 방지)
                      bankAccountsAsync.when(
                        data: (banks) {
                          if (banks.isEmpty) return const SizedBox.shrink();
                          final selectedAlias = selectedBankAcc == null
                              ? '계좌 전체'
                              : banks
                                  .firstWhere((b) => b.pk == selectedBankAcc,
                                      orElse: () => banks.first)
                                  .aliasName;

                          return PopupMenuButton<int>(
                            initialValue: selectedBankAcc ?? 0,
                            tooltip: selectedAlias,
                            onSelected: (val) {
                              ref
                                  .read(
                                      ledgerSelectedBankAccFilterProvider.notifier)
                                  .state = val == 0 ? null : val;
                              ref
                                  .read(projectTransactionsProvider.notifier)
                                  .fetchInitial();
                            },
                            child: Container(
                              constraints: const BoxConstraints(maxWidth: 130),
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: selectedBankAcc != null
                                    ? context.colors.accentProject.withAlpha(20)
                                    : context.colors.bgSurface,
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
                                        fontWeight: selectedBankAcc != null
                                            ? FontWeight.bold
                                            : FontWeight.normal,
                                        color: selectedBankAcc != null
                                            ? context.colors.accentProject
                                            : context.colors.textPrimary,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  const SizedBox(width: 2),
                                  Icon(Icons.arrow_drop_down,
                                      size: 14, color: context.colors.textMuted),
                                ],
                              ),
                            ),
                            itemBuilder: (ctx) => [
                              const PopupMenuItem<int>(
                                value: 0,
                                child: Text('전체 계좌', style: TextStyle(fontSize: 12)),
                              ),
                              ...banks.map(
                                (b) => PopupMenuItem<int>(
                                  value: b.pk,
                                  child: Text(b.aliasName, style: const TextStyle(fontSize: 12)),
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
            Divider(color: context.colors.border, height: 1),
          ],

          // ── 5. 탭별 맞춤 리스트 ────────────────────────────────────────
          Expanded(
            child: Builder(
              builder: (context) {
                switch (currentTab) {
                  case LedgerSubTab.transactions:
                    return _buildTransactionsView();
                  case LedgerSubTab.balanceStatus:
                    return _buildBalanceStatusView();
                  case LedgerSubTab.imprest:
                    return _buildImprestView();
                }
              },
            ),
          ),
        ],
      ),
    );
  }

  /// 💳 1. 출납 전표 목록 뷰
  Widget _buildTransactionsView() {
    final state = ref.watch(projectTransactionsProvider);
    final numFormat = NumberFormat('#,###');

    if (state.isLoading) {
      return Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: context.colors.accentProject,
        ),
      );
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Text('데이터 로드 실패: ${state.error}',
            style: TextStyle(color: context.colors.error)),
      );
    }

    if (state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search_off_rounded,
                size: 40, color: context.colors.textDisabled),
            const SizedBox(height: 12),
            Text(
              '조회된 출납 거래 내역이 없습니다.',
              style: AppTextStyles.bodySecond
                  .copyWith(color: context.colors.textMuted),
            ),
          ],
        ),
      );
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return ListView.separated(
      controller: _transactionsScrollController,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      itemCount: itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (ctx, index) {
        if (index == state.items.length) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 14),
            child: Center(
              child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2)),
            ),
          );
        }

        final item = state.items[index];
        return Container(
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.zero,
            border: Border.all(
              color: context.colors.textDisabled.withAlpha(180),
              width: 1.2,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withAlpha(12),
                offset: const Offset(0, 2),
                blurRadius: 4,
              ),
            ],
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () => _showTransactionDetailBottomSheet(item),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 카드 상단 헤더
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    color: context.colors.bgSurface,
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: item.sortColor.withAlpha(20),
                            border: Border.all(
                                color: item.sortColor.withAlpha(80), width: 0.6),
                          ),
                          child: Text(
                            item.sortName ?? '출납',
                            style: TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.bold,
                              color: item.sortColor,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            item.bankAccountName ?? '프로젝트 계좌',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                              fontSize: 12.5,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Text(
                          item.dealDate,
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textMuted,
                            fontSize: 11.5,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(Icons.more_vert_rounded,
                            size: 18, color: context.colors.textMuted),
                      ],
                    ),
                  ),
                  Divider(color: context.colors.border, height: 1),

                  // 카드 본문
                  Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                item.content ?? '적요 미입력',
                                style: AppTextStyles.titleSm.copyWith(
                                  color: context.colors.textPrimary,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              '${item.sortSign}${numFormat.format(item.amount)}원',
                              style: AppTextStyles.titleSm.copyWith(
                                color: item.sortColor,
                                fontWeight: FontWeight.bold,
                                fontSize: 14.5,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            if (item.displayTraderName != null &&
                                item.displayTraderName!.isNotEmpty) ...[
                              Icon(Icons.person_outline,
                                  size: 13, color: context.colors.textMuted),
                              const SizedBox(width: 4),
                              Text(
                                item.displayTraderName!,
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textMuted,
                                  fontSize: 11.5,
                                ),
                              ),
                              const SizedBox(width: 8),
                            ],
                            Icon(Icons.folder_open_rounded,
                                size: 13, color: context.colors.textMuted),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                '(${item.displayAccountName})',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textSecond,
                                  fontWeight: item.accountingEntries.length > 1
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                  fontSize: 11.5,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  /// 🏦 2. 계좌별 잔액 현황 뷰
  Widget _buildBalanceStatusView() {
    final balancesAsync = ref.watch(ledgerBalanceByAccountProvider);
    final numFormat = NumberFormat('#,###');

    return balancesAsync.when(
      loading: () => Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: context.colors.accentProject,
        ),
      ),
      error: (err, _) => Center(
        child: Text('잔액 데이터 로드 실패: $err',
            style: TextStyle(color: context.colors.error)),
      ),
      data: (items) {
        if (items.isEmpty) {
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.account_balance_outlined,
                    size: 40, color: context.colors.textDisabled),
                const SizedBox(height: 12),
                Text(
                  '등록된 프로젝트 계좌 정보가 없습니다.',
                  style: AppTextStyles.bodySecond
                      .copyWith(color: context.colors.textMuted),
                ),
              ],
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          itemCount: items.length,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (ctx, index) {
            final acc = items[index];

            return Container(
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.zero,
                border: Border.all(
                  color: context.colors.textDisabled.withAlpha(180),
                  width: 1.2,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withAlpha(12),
                    offset: const Offset(0, 2),
                    blurRadius: 4,
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 헤더
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
                    color: context.colors.bgSurface,
                    child: Row(
                      children: [
                        const Icon(Icons.account_balance_rounded,
                            size: 16, color: Color(0xFF38BDF8)),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            acc.bankAcc,
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                              fontSize: 13.5,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Divider(color: context.colors.border, height: 1),

                  // 본문
                  Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              '현재 잔액',
                              style: AppTextStyles.caption
                                  .copyWith(color: context.colors.textMuted),
                            ),
                            const Spacer(),
                            Text(
                              '${numFormat.format(acc.balance)}원',
                              style: AppTextStyles.titleSm.copyWith(
                                color: acc.balance > 0
                                    ? const Color(0xFF38BDF8)
                                    : context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                                fontSize: 15.5,
                              ),
                            ),
                          ],
                        ),
                        if (acc.bankNum.isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            '계좌번호: ${acc.bankNum}',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textMuted,
                              fontSize: 11,
                            ),
                          ),
                        ],
                        const SizedBox(height: 10),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 8),
                          color: context.colors.bgSurface,
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('총 입금 누계',
                                        style: AppTextStyles.caption.copyWith(
                                            color: context.colors.textMuted,
                                            fontSize: 10.5)),
                                    const SizedBox(height: 2),
                                    Text(
                                      '${numFormat.format(acc.incSum)}원',
                                      style: AppTextStyles.bodySecond.copyWith(
                                        color: const Color(0xFF10B981),
                                        fontWeight: FontWeight.bold,
                                        fontSize: 11.5,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Container(
                                  width: 1,
                                  height: 20,
                                  color: context.colors.border),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('총 출금 누계',
                                        style: AppTextStyles.caption.copyWith(
                                            color: context.colors.textMuted,
                                            fontSize: 10.5)),
                                    const SizedBox(height: 2),
                                    Text(
                                      '${numFormat.format(acc.outSum)}원',
                                      style: AppTextStyles.bodySecond.copyWith(
                                        color: const Color(0xFFEF4444),
                                        fontWeight: FontWeight.bold,
                                        fontSize: 11.5,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  /// 💼 3. 현장 전도금 뷰
  Widget _buildImprestView() {
    final balancesAsync = ref.watch(ledgerBalanceByAccountProvider);
    final numFormat = NumberFormat('#,###');

    return balancesAsync.when(
      loading: () => Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: context.colors.accentProject,
        ),
      ),
      error: (err, _) => Center(
        child: Text('전도금 로드 실패: $err',
            style: TextStyle(color: context.colors.error)),
      ),
      data: (items) {
        final imprestItems =
            items.where((i) => i.bankAcc.contains('운영비') || i.bankAcc.contains('전도금')).toList();

        if (imprestItems.isEmpty) {
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.business_center_outlined,
                    size: 40, color: context.colors.textDisabled),
                const SizedBox(height: 12),
                Text(
                  '현장 전도금(운영비) 전용 계좌 내역이 없습니다.',
                  style: AppTextStyles.bodySecond
                      .copyWith(color: context.colors.textMuted),
                ),
              ],
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          itemCount: imprestItems.length,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (ctx, index) {
            final acc = imprestItems[index];

            return Container(
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.zero,
                border: Border.all(
                  color: context.colors.textDisabled.withAlpha(180),
                  width: 1.2,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withAlpha(12),
                    offset: const Offset(0, 2),
                    blurRadius: 4,
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
                    color: context.colors.bgSurface,
                    child: Row(
                      children: [
                        const Icon(Icons.business_center_rounded,
                            size: 16, color: Color(0xFFF59E0B)),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            acc.bankAcc,
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                              fontSize: 13.5,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF59E0B).withAlpha(20),
                            border: Border.all(
                                color: const Color(0xFFF59E0B).withAlpha(80),
                                width: 0.6),
                          ),
                          child: const Text(
                            '운영비/전도금',
                            style: TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFFF59E0B),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Divider(color: context.colors.border, height: 1),
                  Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text('현장 잔액',
                                style: AppTextStyles.caption
                                    .copyWith(color: context.colors.textMuted)),
                            const Spacer(),
                            Text(
                              '${numFormat.format(acc.balance)}원',
                              style: AppTextStyles.titleSm.copyWith(
                                color: const Color(0xFFF59E0B),
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '정산 누계: 수입 ${numFormat.format(acc.incSum)}원 / 지출 ${numFormat.format(acc.outSum)}원',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textMuted,
                            fontSize: 11.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          },
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

class _DetailRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isHighlight;
  final Color? color;

  const _DetailRow({
    required this.label,
    required this.value,
    this.isHighlight = false,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(label,
                style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted, fontSize: 12)),
          ),
          Expanded(
            child: Text(
              value,
              style: AppTextStyles.bodySecond.copyWith(
                color: color ??
                    (isHighlight
                        ? const Color(0xFF10B981)
                        : context.colors.textPrimary),
                fontWeight:
                    isHighlight ? FontWeight.bold : FontWeight.normal,
                fontSize: 13,
              ),
            ),
          ),
        ],
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
        borderRadius: BorderRadius.zero,
        side: BorderSide(
          color: isSelected ? activeColor : context.colors.border,
          width: isSelected ? 1 : 0.8,
        ),
      ),
      child: InkWell(
        onTap: onTap,
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
          borderRadius: BorderRadius.zero,
          side: BorderSide(
            color: isSelected
                ? context.colors.accentProject
                : context.colors.border,
            width: isSelected ? 1 : 0.8,
          ),
        ),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.zero,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  icon,
                  size: 14,
                  color: isSelected
                      ? context.colors.accentProject
                      : context.colors.textSecond,
                ),
                const SizedBox(width: 4),
                Text(
                  title,
                  style: AppTextStyles.caption.copyWith(
                    color: isSelected
                        ? context.colors.accentProject
                        : context.colors.textSecond,
                    fontWeight:
                        isSelected ? FontWeight.bold : FontWeight.normal,
                    fontSize: 11.5,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
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
        borderRadius: BorderRadius.zero,
        side: BorderSide(
          color: isSelected
              ? context.colors.accentProject
              : context.colors.border,
          width: isSelected ? 1 : 0.8,
        ),
      ),
      child: InkWell(
        onTap: onTap,
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
