import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';
import '../constants/app_colors.dart';

/// 스켈레톤 로딩 — Shimmer 효과
/// [itemCount]: 표시할 스켈레톤 카드 수
/// [itemHeight]: 각 카드 높이 (기본 88)
class LoadingShimmer extends StatelessWidget {
  final int itemCount;
  final double itemHeight;

  const LoadingShimmer({
    super.key,
    this.itemCount = 6,
    this.itemHeight = 88,
  });

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: AppColors.bgCard,
      highlightColor: AppColors.border,
      child: ListView.separated(
        physics: const NeverScrollableScrollPhysics(),
        shrinkWrap: true,
        itemCount: itemCount,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        itemBuilder: (_, __) => Container(
          height: itemHeight,
          decoration: BoxDecoration(
            color: AppColors.bgCard,
            borderRadius: BorderRadius.zero,
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
    return Shimmer.fromColors(
      baseColor: AppColors.bgCard,
      highlightColor: AppColors.border,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          borderRadius: borderRadius != null
              ? BorderRadius.circular(borderRadius!)
              : BorderRadius.zero,
        ),
      ),
    );
  }
}
