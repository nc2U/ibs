import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
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
          color: context.colors.bgCard,
          border: Border.all(color: context.colors.border, width: 0.8),
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
                  Icon(Icons.lock_outline_rounded,
                      size: 14, color: context.colors.textMuted),
              ],
            ),
            const SizedBox(height: 8),

            // ── 제목 ──────────────────────────────────────────────────────────
            Text(
              issue.subject,
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.w600,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 10),

            // ── 하단 행: 담당자 + 기한 + 진척률 ──────────────────────────────
            Row(
              children: [
                // 담당자
                Icon(Icons.person_outline_rounded,
                    size: 13, color: context.colors.textMuted),
                const SizedBox(width: 3),
                Expanded(
                  child: Text(
                    issue.assignedTo?.username ?? '미배정',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textSecond,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                // 기한
                if (issue.dueDate != null) ...[
                  const SizedBox(width: 8),
                  _DueDateBadge(
                    dueDate: issue.dueDate!,
                    isClosed: issue.status.closed,
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
                backgroundColor: context.colors.bgSurface,
                valueColor: AlwaysStoppedAnimation<Color>(
                  issue.doneRatio == 100
                      ? context.colors.success
                      : context.colors.accentWork,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DueDateBadge extends StatelessWidget {
  final String dueDate;
  final bool isClosed;

  const _DueDateBadge({
    required this.dueDate,
    required this.isClosed,
  });

  @override
  Widget build(BuildContext context) {
    String badgeText = '';
    Color statusColor = context.colors.textMuted;
    Color? badgeBgColor;
    bool isUrgent = false;

    if (!isClosed) {
      try {
        final now = DateTime.now();
        final today = DateTime(now.year, now.month, now.day);
        final due = DateTime.parse(dueDate);
        final dueDay = DateTime(due.year, due.month, due.day);
        final diffDays = dueDay.difference(today).inDays;

        if (diffDays < 0) {
          statusColor = context.colors.error;
          badgeText = ' (지연 ${-diffDays}일)';
          badgeBgColor = context.colors.error.withAlpha(30);
          isUrgent = true;
        } else if (diffDays == 0) {
          statusColor = context.colors.error;
          badgeText = ' (오늘 마감)';
          badgeBgColor = context.colors.error.withAlpha(30);
          isUrgent = true;
        } else if (diffDays <= 3) {
          statusColor = context.colors.warning;
          badgeText = ' (D-$diffDays)';
          badgeBgColor = context.colors.warning.withAlpha(30);
          isUrgent = true;
        }
      } catch (_) {}
    }

    final formatted = _formatDate(dueDate);

    if (isUrgent && !isClosed) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
        decoration: BoxDecoration(
          color: badgeBgColor,
          borderRadius: BorderRadius.circular(3),
          border: Border.all(color: statusColor, width: 0.6),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.event_outlined, size: 11, color: statusColor),
            const SizedBox(width: 2),
            Text(
              '$formatted$badgeText',
              style: AppTextStyles.caption.copyWith(
                color: statusColor,
                fontWeight: FontWeight.bold,
                fontSize: 10.5,
              ),
            ),
          ],
        ),
      );
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.event_outlined,
            size: 13,
            color: isClosed ? context.colors.textDisabled : statusColor),
        const SizedBox(width: 3),
        Text(
          formatted,
          style: AppTextStyles.caption.copyWith(
            color: isClosed ? context.colors.textDisabled : statusColor,
          ),
        ),
      ],
    );
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
        color: context.colors.accentWork.withAlpha(30),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: context.colors.accentWork.withAlpha(80)),
      ),
      child: Text(
        name,
        style: AppTextStyles.label.copyWith(color: context.colors.accentWork),
      ),
    );
  }
}

// ── 상태 칩 ────────────────────────────────────────────────────────────────────
class _StatusChip extends StatelessWidget {
  final IssueStatusModel status;
  const _StatusChip({required this.status});

  Color _getColor(BuildContext context) {
    if (status.closed) return context.colors.textDisabled;
    return context.colors.success;
  }

  @override
  Widget build(BuildContext context) {
    final color = _getColor(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(30),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: color.withAlpha(80)),
      ),
      child: Text(
        status.name,
        style: AppTextStyles.label.copyWith(color: color),
      ),
    );
  }
}

// ── 우선순위 칩 ────────────────────────────────────────────────────────────────
class _PriorityChip extends StatelessWidget {
  final IssuePriorityModel priority;
  const _PriorityChip({required this.priority});

  Color _getColor(BuildContext context) {
    return switch (priority.pk) {
      1 => context.colors.textDisabled, // 낮음
      2 => context.colors.accentWork,   // 보통
      3 => context.colors.warning,      // 높음
      4 => context.colors.error,        // 긴급
      _ => context.colors.accentApproval, // 즉시
    };
  }

  @override
  Widget build(BuildContext context) {
    final color = _getColor(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(30),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: color.withAlpha(80)),
      ),
      child: Text(
        priority.name,
        style: AppTextStyles.label.copyWith(color: color),
      ),
    );
  }
}

// ── 진척률 배지 ────────────────────────────────────────────────────────────────
class _DoneRatioBadge extends StatelessWidget {
  final int ratio;
  const _DoneRatioBadge({required this.ratio});

  @override
  Widget build(BuildContext context) {
    final color = ratio == 100 ? context.colors.success : context.colors.accentWork;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withAlpha(30),
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: color.withAlpha(80)),
      ),
      child: Text(
        '$ratio%',
        style: AppTextStyles.label.copyWith(
          color: color,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
