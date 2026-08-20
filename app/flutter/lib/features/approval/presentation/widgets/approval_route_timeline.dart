import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/approval_model.dart';

class ApprovalRouteTimeline extends StatelessWidget {
  final List<ApprovalStepModel> steps;
  final String drafterName;
  final String? submittedAt;

  const ApprovalRouteTimeline({
    super.key,
    required this.steps,
    required this.drafterName,
    this.submittedAt,
  });

  String _formatTime(String? raw) {
    if (raw == null || raw.isEmpty) return '';
    try {
      final dt = DateTime.parse(raw).toLocal();
      return '${dt.month}/${dt.day} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.account_tree_outlined,
                size: 16,
                color: context.colors.accentApproval,
              ),
              const SizedBox(width: 6),
              Text(
                '결재선 진행 현황',
                style: AppTextStyles.titleSm.copyWith(
                  fontWeight: FontWeight.w700,
                  color: context.colors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // ── 기안자 노드 ─────────────────────────────────────────────
          _buildNode(
            context,
            isFirst: true,
            isLast: steps.isEmpty,
            statusColor: context.colors.success,
            icon: Icons.check_circle_rounded,
            roleLabel: '기안',
            nameText: drafterName,
            timeText: _formatTime(submittedAt),
            statusText: '상신완료',
          ),

          // ── 결재 단계별 노드 ─────────────────────────────────────────
          for (int i = 0; i < steps.length; i++) ...[
            _buildStepNode(
              context,
              step: steps[i],
              isLast: i == steps.length - 1,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStepNode(
    BuildContext context, {
    required ApprovalStepModel step,
    required bool isLast,
  }) {
    Color nodeColor;
    IconData nodeIcon;
    String statusStr;
    String timeStr = '';
    String? commentStr;

    // 단계 내 액션 기록 확인
    final approvedAction = step.actions.where((a) => a.action == 'approved').firstOrNull;
    final rejectedAction = step.actions.where((a) => a.action == 'rejected').firstOrNull;

    if (rejectedAction != null) {
      nodeColor = context.colors.error;
      nodeIcon = Icons.cancel_rounded;
      statusStr = '반려';
      timeStr = _formatTime(rejectedAction.actedAt);
      commentStr = rejectedAction.comment;
    } else if (approvedAction != null) {
      nodeColor = context.colors.success;
      nodeIcon = Icons.check_circle_rounded;
      statusStr = '승인';
      timeStr = _formatTime(approvedAction.actedAt);
      commentStr = approvedAction.comment.isNotEmpty ? approvedAction.comment : null;
    } else if (step.status == 'approved') {
      nodeColor = context.colors.success;
      nodeIcon = Icons.check_circle_rounded;
      statusStr = '승인완료';
    } else if (step.status == 'pending') {
      nodeColor = context.colors.warning;
      nodeIcon = Icons.access_time_filled_rounded;
      statusStr = '결재대기';
    } else if (step.status == 'skipped') {
      nodeColor = Colors.grey;
      nodeIcon = Icons.remove_circle_outline_rounded;
      statusStr = '전결/건너뜀';
    } else {
      nodeColor = context.colors.textMuted.withAlpha(120);
      nodeIcon = Icons.radio_button_unchecked_rounded;
      statusStr = '대기';
    }

    final approverNames = step.approvers.map((u) => u.username).join(', ');
    final conditionSuffix = step.condition == 'OR' ? ' (1인승인)' : (step.approvers.length > 1 ? ' (전원승인)' : '');

    return _buildNode(
      context,
      isFirst: false,
      isLast: isLast,
      statusColor: nodeColor,
      icon: nodeIcon,
      roleLabel: '${step.roleLabel}$conditionSuffix',
      nameText: approverNames.isNotEmpty ? approverNames : '지정자 없음',
      timeText: timeStr,
      statusText: statusStr,
      comment: commentStr,
    );
  }

  Widget _buildNode(
    BuildContext context, {
    required bool isFirst,
    required bool isLast,
    required Color statusColor,
    required IconData icon,
    required String roleLabel,
    required String nameText,
    required String timeText,
    required String statusText,
    String? comment,
  }) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 왼쪽 인디케이터 (아이콘 + 수직 연결선) ──────────────────
          SizedBox(
            width: 24,
            child: Column(
              children: [
                Icon(icon, size: 18, color: statusColor),
                if (!isLast)
                  Expanded(
                    child: Container(
                      width: 1.5,
                      margin: const EdgeInsets.symmetric(vertical: 2),
                      color: context.colors.border,
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 10),

          // ── 오른쪽 단계 정보 ────────────────────────────────────────
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(bottom: isLast ? 0 : 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        roleLabel,
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w700,
                          color: context.colors.textPrimary,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        nameText,
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                          color: context.colors.textSecond,
                        ),
                      ),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                        decoration: BoxDecoration(
                          color: statusColor.withAlpha(20),
                          borderRadius: BorderRadius.zero,
                          border: Border.all(color: statusColor.withAlpha(60), width: 0.5),
                        ),
                        child: Text(
                          statusText,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                            color: statusColor,
                          ),
                        ),
                      ),
                    ],
                  ),
                  if (timeText.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      timeText,
                      style: TextStyle(
                        fontSize: 10.5,
                        color: context.colors.textMuted,
                      ),
                    ),
                  ],
                  if (comment != null && comment.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                      decoration: BoxDecoration(
                        color: context.colors.bgSurface,
                        borderRadius: BorderRadius.zero,
                        border: Border.all(color: context.colors.borderSubtle, width: 0.6),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            Icons.chat_bubble_outline_rounded,
                            size: 11,
                            color: context.colors.textMuted,
                          ),
                          const SizedBox(width: 5),
                          Expanded(
                            child: Text(
                              comment,
                              style: TextStyle(
                                fontSize: 11,
                                color: context.colors.textSecond,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
