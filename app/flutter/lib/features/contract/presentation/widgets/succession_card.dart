import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/contract_models.dart';

/// 🔄 권리의무 승계 개별 카드 위젯
class SuccessionCard extends StatelessWidget {
  final SuccessionItemModel succession;
  final VoidCallback onCallBuyer;

  const SuccessionCard({
    super.key,
    required this.succession,
    required this.onCallBuyer,
  });

  @override
  Widget build(BuildContext context) {
    Color statusColor;
    if (succession.status == '3') {
      statusColor = const Color(0xFF34D399); // 승계완료
    } else if (succession.status == '9') {
      statusColor = context.colors.error; // 취소
    } else {
      statusColor = const Color(0xFF8B5CF6); // 접수/대기
    }

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
                Icon(Icons.swap_horiz_rounded, size: 16, color: context.colors.accentProject),
                const SizedBox(width: 8),
                Text(
                  '일련번호: ${succession.serialNumber ?? '-'}',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: statusColor.withAlpha(20),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: statusColor.withAlpha(80), width: 0.6),
                  ),
                  child: Text(
                    succession.statusDisplay,
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
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('양도인 (매도)',
                              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11)),
                          const SizedBox(height: 2),
                          Text(succession.sellerName,
                              style: AppTextStyles.titleSm.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              )),
                        ],
                      ),
                    ),
                    const Icon(Icons.arrow_forward_rounded, size: 16, color: Color(0xFF8B5CF6)),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text('양수인 (매수)',
                              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11)),
                          const SizedBox(height: 2),
                          Text(succession.buyerName,
                              style: AppTextStyles.titleSm.copyWith(
                                color: const Color(0xFF38BDF8),
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              )),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Text('신청일: ${succession.applyDate}',
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5)),
                    const Spacer(),
                    if (succession.approvalDate != null)
                      Text('승인일: ${succession.approvalDate}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11.5)),
                  ],
                ),
              ],
            ),
          ),
          if (succession.buyerCellPhone != null && succession.buyerCellPhone!.isNotEmpty) ...[
            Divider(color: context.colors.border, height: 1),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              child: Row(
                children: [
                  TextButton.icon(
                    onPressed: onCallBuyer,
                    icon: const Icon(Icons.phone_outlined, size: 14, color: Color(0xFF0D9488)),
                    label: Text('양수인 전화 (${succession.buyerCellPhone})',
                        style: const TextStyle(fontSize: 11.5, color: Color(0xFF0D9488))),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
