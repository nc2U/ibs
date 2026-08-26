import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../contract/data/models/contract_models.dart';
import '../../contract/providers/contract_provider.dart';
import '../data/models/payment_models.dart';
import '../providers/payment_provider.dart';

/// 💳 대금 수납 관리 (Payment) 메인 화면
class PaymentListScreen extends ConsumerStatefulWidget {
  final VoidCallback onBackToMain;

  const PaymentListScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  ConsumerState<PaymentListScreen> createState() => _PaymentListScreenState();
}

class _PaymentListScreenState extends ConsumerState<PaymentListScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _transactionsScrollController = ScrollController();
  final ScrollController _contractsScrollController = ScrollController();
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    _transactionsScrollController.addListener(_onTransactionsScroll);
    _contractsScrollController.addListener(_onContractsScroll);
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _searchController.dispose();
    _transactionsScrollController.dispose();
    _contractsScrollController.dispose();
    super.dispose();
  }

  void _onTransactionsScroll() {
    if (_transactionsScrollController.position.pixels >=
        _transactionsScrollController.position.maxScrollExtent - 200) {
      ref.read(paymentTransactionsProvider.notifier).fetchNextPage();
    }
  }

  void _onContractsScroll() {
    if (_contractsScrollController.position.pixels >=
        _contractsScrollController.position.maxScrollExtent - 200) {
      ref.read(validContractListProvider.notifier).fetchNextPage();
    }
  }

  void _onSearchChanged(String value) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 350), () {
      if (!mounted) return;
      ref.read(paymentSearchQueryProvider.notifier).state = value;
      ref.read(contractSearchQueryProvider.notifier).state = value;
      ref.read(paymentTransactionsProvider.notifier).fetchInitial();
      ref.read(validContractListProvider.notifier).fetchInitial();
    });
  }

  void _onClearSearch() {
    _debounceTimer?.cancel();
    _searchController.clear();
    ref.read(paymentSearchQueryProvider.notifier).state = '';
    ref.read(contractSearchQueryProvider.notifier).state = '';
    ref.read(paymentTransactionsProvider.notifier).fetchInitial();
    ref.read(validContractListProvider.notifier).fetchInitial();
  }

  Future<void> _makePhoneCall(String? phoneNumber, {String? contractorName, String? unitStr}) async {
    if (phoneNumber == null || phoneNumber.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('등록된 연락처가 없습니다.'),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }

    final cleanNumber = phoneNumber.replaceAll(RegExp(r'[^0-9]'), '');

    final bool? shouldCall = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.zero,
          side: BorderSide(color: context.colors.border, width: 0.8),
        ),
        title: Row(
          children: [
            const Icon(Icons.phone_in_talk_outlined, size: 20, color: Color(0xFF0D9488)),
            const SizedBox(width: 8),
            Text(
              '계약자 전화 연결',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${contractorName ?? '계약자'}${unitStr != null ? ' ($unitStr)' : ''}',
              style: AppTextStyles.bodyMd.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              phoneNumber,
              style: AppTextStyles.titleMd.copyWith(
                color: const Color(0xFF0D9488),
                fontWeight: FontWeight.bold,
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              color: context.colors.bgSurface,
              child: Row(
                children: [
                  Icon(Icons.info_outline, size: 14, color: context.colors.textMuted),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      '확인 버튼을 누르면 기기의 기본 전화 앱으로 연결됩니다.',
                      style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0D9488),
              foregroundColor: Colors.white,
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            icon: const Icon(Icons.call, size: 16),
            label: const Text('통화 시작', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (shouldCall == true) {
      final Uri launchUri = Uri(scheme: 'tel', path: cleanNumber);
      if (await canLaunchUrl(launchUri)) {
        await launchUrl(launchUri);
      }
    }
  }

  void _showTransactionDetailBottomSheet(PaymentTransactionItemModel item) {
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
                        color: const Color(0xFF10B981).withAlpha(25),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.receipt_long_outlined, size: 20, color: Color(0xFF10B981)),
                    ),
                    const SizedBox(width: 10),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${item.contractorName ?? '입금자'} (${item.unitStr})',
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          '입금일시: ${item.dealDate}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                      ],
                    ),
                    const Spacer(),
                    IconButton(
                      icon: const Icon(Icons.close, size: 18),
                      onPressed: () => Navigator.pop(ctx),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 14),

                // 상세 데이터 테이블
                _DetailRow(label: '납부 회차', value: item.payName ?? '-'),
                _DetailRow(label: '수납 금액', value: '${numFormat.format(item.amount)}원', isHighlight: true),
                _DetailRow(label: '입금 계좌', value: item.bankAccountName ?? '수납 전용 계좌'),
                if (item.trader != null && item.trader!.isNotEmpty)
                  _DetailRow(label: '실제 통장표시 입금자', value: item.trader!),
                if (item.note != null && item.note!.isNotEmpty)
                  _DetailRow(label: '비고 / 메모', value: item.note!),

                const SizedBox(height: 14),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 10),

                // 하단 퀵 액션
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: context.colors.textPrimary,
                          side: BorderSide(color: context.colors.border),
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onPressed: () {
                          Navigator.pop(ctx);
                          Clipboard.setData(ClipboardData(text: '${item.contractorName} ${item.unitStr} ${numFormat.format(item.amount)}원'));
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('수납 정보가 복사되었습니다.'), behavior: SnackBarBehavior.floating),
                          );
                        },
                        icon: const Icon(Icons.copy_rounded, size: 16),
                        label: const Text('정보 복사', style: TextStyle(fontSize: 12.5)),
                      ),
                    ),
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
    final selectedProject = ref.watch(selectedRealEstateProjectProvider);
    final aggregateAsync = ref.watch(paymentOverallAggregateProvider);
    final currentTab = ref.watch(paymentCurrentSubTabProvider);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: Column(
        children: [
          // ── 1. 수납 모듈 헤더 배너 ─────────────────────────────────────────
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: const Color(0xFF10B981).withAlpha(30),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: const Icon(Icons.payments_outlined,
                      size: 20, color: Color(0xFF10B981)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '대금 수납 관리 (Payment)',
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                        ),
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
                    ref.invalidate(paymentOverallAggregateProvider);
                    ref.invalidate(installmentStatusListProvider);
                    ref.read(paymentTransactionsProvider.notifier).fetchInitial();
                    ref.read(validContractListProvider.notifier).fetchInitial();
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

          // ── 2. KPI 대시보드 (수납 현황 요약 배너) ───────────────────────────
          aggregateAsync.when(
            loading: () => const SizedBox(
              height: 72,
              child: Center(child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))),
            ),
            error: (_, __) => const SizedBox.shrink(),
            data: (aggregate) {
              if (aggregate == null) return const SizedBox.shrink();
              return Container(
                color: context.colors.bgCard,
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                child: Row(
                  children: [
                    _KpiItem(
                      label: '총 분양가',
                      value: _formatToBillion(aggregate.totalSalesPrice),
                      color: context.colors.textPrimary,
                    ),
                    _divider(),
                    _KpiItem(
                      label: '기수납 총액',
                      value: _formatToBillion(aggregate.totalPaidAmount),
                      color: const Color(0xFF10B981),
                    ),
                    _divider(),
                    _KpiItem(
                      label: '수납률',
                      value: '${aggregate.paymentRate.toStringAsFixed(1)}%',
                      color: const Color(0xFF38BDF8),
                    ),
                    _divider(),
                    _KpiItem(
                      label: '미수납액',
                      value: _formatToBillion(aggregate.totalUnpaidAmount),
                      color: const Color(0xFFF59E0B),
                    ),
                  ],
                ),
              );
            },
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 3. 3대 서브 탭 바 ──────────────────────────────────────────
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            child: Row(
              children: [
                _SubTabButton(
                  title: '납부 내역',
                  icon: Icons.receipt_long_outlined,
                  isSelected: currentTab == PaymentSubTab.transactions,
                  onTap: () {
                    ref.read(paymentCurrentSubTabProvider.notifier).state = PaymentSubTab.transactions;
                  },
                ),
                const SizedBox(width: 6),
                _SubTabButton(
                  title: '계약건별 납부',
                  icon: Icons.person_search_outlined,
                  isSelected: currentTab == PaymentSubTab.byContract,
                  onTap: () {
                    ref.read(paymentCurrentSubTabProvider.notifier).state = PaymentSubTab.byContract;
                  },
                ),
                const SizedBox(width: 6),
                _SubTabButton(
                  title: '회차별 현황',
                  icon: Icons.bar_chart_rounded,
                  isSelected: currentTab == PaymentSubTab.byInstallment,
                  onTap: () {
                    ref.read(paymentCurrentSubTabProvider.notifier).state = PaymentSubTab.byInstallment;
                  },
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 4. 검색창 (납부내역 & 계약건별 탭에서 활성화) ────────────────────
          if (currentTab != PaymentSubTab.byInstallment) ...[
            Container(
              color: context.colors.bgCard,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Container(
                height: 38,
                decoration: BoxDecoration(
                  color: context.colors.bgSurface,
                  borderRadius: BorderRadius.zero,
                  border: Border.all(color: context.colors.border, width: 0.8),
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
                    hintText: currentTab == PaymentSubTab.transactions
                        ? '입금자명, 계약자명, 동·호수, 계좌 검색...'
                        : '계약자명, 동·호수, 연락처, 일련번호 검색...',
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
            ),
            Divider(color: context.colors.border, height: 1),
          ],

          // ── 5. 탭별 맞춤 리스트 ────────────────────────────────────────
          Expanded(
            child: Builder(
              builder: (context) {
                switch (currentTab) {
                  case PaymentSubTab.transactions:
                    return _buildTransactionsView();
                  case PaymentSubTab.byContract:
                    return _buildByContractView();
                  case PaymentSubTab.byInstallment:
                    return _buildByInstallmentView();
                }
              },
            ),
          ),
        ],
      ),
    );
  }

  /// 💰 1. 납부 내역 목록 뷰 (실시간 입금 거래 단위)
  Widget _buildTransactionsView() {
    final state = ref.watch(paymentTransactionsProvider);
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
        child: Text('데이터 로드 실패: ${state.error}', style: TextStyle(color: context.colors.error)),
      );
    }

    if (state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search_off_rounded, size: 40, color: context.colors.textDisabled),
            const SizedBox(height: 12),
            Text(
              '조회된 수납 입금 내역이 없습니다.',
              style: AppTextStyles.bodySecond.copyWith(color: context.colors.textMuted),
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
              child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
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
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    color: context.colors.bgSurface,
                    child: Row(
                      children: [
                        if (item.unitTypeName != null) ...[
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                            decoration: BoxDecoration(
                              color: item.parsedTypeColor,
                              borderRadius: BorderRadius.circular(2),
                              border: Border.all(color: item.typeTextColor.withAlpha(100), width: 0.8),
                            ),
                            child: Text(
                              item.unitTypeName!,
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: item.typeTextColor,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                        ],
                        Expanded(
                          child: Text(
                            item.unitStr ?? '-',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                              fontSize: 13.5,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFF10B981).withAlpha(20),
                            border: Border.all(color: const Color(0xFF10B981).withAlpha(80), width: 0.6),
                          ),
                          child: Text(
                            item.payName ?? '수납',
                            style: const TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF10B981),
                            ),
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(Icons.more_vert_rounded, size: 18, color: context.colors.textMuted),
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
                            Text(
                              item.contractorName ?? '계약자 미상',
                              style: AppTextStyles.titleSm.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                                fontSize: 14.5,
                              ),
                            ),
                            const Spacer(),
                            Text(
                              '입금일: ${item.dealDate}',
                              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          color: context.colors.bgSurface,
                          child: Row(
                            children: [
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('수납 금액', style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5)),
                                  const SizedBox(height: 2),
                                  Text(
                                    '${numFormat.format(item.amount)}원',
                                    style: AppTextStyles.titleSm.copyWith(
                                      color: const Color(0xFF10B981),
                                      fontWeight: FontWeight.bold,
                                      fontSize: 13.5,
                                    ),
                                  ),
                                ],
                              ),
                              const Spacer(),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  Text('수납 계좌', style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5)),
                                  const SizedBox(height: 2),
                                  Text(
                                    item.bankAccountName ?? '수납계좌',
                                    style: AppTextStyles.bodySecond.copyWith(
                                      color: context.colors.textPrimary,
                                      fontSize: 11.5,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
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
          ),
        );
      },
    );
  }

  /// 📋 2. 계약건별 납부내역 뷰 (동호수/계약자별 종합 상태 및 바텀시트 연계)
  Widget _buildByContractView() {
    final state = ref.watch(validContractListProvider);

    if (state.isLoading) {
      return Center(
        child: CircularProgressIndicator(strokeWidth: 2, color: context.colors.accentProject),
      );
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(child: Text('데이터 로드 실패: ${state.error}', style: TextStyle(color: context.colors.error)));
    }

    if (state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search_off_rounded, size: 40, color: context.colors.textDisabled),
            const SizedBox(height: 12),
            Text('일치하는 계약 정보가 없습니다.', style: AppTextStyles.bodySecond.copyWith(color: context.colors.textMuted)),
          ],
        ),
      );
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return ListView.separated(
      controller: _contractsScrollController,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      itemCount: itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (ctx, index) {
        if (index == state.items.length) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 14),
            child: Center(child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))),
          );
        }

        final item = state.items[index];
        return _ByContractPaymentCard(
          contract: item,
          onCall: () => _makePhoneCall(
            item.contractor?.contact?.cellPhone,
            contractorName: item.contractor?.name,
            unitStr: item.displayUnit,
          ),
        );
      },
    );
  }

  /// 📊 3. 회차별 납부 현황 뷰 (차수/회차별 집계 카드 목록)
  Widget _buildByInstallmentView() {
    final listAsync = ref.watch(installmentStatusListProvider);
    final numFormat = NumberFormat('#,###');

    return listAsync.when(
      loading: () => Center(
        child: CircularProgressIndicator(strokeWidth: 2, color: context.colors.accentProject),
      ),
      error: (err, _) => Center(
        child: Text('회차별 현황 로드 실패: $err', style: TextStyle(color: context.colors.error)),
      ),
      data: (items) {
        if (items.isEmpty) {
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.bar_chart_outlined, size: 40, color: context.colors.textDisabled),
                const SizedBox(height: 12),
                Text('등록된 납부 회차 정보가 없습니다.', style: AppTextStyles.bodySecond.copyWith(color: context.colors.textMuted)),
              ],
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          itemCount: items.length,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (ctx, index) {
            final order = items[index];

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
                  // 상단 헤더
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
                    color: context.colors.bgSurface,
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: const Color(0xFF38BDF8).withAlpha(25),
                            borderRadius: BorderRadius.circular(2),
                            border: Border.all(color: const Color(0xFF38BDF8).withAlpha(100), width: 0.8),
                          ),
                          child: Text(
                            order.payName,
                            style: const TextStyle(
                              fontSize: 11.5,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF38BDF8),
                            ),
                          ),
                        ),
                        if (order.aliasName != null && order.aliasName!.isNotEmpty) ...[
                          const SizedBox(width: 8),
                          Text(
                            '(${order.aliasName})',
                            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5),
                          ),
                        ],
                        const Spacer(),
                        Text(
                          '약정일: ${order.displayDueDate}',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textMuted,
                            fontWeight: FontWeight.w600,
                            fontSize: 11.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Divider(color: context.colors.border, height: 1),

                  // 본문 요약 바
                  Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              '수납률: ${order.collectionRate.toStringAsFixed(1)}%',
                              style: AppTextStyles.titleSm.copyWith(
                                color: order.collectionRate >= 90
                                    ? const Color(0xFF10B981)
                                    : (order.collectionRate >= 50 ? const Color(0xFF38BDF8) : const Color(0xFFF59E0B)),
                                fontWeight: FontWeight.bold,
                                fontSize: 14.5,
                              ),
                            ),
                            const Spacer(),
                            if (order.payRatio > 0)
                              Text(
                                '회당 비율: ${order.payRatio.toStringAsFixed(0)}%',
                                style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5),
                              ),
                          ],
                        ),
                        const SizedBox(height: 10),

                        // 프로그레스 바
                        ClipRRect(
                          borderRadius: BorderRadius.circular(2),
                          child: LinearProgressIndicator(
                            value: (order.collectionRate / 100).clamp(0.0, 1.0),
                            minHeight: 6,
                            backgroundColor: context.colors.border,
                            color: order.collectionRate >= 90
                                ? const Color(0xFF10B981)
                                : const Color(0xFF38BDF8),
                          ),
                        ),
                        const SizedBox(height: 12),

                        // 금액 요약 박스
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                          color: context.colors.bgSurface,
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('실제 수납액', style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5)),
                                    const SizedBox(height: 2),
                                    Text(
                                      order.totalPaidAmount > 0
                                          ? '${numFormat.format(order.totalPaidAmount)}원'
                                          : '0원',
                                      style: AppTextStyles.bodySecond.copyWith(
                                        color: const Color(0xFF10B981),
                                        fontWeight: FontWeight.bold,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Container(width: 1, height: 20, color: context.colors.border),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('총 약정액', style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5)),
                                    const SizedBox(height: 2),
                                    Text(
                                      order.totalDueAmount > 0
                                          ? '${numFormat.format(order.totalDueAmount)}원'
                                          : '산정 전',
                                      style: AppTextStyles.bodySecond.copyWith(
                                        color: context.colors.textPrimary,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 12,
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

  String _formatToBillion(int amount) {
    if (amount <= 0) return '0원';
    final double billion = amount / 100000000;
    if (billion >= 10000) {
      final double trillion = billion / 10000;
      return '${trillion.toStringAsFixed(1)}조원';
    }
    return '${billion.toStringAsFixed(1)}억원';
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

/// 📋 계약건별 수납 종합 카드 (Payment 전용)
class _ByContractPaymentCard extends StatelessWidget {
  final ContractItemModel contract;
  final VoidCallback onCall;

  const _ByContractPaymentCard({
    required this.contract,
    required this.onCall,
  });

  @override
  Widget build(BuildContext context) {
    final numFormat = NumberFormat('#,###');
    final contractor = contract.contractor;

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
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                  decoration: BoxDecoration(
                    color: contract.parsedTypeColor,
                    borderRadius: BorderRadius.circular(2),
                    border: Border.all(color: contract.typeBorderColor, width: 0.8),
                  ),
                  child: Text(
                    contract.unitTypeName ?? '타입',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: contract.typeTextColor,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    contract.displayUnit,
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF10B981).withAlpha(20),
                    border: Border.all(color: const Color(0xFF10B981).withAlpha(80), width: 0.6),
                  ),
                  child: Text(
                    '수납 ${contract.paymentRate.toStringAsFixed(0)}%',
                    style: const TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF10B981),
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
                    Text(
                      contractor?.name ?? '계약자 미등록',
                      style: AppTextStyles.titleSm.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                        fontSize: 14.5,
                      ),
                    ),
                    const SizedBox(width: 8),
                    if (contract.serialNumber != null && contract.serialNumber!.isNotEmpty)
                      Text(
                        '[${contract.serialNumber}]',
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
                      ),
                    const Spacer(),
                    if (contractor?.contact?.cellPhone != null)
                      TextButton.icon(
                        onPressed: onCall,
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        icon: const Icon(Icons.phone_outlined, size: 13, color: Color(0xFF0D9488)),
                        label: Text(
                          contractor!.contact!.cellPhone!,
                          style: const TextStyle(fontSize: 11.5, color: Color(0xFF0D9488), fontWeight: FontWeight.bold),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  color: context.colors.bgSurface,
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('분양 공급가', style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5)),
                            const SizedBox(height: 2),
                            Text(
                              contract.price > 0 ? '${numFormat.format(contract.price)}원' : '산정 전',
                              style: AppTextStyles.bodySecond.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                                fontSize: 12.5,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Container(width: 1, height: 20, color: context.colors.border),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('기수납 누계', style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5)),
                            const SizedBox(height: 2),
                            Text(
                              '${numFormat.format(contract.totalPaid)}원',
                              style: AppTextStyles.bodySecond.copyWith(
                                color: const Color(0xFF10B981),
                                fontWeight: FontWeight.bold,
                                fontSize: 12.5,
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
  }
}

class _DetailRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isHighlight;

  const _DetailRow({required this.label, required this.value, this.isHighlight = false});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(label, style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 12)),
          ),
          Expanded(
            child: Text(
              value,
              style: AppTextStyles.bodySecond.copyWith(
                color: isHighlight ? const Color(0xFF10B981) : context.colors.textPrimary,
                fontWeight: isHighlight ? FontWeight.bold : FontWeight.normal,
                fontSize: 13,
              ),
            ),
          ),
        ],
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
        color: isSelected ? context.colors.accentProject.withAlpha(25) : context.colors.bgCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.zero,
          side: BorderSide(
            color: isSelected ? context.colors.accentProject : context.colors.border,
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
                  color: isSelected ? context.colors.accentProject : context.colors.textSecond,
                ),
                const SizedBox(width: 4),
                Text(
                  title,
                  style: AppTextStyles.caption.copyWith(
                    color: isSelected ? context.colors.accentProject : context.colors.textSecond,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
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
          Text(label, style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5)),
          const SizedBox(height: 2),
          Text(
            value,
            style: AppTextStyles.titleSm.copyWith(
              color: color,
              fontSize: 12.5,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
