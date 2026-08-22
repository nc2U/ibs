import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/issue_model.dart';

/// 댓글 타일 위젯
class IssueCommentTile extends StatelessWidget {
  final IssueCommentModel comment;

  const IssueCommentTile({super.key, required this.comment});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        border: Border.all(color: context.colors.border, width: 0.8),
        borderRadius: BorderRadius.zero,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 작성자 + 날짜
          Row(
            children: [
              CircleAvatar(
                radius: 14,
                backgroundColor: context.colors.accentWork.withAlpha(50),
                child: Text(
                  comment.creator.username.isNotEmpty
                      ? comment.creator.username[0].toUpperCase()
                      : '?',
                  style: AppTextStyles.label
                      .copyWith(color: context.colors.accentWork),
                ),
              ),
              const SizedBox(width: 8),
              Text(comment.creator.username, style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
              const Spacer(),
              if (comment.isPrivate)
                Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: Icon(Icons.lock_outline_rounded,
                      size: 13, color: context.colors.textMuted),
                ),
              Text(_formatDateTime(comment.created),
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted)),
            ],
          ),
          const SizedBox(height: 10),
          // 내용
          Text(comment.content, style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary)),
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
