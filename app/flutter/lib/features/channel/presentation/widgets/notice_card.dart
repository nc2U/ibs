import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../data/models/notice_model.dart';

/// 공지사항 목록 아이템 카드 (radius = 0)
class NoticeCard extends StatelessWidget {
  final NoticeModel notice;
  final VoidCallback onTap;
  final bool showWorkspaceBadge;

  const NoticeCard({
    super.key,
    required this.notice,
    required this.onTap,
    this.showWorkspaceBadge = false,
  });

  @override
  Widget build(BuildContext context) {
    final hasFiles = notice.files.isNotEmpty;
    final hasComments = notice.comments.isNotEmpty;

    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(
            color: notice.isImportant
                ? AppColors.error.withAlpha(120)
                : AppColors.border,
            width: notice.isImportant ? 1.2 : 0.8,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 상단 뱃지 라인 (중요 / 워크스페이스 / New) ───────────────────
            Row(
              children: [
                if (notice.isImportant) ...[
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.error.withAlpha(25),
                      borderRadius: BorderRadius.zero,
                      border: Border.all(color: AppColors.error, width: 0.8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.campaign_rounded,
                            size: 13, color: AppColors.error),
                        const SizedBox(width: 3),
                        Text(
                          '중요 공지',
                          style: AppTextStyles.caption.copyWith(
                            color: AppColors.error,
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 6),
                ],
                if (showWorkspaceBadge && notice.project != null) ...[
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.accentWork.withAlpha(20),
                      borderRadius: BorderRadius.zero,
                      border:
                          Border.all(color: AppColors.accentWork, width: 0.8),
                    ),
                    child: Text(
                      notice.project!.name,
                      style: AppTextStyles.caption.copyWith(
                        color: AppColors.accentWork,
                        fontSize: 11,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 6),
                ],
                if (notice.isNew) ...[
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE53935),
                      borderRadius: BorderRadius.zero,
                    ),
                    child: const Text(
                      'N',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
                const Spacer(),
                if (notice.created != null)
                  Text(
                    _formatDate(notice.created!),
                    style: AppTextStyles.caption
                        .copyWith(color: AppColors.textMuted),
                  ),
              ],
            ),
            const SizedBox(height: 8),

            // ── 공지 제목 ───────────────────────────────────────────────────
            Text(
              notice.title,
              style: AppTextStyles.titleSm.copyWith(
                fontWeight:
                    notice.isImportant ? FontWeight.bold : FontWeight.w600,
                color: notice.isImportant
                    ? AppColors.textPrimary
                    : AppColors.textPrimary,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),

            // ── 요약문 (있을 경우) ──────────────────────────────────────────
            if (_stripHtml(notice.summary).isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                _stripHtml(notice.summary),
                style: AppTextStyles.bodySm
                    .copyWith(color: AppColors.textSecond, height: 1.3),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            const SizedBox(height: 10),

            // ── 하단 메타 (작성자 + 첨부파일 + 댓글 수) ────────────────────────
            Row(
              children: [
                Icon(Icons.person_outline_rounded,
                    size: 14, color: AppColors.textMuted),
                const SizedBox(width: 4),
                Text(
                  notice.author?.username ?? '작성자 미상',
                  style: AppTextStyles.caption
                      .copyWith(color: AppColors.textSecond),
                ),
                const Spacer(),
                if (hasFiles) ...[
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.attach_file_rounded,
                          size: 14, color: AppColors.textMuted),
                      const SizedBox(width: 2),
                      Text(
                        '${notice.files.length}',
                        style: AppTextStyles.caption
                            .copyWith(color: AppColors.textSecond),
                      ),
                    ],
                  ),
                  const SizedBox(width: 10),
                ],
                if (hasComments) ...[
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.chat_bubble_outline_rounded,
                          size: 13, color: AppColors.accentWork),
                      const SizedBox(width: 3),
                      Text(
                        '${notice.comments.length}',
                        style: AppTextStyles.caption.copyWith(
                          color: AppColors.accentWork,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(String raw) {
    if (raw.length >= 10) {
      return raw.substring(0, 10);
    }
    return raw;
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
