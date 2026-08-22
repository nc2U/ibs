import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';
import '../theme/app_colors_extension.dart';

/// 스켈레톤 로딩 — Shimmer 효과 (라이트 / 다크 테마 완벽 지원)
/// [itemCount]: 표시할 스켈레톤 카드 수
/// [itemHeight]: 각 카드 높이 (기본 92)
class LoadingShimmer extends StatelessWidget {
  final int itemCount;
  final double itemHeight;

  const LoadingShimmer({
    super.key,
    this.itemCount = 6,
    this.itemHeight = 92,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = context.isDarkMode;
    // 라이트 모드: 부드러운 Slate 200/Slate 100 쉬머
    // 다크 모드: 기존 다크 카드/보더 쉬머
    final baseColor = isDark
        ? context.colors.bgCard
        : const Color(0xFFE2E8F0); // Slate 200
    final highlightColor = isDark
        ? context.colors.border
        : const Color(0xFFF8FAFC); // Slate 50
    final cardBgColor = isDark ? context.colors.bgCard : context.colors.bgCard;

    return ListView.separated(
      physics: const NeverScrollableScrollPhysics(),
      shrinkWrap: true,
      itemCount: itemCount,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemBuilder: (_, __) => Container(
        height: itemHeight,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: cardBgColor,
          borderRadius: BorderRadius.zero,
          border: Border.all(color: context.colors.border, width: 0.8),
        ),
        child: Shimmer.fromColors(
          baseColor: baseColor,
          highlightColor: highlightColor,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // 1. 상단 뱃지 라인
              Row(
                children: [
                  Container(
                    width: 50,
                    height: 18,
                    decoration: BoxDecoration(
                      color: baseColor,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const SizedBox(width: 6),
                  Container(
                    width: 42,
                    height: 18,
                    decoration: BoxDecoration(
                      color: baseColor,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const Spacer(),
                  Container(
                    width: 55,
                    height: 14,
                    decoration: BoxDecoration(
                      color: baseColor,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ],
              ),
              // 2. 제목 라인
              Container(
                width: double.infinity,
                height: 16,
                decoration: BoxDecoration(
                  color: baseColor,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              // 3. 하단 정보 라인
              Row(
                children: [
                  Container(
                    width: 70,
                    height: 14,
                    decoration: BoxDecoration(
                      color: baseColor,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Container(
                    width: 60,
                    height: 14,
                    decoration: BoxDecoration(
                      color: baseColor,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const Spacer(),
                  Container(
                    width: 40,
                    height: 14,
                    decoration: BoxDecoration(
                      color: baseColor,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// 인라인 shimmer 박스 (단일 요소용)
class ShimmerBox extends StatelessWidget {
  final double width;
  final double height;
  final double? borderRadius;

  const ShimmerBox({
    super.key,
    required this.width,
    required this.height,
    this.borderRadius,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = context.isDarkMode;
    final baseColor = isDark ? context.colors.bgCard : const Color(0xFFE2E8F0);
    final highlightColor =
        isDark ? context.colors.border : const Color(0xFFF8FAFC);

    return Shimmer.fromColors(
      baseColor: baseColor,
      highlightColor: highlightColor,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: baseColor,
          borderRadius: borderRadius != null
              ? BorderRadius.circular(borderRadius!)
              : BorderRadius.zero,
        ),
      ),
    );
  }
}
