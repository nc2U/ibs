import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/forum_model.dart';

/// 게시판 게시글 카드 위젯 (radius = 0)
class PostCard extends StatelessWidget {
  final PostModel post;
  final bool showWorkspaceBadge;
  final VoidCallback onTap;

  const PostCard({
    super.key,
    required this.post,
    this.showWorkspaceBadge = false,
    required this.onTap,
  });

  static const _noticeAccent = Color(0xFFE5A93C); // 품위 있는 웜 앰버-골드

  @override
  Widget build(BuildContext context) {
    final isDark = context.isDarkMode;
    final noticeBg = isDark
        ? const Color(0xFF222538)
        : const Color(0xFFFFFBEB); // 웜 앰버 라이트 틴트 (Amber 50)

    final plainContent = _stripHtml(post.content);
    final hasFiles = post.files.isNotEmpty;
    final hasComments = post.comments.isNotEmpty;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: post.isNotice ? noticeBg : context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: post.isNotice
            ? Border(
                left: const BorderSide(color: _noticeAccent, width: 3.5),
                top: BorderSide(
                    color: _noticeAccent.withAlpha(isDark ? 96 : 140),
                    width: 0.8),
                right: BorderSide(
                    color: _noticeAccent.withAlpha(isDark ? 96 : 140),
                    width: 0.8),
                bottom: BorderSide(
                    color: _noticeAccent.withAlpha(isDark ? 96 : 140),
                    width: 0.8),
              )
            : Border.all(color: context.colors.border, width: 0.8),
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
                // ── 1. 상단 배지 바 (공지 + 카테고리 + 게시판명) ───────────────
                Row(
                  children: [
                    if (post.isNotice) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 7, vertical: 2.5),
                        decoration: BoxDecoration(
                          color: _noticeAccent.withAlpha(28),
                          borderRadius: BorderRadius.zero,
                          border: Border.all(
                              color: _noticeAccent.withAlpha(120), width: 0.8),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.campaign_rounded,
                                size: 13, color: _noticeAccent),
                            const SizedBox(width: 4),
                            Text(
                              '공지',
                              style: AppTextStyles.caption.copyWith(
                                color: _noticeAccent,
                                fontWeight: FontWeight.bold,
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 6),
                    ],
                    if (post.cateName != null && post.cateName!.isNotEmpty) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: context.colors.accentChannel.withAlpha(15),
                          borderRadius: BorderRadius.zero,
                          border: Border.all(
                            color: context.colors.accentChannel.withAlpha(60),
                            width: 0.8,
                          ),
                        ),
                        child: Text(
                          post.cateName!,
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.accentChannel,
                            fontWeight: FontWeight.w600,
                            fontSize: 11,
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                    ],
                    if (post.forumName.isNotEmpty) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          borderRadius: BorderRadius.zero,
                          border: Border.all(
                            color: context.colors.border,
                            width: 0.8,
                          ),
                        ),
                        child: Text(
                          post.forumName,
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textSecond,
                            fontSize: 11,
                          ),
                        ),
                      ),
                    ],
                    const Spacer(),
                    if (post.isNew) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 5, vertical: 1),
                        decoration: BoxDecoration(
                          color: context.colors.warning.withAlpha(30),
                          borderRadius: BorderRadius.zero,
                        ),
                        child: Text(
                          'N',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.warning,
                            fontWeight: FontWeight.bold,
                            fontSize: 10,
                          ),
                        ),
                      ),
                      const SizedBox(width: 4),
                    ],
                    if (post.isSecret)
                      Icon(Icons.lock_rounded,
                          size: 14, color: context.colors.warning),
                  ],
                ),
                const SizedBox(height: 8),

                // ── 2. 게시글 제목 ──────────────────────────────────────────
                Text(
                  post.title,
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight:
                        post.isNotice ? FontWeight.bold : FontWeight.w600,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),

                // ── 3. 본문 텍스트 프리뷰 ──────────────────────────────────
                if (plainContent.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    plainContent,
                    style: AppTextStyles.bodySm
                        .copyWith(color: context.colors.textSecond, height: 1.3),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
                const SizedBox(height: 10),

                // ── 4. 하단 메타정보 (작성자 + 작성일 + 조회수 + 좋아요 + 파일/댓글수) ─
                Row(
                  children: [
                    Icon(Icons.person_outline_rounded,
                    size: 14, color: context.colors.textMuted),
                    const SizedBox(width: 4),
                    Text(
                      post.creator?.username ?? '익명',
                      style: AppTextStyles.caption
                          .copyWith(color: context.colors.textSecond),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      _formatDate(post.created ?? ''),
                      style: AppTextStyles.caption
                          .copyWith(color: context.colors.textMuted),
                    ),
                    const Spacer(),
                    // 조회수
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.visibility_outlined,
                            size: 13, color: context.colors.textMuted),
                        const SizedBox(width: 3),
                        Text(
                          '${post.hit}',
                          style: AppTextStyles.caption
                              .copyWith(color: context.colors.textMuted),
                        ),
                      ],
                    ),
                    if (post.like > 0) ...[
                      const SizedBox(width: 8),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.thumb_up_alt_outlined,
                              size: 12, color: context.colors.accentProject),
                          const SizedBox(width: 2),
                          Text(
                            '${post.like}',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.accentProject,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ],
                    if (hasFiles) ...[
                      const SizedBox(width: 8),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.attach_file_rounded,
                              size: 13, color: context.colors.textMuted),
                          const SizedBox(width: 2),
                          Text(
                            '${post.files.length}',
                            style: AppTextStyles.caption
                                .copyWith(color: context.colors.textSecond),
                          ),
                        ],
                      ),
                    ],
                    if (hasComments) ...[
                      const SizedBox(width: 8),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.chat_bubble_outline_rounded,
                              size: 13, color: context.colors.accentChannel),
                          const SizedBox(width: 3),
                          Text(
                            '${post.comments.length}',
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
