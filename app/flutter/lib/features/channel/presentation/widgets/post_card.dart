import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/user_avatar.dart';
import '../../data/models/forum_model.dart';

/// 게시판 소셜 피드 카드 (Social Feed Post Card)
/// - 상단: 작성자 프로필 아바타 + 이름 + 등록 시간 (상대 시간) + 카테고리 태그 칩
/// - 본문: 제목 + 텍스트 미리보기
/// - 하단: 인터랙션 바 (게시판 위치 태그 + 좋아요 ❤️ + 댓글 💬 + 첨부파일 📎 + 조회수)
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
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: post.isNotice ? _noticeAccent.withAlpha(isDark ? 90 : 130) : context.colors.border,
          width: post.isNotice ? 1.0 : 0.8,
        ),
        boxShadow: isDark
            ? null
            : [
                BoxShadow(
                  color: Colors.black.withAlpha(6),
                  blurRadius: 4,
                  offset: const Offset(0, 1.5),
                ),
              ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(8),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── 1. 상단 작성자 프로필 헤더 (글쓴이는 상단 1회만 노출) + 카테고리 태그 ───
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    // 작성자 아바타
                    UserAvatar(
                      fallbackText: post.creator?.username ?? 'U',
                      radius: 15,
                    ),
                    const SizedBox(width: 9),

                    // 작성자 이름 & 상대 시간
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text(
                                post.creator?.username ?? '익명',
                                style: TextStyle(
                                  fontWeight: FontWeight.w700,
                                  color: context.colors.textPrimary,
                                  fontSize: 13,
                                ),
                              ),
                              if (post.isNew) ...[
                                const SizedBox(width: 5),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0.5),
                                  decoration: BoxDecoration(
                                    color: context.colors.warning.withAlpha(30),
                                    borderRadius: BorderRadius.circular(2),
                                  ),
                                  child: Text(
                                    'N',
                                    style: TextStyle(
                                      color: context.colors.warning,
                                      fontSize: 9,
                                      fontWeight: FontWeight.w900,
                                    ),
                                  ),
                                ),
                              ],
                            ],
                          ),
                          const SizedBox(height: 1),
                          Text(
                            _formatRelativeTime(post.created ?? ''),
                            style: TextStyle(
                              color: context.colors.textMuted,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                    ),

                    // 공지 / 카테고리 태그 칩
                    if (post.isNotice) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: _noticeAccent.withAlpha(25),
                          borderRadius: BorderRadius.circular(4),
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
                      const SizedBox(width: 5),
                    ],

                    if (post.cateName != null && post.cateName!.isNotEmpty) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                        decoration: BoxDecoration(
                          color: context.colors.accentChannel.withAlpha(18),
                          borderRadius: BorderRadius.circular(12),
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
                    ],

                    if (post.isSecret) ...[
                      const SizedBox(width: 4),
                      Icon(Icons.lock_rounded, size: 14, color: context.colors.warning),
                    ],
                  ],
                ),
                const SizedBox(height: 10),

                // ── 2. 게시글 제목 ──────────────────────────────────────────
                Text(
                  post.title,
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
                  const SizedBox(height: 6),
                  Text(
                    plainContent,
                    style: TextStyle(
                      color: context.colors.textSecond,
                      height: 1.38,
                      fontSize: 12.5,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
                const SizedBox(height: 12),

                // ── 4. 하단 소셜 인터랙션 바 (좋아요 + 댓글 + 파일 + 조회수) ───────────
                Container(
                  padding: const EdgeInsets.only(top: 10),
                  decoration: BoxDecoration(
                    border: Border(top: BorderSide(color: context.colors.border.withAlpha(70), width: 0.8)),
                  ),
                  child: Row(
                    children: [
                      // 게시판명 (다중 게시판 워크스페이스인 경우)
                      if (post.forumName.isNotEmpty) ...[
                        Icon(Icons.forum_outlined, size: 12.5, color: context.colors.textMuted),
                        const SizedBox(width: 3.5),
                        Text(
                          post.forumName,
                          style: TextStyle(
                            color: context.colors.textMuted,
                            fontSize: 11,
                          ),
                        ),
                        const Spacer(),
                      ] else ...[
                        const Spacer(),
                      ],

                      // 좋아요 인터랙션
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            post.myLike ? Icons.favorite_rounded : Icons.favorite_border_rounded,
                            size: 14,
                            color: post.myLike
                                ? Colors.redAccent
                                : (hasLikes ? Colors.redAccent.withAlpha(180) : context.colors.textMuted),
                          ),
                          const SizedBox(width: 3),
                          Text(
                            '${post.like}',
                            style: TextStyle(
                              color: hasLikes ? Colors.redAccent : context.colors.textMuted,
                              fontWeight: hasLikes ? FontWeight.w700 : FontWeight.normal,
                              fontSize: 11.5,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(width: 14),

                      // 댓글 인터랙션
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.chat_bubble_outline_rounded,
                            size: 13.5,
                            color: hasComments ? context.colors.accentChannel : context.colors.textMuted,
                          ),
                          const SizedBox(width: 3.5),
                          Text(
                            '${post.comments.length}',
                            style: TextStyle(
                              color: hasComments ? context.colors.accentChannel : context.colors.textMuted,
                              fontWeight: hasComments ? FontWeight.w700 : FontWeight.normal,
                              fontSize: 11.5,
                            ),
                          ),
                        ],
                      ),

                      // 첨부파일
                      if (hasFiles) ...[
                        const SizedBox(width: 14),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.attach_file_rounded, size: 13.5, color: context.colors.textMuted),
                            const SizedBox(width: 2),
                            Text(
                              '${post.files.length}',
                              style: TextStyle(
                                color: context.colors.textMuted,
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                      ],

                      const SizedBox(width: 14),
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
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _formatRelativeTime(String raw) {
    if (raw.isEmpty) return '';
    try {
      final dt = DateTime.parse(raw);
      final now = DateTime.now();
      final diff = now.difference(dt);

      if (diff.inMinutes < 1) return '방금 전';
      if (diff.inMinutes < 60) return '${diff.inMinutes}분 전';
      if (diff.inHours < 24) return '${diff.inHours}시간 전';
      if (diff.inDays < 7) return '${diff.inDays}일 전';
      return raw.substring(0, 10);
    } catch (_) {
      return raw.length >= 10 ? raw.substring(0, 10) : raw;
    }
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
