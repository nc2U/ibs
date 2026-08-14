import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../data/models/issue_model.dart';

/// 업무 변경 이력 로그 타일 위젯 (마크다운 렌더링 지원)
class IssueLogTile extends StatelessWidget {
  final IssueLogEntryModel log;

  const IssueLogTile({super.key, required this.log});

  @override
  Widget build(BuildContext context) {
    final creatorName = log.creator?.username ?? '시스템';
    final hasComment = log.comment != null && log.comment!.content.isNotEmpty;
    final detailsList = log.details
        .split('|')
        .map((s) => s.trim())
        .where((s) => s.isNotEmpty)
        .toList();

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        border: Border.all(color: AppColors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 헤더: 작성자 + 변경일시 + 작업 구분 ────────────────────────────
          Row(
            children: [
              CircleAvatar(
                radius: 12,
                backgroundColor: hasComment
                    ? AppColors.accentWork.withAlpha(40)
                    : AppColors.accentProject.withAlpha(40),
                child: Icon(
                  hasComment
                      ? Icons.chat_bubble_outline_rounded
                      : Icons.history_rounded,
                  size: 13,
                  color: hasComment
                      ? AppColors.accentWork
                      : AppColors.accentProject,
                ),
              ),
              const SizedBox(width: 8),
              Text(creatorName, style: AppTextStyles.titleSm),
              const SizedBox(width: 6),
              Text(
                hasComment ? '댓글 작성' : '항목 변경',
                style: AppTextStyles.caption.copyWith(
                  color: hasComment
                      ? AppColors.accentWork
                      : AppColors.accentProject,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              Text(_formatDateTime(log.timestamp),
                  style: AppTextStyles.caption),
            ],
          ),

          // ── 항목 변경 세부 내역 (details) ──────────────────────────────────
          if (detailsList.isNotEmpty) ...[
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: AppColors.bgSurface.withAlpha(120),
                borderRadius: BorderRadius.circular(4),
                border: Border.all(
                    color: AppColors.border.withAlpha(80), width: 0.6),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: detailsList.map((detail) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: MarkdownBody(
                      data: detail.startsWith('- ') || detail.startsWith('* ')
                          ? detail
                          : '• $detail',
                      styleSheet: MarkdownStyleSheet(
                        p: AppTextStyles.bodyMd.copyWith(fontSize: 13),
                        strong: AppTextStyles.bodyMd.copyWith(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                        ),
                        em: AppTextStyles.bodyMd.copyWith(
                          fontSize: 13,
                          fontStyle: FontStyle.italic,
                          color: AppColors.textSecond,
                        ),
                        listBullet: AppTextStyles.caption,
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ],

          // ── 댓글 내용 (마크다운 렌더링) ───────────────────────────────────
          if (hasComment) ...[
            const SizedBox(height: 8),
            MarkdownBody(
              data: log.comment!.content,
              selectable: true,
              styleSheet: MarkdownStyleSheet(
                p: AppTextStyles.bodyMd,
                strong: AppTextStyles.bodyMd.copyWith(
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
                em: AppTextStyles.bodyMd.copyWith(
                  fontStyle: FontStyle.italic,
                  color: AppColors.textSecond,
                ),
                blockquote: AppTextStyles.bodyMd.copyWith(
                  color: AppColors.textMuted,
                  fontStyle: FontStyle.italic,
                ),
                blockquoteDecoration: BoxDecoration(
                  color: AppColors.bgSurface,
                  border: const Border(
                    left: BorderSide(color: AppColors.accentWork, width: 3),
                  ),
                  borderRadius: BorderRadius.circular(2),
                ),
                blockquotePadding: const EdgeInsets.symmetric(
                    horizontal: 10, vertical: 6),
                code: TextStyle(
                  backgroundColor: AppColors.bgSurface,
                  color: AppColors.accentWork,
                  fontFamily: 'monospace',
                  fontSize: 12.5,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _formatDateTime(String iso) {
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.year}.${_pad(dt.month)}.${_pad(dt.day)} '
          '${_pad(dt.hour)}:${_pad(dt.minute)}';
    } catch (_) {
      return iso;
    }
  }

  String _pad(int n) => n.toString().padLeft(2, '0');
}
