import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/models/common_models.dart';
import '../../../../core/providers/docs_context_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/router/app_router.dart';
import '../../../../core/widgets/project_selector_bottom_sheet.dart';
import '../../contract/presentation/contract_list_screen.dart';
import '../../docs/presentation/docs_screen.dart';
import '../../ledger/presentation/ledger_screen.dart';
import '../../payment/presentation/payment_list_screen.dart';
import 'project_settings_screen.dart';

/// 활성화된 서브 모듈 구분
enum ProjectActiveModule { none, docs, contract, payment, ledger, settings }

/// 프로젝트 관리 탭 메인 화면 (IBS Global - type == '2' 부동산 개발 프로젝트 전용)
/// 계약(Contract) / 수납(Payment) / 자금(Ledger) / 설정(Settings) 4대 모듈 접근 UI (radius = 0)
class ProjectScreen extends ConsumerStatefulWidget {
  const ProjectScreen({super.key});

  @override
  ConsumerState<ProjectScreen> createState() => _ProjectScreenState();
}

class _ProjectScreenState extends ConsumerState<ProjectScreen> {
  ProjectActiveModule _activeModule = ProjectActiveModule.none;

  void _openSubModule(ProjectActiveModule module, [SelectedProject? project]) {
    if (module == ProjectActiveModule.docs && project != null) {
      ref.read(docsContextProvider.notifier).state = DocsContext.project(
        SimpleProjectModel(
          pk: project.pk,
          name: project.name,
          slug: project.slug,
        ),
      );
    }
    setState(() {
      _activeModule = module;
    });
  }

  void _closeSubModule() {
    setState(() {
      _activeModule = ProjectActiveModule.none;
    });
  }

  @override
  Widget build(BuildContext context) {
    final selectedProject = ref.watch(selectedProjectProvider);
    final isRealEstateProject =
        selectedProject != null && selectedProject.type == '2';

    // ── 서브 모듈 내부 뷰 모드 (1줄 콤팩트 바 뷰) ──────────────────────
    if (_activeModule != ProjectActiveModule.none && selectedProject != null) {
      Widget contentWidget;
      switch (_activeModule) {
        case ProjectActiveModule.docs:
          contentWidget = const DocsScreen();
          break;
        case ProjectActiveModule.contract:
          contentWidget = ContractListScreen(onBackToMain: _closeSubModule);
          break;
        case ProjectActiveModule.payment:
          contentWidget = PaymentListScreen(onBackToMain: _closeSubModule);
          break;
        case ProjectActiveModule.ledger:
          contentWidget = LedgerScreen(onBackToMain: _closeSubModule);
          break;
        case ProjectActiveModule.settings:
          contentWidget = ProjectSettingsScreen(onBackToMain: _closeSubModule);
          break;
        case ProjectActiveModule.none:
          contentWidget = const SizedBox.shrink();
          break;
      }

      return Scaffold(
        backgroundColor: AppColors.bgPrimary,
        body: Column(
          children: [
            // ── 서브모듈 전용 1줄 고정 프로젝트 선택 바 ──────────────────────
            InkWell(
              onTap: () {
                showProjectSelectorBottomSheet(context, onlyRealEstate: true);
                final updatedProj = ref.read(selectedProjectProvider);
                if (updatedProj != null &&
                    _activeModule == ProjectActiveModule.docs) {
                  ref.read(docsContextProvider.notifier).state =
                      DocsContext.project(
                    SimpleProjectModel(
                      pk: updatedProj.pk,
                      name: updatedProj.name,
                      slug: updatedProj.slug,
                    ),
                  );
                }
              },
              child: Container(
                color: AppColors.bgSurface,
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  children: [
                    const Icon(Icons.business_center_rounded,
                        size: 16, color: AppColors.accentProject),
                    const SizedBox(width: 8),
                    Text(
                      '프로젝트:',
                      style: AppTextStyles.caption
                          .copyWith(color: AppColors.textMuted),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        selectedProject.name,
                        style: AppTextStyles.titleSm
                            .copyWith(color: AppColors.accentProject),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppColors.accentProject.withAlpha(25),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(
                            color: AppColors.accentProject.withAlpha(60)),
                      ),
                      child: Row(
                        children: [
                          Text('프로젝트 변경',
                              style: AppTextStyles.label
                                  .copyWith(color: AppColors.accentProject)),
                          const Icon(Icons.keyboard_arrow_down_rounded,
                              size: 16, color: AppColors.accentProject),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    InkWell(
                      onTap: _closeSubModule,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppColors.accentProject.withAlpha(25),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(
                              color: AppColors.accentProject.withAlpha(80)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.arrow_back_rounded,
                                size: 14, color: AppColors.accentProject),
                            const SizedBox(width: 4),
                            Text('메인으로',
                                style: AppTextStyles.label.copyWith(
                                    color: AppColors.accentProject)),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const Divider(color: AppColors.border, height: 1),

            // ── 활성화된 서브모듈 화면 ─────────────────────────────────────
            Expanded(child: contentWidget),
          ],
        ),
      );
    }

    // 기본 프로젝트 관리 메인 뷰 모드
    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      body: SingleChildScrollView(
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
              border: Border.all(
                color: isRealEstateProject
                    ? AppColors.border
                    : AppColors.warning.withAlpha(100),
                width: 1,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── 상단 행: 상태 배지 + 프로젝트 변경/선택 버튼 ─────────────
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: isRealEstateProject
                            ? AppColors.accentProject.withAlpha(30)
                            : AppColors.warning.withAlpha(30),
                        borderRadius: BorderRadius.zero,
                        border: Border.all(
                          color: isRealEstateProject
                              ? AppColors.accentProject.withAlpha(60)
                              : AppColors.warning.withAlpha(60),
                        ),
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
                    OutlinedButton.icon(
                      onPressed: () => showProjectSelectorBottomSheet(context,
                          onlyRealEstate: true),
                      icon: const Icon(Icons.swap_horiz_rounded, size: 15),
                      label: Text(isRealEstateProject ? '프로젝트 변경' : '프로젝트 선택'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: isRealEstateProject
                            ? AppColors.accentProject
                            : AppColors.warning,
                        side: BorderSide(
                          color: isRealEstateProject
                              ? AppColors.accentProject
                              : AppColors.warning,
                        ),
                        shape: const RoundedRectangleBorder(
                            borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 5),
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // ── 프로젝트 이름 및 설명 ──────────────────────────────────
                Text(
                  isRealEstateProject
                      ? selectedProject.name
                      : '관리 대상 프로젝트를 선택해 주세요',
                  style: AppTextStyles.titleLg.copyWith(fontSize: 17),
                ),
                const SizedBox(height: 4),
                Text(
                  isRealEstateProject
                      ? (selectedProject.description ?? '등록된 프로젝트 설명이 없습니다.')
                      : '계약, 수납, 자금, 문서 모듈은 부동산 개발 프로젝트(type=2) 전용 기능입니다.',
                  style: AppTextStyles.bodySecond.copyWith(
                    color: isRealEstateProject
                        ? AppColors.textSecond
                        : AppColors.textMuted,
                    fontSize: 13,
                  ),
                ),

                // ── 하단 행: 우측 하단 문서함 진입 버튼 ───────────────────────
                if (isRealEstateProject) ...[
                  const SizedBox(height: 14),
                  const Divider(color: AppColors.border, height: 1),
                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      OutlinedButton.icon(
                        onPressed: () => _openSubModule(
                            ProjectActiveModule.docs, selectedProject),
                        icon: const Icon(Icons.folder_shared_outlined,
                            size: 15, color: Colors.white),
                        label: Row(
                          children: [
                            Text(
                              '프로젝트 문서함',
                              style: AppTextStyles.label.copyWith(
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(width: 4),
                            const Icon(Icons.arrow_forward_rounded,
                                size: 14, color: Colors.white),
                          ],
                        ),
                        style: OutlinedButton.styleFrom(
                          backgroundColor: const Color(0xFF6A1B9A), // 솔리드 선명 보라색
                          side: const BorderSide(
                              color: Color(0xFFAB47BC), width: 1),
                          shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 7),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 18),

          // ── 2. 프로젝트 전용 4대 핵심 모듈 접근 섹션 (radius = 0) ───────────
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
            onTap: () => _openSubModule(ProjectActiveModule.contract),
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
            onTap: () => _openSubModule(ProjectActiveModule.payment),
          ),
          const SizedBox(height: 12),

          // 모듈 3: 자금 / 캐시플로우 관리 (Ledger)
          _ModuleCard(
            title: '자금 / 재무 관리 (Ledger)',
            subtitle: '프로젝트 계좌 거래 내역, 운영비 정산 및 자금 집행 현황',
            icon: Icons.account_balance_wallet_outlined,
            accentColor: const Color(0xFFE65100),
            badgeText: 'Ledger',
            isEnabled: isRealEstateProject,
            onTap: () => _openSubModule(ProjectActiveModule.ledger),
          ),
          const SizedBox(height: 12),

          // 모듈 4: 프로젝트 설정 (Settings)
          _ModuleCard(
            title: '프로젝트 설정 (Settings)',
            subtitle: '프로젝트 기본 정보, 차수 정보, 동·호수 유닛 배치 현황 및 예산 설정',
            icon: Icons.settings_outlined,
            accentColor: const Color(0xFF00796B),
            badgeText: 'Settings',
            isEnabled: isRealEstateProject,
            onTap: () => _openSubModule(ProjectActiveModule.settings),
          ),

          const SizedBox(height: 32),
        ],
      ),
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
