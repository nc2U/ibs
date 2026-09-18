import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/inbound_letter_model.dart';

class InboundLetterCard extends StatelessWidget {
  final InboundLetterModel letter;
  final VoidCallback onTap;
  final VoidCallback? onPdfTap;

  const InboundLetterCard({
    super.key,
    required this.letter,
    required this.onTap,
    this.onPdfTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;

    // 상태 뱃지 컬러 및 라벨
    Color badgeColor = colors.textMuted;
    Color badgeBg = colors.bgSurface;
    String badgeLabel = letter.statusDesc ?? '접수';

    switch (letter.status) {
      case 'received':
        badgeColor = colors.info;
        badgeBg = colors.info.withAlpha(25);
        badgeLabel = '접수';
        break;
      case 'in_progress':
        badgeColor = colors.warning;
        badgeBg = colors.warning.withAlpha(25);
        badgeLabel = '처리중';
        break;
      case 'replied':
        badgeColor = colors.success;
        badgeBg = colors.success.withAlpha(25);
        badgeLabel = '회신완료';
        break;
      case 'closed':
        badgeColor = colors.textMuted;
        badgeBg = colors.textMuted.withAlpha(20);
        badgeLabel = '종결';
        break;
      default:
        badgeColor = colors.info;
        badgeBg = colors.info.withAlpha(25);
    }

    // D-Day 뱃지 스타일링
    Widget? dDayBadge;
    if (letter.dDay != null && letter.status != 'closed' && letter.status != 'replied') {
      final dDay = letter.dDay!;
      Color dDayColor = colors.textPrimary;
      Color dDayBg = colors.bgSurface;
      String dDayText = letter.dDayFormatted ?? '';

      if (dDay < 0) {
        dDayColor = colors.error;
        dDayBg = colors.error.withAlpha(25);
      } else if (dDay == 0) {
        dDayColor = Colors.deepOrange;
        dDayBg = Colors.deepOrange.withAlpha(25);
      } else if (dDay <= 3) {
        dDayColor = colors.warning;
        dDayBg = colors.warning.withAlpha(25);
      } else {
        dDayColor = colors.info;
        dDayBg = colors.info.withAlpha(25);
      }

      dDayBadge = Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(
          color: dDayBg,
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: dDayColor.withAlpha(80), width: 0.8),
        ),
        child: Text(
          dDayText,
          style: TextStyle(
            fontSize: 10.5,
            fontWeight: FontWeight.w700,
            color: dDayColor,
          ),
        ),
      );
    }

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      elevation: 0,
      color: colors.bgCard,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: colors.border, width: 0.8),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1행: 접수번호 + 상태 뱃지 + D-Day 뱃지
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: colors.bgSurface,
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(color: colors.borderSubtle, width: 0.8),
                    ),
                    child: Text(
                      letter.receiptNumber.isNotEmpty
                          ? letter.receiptNumber
                          : '접수번호 미채번',
                      style: TextStyle(
                        fontSize: 11,
                        fontFamily: 'monospace',
                        fontWeight: FontWeight.w700,
                        color: colors.textSecond,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: badgeBg,
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(color: badgeColor.withAlpha(80), width: 0.8),
                    ),
                    child: Text(
                      badgeLabel,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: badgeColor,
                      ),
                    ),
                  ),
                  if (dDayBadge != null) ...[
                    const SizedBox(width: 6),
                    dDayBadge,
                  ],
                  const Spacer(),
                  // 원본 스캔본 퀵 버튼
                  if (letter.hasScan && onPdfTap != null)
                    InkWell(
                      onTap: onPdfTap,
                      borderRadius: BorderRadius.circular(4),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: colors.accentApproval.withAlpha(20),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(
                            color: colors.accentApproval.withAlpha(80),
                            width: 0.8,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.picture_as_pdf_outlined,
                              size: 13,
                              color: colors.accentApproval,
                            ),
                            const SizedBox(width: 3),
                            Text(
                              '스캔본',
                              style: TextStyle(
                                fontSize: 10.5,
                                fontWeight: FontWeight.bold,
                                color: colors.accentApproval,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 8),

              // 2행: 공문 제목
              Text(
                letter.title,
                style: AppTextStyles.bodyMd.copyWith(
                  fontWeight: FontWeight.w700,
                  color: colors.textPrimary,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 6),

              // 3행: 발신처 및 발신처 문서번호
              Row(
                children: [
                  Icon(Icons.business_outlined, size: 13, color: colors.textMuted),
                  const SizedBox(width: 4),
                  Flexible(
                    child: Text(
                      letter.senderName.isNotEmpty ? letter.senderName : '발신처 미기입',
                      style: TextStyle(
                        fontSize: 12,
                        color: colors.textSecond,
                        fontWeight: FontWeight.w500,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (letter.documentNumber.isNotEmpty) ...[
                    const SizedBox(width: 6),
                    Text(
                      '(${letter.documentNumber})',
                      style: TextStyle(
                        fontSize: 11.5,
                        color: colors.textMuted,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 8),

              // 4행: 하단 메타 (접수일, 담당 부서/담당자, 첨부 여부)
              Row(
                children: [
                  Icon(Icons.calendar_today_outlined, size: 12, color: colors.textMuted),
                  const SizedBox(width: 4),
                  Text(
                    '접수: ${letter.receivedDate}',
                    style: TextStyle(fontSize: 11.5, color: colors.textMuted),
                  ),
                  if (letter.replyDueDate != null && letter.replyDueDate!.isNotEmpty) ...[
                    const SizedBox(width: 8),
                    Text(
                      '|  회신기한: ${letter.replyDueDate}',
                      style: TextStyle(fontSize: 11.5, color: colors.textMuted),
                    ),
                  ],
                  const Spacer(),
                  if (letter.recipientDeptName != null &&
                      letter.recipientDeptName!.isNotEmpty) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                      decoration: BoxDecoration(
                        color: colors.bgSurface,
                        borderRadius: BorderRadius.circular(3),
                        border: Border.all(color: colors.borderSubtle, width: 0.6),
                      ),
                      child: Text(
                        letter.recipientDeptName!,
                        style: TextStyle(fontSize: 10.5, color: colors.textSecond),
                      ),
                    ),
                    const SizedBox(width: 6),
                  ],
                  if (letter.hasAttachments)
                    Icon(
                      Icons.attach_file_rounded,
                      size: 14,
                      color: colors.textMuted,
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
