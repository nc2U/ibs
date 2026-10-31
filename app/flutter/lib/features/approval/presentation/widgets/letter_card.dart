import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/letter_model.dart';

class LetterCard extends StatelessWidget {
  final OfficialLetterModel letter;
  final VoidCallback onTap;
  final VoidCallback? onPdfTap;

  const LetterCard({
    super.key,
    required this.letter,
    required this.onTap,
    this.onPdfTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final isDispatched = letter.dispatchedAt != null;
    final isApproved = letter.approvalStatus == 'approved';
    final isPending = letter.approvalStatus == 'pending';

    // 상태 뱃지 컬러 및 라벨
    Color badgeColor = colors.textMuted;
    Color badgeBg = colors.bgSurface;
    String badgeLabel = '미상신';

    if (isDispatched) {
      badgeColor = colors.success;
      badgeBg = colors.success.withAlpha(25);
      badgeLabel = '발송완료';
    } else if (isApproved) {
      badgeColor = colors.info;
      badgeBg = colors.info.withAlpha(25);
      badgeLabel = '결재승인';
    } else if (isPending) {
      badgeColor = colors.warning;
      badgeBg = colors.warning.withAlpha(25);
      badgeLabel = '결재진행';
    } else if (letter.isSoloApproval) {
      badgeColor = colors.accentApproval;
      badgeBg = colors.accentApproval.withAlpha(25);
      badgeLabel = '단독발송';
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
              // 1행: 문서번호 + 상태 뱃지 + 발송방법
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
                      letter.documentNumber.isNotEmpty
                          ? letter.documentNumber
                          : '문서번호 미채번',
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
                  const Spacer(),
                  if (letter.dispatchMethodDesc != null &&
                      letter.dispatchMethodDesc!.isNotEmpty) ...[
                    Text(
                      letter.dispatchMethodDesc!,
                      style: TextStyle(
                        fontSize: 11,
                        color: colors.textMuted,
                      ),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 10),

              // 2행: 공문 제목
              Text(
                letter.title,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: AppTextStyles.titleSm.copyWith(
                  fontWeight: FontWeight.w700,
                  color: colors.textPrimary,
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 10),

              // 3행: 수신처 / 기안자 / 일자 정보
              Row(
                children: [
                  Icon(Icons.business_rounded, size: 13, color: colors.textMuted),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      '수신: ${letter.recipientName}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 12,
                        color: colors.textSecond,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  if (letter.hasAttachments) ...[
                    const SizedBox(width: 6),
                    Icon(Icons.attach_file_rounded, size: 14, color: colors.accentApproval),
                  ],
                ],
              ),
              const SizedBox(height: 4),
              Row(
                children: [
                  Icon(Icons.person_outline_rounded, size: 13, color: colors.textMuted),
                  const SizedBox(width: 4),
                  Text(
                    '기안: ${letter.drafterName}',
                    style: TextStyle(fontSize: 11.5, color: colors.textMuted),
                  ),
                  const Spacer(),
                  Icon(Icons.calendar_today_outlined, size: 12, color: colors.textMuted),
                  const SizedBox(width: 4),
                  Text(
                    letter.effectiveIssueDate ?? letter.issueDate ?? '',
                    style: TextStyle(
                      fontSize: 11.5,
                      color: colors.textMuted,
                    ),
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
