import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/sales_models.dart';
import '../../data/sales_repository.dart';
import '../../providers/sales_provider.dart';

/// 개인별 수수료 정산 및 세금 공제 상세 바텀시트 열기 함수
void showPayoutDetailSheet(
  BuildContext context, {
  required CommissionPayoutModel payout,
  String? projectSlug,
  bool? canPayout,
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
      child: PayoutDetailSheet(
        payout: payout,
        projectSlug: projectSlug,
        canPayout: canPayout,
      ),
    ),
  );
}

class PayoutDetailSheet extends ConsumerStatefulWidget {
  final CommissionPayoutModel payout;
  final String? projectSlug;
  final bool? canPayout;

  const PayoutDetailSheet({
    super.key,
    required this.payout,
    this.projectSlug,
    this.canPayout,
  });

  @override
  ConsumerState<PayoutDetailSheet> createState() => _PayoutDetailSheetState();
}

class _PayoutDetailSheetState extends ConsumerState<PayoutDetailSheet> {
  late CommissionPayoutModel _payout;
  bool _isUpdatingStatus = false;

  @override
  void initState() {
    super.initState();
    _payout = widget.payout;
  }

  Future<void> _updatePayStatus(String newStatus) async {
    setState(() => _isUpdatingStatus = true);
    try {
      final repository = ref.read(salesRepositoryProvider);
      await repository.updatePayStatus(_payout.id, newStatus);
      ref.invalidate(commissionPayoutsProvider);

      if (mounted) {
        setState(() {
          _payout = CommissionPayoutModel(
            id: _payout.id,
            period: _payout.period,
            salesPerson: _payout.salesPerson,
            salesPersonName: _payout.salesPersonName,
            dutyDisplay: _payout.dutyDisplay,
            teamName: _payout.teamName,
            basePay: _payout.basePay,
            contractCount: _payout.contractCount,
            commissionAmount: _payout.commissionAmount,
            bonusAmount: _payout.bonusAmount,
            deductionAmount: _payout.deductionAmount,
            grossAmount: _payout.grossAmount,
            incomeTax: _payout.incomeTax,
            localIncomeTax: _payout.localIncomeTax,
            totalTax: _payout.totalTax,
            netAmount: _payout.netAmount,
            payStatus: newStatus,
            payStatusDisplay: _getStatusLabel(newStatus),
            paidDate: _payout.paidDate,
            bankName: _payout.bankName,
            accountNumber: _payout.accountNumber,
            accountHolder: _payout.accountHolder,
            note: _payout.note,
            contractDetails: _payout.contractDetails,
          );
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('지급 상태가 [${_getStatusLabel(newStatus)}](으)로 변경되었습니다.'),
            backgroundColor: const Color(0xFF10B981),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('상태 변경 중 오류가 발생했습니다: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isUpdatingStatus = false);
      }
    }
  }

  String _getStatusLabel(String code) {
    switch (code) {
      case '1':
        return '대기';
      case '2':
        return '승인';
      case '3':
        return '지급 완료';
      case '4':
        return '지급 보류';
      default:
        return '대기';
    }
  }

  Color _getStatusColor(String code) {
    switch (code) {
      case '1':
        return const Color(0xFFF59E0B); // Amber
      case '2':
        return const Color(0xFF38BDF8); // Sky Blue
      case '3':
        return const Color(0xFF10B981); // Emerald
      case '4':
        return const Color(0xFFEF4444); // Red
      default:
        return const Color(0xFF64748B);
    }
  }

  @override
  Widget build(BuildContext context) {
    final canPayout = widget.canPayout ?? ref.can(Perm.salesPayout, projectSlug: widget.projectSlug);
    final hasAccount =
        _payout.accountNumber != null && _payout.accountNumber!.isNotEmpty;

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.88,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 상단 헤더
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              border: Border(bottom: BorderSide(color: context.colors.border, width: 0.8)),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.receipt_long_outlined,
                  size: 20,
                  color: Color(0xFF10B981),
                ),
                const SizedBox(width: 8),
                Text(
                  '수수료 정산 및 공제 명세',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.close, size: 20),
                  color: context.colors.textMuted,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
          ),

          // 스크롤 바디
          Flexible(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 1. 인적사항 및 입금 계좌 카드
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: context.colors.bgSurface,
                      border: Border.all(color: context.colors.border, width: 0.8),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              _payout.salesPersonName ?? '영업직원',
                              style: AppTextStyles.titleSm.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(width: 8),
                            // 직책 뱃지
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFF38BDF8).withAlpha(20),
                                border: Border.all(
                                    color: const Color(0xFF38BDF8).withAlpha(80),
                                    width: 0.8),
                              ),
                              child: Text(
                                _payout.dutyDisplay ?? '상담사',
                                style: const TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  color: Color(0xFF0284C7),
                                ),
                              ),
                            ),
                            const SizedBox(width: 4),
                            // 팀명 뱃지
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: context.colors.bgCard,
                                border: Border.all(color: context.colors.border, width: 0.8),
                              ),
                              child: Text(
                                _payout.teamName ?? '소속팀 미배정',
                                style: TextStyle(
                                  fontSize: 10,
                                  color: context.colors.textSecond,
                                ),
                              ),
                            ),
                            const Spacer(),
                            // 지급 상태 뱃지
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: _getStatusColor(_payout.payStatus).withAlpha(20),
                                border: Border.all(
                                    color: _getStatusColor(_payout.payStatus).withAlpha(80),
                                    width: 0.8),
                              ),
                              child: Text(
                                _payout.payStatusDisplay ?? _getStatusLabel(_payout.payStatus),
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  color: _getStatusColor(_payout.payStatus),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            Icon(Icons.account_balance_outlined,
                                size: 14, color: context.colors.textMuted),
                            const SizedBox(width: 6),
                            Text(
                              hasAccount
                                  ? '${_payout.bankName} ${_payout.accountNumber} (예금주: ${_payout.accountHolder})'
                                  : '계좌 미등록',
                              style: TextStyle(
                                fontSize: 12,
                                color: hasAccount
                                    ? context.colors.textSecond
                                    : context.colors.textMuted,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),

                  // 2. 실지급액 (세후) 하이라이트 배너
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF10B981).withAlpha(15),
                      border: Border.all(
                        color: const Color(0xFF10B981).withAlpha(60),
                        width: 1,
                      ),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '최종 실지급액 (세후)',
                              style: AppTextStyles.caption.copyWith(
                                color: context.colors.textSecond,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '3.3% 원천세 공제 완료',
                              style: TextStyle(
                                fontSize: 10.5,
                                color: context.colors.textMuted,
                              ),
                            ),
                          ],
                        ),
                        Text(
                          '₩ ${NumberFormat('#,###').format(_payout.netAmount)}원',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF059669),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),

                  // 3. 정산 금액 구성 항목 그리드 (4칸)
                  Row(
                    children: [
                      _buildAmountTile(
                        label: '인센티브 합계',
                        value: '${NumberFormat('#,###').format(_payout.commissionAmount)}원',
                        subText: '${_payout.contractCount}건 계약',
                        color: const Color(0xFF6366F1),
                      ),
                      const SizedBox(width: 8),
                      _buildAmountTile(
                        label: '기본급 / 일비',
                        value: '${NumberFormat('#,###').format(_payout.basePay)}원',
                        subText: '고정 급여',
                        color: context.colors.textPrimary,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      _buildAmountTile(
                        label: '보너스 / 활동비',
                        value: '${NumberFormat('#,###').format(_payout.bonusAmount)}원',
                        subText: '추가 지급',
                        color: const Color(0xFF38BDF8),
                      ),
                      const SizedBox(width: 8),
                      _buildAmountTile(
                        label: '공제 / 환수액',
                        value: _payout.deductionAmount > 0
                            ? '-${NumberFormat('#,###').format(_payout.deductionAmount)}원'
                            : '0원',
                        subText: '차감 항목',
                        color: _payout.deductionAmount > 0
                            ? const Color(0xFFEF4444)
                            : context.colors.textMuted,
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // 4. 원천징수 세액 상세 테이블
                  Container(
                    decoration: BoxDecoration(
                      color: context.colors.bgCard,
                      border: Border.all(color: context.colors.border, width: 0.8),
                    ),
                    child: Column(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          color: context.colors.bgSurface,
                          child: Row(
                            children: [
                              Text(
                                '3.3% 프리랜서 사업소득세 계산 내역',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textPrimary,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            children: [
                              _buildTaxRow('총 지급액 (세전 합계)',
                                  '${NumberFormat('#,###').format(_payout.grossAmount)}원',
                                  isBold: true),
                              const Divider(height: 12),
                              _buildTaxRow('• 사업소득세 (3.0%)',
                                  '-${NumberFormat('#,###').format(_payout.incomeTax)}원',
                                  color: const Color(0xFFEF4444)),
                              const SizedBox(height: 4),
                              _buildTaxRow('• 지방소득세 (0.3%)',
                                  '-${NumberFormat('#,###').format(_payout.localIncomeTax)}원',
                                  color: const Color(0xFFEF4444)),
                              const Divider(height: 12),
                              _buildTaxRow('원천징수 합계 (3.3%)',
                                  '-${NumberFormat('#,###').format(_payout.totalTax)}원',
                                  color: const Color(0xFFEF4444), isBold: true),
                              const Divider(height: 12),
                              _buildTaxRow('실지급액 (세후 수령액)',
                                  '${NumberFormat('#,###').format(_payout.netAmount)}원',
                                  color: const Color(0xFF10B981), isBold: true),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // 5. 정산 귀속 계약 건별 상세 리스트
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '정산 대상 계약 목록 (${_payout.contractDetails.length}건)',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  if (_payout.contractDetails.isEmpty)
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: context.colors.bgSurface,
                        border: Border.all(color: context.colors.border, width: 0.8),
                      ),
                      child: Center(
                        child: Text(
                          '정산 대상 개별 계약 내역이 없습니다.',
                          style: TextStyle(
                            fontSize: 12,
                            color: context.colors.textMuted,
                          ),
                        ),
                      ),
                    )
                  else
                    Column(
                      children: _payout.contractDetails.map((detail) {
                        return Container(
                          margin: const EdgeInsets.only(bottom: 6),
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                          decoration: BoxDecoration(
                            color: context.colors.bgSurface,
                            border: Border.all(color: context.colors.border, width: 0.8),
                          ),
                          child: Row(
                            children: [
                              const Icon(
                                Icons.assignment_outlined,
                                size: 16,
                                color: Color(0xFF6366F1),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '${detail.contractorName ?? "계약자"} (${detail.contractSerial ?? "계약"})',
                                      style: const TextStyle(
                                        fontSize: 12.5,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      '지급구분: ${detail.roleTypeDisplay ?? detail.roleType}',
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: context.colors.textMuted,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Text(
                                '₩ ${NumberFormat('#,###').format(detail.unitFee)}원',
                                style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.bold,
                                  color: Color(0xFF6366F1),
                                ),
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                    ),
                ],
              ),
            ),
          ),

          // 하단 지급 상태 제어 바
          if (canPayout)
            Container(
              padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
            ),
            child: Row(
              children: [
                Text(
                  '지급 상태 변경:',
                  style: TextStyle(fontSize: 12, color: context.colors.textMuted),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Row(
                    children: [
                      // 승인 버튼
                      Expanded(
                        child: OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: const Color(0xFF38BDF8),
                            side: const BorderSide(color: Color(0xFF38BDF8)),
                            shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.zero),
                            padding: const EdgeInsets.symmetric(vertical: 8),
                          ),
                          onPressed: _isUpdatingStatus
                              ? null
                              : () => _updatePayStatus('2'),
                          child: const Text('승인', style: TextStyle(fontSize: 11.5)),
                        ),
                      ),
                      const SizedBox(width: 4),
                      // 완료 버튼
                      Expanded(
                        child: OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: const Color(0xFF10B981),
                            side: const BorderSide(color: Color(0xFF10B981)),
                            shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.zero),
                            padding: const EdgeInsets.symmetric(vertical: 8),
                          ),
                          onPressed: _isUpdatingStatus
                              ? null
                              : () => _updatePayStatus('3'),
                          child: const Text('지급완료', style: TextStyle(fontSize: 11.5)),
                        ),
                      ),
                      const SizedBox(width: 4),
                      // 보류 버튼
                      Expanded(
                        child: OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: const Color(0xFFEF4444),
                            side: const BorderSide(color: Color(0xFFEF4444)),
                            shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.zero),
                            padding: const EdgeInsets.symmetric(vertical: 8),
                          ),
                          onPressed: _isUpdatingStatus
                              ? null
                              : () => _updatePayStatus('4'),
                          child: const Text('보류', style: TextStyle(fontSize: 11.5)),
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

  Widget _buildAmountTile({
    required String label,
    required String value,
    required String subText,
    required Color color,
  }) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: context.colors.bgSurface,
          border: Border.all(color: context.colors.border, width: 0.8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: TextStyle(fontSize: 11, color: context.colors.textMuted),
            ),
            const SizedBox(height: 2),
            Text(
              value,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: color,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            Text(
              subText,
              style: TextStyle(fontSize: 10, color: context.colors.textMuted),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTaxRow(String label, String value,
      {bool isBold = false, Color? color}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            color: context.colors.textSecond,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            fontSize: 12.5,
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            color: color ?? context.colors.textPrimary,
          ),
        ),
      ],
    );
  }
}
