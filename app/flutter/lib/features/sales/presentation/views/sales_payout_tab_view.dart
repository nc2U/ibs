import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/sales_models.dart';
import '../../data/sales_repository.dart';
import '../../providers/sales_provider.dart';
import '../widgets/banking_csv_helper.dart';
import '../widgets/payout_detail_sheet.dart';
import '../widgets/person_payout_history_sheet.dart';
import '../widgets/sales_common_widgets.dart';

/// 3. 수수료 지급 관리 탭 뷰 (지급 대장 & 은행 대량 이체 연동 & 대행사 지급 관리)
class SalesPayoutTabView extends ConsumerStatefulWidget {
  final SelectedProject project;

  const SalesPayoutTabView({
    super.key,
    required this.project,
  });

  @override
  ConsumerState<SalesPayoutTabView> createState() => _SalesPayoutTabViewState();
}

class _SalesPayoutTabViewState extends ConsumerState<SalesPayoutTabView> {
  final TextEditingController _payoutSearchController = TextEditingController();
  Timer? _payoutDebounceTimer;
  bool _isBatchProcessing = false;

  @override
  void dispose() {
    _payoutSearchController.dispose();
    _payoutDebounceTimer?.cancel();
    super.dispose();
  }

  void _onPayoutSearchChanged(String value) {
    _payoutDebounceTimer?.cancel();
    _payoutDebounceTimer = Timer(const Duration(milliseconds: 300), () {
      if (!mounted) return;
      ref.read(payoutTabSearchQueryProvider.notifier).state = value.trim();
    });
  }

  Future<void> _handleCompletePeriod(SettlementPeriodModel period) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: Row(
          children: [
            const Icon(Icons.done_all_rounded, size: 20, color: Color(0xFF10B981)),
            const SizedBox(width: 8),
            Text(
              '회차 지급 종결 처리',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Text(
          '【${period.title}】\n\n모든 대상자의 수수료 지급이 완료되었습니까?\n\n회차 상태를 [지급 완료] 상태로 종결 처리합니다.',
          style: AppTextStyles.bodySm.copyWith(
            color: context.colors.textSecond,
            height: 1.4,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF10B981),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('지급 종결'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    try {
      final repo = ref.read(salesRepositoryProvider);
      await repo.completeSettlementPeriod(period.id);
      ref.invalidate(settlementPeriodsProvider);
      ref.invalidate(payoutTabPayoutsProvider);
      ref.invalidate(payoutTabAgencyPayoutsProvider);
      ref.invalidate(commissionPayoutsProvider);
      ref.invalidate(agencyPayoutsProvider);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('정산 회차가 [지급 완료] 상태로 종결되었습니다.'),
          backgroundColor: Color(0xFF10B981),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('지급 종결 처리 실패: $e'),
          backgroundColor: context.colors.error,
        ),
      );
    }
  }

  Future<void> _handleBatchStatusUpdate(
    List<int> ids,
    String targetStatus,
    String statusLabel,
  ) async {
    if (ids.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('상태를 변경할 대상을 1명 이상 선택해 주세요.')),
      );
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: Row(
          children: [
            const Icon(Icons.playlist_add_check, size: 20, color: Color(0xFF10B981)),
            const SizedBox(width: 8),
            Text(
              '일괄 상태 변경',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Text(
          '선택한 ${ids.length}명의 지급 상태를 [ $statusLabel ] 상태로 일괄 변경하시겠습니까?'
          '${targetStatus == '3' ? '\n(지급일자가 오늘 일자로 자동 기록됩니다.)' : ''}',
          style: AppTextStyles.bodySm.copyWith(
            color: context.colors.textSecond,
            height: 1.4,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF10B981),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('일괄 변경'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    setState(() => _isBatchProcessing = true);
    try {
      final repo = ref.read(salesRepositoryProvider);
      await repo.batchUpdatePayStatus(ids, targetStatus);
      ref.invalidate(payoutTabPayoutsProvider);
      ref.invalidate(settlementPeriodsProvider);
      ref.read(payoutTabSelectedIdsProvider.notifier).state = {};

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${ids.length}명의 지급 상태가 [$statusLabel] 상태로 변경되었습니다.'),
          backgroundColor: const Color(0xFF10B981),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('일괄 상태 변경 실패: $e'),
          backgroundColor: context.colors.error,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isBatchProcessing = false);
      }
    }
  }

  Future<void> _handleIndividualStatusUpdate(
    CommissionPayoutModel payout,
    String newStatus,
  ) async {
    if (payout.payStatus == newStatus) return;

    try {
      final repo = ref.read(salesRepositoryProvider);
      await repo.updatePayStatus(payout.id, newStatus);
      ref.invalidate(payoutTabPayoutsProvider);
      ref.invalidate(settlementPeriodsProvider);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('지급 상태가 업데이트되었습니다.'),
          backgroundColor: Color(0xFF10B981),
          duration: Duration(seconds: 1),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('지급 상태 변경 실패: $e'),
          backgroundColor: context.colors.error,
        ),
      );
    }
  }

  Future<void> _handleAgencyStatusUpdate(AgencyPayoutModel ap, String newStatus) async {
    if (ap.payStatus == newStatus) return;

    try {
      final repo = ref.read(salesRepositoryProvider);
      await repo.updateAgencyPayStatus(ap.id, newStatus);
      ref.invalidate(payoutTabAgencyPayoutsProvider);
      ref.invalidate(agencyPayoutsProvider);
      ref.invalidate(settlementPeriodsProvider);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${ap.agencyName ?? "대행사"}의 지급 상태가 변경되었습니다.'),
          backgroundColor: const Color(0xFF8B5CF6),
          duration: const Duration(seconds: 1),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('대행사 상태 변경 실패: $e'),
          backgroundColor: context.colors.error,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final periodsAsync = ref.watch(settlementPeriodsProvider);
    final currentPeriod = ref.watch(currentPayoutPeriodProvider);
    final payoutsAsync = ref.watch(payoutTabPayoutsProvider);
    final filteredList = ref.watch(payoutTabFilteredListProvider);
    final summary = ref.watch(payoutTabSummaryProvider);
    final selectedIds = ref.watch(payoutTabSelectedIdsProvider);
    final payoutMode = ref.watch(payoutTabModeProvider);
    final agencyPayoutsAsync = ref.watch(payoutTabAgencyPayoutsProvider);
    final agencySummary = ref.watch(payoutTabAgencySummaryProvider);
    final filteredAgencyPayouts = ref.watch(payoutTabFilteredAgencyPayoutsProvider);

    return RefreshIndicator(
      color: const Color(0xFF10B981),
      onRefresh: () async {
        ref.read(payoutTabSelectedIdsProvider.notifier).state = {};
        await Future.wait([
          ref.refresh(settlementPeriodsProvider.future),
          ref.refresh(payoutTabPayoutsProvider.future),
          ref.refresh(payoutTabAgencyPayoutsProvider.future),
        ]);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 1. 상단 안내 배너
          buildInfoBanner(
            context: context,
            title: '수수료 지급 대장 & 금융 이체',
            subtitle: '확정된 회차별 수수료 이체 집행, 지급 승인/완료 처리 및 개인/외주 대행사 지급 관리를 수행합니다.',
            icon: Icons.account_balance_outlined,
            color: const Color(0xFF10B981),
          ),
          const SizedBox(height: 14),

          // 2. 정산 회차 선택기 & 회차 종결 관리 바
          periodsAsync.when(
            loading: () => Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: context.colors.border),
              ),
              child: const Center(
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF10B981)),
                ),
              ),
            ),
            error: (err, _) => buildErrorBanner(
              context: context,
              message: '회차 데이터를 불러오지 못했습니다: $err',
              onRetry: () => ref.invalidate(settlementPeriodsProvider),
            ),
            data: (periods) => _buildPayoutPeriodSection(widget.project, periods, currentPeriod, summary),
          ),
          const SizedBox(height: 14),

          // 2-1. 개인별 vs 대행사별 지급 전환 탭 (Segmented Control)
          _buildPayoutSubModeSelector(payoutMode),
          const SizedBox(height: 14),

          if (payoutMode == 'person') ...[
            // 3. 2×2 지급 진행 현황 대시보드 (개인)
            _buildPayoutSummaryKpi(summary),
            const SizedBox(height: 14),

            // 4. 검색 & 지급 상태 필터 바
            _buildPayoutFilterBar(),
            const SizedBox(height: 14),

            // 5. 다중 선택 & 일괄 상태 변경 & 이체 파일 다운로드 툴바
            _buildPayoutBatchActionBar(widget.project, currentPeriod, filteredList, selectedIds),
            const SizedBox(height: 14),

            // 6. 개인별 지급 대장 카드 리스트
            _buildPayoutExecutionListSection(widget.project, currentPeriod, payoutsAsync, filteredList, selectedIds),
          ] else ...[
            // 3-B. 2×2 대행사 지급 진행 현황 대시보드
            _buildPayoutAgencySummaryKpi(agencySummary),
            const SizedBox(height: 14),

            // 4-B. 대행사 검색 & 상태 필터 바
            _buildPayoutAgencyFilterBar(),
            const SizedBox(height: 14),

            // 5-B. 대행사별 지급 명세 카드 리스트
            _buildPayoutAgencyExecutionListSection(widget.project, currentPeriod, agencyPayoutsAsync, filteredAgencyPayouts),
          ],
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  /// 지급 관리 전용 회차 선택기 & 종결 관리 바
  Widget _buildPayoutPeriodSection(
    SelectedProject project,
    List<SettlementPeriodModel> periods,
    SettlementPeriodModel? currentPeriod,
    PayoutStatusSummaryModel summary,
  ) {
    final canPayout = ref.can(Perm.salesPayout, projectSlug: project.slug);

    if (periods.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: const Color(0xFF10B981).withAlpha(80), width: 0.8),
        ),
        child: Column(
          children: [
            Icon(Icons.event_busy_outlined, size: 36, color: context.colors.textMuted),
            const SizedBox(height: 10),
            Text(
              '등록된 정산 회차가 없습니다',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              '[수수료 정산] 탭에서 정산 회차를 생성하고 정산을 확정한 후 지급 관리를 진행하세요.',
              textAlign: TextAlign.center,
              style: AppTextStyles.caption.copyWith(color: context.colors.textSecond),
            ),
          ],
        ),
      );
    }

    final period = currentPeriod ?? periods.first;

    // 모든 인원이 지급 완료되었고, 회차가 확정 상태인 경우 종결 가능
    final canCompletePeriod = period.isConfirmed &&
        summary.totalCount > 0 &&
        summary.paidCount == summary.totalCount;

    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 회차 헤더 & 선택기
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: context.colors.bgSurface,
              border: Border(
                bottom: BorderSide(color: context.colors.borderSubtle, width: 0.8),
              ),
            ),
            child: Row(
              children: [
                const Icon(Icons.account_balance_outlined, size: 18, color: Color(0xFF10B981)),
                const SizedBox(width: 8),
                Expanded(
                  child: PopupMenuButton<int>(
                    tooltip: '지급 회차 전환',
                    padding: EdgeInsets.zero,
                    onSelected: (id) {
                      ref.read(payoutTabPeriodIdProvider.notifier).state = id;
                      ref.read(payoutTabSelectedIdsProvider.notifier).state = {};
                      ref.invalidate(payoutTabPayoutsProvider);
                    },
                    itemBuilder: (ctx) => periods.map((p) {
                      final isSelected = p.id == period.id;
                      Color pColor = p.isCompleted
                          ? const Color(0xFF10B981)
                          : p.isConfirmed
                              ? const Color(0xFF0284C7)
                              : const Color(0xFFF59E0B);
                      return PopupMenuItem<int>(
                        value: p.id,
                        child: Row(
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: BoxDecoration(color: pColor, shape: BoxShape.circle),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                p.title,
                                style: AppTextStyles.bodySm.copyWith(
                                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                  color: isSelected ? const Color(0xFF10B981) : context.colors.textPrimary,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                              decoration: BoxDecoration(
                                color: pColor.withAlpha(25),
                                borderRadius: BorderRadius.circular(4),
                                border: Border.all(color: pColor.withAlpha(90), width: 0.5),
                              ),
                              child: Text(
                                p.statusDisplay ?? '',
                                style: AppTextStyles.caption.copyWith(
                                  color: pColor,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          period.title,
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(Icons.arrow_drop_down, color: context.colors.textMuted, size: 20),
                      ],
                    ),
                  ),
                ),
                // 회차 상태 뱃지
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: (period.isCompleted
                            ? const Color(0xFF10B981)
                            : period.isConfirmed
                                ? const Color(0xFF0284C7)
                                : const Color(0xFFF59E0B))
                        .withAlpha(25),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: (period.isCompleted
                              ? const Color(0xFF10B981)
                              : period.isConfirmed
                                  ? const Color(0xFF0284C7)
                                  : const Color(0xFFF59E0B))
                          .withAlpha(90),
                      width: 0.8,
                    ),
                  ),
                  child: Text(
                    period.statusDisplay ?? '',
                    style: AppTextStyles.caption.copyWith(
                      color: period.isCompleted
                          ? const Color(0xFF10B981)
                          : period.isConfirmed
                              ? const Color(0xFF0284C7)
                              : const Color(0xFFF59E0B),
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // 회차 세부 일자 & 종결 액션
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
            child: Row(
              children: [
                Expanded(
                  child: Row(
                    children: [
                      Icon(Icons.event_available, size: 14, color: context.colors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        '지급예정: ${period.payoutDate ?? '-'}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textSecond,
                          fontSize: 11,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '| 대상: ${period.startDate} ~ ${period.endDate}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                // 회차 완료 버튼 (조건 충족 시)
                if (canPayout && canCompletePeriod) ...[
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF10B981),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                    ),
                    icon: const Icon(Icons.done_all, size: 13),
                    label: const Text('회차 지급 종결', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                    onPressed: () => _handleCompletePeriod(period),
                  ),
                ] else if (period.isCompleted) ...[
                  const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.check_circle, size: 14, color: Color(0xFF10B981)),
                      SizedBox(width: 4),
                      Text(
                        '지급 완료 회차',
                        style: TextStyle(color: Color(0xFF10B981), fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ] else if (period.isDraft) ...[
                  Text(
                    '※ 정산 미확정 회차',
                    style: TextStyle(color: context.colors.textMuted, fontSize: 11),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 2×2 수수료 지급 진행 요약 대시보드
  Widget _buildPayoutSummaryKpi(PayoutStatusSummaryModel summary) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: buildSingleKpiTile(
                context: context,
                label: '총 실지급 대상액 (세후)',
                value: '₩ ${NumberFormat('#,###').format(summary.totalNetAmount)}',
                subText: '${summary.totalCount}명 지급 대상',
                accentColor: const Color(0xFF0284C7), // Blue
                icon: Icons.account_balance_wallet_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: buildSingleKpiTile(
                context: context,
                label: '지급 완료액 (이체완료)',
                value: '₩ ${NumberFormat('#,###').format(summary.paidNetAmount)}',
                subText: '${summary.completionRate}% 완료 (${summary.paidCount}명 완료)',
                accentColor: const Color(0xFF10B981), // Emerald
                icon: Icons.check_circle_outline,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: buildSingleKpiTile(
                context: context,
                label: '지급 잔액 (대기/보류)',
                value: '₩ ${NumberFormat('#,###').format(summary.unpaidNetAmount)}',
                subText: '${summary.unpaidCount}명 대기/보류 중',
                accentColor: summary.unpaidNetAmount > 0 ? const Color(0xFFF59E0B) : context.colors.textMuted,
                icon: Icons.pending_actions_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: buildSingleKpiTile(
                context: context,
                label: '원천세 예수금 (3.3%)',
                value: '₩ ${NumberFormat('#,###').format(summary.totalTaxAmount)}',
                subText: '익월 10일 세무 신고 납부 대상',
                accentColor: const Color(0xFFEF4444), // Red
                icon: Icons.receipt_long_outlined,
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// 검색 및 지급 상태 필터 바
  Widget _buildPayoutFilterBar() {
    final statusFilter = ref.watch(payoutTabStatusFilterProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: context.colors.border, width: 0.8),
          ),
          child: ValueListenableBuilder<TextEditingValue>(
            valueListenable: _payoutSearchController,
            builder: (context, value, _) => TextField(
              controller: _payoutSearchController,
              onChanged: _onPayoutSearchChanged,
              style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
              decoration: InputDecoration(
                isDense: true,
                hintText: '성명, 소속팀, 은행명, 계좌번호, 예금주 검색...',
                hintStyle: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                prefixIcon: Icon(Icons.search, size: 18, color: context.colors.textMuted),
                suffixIcon: value.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, size: 16),
                        onPressed: () {
                          _payoutSearchController.clear();
                          ref.read(payoutTabSearchQueryProvider.notifier).state = '';
                        },
                      )
                    : null,
                border: InputBorder.none,
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),

        // 지급 상태 필터 칩
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              Text(
                '지급상태: ',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
              buildFilterChip(
                context: context,
                label: '전체',
                isSelected: statusFilter.isEmpty,
                onTap: () => ref.read(payoutTabStatusFilterProvider.notifier).state = '',
                activeColor: const Color(0xFF10B981),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '대기',
                isSelected: statusFilter == '1',
                onTap: () => ref.read(payoutTabStatusFilterProvider.notifier).state = '1',
                activeColor: const Color(0xFFF59E0B),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '승인',
                isSelected: statusFilter == '2',
                onTap: () => ref.read(payoutTabStatusFilterProvider.notifier).state = '2',
                activeColor: const Color(0xFF0284C7),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '완료',
                isSelected: statusFilter == '3',
                onTap: () => ref.read(payoutTabStatusFilterProvider.notifier).state = '3',
                activeColor: const Color(0xFF10B981),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '보류',
                isSelected: statusFilter == '4',
                onTap: () => ref.read(payoutTabStatusFilterProvider.notifier).state = '4',
                activeColor: const Color(0xFFEF4444),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// 다중 선택 및 일괄 처리 & 이체 파일 다운로드 액션 바
  Widget _buildPayoutBatchActionBar(
    SelectedProject project,
    SettlementPeriodModel? currentPeriod,
    List<CommissionPayoutModel> filteredList,
    Set<int> selectedIds,
  ) {
    final canPayout = ref.can(Perm.salesPayout, projectSlug: project.slug);
    final isAllSelected = filteredList.isNotEmpty &&
        filteredList.every((item) => selectedIds.contains(item.id));

    final selectedTotalAmount = filteredList
        .where((item) => selectedIds.contains(item.id))
        .fold<int>(0, (sum, item) => sum + item.netAmount);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // 전체 선택 체크박스
              InkWell(
                onTap: () {
                  if (isAllSelected) {
                    ref.read(payoutTabSelectedIdsProvider.notifier).state = {};
                  } else {
                    ref.read(payoutTabSelectedIdsProvider.notifier).state =
                            filteredList.map((e) => e.id).toSet();
                  }
                },
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox(
                      width: 20,
                      height: 20,
                      child: Checkbox(
                        value: isAllSelected,
                        activeColor: const Color(0xFF10B981),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                        onChanged: (val) {
                          if (val == true) {
                            ref.read(payoutTabSelectedIdsProvider.notifier).state =
                                filteredList.map((e) => e.id).toSet();
                          } else {
                            ref.read(payoutTabSelectedIdsProvider.notifier).state = {};
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      '전체선택',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),

              // 선택된 인원 및 금액 요약
              Expanded(
                child: Text(
                  selectedIds.isNotEmpty
                      ? '선택 ${selectedIds.length}명 (₩${NumberFormat('#,###').format(selectedTotalAmount)})'
                      : '총 ${filteredList.length}건 조회됨',
                  style: AppTextStyles.caption.copyWith(
                    color: selectedIds.isNotEmpty ? const Color(0xFF10B981) : context.colors.textMuted,
                    fontWeight: selectedIds.isNotEmpty ? FontWeight.bold : FontWeight.normal,
                    fontSize: 11,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),

              // [은행 이체용 CSV 공유] 버튼
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF10B981),
                  side: const BorderSide(color: Color(0xFF10B981), width: 0.8),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  minimumSize: Size.zero,
                ),
                icon: const Icon(Icons.file_download_outlined, size: 14),
                label: const Text('이체 CSV', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                onPressed: () {
                  final targets = selectedIds.isNotEmpty
                      ? filteredList.where((p) => selectedIds.contains(p.id)).toList()
                      : filteredList;
                  BankingCsvHelper.exportAndShareCsv(
                    context: context,
                    payouts: targets,
                    periodTitle: currentPeriod?.title ?? '수수료지급',
                  );
                },
              ),
            ],
          ),

          // 선택 항목이 있을 때 일괄 상태 변경 버튼 그룹 표출 (지급 권한 보유 시)
          if (canPayout && selectedIds.isNotEmpty) ...[
            const SizedBox(height: 8),
            Divider(height: 1, thickness: 0.5, color: context.colors.borderSubtle),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0284C7),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                    ),
                    icon: const Icon(Icons.check, size: 13),
                    label: const Text('선택 승인', style: TextStyle(fontSize: 11)),
                    onPressed: _isBatchProcessing
                        ? null
                        : () => _handleBatchStatusUpdate(selectedIds.toList(), '2', '승인 완료'),
                  ),
                  const SizedBox(width: 6),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF10B981),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                    ),
                    icon: const Icon(Icons.done_all, size: 13),
                    label: const Text('선택 지급완료', style: TextStyle(fontSize: 11)),
                    onPressed: _isBatchProcessing
                        ? null
                        : () => _handleBatchStatusUpdate(selectedIds.toList(), '3', '지급 완료'),
                  ),
                  const SizedBox(width: 6),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFEF4444),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                    ),
                    icon: const Icon(Icons.pause_circle_outline, size: 13),
                    label: const Text('선택 지급보류', style: TextStyle(fontSize: 11)),
                    onPressed: _isBatchProcessing
                        ? null
                        : () => _handleBatchStatusUpdate(selectedIds.toList(), '4', '지급 보류'),
                  ),
                  const SizedBox(width: 6),
                  TextButton(
                    style: TextButton.styleFrom(
                      foregroundColor: context.colors.textMuted,
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      minimumSize: Size.zero,
                    ),
                    onPressed: () => ref.read(payoutTabSelectedIdsProvider.notifier).state = {},
                    child: const Text('선택 해제', style: TextStyle(fontSize: 11)),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  /// 개인별 수수료 지급 대장 카드 리스트 (지급 탭)
  Widget _buildPayoutExecutionListSection(
    SelectedProject project,
    SettlementPeriodModel? currentPeriod,
    AsyncValue<List<CommissionPayoutModel>> payoutsAsync,
    List<CommissionPayoutModel> filteredList,
    Set<int> selectedIds,
  ) {
    if (currentPeriod == null) {
      return const SizedBox.shrink();
    }

    return payoutsAsync.when(
      loading: () => Container(
        padding: const EdgeInsets.all(40),
        child: const Center(
          child: SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: Color(0xFF10B981),
            ),
          ),
        ),
      ),
      error: (err, _) => buildErrorBanner(
        context: context,
        message: '지급 명세 목록을 불러오지 못했습니다: $err',
        onRetry: () => ref.invalidate(payoutTabPayoutsProvider),
      ),
      data: (allPayouts) {
        if (allPayouts.isEmpty) {
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: context.colors.border),
            ),
            child: Column(
              children: [
                Icon(Icons.payments_outlined, size: 40, color: context.colors.textMuted),
                const SizedBox(height: 12),
                Text(
                  '지급 대상 명세가 없습니다',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '[수수료 정산] 탭에서 정산 계산을 실행하고 정산을 확정한 후 지급 관리를 진행해 주세요.',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.caption.copyWith(color: context.colors.textSecond),
                ),
              ],
            ),
          );
        }

        if (filteredList.isEmpty) {
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 20),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: context.colors.border),
            ),
            child: Column(
              children: [
                Icon(Icons.filter_list_off_outlined, size: 36, color: context.colors.textMuted),
                const SizedBox(height: 10),
                Text(
                  '조건에 일치하는 지급 명세가 없습니다',
                  style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: context.colors.textSecond,
                    side: BorderSide(color: context.colors.border),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                  ),
                  onPressed: () {
                    _payoutSearchController.clear();
                    ref.read(payoutTabSearchQueryProvider.notifier).state = '';
                    ref.read(payoutTabStatusFilterProvider.notifier).state = '';
                  },
                  child: const Text('검색 및 필터 초기화'),
                ),
              ],
            ),
          );
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '지급 대상 대장 (${filteredList.length}명)',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  '상태 뱃지를 눌러 즉시 변경 가능',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: filteredList.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (ctx, index) {
                final item = filteredList[index];
                final isSelected = selectedIds.contains(item.id);
                return _buildPayoutExecutionCard(context, item, isSelected, project);
              },
            ),
          ],
        );
      },
    );
  }

  /// 개인별 수수료 지급 대장 카드
  Widget _buildPayoutExecutionCard(
    BuildContext context,
    CommissionPayoutModel item,
    bool isSelected,
    SelectedProject project,
  ) {
    final canPayout = ref.can(Perm.salesPayout, projectSlug: project.slug);
    Color statusColor;
    switch (item.payStatus) {
      case '2': // 승인 완료
        statusColor = const Color(0xFF0284C7);
        break;
      case '3': // 지급 완료
        statusColor = const Color(0xFF10B981);
        break;
      case '4': // 지급 보류
        statusColor = const Color(0xFFEF4444);
        break;
      case '1': // 지급 대기
      default:
        statusColor = const Color(0xFFF59E0B);
        break;
    }

    Color dutyColor;
    if (item.dutyDisplay?.contains('본부장') ?? false) {
      dutyColor = const Color(0xFF8B5CF6);
    } else if (item.dutyDisplay?.contains('팀장') ?? false) {
      dutyColor = const Color(0xFF0284C7);
    } else {
      dutyColor = const Color(0xFF10B981);
    }

    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: isSelected ? const Color(0xFF10B981).withAlpha(10) : context.colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isSelected ? const Color(0xFF10B981) : context.colors.border,
          width: isSelected ? 1.2 : 0.8,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => showPayoutDetailSheet(context, payout: item, projectSlug: project.slug),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. 헤더: 다중선택 체크박스 + 성명 + 직책 + 소속팀 + 상태 변경 팝업
                Row(
                  children: [
                    SizedBox(
                      width: 20,
                      height: 20,
                      child: Checkbox(
                        value: isSelected,
                        activeColor: const Color(0xFF10B981),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                        onChanged: (val) {
                          final currentSet = {...ref.read(payoutTabSelectedIdsProvider)};
                          if (val == true) {
                            currentSet.add(item.id);
                          } else {
                            currentSet.remove(item.id);
                          }
                          ref.read(payoutTabSelectedIdsProvider.notifier).state = currentSet;
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    InkWell(
                      onTap: () {
                        showPersonPayoutHistorySheet(
                          context,
                          salesPersonId: item.salesPerson,
                          salesPersonName: item.salesPersonName ?? '미지정',
                          teamName: item.teamName,
                          dutyDisplay: item.dutyDisplay,
                        );
                      },
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            item.salesPersonName ?? '미지정',
                            style: AppTextStyles.titleSm.copyWith(
                              color: const Color(0xFF10B981),
                              fontWeight: FontWeight.bold,
                              decoration: TextDecoration.underline,
                            ),
                          ),
                          const SizedBox(width: 3),
                          const Icon(Icons.history_rounded, size: 14, color: Color(0xFF10B981)),
                        ],
                      ),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: dutyColor.withAlpha(20),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: dutyColor.withAlpha(70), width: 0.5),
                      ),
                      child: Text(
                        item.dutyDisplay ?? '상담사',
                        style: AppTextStyles.caption.copyWith(
                          color: dutyColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 10,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        item.teamName ?? '-',
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),

                    // 원클릭 상태 전환 팝업 메뉴 (권한 보유 시 팝업, 미보유 시 단순 뱃지)
                    if (canPayout)
                      PopupMenuButton<String>(
                        tooltip: '지급 상태 변경',
                        padding: EdgeInsets.zero,
                        onSelected: (newStatus) => _handleIndividualStatusUpdate(item, newStatus),
                        itemBuilder: (ctx) => [
                          const PopupMenuItem(value: '1', child: Text('지급 대기')),
                          const PopupMenuItem(value: '2', child: Text('승인 완료')),
                          const PopupMenuItem(value: '3', child: Text('지급 완료 (오늘 일자)')),
                          const PopupMenuItem(value: '4', child: Text('지급 보류')),
                        ],
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                          decoration: BoxDecoration(
                            color: statusColor.withAlpha(25),
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(color: statusColor.withAlpha(90), width: 0.8),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                item.payStatusDisplay ?? '지급 대기',
                                style: AppTextStyles.caption.copyWith(
                                  color: statusColor,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 11,
                                ),
                              ),
                              const SizedBox(width: 2),
                              Icon(Icons.arrow_drop_down, size: 14, color: statusColor),
                            ],
                          ),
                        ),
                      )
                    else
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                        decoration: BoxDecoration(
                          color: statusColor.withAlpha(25),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: statusColor.withAlpha(90), width: 0.8),
                        ),
                        child: Text(
                          item.payStatusDisplay ?? '지급 대기',
                          style: AppTextStyles.caption.copyWith(
                            color: statusColor,
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 10),

                // 2. 세후 실지급액 강조
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text(
                      '세후 실지급액 (이체 대상)',
                      style: AppTextStyles.caption.copyWith(color: context.colors.textSecond),
                    ),
                    Text(
                      '₩ ${NumberFormat('#,###').format(item.netAmount)}',
                      style: AppTextStyles.titleLg.copyWith(
                        color: const Color(0xFF10B981),
                        fontWeight: FontWeight.bold,
                        letterSpacing: -0.5,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                // 3. 은행 계좌 정보 박스 & 복사 버튼
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: context.colors.bgSurface,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: context.colors.borderSubtle, width: 0.8),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.account_balance_rounded, size: 15, color: Color(0xFF10B981)),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          '${item.bankName ?? '-'} ${item.accountNumber ?? '-'} (예금주: ${item.accountHolder ?? '-'})',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.w600,
                            fontSize: 11.5,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      InkWell(
                        onTap: () {
                          final copyText = '${item.bankName ?? ''} ${item.accountNumber ?? ''} ${item.accountHolder ?? ''}'.trim();
                          if (copyText.isNotEmpty) {
                            Clipboard.setData(ClipboardData(text: copyText));
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('계좌 정보가 클립보드에 복사되었습니다.'),
                                duration: Duration(seconds: 1),
                              ),
                            );
                          }
                        },
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.copy_rounded, size: 13, color: context.colors.textMuted),
                              const SizedBox(width: 3),
                              Text(
                                '복사',
                                style: TextStyle(color: context.colors.textMuted, fontSize: 11),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 8),

                // 4. 하단 요약 (세전, 원천세, 지급일자) 및 상세 링크
                Row(
                  children: [
                    Text(
                      '세전 ₩${NumberFormat('#,###').format(item.grossAmount)} | 원천세 -₩${NumberFormat('#,###').format(item.totalTax)}',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                        fontSize: 11,
                      ),
                    ),
                    const Spacer(),
                    if (item.paidDate != null && item.paidDate!.isNotEmpty) ...[
                      Text(
                        '지급: ${item.paidDate}',
                        style: const TextStyle(
                          color: Color(0xFF10B981),
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(width: 8),
                    ],
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '상세보기',
                          style: AppTextStyles.caption.copyWith(
                            color: const Color(0xFF10B981),
                            fontWeight: FontWeight.w600,
                            fontSize: 11,
                          ),
                        ),
                        const Icon(Icons.chevron_right, size: 14, color: Color(0xFF10B981)),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ── 지급 탭 개인 vs 대행사 서브 모드 셀렉터 ─────────────────
  Widget _buildPayoutSubModeSelector(String currentMode) {
    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgSurface,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Row(
        children: [
          Expanded(
            child: Material(
              color: currentMode == 'person'
                  ? const Color(0xFF10B981)
                  : Colors.transparent,
              child: InkWell(
                onTap: () {
                  ref.read(payoutTabModeProvider.notifier).state = 'person';
                },
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.person_outline,
                        size: 16,
                        color: currentMode == 'person'
                            ? Colors.white
                            : context.colors.textSecond,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        '개인별 지급 대장',
                        style: AppTextStyles.label.copyWith(
                          fontWeight: FontWeight.bold,
                          color: currentMode == 'person'
                              ? Colors.white
                              : context.colors.textSecond,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          Container(width: 1, height: 28, color: context.colors.border),
          Expanded(
            child: Material(
              color: currentMode == 'agency'
                  ? const Color(0xFF8B5CF6)
                  : Colors.transparent,
              child: InkWell(
                onTap: () {
                  ref.read(payoutTabModeProvider.notifier).state = 'agency';
                },
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.business_center_outlined,
                        size: 16,
                        color: currentMode == 'agency'
                            ? Colors.white
                            : context.colors.textSecond,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        '대행사별 정산 관리',
                        style: AppTextStyles.label.copyWith(
                          fontWeight: FontWeight.bold,
                          color: currentMode == 'agency'
                              ? Colors.white
                              : context.colors.textSecond,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── 대행사 지급 진행 현황 2x2 KPI ──────────────────────
  Widget _buildPayoutAgencySummaryKpi(AgencyPayoutSummaryModel summary) {
    final fmt = NumberFormat('#,###');
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: buildSingleKpiTile(
                context: context,
                label: '총 정산 금액 (VAT포함)',
                value: '${fmt.format(summary.totalAmount)}원',
                subText: '${summary.totalCount}개 대행사 대상',
                accentColor: const Color(0xFF8B5CF6),
                icon: Icons.payments_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: buildSingleKpiTile(
                context: context,
                label: '지급 완료 금액',
                value: '${fmt.format(summary.paidAmount)}원',
                subText: '${summary.paidCount}개사 완료',
                accentColor: const Color(0xFF10B981),
                icon: Icons.check_circle_outline,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: buildSingleKpiTile(
                context: context,
                label: '미지급 잔액',
                value: '${fmt.format(summary.unpaidAmount)}원',
                subText: '${summary.unpaidCount}개사 대기/진행 중',
                accentColor: summary.unpaidAmount > 0
                    ? const Color(0xFFF59E0B)
                    : context.colors.textMuted,
                icon: Icons.hourglass_empty_rounded,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: buildSingleKpiTile(
                context: context,
                label: '지급 완료율',
                value: summary.totalAmount > 0
                    ? '${((summary.paidAmount / summary.totalAmount) * 100).round()}%'
                    : '0%',
                subText: '${summary.paidCount}/${summary.totalCount}개사 완료',
                accentColor: const Color(0xFF0284C7),
                icon: Icons.donut_large_rounded,
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ── 대행사 지급 검색 및 상태 필터 ────────────────────────
  Widget _buildPayoutAgencyFilterBar() {
    final statusFilter = ref.watch(payoutTabAgencyStatusFilterProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: context.colors.border, width: 0.8),
          ),
          child: TextField(
            onChanged: (val) => ref.read(payoutTabAgencySearchQueryProvider.notifier).state = val.trim(),
            style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
            decoration: InputDecoration(
              isDense: true,
              hintText: '대행사명, 사업자번호, 예금주 검색...',
              hintStyle: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
              prefixIcon: Icon(Icons.search, size: 18, color: context.colors.textMuted),
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            ),
          ),
        ),
        const SizedBox(height: 8),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              Text(
                '지급상태: ',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
              buildFilterChip(
                context: context,
                label: '전체',
                isSelected: statusFilter.isEmpty,
                onTap: () => ref.read(payoutTabAgencyStatusFilterProvider.notifier).state = '',
                activeColor: const Color(0xFF8B5CF6),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '대기',
                isSelected: statusFilter == '1',
                onTap: () => ref.read(payoutTabAgencyStatusFilterProvider.notifier).state = '1',
                activeColor: const Color(0xFFF59E0B),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '승인',
                isSelected: statusFilter == '2',
                onTap: () => ref.read(payoutTabAgencyStatusFilterProvider.notifier).state = '2',
                activeColor: const Color(0xFF0284C7),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '지급완료',
                isSelected: statusFilter == '3',
                onTap: () => ref.read(payoutTabAgencyStatusFilterProvider.notifier).state = '3',
                activeColor: const Color(0xFF10B981),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '보류',
                isSelected: statusFilter == '4',
                onTap: () => ref.read(payoutTabAgencyStatusFilterProvider.notifier).state = '4',
                activeColor: const Color(0xFFEF4444),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ── 대행사별 지급 명세 카드 리스트 ──────────────────────
  Widget _buildPayoutAgencyExecutionListSection(
    SelectedProject project,
    SettlementPeriodModel? currentPeriod,
    AsyncValue<List<AgencyPayoutModel>> agencyPayoutsAsync,
    List<AgencyPayoutModel> filteredAgencyPayouts,
  ) {
    final canPayout = ref.can(Perm.salesPayout, projectSlug: project.slug);

    return agencyPayoutsAsync.when(
      loading: () => Container(
        padding: const EdgeInsets.all(30),
        child: const Center(
          child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF8B5CF6)),
        ),
      ),
      error: (err, _) => buildErrorBanner(
        context: context,
        message: '대행사 지급 데이터를 불러오지 못했습니다: $err',
        onRetry: () => ref.invalidate(payoutTabAgencyPayoutsProvider),
      ),
      data: (allAgencies) {
        if (allAgencies.isEmpty) {
          return Container(
            padding: const EdgeInsets.all(32),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: context.colors.border),
            ),
            child: Center(
              child: Text('해당 회차에 정산된 대행사가 없습니다.',
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted)),
            ),
          );
        }

        if (filteredAgencyPayouts.isEmpty) {
          return Container(
            padding: const EdgeInsets.all(32),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: context.colors.border),
            ),
            child: Center(
              child: Text('조건에 일치하는 대행사가 없습니다.',
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted)),
            ),
          );
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '대행사 지급/청구 명세 (${filteredAgencyPayouts.length}개사)',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            ...filteredAgencyPayouts.map((ap) {
              return _buildAgencyPayoutCard(context, ap, project, canPayout);
            }),
          ],
        );
      },
    );
  }

  // ── 대행사별 지급 카드 ────────────────────────────────────
  Widget _buildAgencyPayoutCard(
    BuildContext context,
    AgencyPayoutModel ap,
    SelectedProject project,
    bool canPayout,
  ) {
    final fmt = NumberFormat('#,###');
    Color statusColor;
    switch (ap.payStatus) {
      case '2': // 승인
        statusColor = const Color(0xFF0284C7);
        break;
      case '3': // 완료
        statusColor = const Color(0xFF10B981);
        break;
      case '4': // 보류
        statusColor = const Color(0xFFEF4444);
        break;
      case '1': // 대기
      default:
        statusColor = const Color(0xFFF59E0B);
        break;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                ap.agencyName ?? '대행사',
                style: AppTextStyles.titleSm.copyWith(
                  color: context.colors.textPrimary,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(width: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                decoration: BoxDecoration(
                  color: ap.isDirectManaged
                      ? const Color(0xFF0284C7).withAlpha(25)
                      : const Color(0xFF8B5CF6).withAlpha(25),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  ap.isDirectManaged ? '직영운영' : '외주대행',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: ap.isDirectManaged
                        ? const Color(0xFF0284C7)
                        : const Color(0xFF8B5CF6),
                  ),
                ),
              ),
              const Spacer(),
              if (canPayout)
                PopupMenuButton<String>(
                  tooltip: '대행사 지급 상태 변경',
                  padding: EdgeInsets.zero,
                  onSelected: (newStatus) => _handleAgencyStatusUpdate(ap, newStatus),
                  itemBuilder: (ctx) => [
                    const PopupMenuItem(value: '1', child: Text('지급 대기')),
                    const PopupMenuItem(value: '2', child: Text('승인 완료')),
                    const PopupMenuItem(value: '3', child: Text('지급 완료')),
                    const PopupMenuItem(value: '4', child: Text('지급 보류')),
                  ],
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                    decoration: BoxDecoration(
                      color: statusColor.withAlpha(25),
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(color: statusColor.withAlpha(90), width: 0.8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          ap.payStatusDisplay ?? '지급 대기',
                          style: TextStyle(
                            color: statusColor,
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                        const SizedBox(width: 2),
                        Icon(Icons.arrow_drop_down, size: 14, color: statusColor),
                      ],
                    ),
                  ),
                )
              else
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                  decoration: BoxDecoration(
                    color: statusColor.withAlpha(25),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: statusColor.withAlpha(90), width: 0.8),
                  ),
                  child: Text(
                    ap.payStatusDisplay ?? '지급 대기',
                    style: TextStyle(
                      color: statusColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '청구 총액 (VAT포함)',
                style: AppTextStyles.caption.copyWith(color: context.colors.textSecond),
              ),
              Text(
                '₩ ${fmt.format(ap.totalAmount)}',
                style: AppTextStyles.titleLg.copyWith(
                  color: const Color(0xFF8B5CF6),
                  fontWeight: FontWeight.bold,
                  letterSpacing: -0.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              color: context.colors.bgSurface,
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: context.colors.borderSubtle, width: 0.8),
            ),
            child: Row(
              children: [
                const Icon(Icons.account_balance_rounded, size: 15, color: Color(0xFF8B5CF6)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    '${ap.bankName ?? "-"} ${ap.accountNumber ?? "-"} (예금주: ${ap.accountHolder ?? "-"})',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 11.5,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Text(
                '공급가: ${fmt.format(ap.agencyFeeSum)}원 | VAT: ${fmt.format(ap.vatAmount)}원',
                style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
              ),
              if (ap.unallocatedFee > 0) ...[
                const SizedBox(width: 6),
                Text(
                  '| 시행사 귀속: ${fmt.format(ap.unallocatedFee)}원',
                  style: AppTextStyles.caption.copyWith(color: const Color(0xFF10B981), fontSize: 11),
                ),
              ],
              const Spacer(),
              if (ap.paidDate != null && ap.paidDate!.isNotEmpty)
                Text(
                  '지급: ${ap.paidDate}',
                  style: const TextStyle(color: Color(0xFF10B981), fontSize: 11, fontWeight: FontWeight.bold),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
