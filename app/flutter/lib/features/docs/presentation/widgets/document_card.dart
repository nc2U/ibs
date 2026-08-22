import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/docs_model.dart';

/// 공용 문서 카드 위젯 (radius = 0)
class DocumentCard extends StatelessWidget {
  final DocumentModel doc;
  final VoidCallback onTap;

  const DocumentCard({
    super.key,
    required this.doc,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isRealEstate = doc.projType == '2';
    final scopeLabel = doc.project != null
        ? (isRealEstate ? '🏗 ${doc.project!.name}' : '📋 ${doc.project!.name}')
        : '전체 공용';
    final scopeColor = isRealEstate ? context.colors.accentProject : const Color(0xFF1565C0);

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(
          color: doc.isPinned
              ? context.colors.accentWork.withAlpha(120)
              : context.colors.border,
          width: doc.isPinned ? 1.2 : 0.8,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.zero,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.zero,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── 상단 배지 바 (소속 범위 + 상단고정 + 비밀글) ────────────────
                Row(
                  children: [
                    // 소속 범위 뱃지
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 7, vertical: 2),
                      decoration: BoxDecoration(
                        color: scopeColor.withAlpha(25),
                        borderRadius: BorderRadius.zero,
                        border: Border.all(color: scopeColor.withAlpha(60)),
                      ),
                      child: Text(
                        scopeLabel,
                        style: AppTextStyles.caption.copyWith(
                          color: scopeColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 11,
                        ),
                      ),
                    ),
                    if (doc.cateName != null && doc.cateName!.isNotEmpty) ...[
                      const SizedBox(width: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          borderRadius: BorderRadius.zero,
                          border: Border.all(color: context.colors.border),
                        ),
                        child: Text(
                          doc.cateName!,
                          style: AppTextStyles.caption.copyWith(
                            fontSize: 11,
                            color: context.colors.textMuted,
                          ),
                        ),
                      ),
                    ],
                    const Spacer(),
                    if (doc.isPinned) ...[
                      Icon(Icons.push_pin_rounded,
                          size: 15, color: context.colors.accentWork),
                      const SizedBox(width: 4),
                    ],
                    if (doc.isSecret)
                      Icon(Icons.lock_rounded,
                          size: 15, color: context.colors.warning),
                  ],
                ),
                const SizedBox(height: 10),

                // ── 제목 ───────────────────────────────────────────────────
                Text(
                  doc.title,
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: doc.isPinned ? FontWeight.bold : FontWeight.w600,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                if (_stripHtml(doc.description).isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    _stripHtml(doc.description),
                    style: AppTextStyles.bodySm
                        .copyWith(color: context.colors.textMuted),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
                const SizedBox(height: 10),

                // ── 하단 정보 (시행일 / 등록자 / 첨부파일 수) ─────────────────
                Row(
                  children: [
                    if (doc.executionDate != null && doc.executionDate!.isNotEmpty) ...[
                      Icon(Icons.event_note_rounded,
                          size: 13, color: context.colors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        doc.executionDate!,
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                      ),
                      const SizedBox(width: 12),
                    ],
                    if (doc.creator != null) ...[
                      Icon(Icons.person_outline_rounded,
                          size: 13, color: context.colors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        doc.creator!.username,
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                      ),
                      const SizedBox(width: 12),
                    ],
                    if (doc.files.isNotEmpty) ...[
                      Icon(Icons.attach_file_rounded,
                          size: 13, color: context.colors.accentWork),
                      const SizedBox(width: 2),
                      Text(
                        '${doc.files.length}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.accentWork,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _stripHtml(String html) {
    if (html.isEmpty) return '';
    return html
        .replaceAll(RegExp(r'<[^>]*>'), ' ')
        .replaceAll('&nbsp;', ' ')
        .replaceAll('&amp;', '&')
        .replaceAll('&lt;', '<')
        .replaceAll('&gt;', '>')
        .replaceAll('&quot;', '"')
        .replaceAll('&#39;', "'")
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
  }
}
