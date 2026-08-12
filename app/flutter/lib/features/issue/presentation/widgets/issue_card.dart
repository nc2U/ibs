import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../data/models/issue_model.dart';

/// 업무 목록 카드 위젯
class IssueCard extends StatelessWidget {
  final IssueModel issue;
  final VoidCallback? onTap;
  final VoidCallback? onDoneRatioTap;

  const IssueCard({
    super.key,
    required this.issue,
    this.onTap,
    this.onDoneRatioTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          border: Border.all(color: AppColors.border, width: 0.8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 상단 행: 트래커 + 상태 + 우선순위 + 비공개 아이콘 ──────────────
            Row(
              children: [
                _TrackerChip(name: issue.tracker.name),
                const SizedBox(width: 6),
                _StatusChip(status: issue.status),
                const SizedBox(width: 6),
                _PriorityChip(priority: issue.priority),
                const Spacer(),
                if (issue.isPrivate)
                  const Icon(Icons.lock_outline_rounded,
                      size: 14, color: AppColors.textMuted),
              ],
            ),
            const SizedBox(height: 8),

            // ── 제목 ──────────────────────────────────────────────────────────
            Text(
              issue.subject,
              style: AppTextStyles.titleSm,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 10),

            // ── 하단 행: 담당자 + 기한 + 진척률 ──────────────────────────────
            Row(
              children: [
                // 담당자
                Icon(Icons.person_outline_rounded,
                    size: 13, color: AppColors.textMuted),
                const SizedBox(width: 3),
                Expanded(
                  child: Text(
                    issue.assignedTo?.username ?? '미배정',
                    style: AppTextStyles.caption,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                // 기한
                if (issue.dueDate != null) ...[
                  const SizedBox(width: 8),
                  Icon(Icons.event_outlined,
                      size: 13, color: _dueDateColor(issue.dueDate!)),
                  const SizedBox(width: 3),
                  Text(
                    _formatDate(issue.dueDate!),
                    style: AppTextStyles.caption
                        .copyWith(color: _dueDateColor(issue.dueDate!)),
                  ),
                ],
                const SizedBox(width: 10),
                // 진척률 (탭 → 바텀 시트)
                GestureDetector(
                  onTap: onDoneRatioTap,
                  behavior: HitTestBehavior.opaque,
                  child: _DoneRatioBadge(ratio: issue.doneRatio),
                ),
              ],
            ),

            // ── 진척률 프로그레스바 ────────────────────────────────────────────
            const SizedBox(height: 6),
            ClipRRect(
              borderRadius: BorderRadius.circular(2),
              child: LinearProgressIndicator(
                value: issue.doneRatio / 100.0,
                minHeight: 3,
                backgroundColor: AppColors.bgSurface,
                valueColor: AlwaysStoppedAnimation<Color>(
                  issue.doneRatio == 100
                      ? AppColors.success
                      : AppColors.accentWork,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _dueDateColor(String dueDate) {
    try {
      final due = DateTime.parse(dueDate);
      final now = DateTime.now();
      if (due.isBefore(now)) return AppColors.error;
      if (due.difference(now).inDays <= 3) return AppColors.warning;
    } catch (_) {}
    return AppColors.textMuted;
  }

  String _formatDate(String isoDate) {
    try {
      final dt = DateTime.parse(isoDate);
      return '${dt.month}/${dt.day}';
    } catch (_) {
      return isoDate;
    }
  }
}

// ── 트래커 칩 ──────────────────────────────────────────────────────────────────
class _TrackerChip extends StatelessWidget {
  final String name;
  const _TrackerChip({required this.name});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: AppColors.accentWork.withAlpha(30),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: AppColors.accentWork.withAlpha(80)),
      ),
      child: Text(name,
          style: AppTextStyles.label.copyWith(color: AppColors.accentWork)),
    );
  }
}

// ── 상태 칩 ────────────────────────────────────────────────────────────────────
class _StatusChip extends StatelessWidget {
  final IssueStatusModel status;
  const _StatusChip({required this.status});

  Color get _color {
    if (status.closed) return AppColors.textDisabled;
    return AppColors.success;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: _color.withAlpha(30),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: _color.withAlpha(80)),
      ),
      child: Text(status.name,
          style: AppTextStyles.label.copyWith(color: _color)),
    );
  }
}

// ── 우선순위 칩 ────────────────────────────────────────────────────────────────
class _PriorityChip extends StatelessWidget {
  final IssuePriorityModel priority;
  const _PriorityChip({required this.priority});

  Color get _color {
    return switch (priority.pk) {
      1 => AppColors.textDisabled,      // 낮음
      2 => AppColors.accentWork,        // 보통
      3 => AppColors.warning,           // 높음
      4 => AppColors.error,             // 긴급
      _ => AppColors.accentApproval,    // 즉시
    };
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: _color.withAlpha(30),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: _color.withAlpha(80)),
      ),
      child: Text(priority.name,
          style: AppTextStyles.label.copyWith(color: _color)),
    );
  }
}

// ── 진척률 배지 ────────────────────────────────────────────────────────────────
class _DoneRatioBadge extends StatelessWidget {
  final int ratio;
  const _DoneRatioBadge({required this.ratio});

  @override
  Widget build(BuildContext context) {
    final color = ratio == 100 ? AppColors.success : AppColors.accentWork;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withAlpha(30),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: color.withAlpha(80)),
      ),
      child: Text('$ratio%',
          style: AppTextStyles.label.copyWith(
              color: color, fontWeight: FontWeight.bold)),
    );
  }
}
