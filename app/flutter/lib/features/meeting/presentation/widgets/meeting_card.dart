import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/meeting_model.dart';

/// 회의 목록 카드 위젯
class MeetingCard extends StatelessWidget {
  final MeetingModel meeting;
  final VoidCallback? onTap;
  final VoidCallback? onExportPdf;

  const MeetingCard({
    super.key,
    required this.meeting,
    this.onTap,
    this.onExportPdf,
  });

  @override
  Widget build(BuildContext context) {
    final statusColor = _statusColor(context, meeting.status);

    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          border: Border.all(color: context.colors.border, width: 0.8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 상단 행: 카테고리 + 상태배지 + 확정 여부 ──────────────────────
            Row(
              children: [
                if (meeting.categoryDesc != null) ...[
                  _CategoryBadge(
                    name: meeting.categoryDesc!.name,
                    colorHex: meeting.categoryDesc!.color,
                  ),
                  const SizedBox(width: 6),
                ],
                _StatusBadge(
                  label: meeting.statusDisplay,
                  color: statusColor,
                ),
                if (meeting.isConfirmed) ...[
                  const SizedBox(width: 6),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: context.colors.accentProject.withAlpha(30),
                      borderRadius: BorderRadius.circular(3),
                      border: Border.all(
                          color: context.colors.accentProject.withAlpha(80)),
                    ),
                    child: Text(
                      '확정',
                      style: AppTextStyles.label
                          .copyWith(color: context.colors.accentProject),
                    ),
                  ),
                ],
                const Spacer(),
                Icon(Icons.calendar_today_outlined,
                    size: 13, color: context.colors.textMuted),
                const SizedBox(width: 4),
                Text(
                  _formatDate(meeting.meetingDate),
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                ),
              ],
            ),
            const SizedBox(height: 8),

            // ── 제목 ──────────────────────────────────────────────────────────
            Text(
              meeting.title,
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.w600,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 10),

            // ── 하단 행: 참석자 수 + 액션아이템/이슈 수 + PDF 출력 ─────────────
            Row(
              children: [
                Icon(Icons.people_outline_rounded,
                    size: 14, color: context.colors.textMuted),
                const SizedBox(width: 4),
                Text(
                  '${meeting.attendeesDesc.length}명 참석',
                  style: AppTextStyles.caption.copyWith(color: context.colors.textSecond),
                ),
                if (meeting.issues.isNotEmpty) ...[
                  const SizedBox(width: 12),
                  Icon(Icons.task_alt_rounded,
                      size: 14, color: context.colors.accentWork),
                  const SizedBox(width: 4),
                  Text(
                    '액션아이템 ${meeting.issues.length}건',
                    style: AppTextStyles.caption
                        .copyWith(color: context.colors.accentWork, fontWeight: FontWeight.w600),
                  ),
                ],
                const Spacer(),
                if (onExportPdf != null)
                  Material(
                    color: context.colors.accentWork.withAlpha(20),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.zero,
                      side: BorderSide(
                        color: context.colors.accentWork.withAlpha(70),
                        width: 0.8,
                      ),
                    ),
                    child: InkWell(
                      onTap: onExportPdf,
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 3),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.picture_as_pdf_outlined,
                              size: 13,
                              color: Color(0xFFEF5350),
                            ),
                            const SizedBox(width: 4),
                            Text(
                              'PDF',
                              style: AppTextStyles.caption.copyWith(
                                color: context.colors.accentWork,
                                fontWeight: FontWeight.w600,
                                fontSize: 11,
                                letterSpacing: 0.3,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Color _statusColor(BuildContext context, String status) {
    switch (status) {
      case '1': // 준비
        return context.colors.accentWork;
      case '2': // 종료
        return context.colors.textDisabled;
      case '3': // 취소
        return context.colors.error;
      default:
        return context.colors.accentWork;
    }
  }

  String _formatDate(String dateStr) {
    if (dateStr.isEmpty) return '';
    var formatted = dateStr.replaceAll('T', ' ');
    if (formatted.length >= 16) {
      final datePart = formatted.substring(0, 10).replaceAll('-', '.');
      final timePart = formatted.substring(11, 16);
      return '$datePart $timePart';
    }
    return dateStr;
  }
}

class _CategoryBadge extends StatelessWidget {
  final String name;
  final String colorHex;
  const _CategoryBadge({required this.name, required this.colorHex});

  Color _parseColor(BuildContext context, String hex) {
    try {
      final cleaned = hex.replaceAll('#', '');
      return Color(int.parse('FF$cleaned', radix: 16));
    } catch (_) {
      return context.colors.accentWork;
    }
  }

  Color _adjustTextColor(BuildContext context, Color color) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    if (isDark) {
      return color.computeLuminance() < 0.25
          ? HSLColor.fromColor(color).withLightness(0.65).toColor()
          : color;
    } else {
      // 라이트 모드에서는 색상이 너무 밝으면 가독성이 떨어지므로 어둡게 조정
      return color.computeLuminance() > 0.4
          ? HSLColor.fromColor(color).withLightness(0.35).toColor()
          : color;
    }
  }

  @override
  Widget build(BuildContext context) {
    final rawColor = _parseColor(context, colorHex);
    final textColor = _adjustTextColor(context, rawColor);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: textColor.withAlpha(25),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: textColor.withAlpha(70)),
      ),
      child: Text(
        name,
        style: AppTextStyles.label.copyWith(
          color: textColor,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String label;
  final Color color;
  const _StatusBadge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: color.withAlpha(70)),
      ),
      child: Text(
        label,
        style: AppTextStyles.label.copyWith(
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
