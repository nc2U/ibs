import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../providers/ledger_provider.dart';

/// 📊 캐시플로우 미니 차트 (Cashflow Mini Chart) 위젯
/// - 최근 6개월간의 월별 수입(입금, Green) vs 지출(출금, Red) 가로/세로 막대 차트
/// - 월별 수지차 및 증감 현황 시각화
/// - 차트 바 탭 시 해당 월 수치 툴팁 표시
class CashflowMiniChartCard extends ConsumerWidget {
  const CashflowMiniChartCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cashflowAsync = ref.watch(monthlyCashflowChartProvider);

    return cashflowAsync.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
      data: (items) {
        if (items.isEmpty) return const SizedBox.shrink();

        // 6개월 중 최대 금액 계산 (차트 높이 기준)
        int maxVal = 1;
        for (final item in items) {
          if (item.income > maxVal) maxVal = item.income;
          if (item.expense > maxVal) maxVal = item.expense;
        }

        return Container(
          color: context.colors.bgCard,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 헤더 & 범례 ──
              Row(
                children: [
                  Icon(Icons.bar_chart_rounded, size: 16, color: context.colors.accentProject),
                  const SizedBox(width: 6),
                  Text(
                    '최근 6개월 캐시플로우 추이',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                  const Spacer(),
                  // 수입 범례
                  const _ChartLegend(color: Color(0xFF10B981), label: '입금'),
                  const SizedBox(width: 8),
                  // 지출 범례
                  const _ChartLegend(color: Colors.redAccent, label: '출금'),
                ],
              ),
              const SizedBox(height: 14),

              // ── 6개 월별 듀얼 막대 그래프 ──
              SizedBox(
                height: 90,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: items.map((item) {
                    final incomeRatio = (item.income / maxVal).clamp(0.02, 1.0);
                    final expenseRatio = (item.expense / maxVal).clamp(0.02, 1.0);

                    return Expanded(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          // 막대 바 영역
                          Expanded(
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                // 입금 바 (Green)
                                Tooltip(
                                  message: '${item.yearMonth} 입금: ${NumberFormat('#,###').format(item.income)}원',
                                  child: Container(
                                    width: 11,
                                    height: (incomeRatio * 64).clamp(3.0, 64.0),
                                    decoration: BoxDecoration(
                                      color: item.income > 0
                                          ? const Color(0xFF10B981)
                                          : context.colors.border.withAlpha(60),
                                      borderRadius: const BorderRadius.vertical(top: Radius.circular(2)),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 3),
                                // 출금 바 (Red)
                                Tooltip(
                                  message: '${item.yearMonth} 출금: ${NumberFormat('#,###').format(item.expense)}원',
                                  child: Container(
                                    width: 11,
                                    height: (expenseRatio * 64).clamp(3.0, 64.0),
                                    decoration: BoxDecoration(
                                      color: item.expense > 0
                                          ? Colors.redAccent.withAlpha(220)
                                          : context.colors.border.withAlpha(60),
                                      borderRadius: const BorderRadius.vertical(top: Radius.circular(2)),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 6),
                          // 월 라벨
                          Text(
                            item.monthLabel,
                            style: AppTextStyles.caption.copyWith(
                              fontSize: 10,
                              color: context.colors.textMuted,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _ChartLegend extends StatelessWidget {
  final Color color;
  final String label;

  const _ChartLegend({
    required this.color,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(1.5),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 10,
            color: context.colors.textMuted,
          ),
        ),
      ],
    );
  }
}
