import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/widgets/project_selector_bottom_sheet.dart';
import '../../issue/providers/issue_provider.dart';
import '../../meeting/providers/meeting_provider.dart';

/// 프로젝트 관리 탭 메인 화면
class ProjectScreen extends ConsumerWidget {
  const ProjectScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedProject = ref.watch(selectedProjectProvider);
    final issueListState = ref.watch(issueListProvider);
    final meetingListState = ref.watch(meetingListProvider);

    final issueCount = issueListState.valueOrNull?.totalCount ?? 0;
    final meetingCount = meetingListState.valueOrNull?.totalCount ?? 0;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 프로젝트 개요 카드 ────────────────────────────────────────────────
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.bgCard,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.border, width: 0.8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.accentProject.withAlpha(30),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        selectedProject == null ? '전사 공통' : '선택된 프로젝트',
                        style: AppTextStyles.label
                            .copyWith(color: AppColors.accentProject),
                      ),
                    ),
                    const Spacer(),
                    OutlinedButton.icon(
                      onPressed: () => showProjectSelectorBottomSheet(context),
                      icon: const Icon(Icons.swap_horiz_rounded, size: 16),
                      label: const Text('프로젝트 변경'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.accentProject,
                        side: const BorderSide(color: AppColors.accentProject),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 6),
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  selectedProject?.name ?? '전사 공통 (전체 프로젝트)',
                  style: AppTextStyles.titleLg,
                ),
                if (selectedProject?.description != null &&
                    selectedProject!.description!.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Text(selectedProject.description!,
                      style: AppTextStyles.bodySecond),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),

          // ── 통계 요약 ───────────────────────────────────────────────────
          Row(
            children: [
              Expanded(
                child: _StatCard(
                  title: '회의록',
                  countText: '$meetingCount 건',
                  icon: Icons.groups_outlined,
                  accentColor: AppColors.accentWork,
                  onTap: () => context.go('/work/meetings'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _StatCard(
                  title: '업무',
                  countText: '$issueCount 건',
                  icon: Icons.task_alt_rounded,
                  accentColor: AppColors.accentApproval,
                  onTap: () => context.go('/work/issues'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // ── 사업 / 계약 관리 카드 ─────────────────────────────────────────
          _SectionTitle(title: '계약 현황 (Contract)'),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.bgCard,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.border, width: 0.8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.description_outlined,
                        size: 20, color: AppColors.accentProject),
                    const SizedBox(width: 8),
                    Text('프로젝트별 분양 & 계약 통계', style: AppTextStyles.titleSm),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  '선택된 프로젝트의 계약 내역 및 수납 청구 데이터를 실시간 조회합니다.',
                  style: AppTextStyles.bodyMuted,
                ),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('계약 상세 내역 모듈 준비 중입니다.')),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.accentProject,
                    foregroundColor: Colors.white,
                    minimumSize: const Size(double.infinity, 40),
                  ),
                  child: const Text('계약 현황 조회'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // ── 입출금 / 재무 거래 카드 ─────────────────────────────────────
          _SectionTitle(title: '재무 / 캐시플로우 (Ledger)'),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.bgCard,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.border, width: 0.8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.account_balance_wallet_outlined,
                        size: 20, color: AppColors.accentCorp),
                    const SizedBox(width: 8),
                    Text('프로젝트 자금 흐름 & 입출금', style: AppTextStyles.titleSm),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  '프로젝트 계좌 입출금 거래 이력 및 계정별 집행 현황을 모니터링합니다.',
                  style: AppTextStyles.bodyMuted,
                ),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('재무/입출금 모듈 준비 중입니다.')),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.accentCorp,
                    foregroundColor: Colors.white,
                    minimumSize: const Size(double.infinity, 40),
                  ),
                  child: const Text('입출금 이력 조회'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;
  const _SectionTitle({required this.title});

  @override
  Widget build(BuildContext context) {
    return Text(title,
        style: AppTextStyles.titleSm.copyWith(color: AppColors.textMuted));
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String countText;
  final IconData icon;
  final Color accentColor;
  final VoidCallback onTap;

  const _StatCard({
    required this.title,
    required this.countText,
    required this.icon,
    required this.accentColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.border, width: 0.8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 22, color: accentColor),
            const SizedBox(height: 8),
            Text(title, style: AppTextStyles.caption),
            const SizedBox(height: 2),
            Text(countText,
                style: AppTextStyles.titleLg.copyWith(color: accentColor)),
          ],
        ),
      ),
    );
  }
}
