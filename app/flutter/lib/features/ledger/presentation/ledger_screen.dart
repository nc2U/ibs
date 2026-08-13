import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';

/// 자금/재무 관리 (Ledger) 메인 화면 (Phase 2 스케일러블 플레이스홀더)
class LedgerScreen extends ConsumerWidget {
  final VoidCallback onBackToMain;

  const LedgerScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      children: [
        // ── 1. 자금/재무 모듈 헤더 배너 ─────────────────────────────────────
        Container(
          color: AppColors.bgSurface,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: const Color(0xFFE65100).withAlpha(30),
                  borderRadius: BorderRadius.zero,
                ),
                child: const Icon(Icons.account_balance_outlined,
                    size: 20, color: Color(0xFFE65100)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('자금 / 재무 관리 (Ledger)',
                        style: AppTextStyles.titleSm
                            .copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 2),
                    Text('프로젝트 계좌 관리, 입출금 거래 내역 및 캐시플로우',
                        style: AppTextStyles.caption
                            .copyWith(color: AppColors.textMuted)),
                  ],
                ),
              ),
            ],
          ),
        ),
        const Divider(color: AppColors.border, height: 1),

        // ── 2. 검색 및 계좌 필터바 ──────────────────────────────────────────
        Container(
          color: AppColors.bgSurface,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  style: AppTextStyles.bodyMd,
                  decoration: const InputDecoration(
                    hintText: '적요, 계좌명, 거래처 검색...',
                    prefixIcon: Icon(Icons.search_rounded,
                        size: 18, color: AppColors.textMuted),
                    contentPadding: EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              OutlinedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.account_balance_rounded, size: 16),
                label: const Text('계좌 전체'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.textSecond,
                  side: const BorderSide(color: AppColors.border),
                  shape: const RoundedRectangleBorder(
                      borderRadius: BorderRadius.zero),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
                ),
              ),
            ],
          ),
        ),
        const Divider(color: AppColors.border, height: 1),

        // ── 3. 자금/재무 목록 플레이스홀더 ──────────────────────────────────
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                // 요약 카드 3종
                Row(
                  children: [
                    _SummaryMiniCard(
                      title: '총 입금액',
                      value: '₩0원',
                      accentColor: const Color(0xFF1565C0),
                    ),
                    const SizedBox(width: 8),
                    _SummaryMiniCard(
                      title: '총 출금액',
                      value: '₩0원',
                      accentColor: const Color(0xFFC62828),
                    ),
                    const SizedBox(width: 8),
                    _SummaryMiniCard(
                      title: '현재 잔액합계',
                      value: '₩0원',
                      accentColor: const Color(0xFFE65100),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // 데이터 준비 중 안내 카드
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(
                    color: AppColors.bgCard,
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: AppColors.border, width: 0.8),
                  ),
                  child: Column(
                    children: [
                      const Icon(Icons.analytics_outlined,
                          size: 48, color: AppColors.textDisabled),
                      const SizedBox(height: 16),
                      Text('자금 / 재무 관리 모듈 준비 중입니다.',
                          style: AppTextStyles.titleSm
                              .copyWith(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Text(
                        '사업지별 프로젝트 전용 계좌 내역,\n실시간 입출금 거래 및 자금 흐름(Cashflow) 집계 기능이 연동됩니다.',
                        style: AppTextStyles.bodySecond
                            .copyWith(color: AppColors.textMuted),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _SummaryMiniCard extends StatelessWidget {
  final String title;
  final String value;
  final Color accentColor;

  const _SummaryMiniCard({
    required this.title,
    required this.value,
    required this.accentColor,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(color: AppColors.border, width: 0.8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style: AppTextStyles.caption
                    .copyWith(color: AppColors.textMuted, fontSize: 11)),
            const SizedBox(height: 4),
            Text(value,
                style: AppTextStyles.titleSm.copyWith(
                  color: accentColor,
                  fontWeight: FontWeight.bold,
                )),
          ],
        ),
      ),
    );
  }
}
