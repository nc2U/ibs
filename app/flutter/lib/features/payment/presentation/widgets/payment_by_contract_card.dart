import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../contract/data/models/contract_models.dart';

/// 📋 계약건별 수납 종합 카드 (Payment 전용)
class PaymentByContractCard extends StatelessWidget {
  final ContractItemModel contract;
  final VoidCallback onCall;
  final VoidCallback? onSelect;

  const PaymentByContractCard({
    super.key,
    required this.contract,
    required this.onCall,
    this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    final numFormat = NumberFormat('#,###');
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
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onSelect,
          borderRadius: BorderRadius.circular(8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 8,
                ),
                color: context.colors.bgSurface,
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 7,
                        vertical: 2.5,
                      ),
                      decoration: BoxDecoration(
                        color: contract.parsedTypeColor,
                        borderRadius: BorderRadius.circular(4),
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
                      padding: const EdgeInsets.symmetric(
                        horizontal: 6,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: context.colors.success.withAlpha(20),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(
                          color: context.colors.success.withAlpha(80),
                          width: 0.6,
                        ),
                      ),
                      child: Text(
                        '수납 ${contract.paymentRate.toStringAsFixed(0)}%',
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.bold,
                          color: context.colors.success,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Icon(
                      Icons.chevron_right_rounded,
                      size: 18,
                      color: context.colors.textMuted,
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
                        if (contract.serialNumber != null &&
                            contract.serialNumber!.isNotEmpty)
                          Text(
                            '[${contract.serialNumber}]',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textMuted,
                              fontSize: 11,
                            ),
                          ),
                        const Spacer(),
                        if (contractor?.contact?.cellPhone != null)
                          TextButton.icon(
                            onPressed: onCall,
                            style: TextButton.styleFrom(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 6,
                                vertical: 2,
                              ),
                              minimumSize: Size.zero,
                              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            ),
                            icon: const Icon(
                              Icons.phone_outlined,
                              size: 13,
                              color: Color(0xFF0D9488),
                            ),
                            label: Text(
                              contractor!.contact!.cellPhone!,
                              style: const TextStyle(
                                fontSize: 11.5,
                                color: Color(0xFF0D9488),
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: context.colors.bgSurface,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '분양 공급가',
                                  style: AppTextStyles.caption.copyWith(
                                    color: context.colors.textMuted,
                                    fontSize: 10.5,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  contract.price > 0
                                      ? '${numFormat.format(contract.price)}원'
                                      : '산정 전',
                                  style: AppTextStyles.bodySecond.copyWith(
                                    color: context.colors.textPrimary,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12.5,
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
                                  '기수납 누계',
                                  style: AppTextStyles.caption.copyWith(
                                    color: context.colors.textMuted,
                                    fontSize: 10.5,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  '${numFormat.format(contract.totalPaid)}원',
                                  style: AppTextStyles.bodySecond.copyWith(
                                    color: context.colors.success,
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
                    const SizedBox(height: 10),
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: context.colors.accentProject,
                          side: BorderSide(
                            color: context.colors.accentProject.withAlpha(120),
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(6),
                          ),
                          padding: const EdgeInsets.symmetric(vertical: 7),
                        ),
                        onPressed: onSelect,
                        icon: const Icon(Icons.receipt_long_outlined, size: 15),
                        label: const Text(
                          '납부 내역 상세 보기',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
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
