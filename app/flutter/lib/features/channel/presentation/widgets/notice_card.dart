import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/notice_model.dart';

/// 공지사항 목록 아이템 카드 (radius = 0)
class NoticeCard extends StatelessWidget {
  final NoticeModel notice;
  final VoidCallback onTap;
  final bool showWorkspaceBadge;

  static const _importantAccent = Color(0xFFE5A93C); // 품위 있는 웜 앰버-골드

  const NoticeCard({
    super.key,
    required this.notice,
    required this.onTap,
    this.showWorkspaceBadge = false,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = context.isDarkMode;
    final importantBg = isDark
        ? const Color(0xFF222538)
        : const Color(0xFFFFFBEB); // 웜 앰버 라이트 틴트 (Amber 50)

    final hasFiles = notice.files.isNotEmpty;
    final hasComments = notice.comments.isNotEmpty;

    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: notice.isImportant ? importantBg : context.colors.bgCard,
          borderRadius: BorderRadius.zero,
          border: notice.isImportant
              ? Border(
                  left: const BorderSide(color: _importantAccent, width: 3.5),
                  top: BorderSide(
                      color: _importantAccent.withAlpha(isDark ? 96 : 140),
                      width: 0.8),
                  right: BorderSide(
                      color: _importantAccent.withAlpha(isDark ? 96 : 140),
                      width: 0.8),
                  bottom: BorderSide(
                      color: _importantAccent.withAlpha(isDark ? 96 : 140),
                      width: 0.8),
                )
              : Border.all(color: context.colors.border, width: 0.8),
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
                        const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                    decoration: BoxDecoration(
                      color: _importantAccent.withAlpha(28),
                      borderRadius: BorderRadius.zero,
                      border: Border.all(
                          color: _importantAccent.withAlpha(120), width: 0.8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.campaign_rounded,
                            size: 13, color: _importantAccent),
                        const SizedBox(width: 4),
                        Text(
                          '중요 공지',
                          style: AppTextStyles.caption.copyWith(
                            color: _importantAccent,
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
                      color: context.colors.accentChannel.withAlpha(20),
                      borderRadius: BorderRadius.zero,
                      border:
                          Border.all(color: context.colors.accentChannel.withAlpha(60), width: 0.8),
                    ),
                    child: Text(
                      notice.project!.name,
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.accentChannel,
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
                      color: context.colors.warning.withAlpha(30),
                      borderRadius: BorderRadius.zero,
                      border: Border.all(
                          color: context.colors.warning.withAlpha(80), width: 0.8),
                    ),
                    child: Text(
                      'N',
                      style: TextStyle(
                        color: context.colors.warning,
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
                        .copyWith(color: context.colors.textMuted),
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
                color: context.colors.textPrimary,
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
                    .copyWith(color: context.colors.textSecond, height: 1.3),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            const SizedBox(height: 10),

            // ── 하단 메타정보 (작성자 + 파일/댓글 카운트) ─────────────────────
            Row(
              children: [
                Icon(Icons.person_outline_rounded,
                    size: 14, color: context.colors.textMuted),
                const SizedBox(width: 4),
                Text(
                  notice.author?.username ?? '관리자',
                  style: AppTextStyles.caption
                      .copyWith(color: context.colors.textSecond),
                ),
                const Spacer(),
                if (hasFiles) ...[
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.attach_file_rounded,
                          size: 13, color: context.colors.textMuted),
                      const SizedBox(width: 2),
                      Text(
                        '${notice.files.length}',
                        style: AppTextStyles.caption
                            .copyWith(color: context.colors.textSecond),
                      ),
                    ],
                  ),
                  const SizedBox(width: 8),
                ],
                if (hasComments) ...[
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.chat_bubble_outline_rounded,
                          size: 13, color: context.colors.accentChannel),
                      const SizedBox(width: 3),
                      Text(
                        '${notice.comments.length}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.accentChannel,
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
