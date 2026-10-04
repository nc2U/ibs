import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';

/// 🗺️ 부지 관리 상단 고정 헤더 델리게이트 (SliverPersistentHeader용)
class SitePinnedHeaderDelegate extends SliverPersistentHeaderDelegate {
  final Widget child;
  final double height;

  SitePinnedHeaderDelegate({required this.child, required this.height});

  @override
  double get minExtent => height;

  @override
  double get maxExtent => height;

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    return SizedBox.expand(child: child);
  }

  @override
  bool shouldRebuild(covariant SitePinnedHeaderDelegate oldDelegate) {
    return height != oldDelegate.height || child != oldDelegate.child;
  }
}

/// 🗺️ 서브 탭 버튼 위젯 (선택 시 명확한 테두리 및 액센트 배경 대비 적용)
class SiteSubTabButton extends StatelessWidget {
  final String title;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  const SiteSubTabButton({
    super.key,
    required this.title,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    const activeColor = Color(0xFF0D9488); // Teal 브랜드 컬러

    return Expanded(
      child: Material(
        color: isSelected ? activeColor.withAlpha(28) : context.colors.bgCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.zero,
          side: BorderSide(
            color: isSelected ? activeColor : context.colors.border,
            width: isSelected ? 1.4 : 0.8,
          ),
        ),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.zero,
          child: Container(
            height: 38,
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  icon,
                  size: 15,
                  color: isSelected ? activeColor : context.colors.textMuted,
                ),
                const SizedBox(width: 5),
                Flexible(
                  child: Text(
                    title,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                      color: isSelected ? activeColor : context.colors.textSecond,
                      height: 1.15,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// 🗺️ 상단 종합 집계 KPI 아이템
class SiteKpiItem extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const SiteKpiItem({
    super.key,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        children: [
          Text(
            label,
            style: AppTextStyles.caption.copyWith(
              color: context.colors.textMuted,
              fontSize: 10,
            ),
          ),
          const SizedBox(height: 1),
          Text(
            value,
            style: AppTextStyles.caption.copyWith(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

/// 🗺️ 빠른 필터 칩 버튼
class SiteFilterChipBtn extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const SiteFilterChipBtn({
    super.key,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF0D9488).withAlpha(20) : context.colors.bgSurface,
          borderRadius: BorderRadius.zero,
          border: Border.all(
            color: isSelected ? const Color(0xFF0D9488) : context.colors.border,
            width: isSelected ? 1 : 0.8,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 10.5,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            color: isSelected ? const Color(0xFF0D9488) : context.colors.textSecond,
          ),
        ),
      ),
    );
  }
}

/// 🗺️ 상세 정보 행 위젯
class SiteDetailRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isHighlight;
  final Color? color;
  final bool isDanger;
  final bool isPhone;
  final VoidCallback? onPhoneTap;
  final VoidCallback? onSmsTap;

  const SiteDetailRow({
    super.key,
    required this.label,
    required this.value,
    this.isHighlight = false,
    this.color,
    this.isDanger = false,
    this.isPhone = false,
    this.onPhoneTap,
    this.onSmsTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3.5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: AppTextStyles.bodySecond.copyWith(
                color: isDanger
                    ? const Color(0xFFEF4444)
                    : (isHighlight
                        ? (color ?? context.colors.textPrimary)
                        : context.colors.textPrimary),
                fontWeight: (isHighlight || isDanger) ? FontWeight.bold : FontWeight.normal,
                fontSize: 12.5,
              ),
            ),
          ),
          if (isPhone) ...[
            InkWell(
              onTap: onPhoneTap,
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 4),
                child: Icon(Icons.call, size: 16, color: Color(0xFF10B981)),
              ),
            ),
            InkWell(
              onTap: onSmsTap,
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 4),
                child: Icon(Icons.sms_outlined, size: 16, color: Color(0xFF38BDF8)),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// 🗺️ 분할 지급 단계 행 위젯
class SitePaymentStepRow extends StatelessWidget {
  final String title;
  final int? amount;
  final String? date;
  final bool isPaid;

  const SitePaymentStepRow({
    super.key,
    required this.title,
    this.amount,
    this.date,
    required this.isPaid,
  });

  @override
  Widget build(BuildContext context) {
    final numFormat = NumberFormat('#,###');

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2.5),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
            decoration: BoxDecoration(
              color: isPaid ? const Color(0xFF10B981).withAlpha(25) : context.colors.border.withAlpha(60),
              borderRadius: BorderRadius.zero,
            ),
            child: Text(
              isPaid ? '지급완료' : '미지급',
              style: TextStyle(
                fontSize: 9.5,
                fontWeight: FontWeight.bold,
                color: isPaid ? const Color(0xFF10B981) : context.colors.textMuted,
              ),
            ),
          ),
          const SizedBox(width: 6),
          Text(
            title,
            style: AppTextStyles.caption.copyWith(
              color: context.colors.textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
          if (date != null && date!.isNotEmpty) ...[
            const SizedBox(width: 4),
            Text(
              '($date)',
              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5),
            ),
          ],
          const Spacer(),
          Text(
            amount != null ? '${numFormat.format(amount)}원' : '-',
            style: AppTextStyles.caption.copyWith(
              color: isPaid ? context.colors.textPrimary : context.colors.textMuted,
              fontWeight: isPaid ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }
}

/// 📞 원터치 통화 연결 확인 다이얼로그
Future<void> makeSitePhoneCall(
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
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${targetName != null ? "소유자 [$targetName] 님께" : "해당 연락처로"} 전화를 연결하시겠습니까?',
            style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
          ),
          const SizedBox(height: 10),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(10),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                const Icon(Icons.phone, size: 16, color: Color(0xFF10B981)),
                const SizedBox(width: 8),
                Text(
                  phone,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.5,
                    color: Color(0xFF10B981),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx, false),
          child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
        ),
        ElevatedButton.icon(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF10B981),
            foregroundColor: Colors.white,
            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          ),
          onPressed: () => Navigator.pop(ctx, true),
          icon: const Icon(Icons.phone, size: 16),
          label: const Text('통화 연결', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
        ),
      ],
    ),
  );

  if (shouldCall == true) {
    final uri = Uri.parse('tel:$cleanPhone');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }
}

/// 💬 SMS 문자 발송
Future<void> sendSiteSms(String phone) async {
  final cleanPhone = phone.replaceAll(RegExp(r'[^0-9]'), '');
  if (cleanPhone.isEmpty) return;
  final uri = Uri.parse('sms:$cleanPhone');
  if (await canLaunchUrl(uri)) {
    await launchUrl(uri);
  }
}
