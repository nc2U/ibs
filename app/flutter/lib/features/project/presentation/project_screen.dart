import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/widgets/project_selector_bottom_sheet.dart';

/// 프로젝트 관리 탭 메인 화면 (IBS Global - type == '2' 부동산 개발 프로젝트 전용)
/// 계약(Contract) / 수납(Payment) / 자금(Ledger) / 문서(Docs) / 설정(Settings) 5대 모듈 접근 UI (radius = 0)
class ProjectScreen extends ConsumerWidget {
  const ProjectScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedProject = ref.watch(selectedProjectProvider);
    final isRealEstateProject =
        selectedProject != null && selectedProject.type == '2';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 1. 현재 선택된 프로젝트 개요 카드 (radius = 0) ───────────────────
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.bgCard,
              borderRadius: BorderRadius.zero,
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
                        color: isRealEstateProject
                            ? AppColors.accentProject.withAlpha(30)
                            : AppColors.warning.withAlpha(30),
                        borderRadius: BorderRadius.zero,
                      ),
                      child: Text(
                        isRealEstateProject
                            ? '프로젝트 (IBS Global)'
                            : (selectedProject == null
                                ? '프로젝트 미선택'
                                : '일반 워크스페이스'),
                        style: AppTextStyles.label.copyWith(
                          color: isRealEstateProject
                              ? AppColors.accentProject
                              : AppColors.warning,
                        ),
                      ),
                    ),
                    const Spacer(),
                    OutlinedButton.icon(
                      onPressed: () => showProjectSelectorBottomSheet(context,
                          onlyRealEstate: true),
                      icon: const Icon(Icons.swap_horiz_rounded, size: 16),
                      label: const Text('프로젝트 변경'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.accentProject,
                        side: const BorderSide(color: AppColors.accentProject),
                        shape: const RoundedRectangleBorder(
                            borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 6),
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  selectedProject?.name ?? '프로젝트를 선택해 주세요',
                  style: AppTextStyles.titleLg,
                ),
                if (selectedProject?.description != null &&
                    selectedProject!.description!.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(selectedProject.description!,
                      style: AppTextStyles.bodySecond),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),

          // ── 2. 미선택 시 안내 경고 바 (radius = 0) ─────────────────────────
          if (!isRealEstateProject) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.warning.withAlpha(15),
                borderRadius: BorderRadius.zero,
                border: Border.all(
                    color: AppColors.warning.withAlpha(80), width: 1),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.info_outline_rounded,
                          color: AppColors.warning, size: 20),
                      const SizedBox(width: 8),
                      Text('프로젝트 전용 모듈',
                          style: AppTextStyles.titleSm
                              .copyWith(color: AppColors.warning)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '계약, 수납, 자금(입출금), 공용문서 등 IBS 관리 모듈은 프로젝트(type=2)에서만 연동됩니다.\n아래 버튼을 눌러 관리 대상 프로젝트를 선택해 주세요.',
                    style: AppTextStyles.bodyMd
                        .copyWith(color: AppColors.textSecond, height: 1.4),
                  ),
                  const SizedBox(height: 14),
                  ElevatedButton.icon(
                    onPressed: () => showProjectSelectorBottomSheet(context,
                        onlyRealEstate: true),
                    icon: const Icon(Icons.business_center_rounded, size: 18),
                    label: const Text('프로젝트 선택'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.warning,
                      foregroundColor: Colors.black,
                      shape: const RoundedRectangleBorder(
                          borderRadius: BorderRadius.zero),
                      minimumSize: const Size(double.infinity, 42),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // ── 3. 프로젝트 전용 5대 핵심 모듈 접근 섹션 (radius = 0) ───────────
          Text('핵심 관리 모듈',
              style: AppTextStyles.titleSm
                  .copyWith(color: AppColors.textMuted)),
          const SizedBox(height: 10),

          // 모듈 1: 계약 관리 (Contract)
          _ModuleCard(
            title: '계약 관리 (Contract)',
            subtitle: '분양 계약 내역, 계약자 상세 정보, 권리의무 승계 및 계약 해지 관리',
            icon: Icons.assignment_outlined,
            accentColor: const Color(0xFF3565A6),
            badgeText: 'Contract',
            isEnabled: isRealEstateProject,
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('계약 관리 모듈 준비 중입니다.')),
              );
            },
          ),
          const SizedBox(height: 12),

          // 모듈 2: 대금 수납 관리 (Payment)
          _ModuleCard(
            title: '대금 수납 관리 (Payment)',
            subtitle: '차수별 납부 내역, 건별 수납 등록, 미납금 및 수납 현황 집계',
            icon: Icons.payments_outlined,
            accentColor: const Color(0xFF2E7D32),
            badgeText: 'Payment',
            isEnabled: isRealEstateProject,
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('대금 수납 관리 모듈 준비 중입니다.')),
              );
            },
          ),
          const SizedBox(height: 12),

          // 모듈 3: 자금 / 캐시플로우 관리 (Ledger)
          _ModuleCard(
            title: '자금 / 재무 관리 (Ledger)',
            subtitle: '프로젝트 계좌 거래 내역, 운영비 정산 및 자금 집행 현황',
            icon: Icons.account_balance_wallet_outlined,
            accentColor: const Color(0xFF5E35B1),
            badgeText: 'Ledger',
            isEnabled: isRealEstateProject,
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('자금/재무 관리 모듈 준비 중입니다.')),
              );
            },
          ),
          const SizedBox(height: 12),

          // 모듈 4: 문서 / 소송 관리 (Docs)
          _ModuleCard(
            title: '문서 / 소송 관리 (Docs)',
            subtitle: '프로젝트 일반 문서, 소송 사건 이력 및 공용 서류 보관소',
            icon: Icons.folder_shared_outlined,
            accentColor: const Color(0xFFE65100),
            badgeText: 'Docs',
            isEnabled: isRealEstateProject,
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('문서/소송 관리 모듈 준비 중입니다.')),
              );
            },
          ),
          const SizedBox(height: 12),

          // 모듈 5: 프로젝트 설정 (Settings)
          _ModuleCard(
            title: '프로젝트 설정 (Settings)',
            subtitle: '프로젝트 기본 정보, 차수 정보, 동·호수 유닛 배치 현황 및 예산 설정',
            icon: Icons.settings_outlined,
            accentColor: const Color(0xFF00796B),
            badgeText: 'Settings',
            isEnabled: isRealEstateProject,
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('프로젝트 설정 모듈 준비 중입니다.')),
              );
            },
          ),

          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

/// radius = 0 이 적용된 모듈 카드 위젯
class _ModuleCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color accentColor;
  final String badgeText;
  final bool isEnabled;
  final VoidCallback onTap;

  const _ModuleCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.accentColor,
    required this.badgeText,
    required this.isEnabled,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveColor = isEnabled ? accentColor : AppColors.textDisabled;

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(
          color: isEnabled
              ? accentColor.withAlpha(60)
              : AppColors.border,
          width: 1,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.zero,
        child: InkWell(
          onTap: isEnabled ? onTap : null,
          borderRadius: BorderRadius.zero,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── 아이콘 뱃지 (radius = 0) ──────────────────────────────────
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: effectiveColor.withAlpha(20),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Icon(icon, size: 24, color: effectiveColor),
                ),
                const SizedBox(width: 14),

                // ── 타이틀 & 설명 ─────────────────────────────────────────────
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              title,
                              style: AppTextStyles.titleSm.copyWith(
                                color: isEnabled
                                    ? AppColors.textPrimary
                                    : AppColors.textDisabled,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: effectiveColor.withAlpha(20),
                              borderRadius: BorderRadius.zero,
                            ),
                            child: Text(
                              badgeText,
                              style: AppTextStyles.label.copyWith(
                                color: effectiveColor,
                                fontSize: 11,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        subtitle,
                        style: AppTextStyles.bodyMuted.copyWith(
                          color: isEnabled
                              ? AppColors.textSecond
                              : AppColors.textDisabled,
                          fontSize: 12.5,
                          height: 1.35,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Text(
                            isEnabled ? '모듈 진입' : '프로젝트 선택 필요',
                            style: AppTextStyles.caption.copyWith(
                              color: effectiveColor,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 4),
                          Icon(
                            Icons.arrow_forward_rounded,
                            size: 14,
                            color: effectiveColor,
                          ),
                        ],
                      ),
                    ],
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
