import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/sales_models.dart';
import '../../data/sales_repository.dart';

/// 영업인력 개인별 전 회차 누적 수수료 지급 이력 바텀시트 열기
void showPersonPayoutHistorySheet(
  BuildContext context, {
  required int salesPersonId,
  required String salesPersonName,
  String? teamName,
  String? dutyDisplay,
}) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: context.colors.bgCard,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (ctx) => Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(ctx).viewInsets.bottom,
      ),
      child: PersonPayoutHistorySheet(
        salesPersonId: salesPersonId,
        salesPersonName: salesPersonName,
        teamName: teamName,
        dutyDisplay: dutyDisplay,
      ),
    ),
  );
}

class PersonPayoutHistorySheet extends ConsumerStatefulWidget {
  final int salesPersonId;
  final String salesPersonName;
  final String? teamName;
  final String? dutyDisplay;

  const PersonPayoutHistorySheet({
    super.key,
    required this.salesPersonId,
    required this.salesPersonName,
    this.teamName,
    this.dutyDisplay,
  });

  @override
  ConsumerState<PersonPayoutHistorySheet> createState() =>
      _PersonPayoutHistorySheetState();
}

class _PersonPayoutHistorySheetState
    extends ConsumerState<PersonPayoutHistorySheet> {
  bool _isLoading = true;
  List<CommissionPayoutModel> _payoutHistory = [];
  List<CommissionClawbackModel> _clawbackHistory = [];
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final repo = ref.read(salesRepositoryProvider);
    try {
      final results = await Future.wait([
        repo.fetchSalesPersonPayouts(salesPersonId: widget.salesPersonId),
        repo.fetchClawbacks(salesPersonId: widget.salesPersonId),
      ]);

      if (mounted) {
        setState(() {
          _payoutHistory = results[0] as List<CommissionPayoutModel>;
          _clawbackHistory = results[1] as List<CommissionClawbackModel>;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  int get _totalGross =>
      _payoutHistory.fold<int>(0, (sum, p) => sum + p.grossAmount);
  int get _totalTax =>
      _payoutHistory.fold<int>(0, (sum, p) => sum + p.totalTax);
  int get _totalNet =>
      _payoutHistory.fold<int>(0, (sum, p) => sum + p.netAmount);
  int get _totalClawback =>
      _clawbackHistory.fold<int>(0, (sum, c) => sum + c.amount);

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.85,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 상단 드래그 핸들 및 헤더
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 10, bottom: 8),
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: context.colors.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.history_rounded,
                              size: 18, color: Color(0xFF10B981)),
                          const SizedBox(width: 6),
                          Text(
                            widget.salesPersonName,
                            style: AppTextStyles.titleSm.copyWith(
                              fontWeight: FontWeight.bold,
                              color: context.colors.textPrimary,
                            ),
                          ),
                          if (widget.dutyDisplay != null) ...[
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: context.colors.bgSurface,
                                borderRadius: BorderRadius.zero,
                                border: Border.all(
                                    color: context.colors.border, width: 0.8),
                              ),
                              child: Text(
                                widget.dutyDisplay!,
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textSecond,
                                  fontSize: 10.5,
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${widget.teamName ?? "소속"} • 전 회차 누적 수수료 지급 및 환수 이력',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close_rounded, size: 20),
                  onPressed: () => Navigator.of(context).pop(),
                  color: context.colors.textMuted,
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          Expanded(
            child: _isLoading
                ? const Center(
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : _errorMessage != null
                    ? Center(
                        child: Text(
                          '이력을 불러오지 못했습니다: $_errorMessage',
                          style: AppTextStyles.caption
                              .copyWith(color: context.colors.error),
                        ),
                      )
                    : ListView(
                        padding: const EdgeInsets.all(16),
                        children: [
                          // 1. 누적 KPI 요약 카드
                          _buildKpiSummary(context),
                          const SizedBox(height: 16),

                          // 2. 환수 이력 요약 (있을 경우)
                          if (_clawbackHistory.isNotEmpty) ...[
                            _buildClawbackSection(context),
                            const SizedBox(height: 16),
                          ],

                          // 3. 회차별 지급 이력
                          _buildPayoutListSection(context),
                        ],
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildKpiSummary(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: context.colors.bgSurface,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '전체 누적 정산 현황 (${_payoutHistory.length}회차)',
            style: AppTextStyles.caption.copyWith(
              fontWeight: FontWeight.bold,
              color: context.colors.textSecond,
              fontSize: 11,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _buildKpiItem(
                  context,
                  label: '누적 세전 총액',
                  amount: _totalGross,
                  color: context.colors.textPrimary,
                ),
              ),
              Container(width: 1, height: 32, color: context.colors.border),
              Expanded(
                child: _buildKpiItem(
                  context,
                  label: '누적 원천세 (3.3%)',
                  amount: _totalTax,
                  color: const Color(0xFFEF4444),
                ),
              ),
              Container(width: 1, height: 32, color: context.colors.border),
              Expanded(
                child: _buildKpiItem(
                  context,
                  label: '누적 실지급액',
                  amount: _totalNet,
                  color: const Color(0xFF10B981),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildKpiItem(
    BuildContext context, {
    required String label,
    required int amount,
    required Color color,
  }) {
    final fmt = NumberFormat('#,###');
    return Column(
      children: [
        Text(
          label,
          style: AppTextStyles.caption.copyWith(
            color: context.colors.textMuted,
            fontSize: 10,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          '${fmt.format(amount)}원',
          style: AppTextStyles.label.copyWith(
            fontWeight: FontWeight.bold,
            color: color,
            fontSize: 12,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ],
    );
  }

  Widget _buildClawbackSection(BuildContext context) {
    final fmt = NumberFormat('#,###');
    final unsettledCount =
        _clawbackHistory.where((c) => !c.isSettled).length;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFEF4444).withAlpha(15),
        border: Border.all(
          color: const Color(0xFFEF4444).withAlpha(80),
          width: 0.8,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.warning_amber_rounded,
                      size: 16, color: Color(0xFFEF4444)),
                  const SizedBox(width: 6),
                  Text(
                    '환수 이력 (${_clawbackHistory.length}건)',
                    style: AppTextStyles.caption.copyWith(
                      fontWeight: FontWeight.bold,
                      color: const Color(0xFFEF4444),
                      fontSize: 11.5,
                    ),
                  ),
                ],
              ),
              Text(
                '총 ${fmt.format(_totalClawback)}원 (미상계 $unsettledCount건)',
                style: AppTextStyles.caption.copyWith(
                  fontWeight: FontWeight.bold,
                  color: const Color(0xFFEF4444),
                  fontSize: 11,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ..._clawbackHistory.map((c) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 4, vertical: 1),
                      decoration: BoxDecoration(
                        color: c.isSettled
                            ? const Color(0xFF10B981).withAlpha(30)
                            : const Color(0xFFEF4444).withAlpha(30),
                      ),
                      child: Text(
                        c.isSettled ? '상계완료' : '미상계',
                        style: TextStyle(
                          fontSize: 9.5,
                          fontWeight: FontWeight.bold,
                          color: c.isSettled
                              ? const Color(0xFF10B981)
                              : const Color(0xFFEF4444),
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        '${c.contractSerial ?? "#${c.contract}"} - ${c.reason}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textSecond,
                          fontSize: 10.5,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Text(
                      '-${fmt.format(c.amount)}원',
                      style: AppTextStyles.caption.copyWith(
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFFEF4444),
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              )),
        ],
      ),
    );
  }

  Widget _buildPayoutListSection(BuildContext context) {
    final fmt = NumberFormat('#,###');

    if (_payoutHistory.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(24),
        alignment: Alignment.center,
        child: Text(
          '지급 이력이 없습니다.',
          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '회차별 수수료 지급 명세',
          style: AppTextStyles.caption.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
            fontSize: 12,
          ),
        ),
        const SizedBox(height: 8),
        ..._payoutHistory.map((p) {
          final isCompleted = p.payStatus == '3';
          final isApproved = p.payStatus == '2';
          final isHold = p.payStatus == '4';

          Color statusColor = context.colors.textMuted;
          String statusText = p.payStatusDisplay ?? '대기';
          if (isCompleted) {
            statusColor = const Color(0xFF10B981);
          } else if (isApproved) {
            statusColor = const Color(0xFF0284C7);
          } else if (isHold) {
            statusColor = const Color(0xFFF59E0B);
          }

          return Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              border: Border.all(color: context.colors.border, width: 0.8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '정산 회차 #${p.period} (${p.contractCount}건)',
                      style: AppTextStyles.label.copyWith(
                        fontWeight: FontWeight.bold,
                        color: context.colors.textPrimary,
                        fontSize: 12,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: statusColor.withAlpha(25),
                        border: Border.all(color: statusColor, width: 0.6),
                      ),
                      child: Text(
                        statusText,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: statusColor,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '인센티브: ${fmt.format(p.commissionAmount)}원',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textSecond,
                        fontSize: 10.5,
                      ),
                    ),
                    if (p.deductionAmount > 0)
                      Text(
                        '공제: -${fmt.format(p.deductionAmount)}원',
                        style: AppTextStyles.caption.copyWith(
                          color: const Color(0xFFEF4444),
                          fontSize: 10.5,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 4),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '원천세(3.3%): ${fmt.format(p.totalTax)}원',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                        fontSize: 10.5,
                      ),
                    ),
                    Text(
                      '실지급액: ${fmt.format(p.netAmount)}원',
                      style: AppTextStyles.label.copyWith(
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF10B981),
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
                if (p.paidDate != null && p.paidDate!.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    '지급일자: ${p.paidDate}',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textMuted,
                      fontSize: 10,
                    ),
                  ),
                ],
              ],
            ),
          );
        }),
      ],
    );
  }
}
