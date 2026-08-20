import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/approval_model.dart';
import 'approval_status_chip.dart';

class ApprovalDocCard extends StatelessWidget {
  final ApprovalDocumentModel document;
  final VoidCallback onTap;

  const ApprovalDocCard({
    super.key,
    required this.document,
    required this.onTap,
  });

  String _formatDate(String? rawDate) {
    if (rawDate == null || rawDate.isEmpty) return '-';
    try {
      final dt = DateTime.parse(rawDate).toLocal();
      return '${dt.year}.${dt.month.toString().padLeft(2, '0')}.${dt.day.toString().padLeft(2, '0')}';
    } catch (_) {
      return rawDate.split('T').first;
    }
  }

  @override
  Widget build(BuildContext context) {
    final drafterText = document.drafterName ?? document.drafter.username;
    final assignDesc = document.drafterAssignmentDesc ?? document.departmentName ?? '';

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 상단 메타 바 (문서유형 / 문서번호 / 상태뱃지) ─────────────
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: context.colors.accentApproval.withAlpha(20),
                      borderRadius: BorderRadius.zero,
                      border: Border.all(
                        color: context.colors.accentApproval.withAlpha(70),
                        width: 0.6,
                      ),
                    ),
                    child: Text(
                      document.docTypeName ?? '기안서',
                      style: TextStyle(
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
                        color: context.colors.accentApprovalDeep,
                      ),
                    ),
                  ),
                  if (document.docNumber.isNotEmpty) ...[
                    const SizedBox(width: 6),
                    Text(
                      document.docNumber,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: context.colors.textMuted,
                        fontFamily: 'monospace',
                      ),
                    ),
                  ],
                  const Spacer(),
                  ApprovalStatusChip(
                    status: document.status,
                    statusDesc: document.statusDesc,
                    isSmall: true,
                  ),
                ],
              ),
              const SizedBox(height: 10),

              // ── 문서 제목 ───────────────────────────────────────────────
              Text(
                document.title,
                style: AppTextStyles.titleMd.copyWith(
                  fontWeight: FontWeight.w700,
                  color: context.colors.textPrimary,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 10),

              // ── 하단 정보: 기안자 / 부서 / 첨부 / 일시 ────────────────────
              Row(
                children: [
                  Icon(
                    Icons.person_outline_rounded,
                    size: 14,
                    color: context.colors.textMuted,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    drafterText,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: context.colors.textSecond,
                    ),
                  ),
                  if (assignDesc.isNotEmpty) ...[
                    Text(
                      ' ($assignDesc)',
                      style: TextStyle(
                        fontSize: 11.5,
                        color: context.colors.textMuted,
                      ),
                    ),
                  ],
                  const Spacer(),
                  if (document.attachmentCount > 0) ...[
                    Icon(
                      Icons.attach_file_rounded,
                      size: 13,
                      color: context.colors.textMuted,
                    ),
                    const SizedBox(width: 2),
                    Text(
                      '${document.attachmentCount}',
                      style: TextStyle(
                        fontSize: 11,
                        color: context.colors.textMuted,
                      ),
                    ),
                    const SizedBox(width: 8),
                  ],
                  Icon(
                    Icons.schedule_rounded,
                    size: 13,
                    color: context.colors.textMuted,
                  ),
                  const SizedBox(width: 3),
                  Text(
                    _formatDate(document.submittedAt ?? document.createdAt),
                    style: TextStyle(
                      fontSize: 11,
                      color: context.colors.textMuted,
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
