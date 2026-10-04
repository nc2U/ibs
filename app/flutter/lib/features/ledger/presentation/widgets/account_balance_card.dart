import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/ledger_models.dart';

/// 🏦 계좌별 잔액 및 프로젝트 전도금 현황 카드
class AccountBalanceCard extends StatelessWidget {
  final ProjectBalanceByAccountModel item;
  final bool isImprest;

  static final NumberFormat _currencyFormat = NumberFormat('#,###');

  const AccountBalanceCard({
    super.key,
    required this.item,
    this.isImprest = false,
  });

  @override
  Widget build(BuildContext context) {
    final themeColor = isImprest ? const Color(0xFFF59E0B) : const Color(0xFF38BDF8);

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(8),
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
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 헤더
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                Icon(
                  isImprest ? Icons.business_center_rounded : Icons.account_balance_rounded,
                  size: 16,
                  color: themeColor,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    item.bankAcc,
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
                    ),
                  ),
                ),
                if (isImprest)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF59E0B).withAlpha(20),
                      borderRadius: BorderRadius.circular(3),
                      border: Border.all(
                        color: const Color(0xFFF59E0B).withAlpha(80),
                        width: 0.6,
                      ),
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

          // 본문
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      isImprest ? '전도금 잔액' : '현재 잔액',
                      style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                    ),
                    const Spacer(),
                    Text(
                      '${_currencyFormat.format(item.balance)}원',
                      style: AppTextStyles.titleSm.copyWith(
                        color: item.balance > 0 ? themeColor : context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                        fontSize: 15.5,
                      ),
                    ),
                  ],
                ),
                if (!isImprest && item.bankNum.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    '계좌번호: ${item.bankNum}',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textMuted,
                      fontSize: 11,
                    ),
                  ),
                ],
                const SizedBox(height: 10),
                if (isImprest)
                  Text(
                    '정산 누계: 수입 ${_currencyFormat.format(item.incSum)}원 / 지출 ${_currencyFormat.format(item.outSum)}원',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textMuted,
                      fontSize: 11.5,
                    ),
                  )
                else
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                    decoration: BoxDecoration(
                      color: context.colors.bgSurface,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '총 입금 누계',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textMuted,
                                  fontSize: 10.5,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '${_currencyFormat.format(item.incSum)}원',
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
                          color: context.colors.border,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '총 출금 누계',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textMuted,
                                  fontSize: 10.5,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '${_currencyFormat.format(item.outSum)}원',
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
  }
}
