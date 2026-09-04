import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors_extension.dart';

class ApprovalStatusChip extends StatelessWidget {
  final String status;
  final String? statusDesc;
  final int? currentStep;
  final bool isMyTurn;
  final bool isSmall;

  const ApprovalStatusChip({
    super.key,
    required this.status,
    this.statusDesc,
    this.currentStep,
    this.isMyTurn = false,
    this.isSmall = false,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    Color border;
    String label;

    if (isMyTurn && status == 'pending') {
      bg = context.colors.accentApproval.withAlpha(35);
      fg = context.colors.accentApprovalDeep;
      border = context.colors.accentApproval;
      label = currentStep != null && currentStep! > 0 ? '내 승인 차례 ($currentStep단계)' : '내 승인 차례';
    } else {
      switch (status) {
        case 'draft':
          bg = Colors.grey.withAlpha(25);
          fg = Colors.grey.shade600;
          border = Colors.grey.withAlpha(60);
          label = statusDesc ?? '임시저장';
          break;
        case 'pending':
          bg = context.colors.warning.withAlpha(25);
          fg = const Color(0xFFD97706);
          border = context.colors.warning.withAlpha(80);
          label = currentStep != null && currentStep! > 0
              ? '결재중 ($currentStep단계)'
              : (statusDesc ?? '결재중');
          break;
        case 'approved':
          bg = context.colors.success.withAlpha(25);
          fg = const Color(0xFF059669);
          border = context.colors.success.withAlpha(80);
          label = statusDesc ?? '승인완료';
          break;
      case 'rejected':
        bg = context.colors.error.withAlpha(25);
        fg = const Color(0xFFDC2626);
        border = context.colors.error.withAlpha(80);
        label = statusDesc ?? '반려';
        break;
      case 'cancelled':
        bg = Colors.blueGrey.withAlpha(25);
        fg = Colors.blueGrey;
        border = Colors.blueGrey.withAlpha(60);
        label = statusDesc ?? '취소';
        break;
      default:
        bg = Colors.grey.withAlpha(20);
        fg = Colors.grey;
        border = Colors.grey.withAlpha(50);
        label = statusDesc ?? status;
      }
    }

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isSmall ? 6 : 8,
        vertical: isSmall ? 2 : 4,
      ),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: border, width: 0.8),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: isSmall ? 10 : 11,
          fontWeight: FontWeight.w700,
          color: fg,
          letterSpacing: 0.3,
        ),
      ),
    );
  }
}
