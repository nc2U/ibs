import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/notice_model.dart';

/// 공지사항 공식 브리프 카드 (Official Brief Card)
/// - 좌측 포인트 바 (중요 공지: 앰버, 일반 공지: 슬레이트)
/// - 안드로이드/iOS 모든 환경에서 텍스트 색상 및 레이아웃 완전 일원화
class NoticeCard extends StatelessWidget {
  final NoticeModel notice;
  final VoidCallback onTap;
  final bool showWorkspaceBadge;

  static const _importantAccent = Color(0xFFD97706); // Amber 600
  static const _defaultAccent = Color(0xFF64748B);   // Slate 500

  const NoticeCard({
    super.key,
    required this.notice,
    required this.onTap,
    this.showWorkspaceBadge = false,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = context.isDarkMode;
    final accentColor = notice.isImportant ? _importantAccent : _defaultAccent;

    final cardBg = notice.isImportant
        ? (isDark ? const Color(0xFF1E2130) : const Color(0xFFFFFDF5))
        : context.colors.bgCard;

    final hasFiles = notice.files.isNotEmpty;
    final hasComments = notice.comments.isNotEmpty;
    final summaryText = _stripHtml(notice.summary);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(4),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(4),
          child: IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // ── 좌측 인디케이터 바 ──────────────────────────────────────
                Container(
                  width: notice.isImportant ? 4.0 : 3.0,
                  decoration: BoxDecoration(
                    color: accentColor,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(3),
                      bottomLeft: Radius.circular(3),
                    ),
                  ),
                ),

                // ── 카드 본문 콘텐츠 ─────────────────────────────────────────
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // ── 1. 상단 라인: [중요공지 배지 / 워크스페이스] + [공식 게시일자] ──────
                        Row(
                          children: [
                            if (notice.isImportant) ...[
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: _importantAccent.withAlpha(25),
                                  borderRadius: BorderRadius.circular(3),
                                  border: Border.all(color: _importantAccent.withAlpha(90), width: 0.8),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(Icons.campaign_rounded, size: 12.5, color: _importantAccent),
                                    const SizedBox(width: 3.5),
                                    const Text(
                                      '중요 공지',
                                      style: TextStyle(
                                        color: _importantAccent,
                                        fontWeight: FontWeight.w800,
                                        fontSize: 11,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 6),
                            ] else ...[
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                                decoration: BoxDecoration(
                                  color: context.colors.bgSurface,
                                  borderRadius: BorderRadius.circular(3),
                                  border: Border.all(color: context.colors.border, width: 0.8),
                                ),
                                child: Text(
                                  '공지',
                                  style: TextStyle(
                                    color: context.colors.textSecond,
                                    fontWeight: FontWeight.w600,
                                    fontSize: 11,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 6),
                            ],

                            if (showWorkspaceBadge && notice.project != null) ...[
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                                decoration: BoxDecoration(
                                  color: context.colors.accentWork.withAlpha(15),
                                  borderRadius: BorderRadius.circular(3),
                                ),
                                child: Text(
                                  notice.project!.name,
                                  style: TextStyle(
                                    color: context.colors.accentWork,
                                    fontWeight: FontWeight.w600,
                                    fontSize: 11,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              const SizedBox(width: 6),
                            ],

                            if (notice.isNew) ...[
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
                            if (notice.created != null)
                              Text(
                                _formatDate(notice.created!),
                                style: TextStyle(
                                  color: context.colors.textMuted,
                                  fontSize: 11.5,
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 8),

                        // ── 2. 공지 제목 (글씨 선명도 보장) ─────────────────────────
                        Text(
                          notice.title.isNotEmpty ? notice.title : '공지 제목 없음',
                          style: TextStyle(
                            fontWeight: notice.isImportant ? FontWeight.w800 : FontWeight.w700,
                            color: context.colors.textPrimary,
                            fontSize: 14.5,
                            height: 1.35,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),

                        // ── 3. 공식 요약문 (있을 경우) ──────────────────────────────────
                        if (summaryText.isNotEmpty) ...[
                          const SizedBox(height: 5),
                          Text(
                            summaryText,
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

                        // ── 4. 하단 공지 발신처 / 첨부문서 메타정보 ───────────────────────
                        Row(
                          children: [
                            Icon(Icons.apartment_rounded, size: 13, color: context.colors.textMuted),
                            const SizedBox(width: 4),
                            Text(
                              notice.author?.username.isNotEmpty == true
                                  ? notice.author!.username
                                  : (notice.project?.name.isNotEmpty == true
                                      ? notice.project!.name
                                      : '관리국'),
                              style: TextStyle(
                                color: context.colors.textSecond,
                                fontWeight: FontWeight.w500,
                                fontSize: 11.5,
                              ),
                            ),
                            const Spacer(),

                            // 첨부 문서
                            if (hasFiles) ...[
                              Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.attach_file_rounded, size: 13.5, color: context.colors.textMuted),
                                  const SizedBox(width: 2),
                                  Text(
                                    '문서 ${notice.files.length}',
                                    style: TextStyle(
                                      color: context.colors.textSecond,
                                      fontSize: 11,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(width: 10),
                            ],

                            if (hasComments) ...[
                              Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.chat_bubble_outline_rounded, size: 12, color: context.colors.accentChannel),
                                  const SizedBox(width: 3),
                                  Text(
                                    '${notice.comments.length}',
                                    style: TextStyle(
                                      color: context.colors.accentChannel,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 11,
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
