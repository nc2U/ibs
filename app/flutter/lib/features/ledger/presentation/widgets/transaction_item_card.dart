import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/ledger_models.dart';

/// 💳 출납 전표 리스트 아이템 카드
class TransactionItemCard extends StatelessWidget {
  final ProjectTransactionItemModel item;
  final VoidCallback onTap;

  static final NumberFormat _currencyFormat = NumberFormat('#,###');

  const TransactionItemCard({
    super.key,
    required this.item,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
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
          onTap: onTap,
          borderRadius: BorderRadius.circular(8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 카드 상단 헤더
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                color: context.colors.bgSurface,
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: item.sortColor.withAlpha(20),
                        borderRadius: BorderRadius.circular(3),
                        border: Border.all(
                          color: item.sortColor.withAlpha(80),
                          width: 0.6,
                        ),
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
                    Icon(
                      Icons.more_vert_rounded,
                      size: 18,
                      color: context.colors.textMuted,
                    ),
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
                          '${item.sortSign}${_currencyFormat.format(item.amount)}원',
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
  }
}
