import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/forum_model.dart';

/// 표준 업무용 게시판 카드 (Clean Standard Post Card)
/// - 상단: [공지 / 카테고리 태그] + [등록일자 / N 표시]
/// - 본문: 제목 (가장 강조) + 본문 미리보기
/// - 하단: 작성자 + 인터랙션 (댓글 💬 / 좋아요 ❤️ / 첨부파일 📎 / 조회수 👁️)
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

  static const _noticeAccent = Color(0xFFD97706); // 앰버 600

  @override
  Widget build(BuildContext context) {
    final isDark = context.isDarkMode;
    final plainContent = _stripHtml(post.content);
    final hasFiles = post.files.isNotEmpty;
    final hasComments = post.comments.isNotEmpty;
    final hasLikes = post.like > 0;

    final cardBg = post.isNotice
        ? (isDark ? const Color(0xFF1E2130) : const Color(0xFFFFFDF5))
        : context.colors.bgCard;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(
          color: post.isNotice ? _noticeAccent.withAlpha(isDark ? 90 : 130) : context.colors.border,
          width: 0.8,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(4),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(4),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── 1. 상단 라인: [카테고리 / 공지 / 비밀글] + [등록일자 / N] ──────
                Row(
                  children: [
                    if (post.isNotice) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: _noticeAccent.withAlpha(25),
                          borderRadius: BorderRadius.circular(3),
                          border: Border.all(color: _noticeAccent.withAlpha(90), width: 0.8),
                        ),
                        child: const Text(
                          '공지',
                          style: TextStyle(
                            color: _noticeAccent,
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                    ],

                    if (post.cateName != null && post.cateName!.isNotEmpty) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: context.colors.accentChannel.withAlpha(18),
                          borderRadius: BorderRadius.circular(3),
                          border: Border.all(color: context.colors.accentChannel.withAlpha(60), width: 0.8),
                        ),
                        child: Text(
                          post.cateName!,
                          style: TextStyle(
                            color: context.colors.accentChannel,
                            fontWeight: FontWeight.w600,
                            fontSize: 11,
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                    ],

                    if (post.isSecret) ...[
                      const Icon(Icons.lock_rounded, size: 13, color: Color(0xFFD97706)),
                      const SizedBox(width: 6),
                    ],

                    if (post.isNew) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 4.5, vertical: 1),
                        decoration: BoxDecoration(
                          color: context.colors.warning.withAlpha(30),
                          borderRadius: BorderRadius.circular(2),
                        ),
                        child: Text(
                          'N',
                          style: TextStyle(
                            color: context.colors.warning,
                            fontSize: 9.5,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                    ],

                    const Spacer(),

                    // 등록일
                    if (post.created != null)
                      Text(
                        _formatDate(post.created!),
                        style: TextStyle(
                          color: context.colors.textMuted,
                          fontSize: 11.5,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 8),

                // ── 2. 게시글 제목 (가장 명확하고 또렷하게 노출) ───────────────────
                Text(
                  post.title.isNotEmpty ? post.title : '제목 없음',
                  style: TextStyle(
                    color: context.colors.textPrimary,
                    fontWeight: post.isNotice ? FontWeight.w800 : FontWeight.w700,
                    fontSize: 14.5,
                    height: 1.35,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),

                // ── 3. 본문 텍스트 프리뷰 ──────────────────────────────────
                if (plainContent.isNotEmpty) ...[
                  const SizedBox(height: 5),
                  Text(
                    plainContent,
                    style: TextStyle(
                      color: context.colors.textSecond,
                      height: 1.35,
                      fontSize: 12.5,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
                const SizedBox(height: 10),

                // ── 4. 하단 메타정보 라인: [작성자] + [인터랙션/카운트 정보] ────────
                Row(
                  children: [
                    Icon(Icons.person_outline_rounded, size: 13.5, color: context.colors.textMuted),
                    const SizedBox(width: 4),
                    Text(
                      post.creator?.username ?? '익명',
                      style: TextStyle(
                        color: context.colors.textSecond,
                        fontWeight: FontWeight.w500,
                        fontSize: 11.5,
                      ),
                    ),
                    const Spacer(),

                    // 댓글 카운트
                    if (hasComments) ...[
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.chat_bubble_outline_rounded, size: 12, color: context.colors.accentChannel),
                          const SizedBox(width: 3),
                          Text(
                            '${post.comments.length}',
                            style: TextStyle(
                              color: context.colors.accentChannel,
                              fontWeight: FontWeight.bold,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(width: 10),
                    ],

                    // 좋아요 카운트
                    if (hasLikes) ...[
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            post.myLike ? Icons.favorite_rounded : Icons.favorite_border_rounded,
                            size: 13,
                            color: Colors.redAccent,
                          ),
                          const SizedBox(width: 2.5),
                          Text(
                            '${post.like}',
                            style: const TextStyle(
                              color: Colors.redAccent,
                              fontWeight: FontWeight.w600,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(width: 10),
                    ],

                    // 첨부파일
                    if (hasFiles) ...[
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.attach_file_rounded, size: 13.5, color: context.colors.textMuted),
                          const SizedBox(width: 2),
                          Text(
                            '${post.files.length}',
                            style: TextStyle(
                              color: context.colors.textSecond,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(width: 10),
                    ],

                    // 조회수
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.visibility_outlined, size: 13, color: context.colors.textMuted),
                        const SizedBox(width: 3),
                        Text(
                          '${post.hit}',
                          style: TextStyle(
                            color: context.colors.textMuted,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
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
