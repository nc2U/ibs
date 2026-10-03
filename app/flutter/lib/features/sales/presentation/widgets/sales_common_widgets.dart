import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';

/// 🤝 분양 대행 관리 (Sales Agency) 서브 탭 구분
enum SalesSubTab {
  performance, // 계약 실적 관리
  settlement,  // 수수료 정산 관리
  payout,      // 수수료 지급 관리
  policy,      // 수수료 정책 관리
  organization,// 영업 조직 관리
}

/// 단일 2×2 KPI 카드 타일
Widget buildSingleKpiTile({
  required BuildContext context,
  required String label,
  required String value,
  required String subText,
  required Color accentColor,
  required IconData icon,
}) {
  return Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    decoration: BoxDecoration(
      color: context.colors.bgCard,
      borderRadius: BorderRadius.zero,
      border: Border.all(
        color: accentColor.withAlpha(60),
        width: 0.8,
      ),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: AppTextStyles.caption.copyWith(
                color: context.colors.textMuted,
                fontSize: 11,
              ),
            ),
            Icon(icon, size: 14, color: accentColor),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: AppTextStyles.titleSm.copyWith(
            color: accentColor,
            fontWeight: FontWeight.bold,
            fontSize: 14,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        const SizedBox(height: 2),
        Text(
          subText,
          style: AppTextStyles.caption.copyWith(
            color: context.colors.textMuted,
            fontSize: 10.5,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ],
    ),
  );
}

/// 공통 필터 칩 위젯
Widget buildFilterChip({
  required BuildContext context,
  required String label,
  required bool isSelected,
  required VoidCallback onTap,
  Color activeColor = const Color(0xFF8B5CF6),
}) {
  return Material(
    color: isSelected ? activeColor.withAlpha(25) : context.colors.bgCard,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.zero,
      side: BorderSide(
        color: isSelected ? activeColor : context.colors.border,
        width: 0.8,
      ),
    ),
    child: InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11.5,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            color: isSelected ? activeColor : context.colors.textSecond,
          ),
        ),
      ),
    ),
  );
}

/// 비동기 로딩 실패 시 재시도 버튼을 제공하는 공통 에러 배너
Widget buildErrorBanner({
  required BuildContext context,
  required String message,
  required VoidCallback onRetry,
}) {
  return Container(
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    decoration: BoxDecoration(
      color: context.colors.bgCard,
      borderRadius: BorderRadius.zero,
      border: Border.all(color: context.colors.error.withAlpha(80)),
    ),
    child: Row(
      children: [
        Icon(Icons.error_outline_rounded, size: 18, color: context.colors.error),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            message,
            style: AppTextStyles.caption.copyWith(color: context.colors.error),
          ),
        ),
        const SizedBox(width: 8),
        OutlinedButton.icon(
          onPressed: onRetry,
          icon: const Icon(Icons.refresh_rounded, size: 14),
          label: const Text('다시 시도', style: TextStyle(fontSize: 11.5)),
          style: OutlinedButton.styleFrom(
            foregroundColor: context.colors.textPrimary,
            side: BorderSide(color: context.colors.border),
            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            minimumSize: Size.zero,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
        ),
      ],
    ),
  );
}

/// 상단 안내 배너 위젯
Widget buildInfoBanner({
  required BuildContext context,
  required String title,
  required String subtitle,
  required IconData icon,
  required Color color,
}) {
  return Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: context.colors.bgCard,
      borderRadius: BorderRadius.zero,
      border: Border.all(color: color.withAlpha(70), width: 1),
    ),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: color.withAlpha(25),
            borderRadius: BorderRadius.zero,
            border: Border.all(color: color.withAlpha(70), width: 0.8),
          ),
          child: Icon(icon, size: 20, color: color),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: AppTextStyles.titleSm.copyWith(
                  color: context.colors.textPrimary,
                  fontWeight: FontWeight.bold,
                  fontSize: 15,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: AppTextStyles.bodySecond.copyWith(
                  color: context.colors.textSecond,
                  fontSize: 12,
                  height: 1.35,
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

/// 전화 통화 확인 다이얼로그 및 연결 헬퍼
Future<void> makePhoneCall(
  BuildContext context,
  String phone, {
  String? targetName,
}) async {
  final cleanPhone = phone.replaceAll(RegExp(r'[^0-9]'), '');
  if (cleanPhone.isEmpty) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('등록된 연락처가 없습니다.'),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 2),
        ),
      );
    }
    return;
  }

  final shouldCall = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      backgroundColor: context.colors.bgCard,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      titlePadding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      actionsPadding: const EdgeInsets.all(12),
      title: Row(
        children: [
          const Icon(Icons.phone_in_talk, size: 20, color: Color(0xFF10B981)),
          const SizedBox(width: 8),
          Text(
            '통화 연결 확인',
            style: AppTextStyles.titleSm.copyWith(
              color: context.colors.textPrimary,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
      content: Text(
        targetName != null && targetName.isNotEmpty
            ? '$targetName ($phone) 님에게 전화를 연결하시겠습니까?'
            : '$phone 로 전화를 연결하시겠습니까?',
        style: AppTextStyles.bodySecond.copyWith(
          color: context.colors.textSecond,
          height: 1.4,
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(ctx).pop(false),
          child: Text(
            '취소',
            style: TextStyle(color: context.colors.textMuted),
          ),
        ),
        FilledButton(
          style: FilledButton.styleFrom(
            backgroundColor: const Color(0xFF10B981),
            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
          ),
          onPressed: () => Navigator.of(ctx).pop(true),
          child: const Text('통화 연결'),
        ),
      ],
    ),
  );

  if (shouldCall == true) {
    final uri = Uri.parse('tel:$cleanPhone');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('통화 기능을 실행할 수 없습니다.')),
        );
      }
    }
  }
}

/// 수수료 지급 조건 레이블 변환
String getPayConditionLabel(String code) {
  switch (code) {
    case '1':
      return '계약금 100% 완납 시 전액 지급';
    case '2':
      return '계약금 1차 50%, 2차 완납 50% 분할 지급';
    case '3':
      return '공급계약 체결 시 전액 지급';
    case '4':
      return '청약/가계약금 납부 시 선지급';
    default:
      return '계약금 100% 완납 시 전액 지급';
  }
}
