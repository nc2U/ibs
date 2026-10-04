import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/contract_models.dart';

/// 📋 유효 계약 개별 카드 위젯
class ContractCard extends StatelessWidget {
  static final NumberFormat _currencyFormat = NumberFormat('#,###');

  final ContractItemModel contract;
  final VoidCallback onMoreTap;

  const ContractCard({
    super.key,
    required this.contract,
    required this.onMoreTap,
  });

  @override
  Widget build(BuildContext context) {
    final contractor = contract.contractor;

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
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onMoreTap,
          splashColor: context.colors.accentProject.withAlpha(20),
          highlightColor: context.colors.accentProject.withAlpha(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 카드 상단 헤더 (동호수 & 타입 뱃지 & 계약상태 & 더보기 아이콘) ──
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                color: context.colors.bgSurface,
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                      decoration: BoxDecoration(
                        color: contract.parsedTypeColor,
                        borderRadius: BorderRadius.circular(3),
                        border: Border.all(
                          color: contract.typeBorderColor,
                          width: 0.8,
                        ),
                      ),
                      child: Text(
                        contract.unitTypeName ?? '타입',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: contract.typeTextColor,
                          letterSpacing: 0.2,
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
                        color: const Color(0xFF34D399).withAlpha(20),
                        borderRadius: BorderRadius.circular(3),
                        border: Border.all(color: const Color(0xFF34D399).withAlpha(80), width: 0.6),
                      ),
                      child: const Text(
                        '계약유효',
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF34D399),
                        ),
                      ),
                    ),
                    const SizedBox(width: 4),
                    Icon(
                      Icons.more_vert_rounded,
                      size: 18,
                      color: context.colors.textMuted,
                    ),
                  ],
                ),
              ),
              Divider(color: context.colors.border, height: 1),

              // ── 카드 본문 (계약자명, 시리얼, 계약일, 분양가/납부액) ──
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
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textMuted,
                              fontSize: 11,
                            ),
                          ),
                        const Spacer(),
                        if (contractor?.contractDate != null)
                          Text(
                            '계약일: ${contractor!.contractDate}',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textMuted,
                              fontSize: 11,
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 10),
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
                                Text('분양 공급가',
                                    style: AppTextStyles.caption.copyWith(
                                        color: context.colors.textMuted, fontSize: 10.5)),
                                const SizedBox(height: 2),
                                Text(
                                  contract.price > 0
                                      ? '${_currencyFormat.format(contract.price)}원'
                                      : '동호지정 후 산정',
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
                                Text(
                                  '기납부액 (${contract.paymentRate.toStringAsFixed(0)}%)',
                                  style: AppTextStyles.caption.copyWith(
                                      color: context.colors.textMuted, fontSize: 10.5),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  '${_currencyFormat.format(contract.totalPaid)}원',
                                  style: AppTextStyles.bodySecond.copyWith(
                                    color: const Color(0xFF38BDF8),
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
        ),
      ),
    );
  }
}
