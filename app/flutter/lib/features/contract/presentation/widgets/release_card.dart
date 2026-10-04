import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/contract_models.dart';

/// 🚫 계약 해약/해지 개별 카드 위젯
class ReleaseCard extends StatelessWidget {
  static final NumberFormat _currencyFormat = NumberFormat('#,###');

  final ContractorReleaseItemModel release;

  const ReleaseCard({
    super.key,
    required this.release,
  });

  @override
  Widget build(BuildContext context) {
    Color statusColor;
    if (release.status == '4') {
      statusColor = context.colors.error; // 해지확정
    } else if (release.status == '3') {
      statusColor = const Color(0xFF38BDF8); // 환불완료
    } else {
      statusColor = const Color(0xFFFBBF24); // 신청/정산
    }

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
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                Icon(Icons.cancel_outlined, size: 16, color: context.colors.error),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    release.displayContractorName,
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: statusColor.withAlpha(20),
                    borderRadius: BorderRadius.circular(3),
                    border: Border.all(color: statusColor.withAlpha(80), width: 0.6),
                  ),
                  child: Text(
                    release.statusDisplay,
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: statusColor,
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
                    Text('해약 신청일: ${release.requestDate}',
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5)),
                    const Spacer(),
                    if (release.completionDate != null)
                      Text('완결일: ${release.completionDate}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5)),
                  ],
                ),
                const SizedBox(height: 8),
                if (release.refundAmount != null)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                    decoration: BoxDecoration(
                      color: context.colors.bgSurface,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Row(
                      children: [
                        Text('환불 정산액',
                            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5)),
                        const Spacer(),
                        Text('${_currencyFormat.format(release.refundAmount)}원',
                            style: AppTextStyles.titleSm.copyWith(
                              color: const Color(0xFF38BDF8),
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            )),
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
