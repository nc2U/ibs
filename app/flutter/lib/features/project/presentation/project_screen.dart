import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/models/common_models.dart';
import '../../../../core/providers/docs_context_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/widgets/project_selector_bottom_sheet.dart';
import '../../../../core/widgets/workspace_selector_bar.dart';
import '../../contract/presentation/contract_list_screen.dart';
import '../../docs/presentation/docs_screen.dart';
import '../../ledger/presentation/ledger_screen.dart';
import '../../payment/presentation/payment_list_screen.dart';
import 'project_settings_screen.dart';
import 'site_screen.dart';

/// 활성화된 서브 모듈 구분
enum ProjectActiveModule { none, docs, contract, payment, ledger, site, settings }

/// 프로젝트 관리 탭 메인 화면 (IBS Global - type == '2' 부동산 개발 프로젝트 전용)
/// 계약(Contract) / 수납(Payment) / 자금(Ledger) / 부지(Site) 4대 모듈 접근 UI (radius = 0)
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
        case ProjectActiveModule.site:
          contentWidget = SiteScreen(onBackToMain: _closeSubModule);
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
            // ── 서브모듈 전용 1줄 고정 프로젝트 선택 바 (공용 컴포넌트) ─────────
            WorkspaceSelectorBar(
              onlyRealEstate: true,
              onProjectChanged: () {
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
              trailing: InkWell(
                onTap: _closeSubModule,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.accentProject.withAlpha(20),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(
                        color: AppColors.accentProject.withAlpha(60),
                        width: 0.8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.arrow_back_rounded,
                          size: 13, color: AppColors.accentProject),
                      const SizedBox(width: 4),
                      Text('메인으로',
                          style: AppTextStyles.label.copyWith(
                            color: AppColors.accentProject,
                            fontSize: 11,
                          )),
                    ],
                  ),
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
            // ── 1. 메인 프로젝트 히어로 셀렉터 카드 (radius = 0) ───────────────────
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.bgCard,
                borderRadius: BorderRadius.zero,
                border: Border.all(
                  color: isRealEstateProject
                      ? AppColors.accentProject.withAlpha(80)
                      : AppColors.warning.withAlpha(100),
                  width: 1,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── 상단 행: 프로젝트 이름 + 프로젝트 전환 버튼 ─────────────
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Row(
                          children: [
                            Icon(
                              isRealEstateProject
                                  ? Icons.business_rounded
                                  : Icons.warning_amber_rounded,
                              size: 18,
                              color: isRealEstateProject
                                  ? AppColors.accentProject
                                  : AppColors.warning,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                isRealEstateProject
                                    ? selectedProject.name
                                    : '프로젝트를 선택해 주세요',
                                style: AppTextStyles.titleLg.copyWith(
                                  fontSize: 17,
                                  fontWeight: FontWeight.bold,
                                  letterSpacing: -0.3,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 10),
                      Material(
                        color: isRealEstateProject
                            ? AppColors.accentProject.withAlpha(20)
                            : AppColors.warning.withAlpha(25),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.zero,
                          side: BorderSide(
                            color: isRealEstateProject
                                ? AppColors.accentProject.withAlpha(80)
                                : AppColors.warning.withAlpha(90),
                            width: 0.8,
                          ),
                        ),
                        child: InkWell(
                          onTap: () => showProjectSelectorBottomSheet(
                            context,
                            onlyRealEstate: true,
                          ),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 5),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.swap_horiz_rounded,
                                  size: 14,
                                  color: isRealEstateProject
                                      ? AppColors.accentProject
                                      : AppColors.warning,
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  isRealEstateProject ? '전환' : '선택',
                                  style: AppTextStyles.label.copyWith(
                                    color: isRealEstateProject
                                        ? AppColors.accentProject
                                        : AppColors.warning,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 11.5,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  // ── 프로젝트 설명 ──────────────────────────────────
                  Text(
                    isRealEstateProject
                        ? (selectedProject.description != null &&
                                selectedProject.description!.isNotEmpty
                            ? selectedProject.description!
                            : '분양 계약, 대금 수납, 자금(캐시플로우), 부지 및 문서 통합 관리 사업지입니다.')
                        : '계약, 대금 수납, 자금 회계, 사업 부지 모듈은 부동산 개발 사업 프로젝트 전용 기능입니다.',
                    style: AppTextStyles.bodySecond.copyWith(
                      color: isRealEstateProject
                          ? AppColors.textSecond
                          : AppColors.textMuted,
                      fontSize: 12.5,
                      height: 1.4,
                    ),
                  ),

                  // ── 하단 행: [⚙️ 프로젝트 설정] + [📂 프로젝트 문서함] 퀵 액션 ────────
                  if (isRealEstateProject) ...[
                    const SizedBox(height: 12),
                    const Divider(color: AppColors.border, height: 1),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        // 좌측: 프로젝트 설정 바로가기
                        Material(
                          color: const Color(0xFF00796B).withAlpha(25),
                          shape: const RoundedRectangleBorder(
                            borderRadius: BorderRadius.zero,
                            side: BorderSide(
                              color: Color(0xFF26A69A),
                              width: 0.8,
                            ),
                          ),
                          child: InkWell(
                            onTap: () => _openSubModule(
                              ProjectActiveModule.settings,
                            ),
                            child: Padding(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 10, vertical: 4.5),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(
                                    Icons.settings_outlined,
                                    size: 13,
                                    color: Color(0xFF4DB6AC),
                                  ),
                                  const SizedBox(width: 5),
                                  Text(
                                    '프로젝트 설정',
                                    style: AppTextStyles.label.copyWith(
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 11.5,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                        const Spacer(),

                        // 우측: 프로젝트 문서함 바로가기
                        Material(
                          color: const Color(0xFF8E24AA).withAlpha(30),
                          shape: const RoundedRectangleBorder(
                            borderRadius: BorderRadius.zero,
                            side: BorderSide(
                              color: Color(0xFFBA68C8),
                              width: 0.8,
                            ),
                          ),
                          child: InkWell(
                            onTap: () => _openSubModule(
                              ProjectActiveModule.docs,
                              selectedProject,
                            ),
                            child: Padding(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 10, vertical: 4.5),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(
                                    Icons.folder_shared_outlined,
                                    size: 13,
                                    color: Color(0xFFCE93D8),
                                  ),
                                  const SizedBox(width: 5),
                                  Text(
                                    '프로젝트 문서함',
                                    style: AppTextStyles.label.copyWith(
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 11.5,
                                    ),
                                  ),
                                  const SizedBox(width: 3),
                                  const Icon(
                                    Icons.arrow_forward_rounded,
                                    size: 12,
                                    color: Color(0xFFCE93D8),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 20),

            // ── 2. 프로젝트 전용 4대 핵심 모듈 접근 섹션 (radius = 0) ───────────
            Row(
              children: [
                Container(
                  width: 3,
                  height: 14,
                  color: AppColors.accentProject,
                  margin: const EdgeInsets.only(right: 6),
                ),
                Text(
                  '핵심 관리 모듈',
                  style: AppTextStyles.titleSm.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  isRealEstateProject ? '4개 모듈 활성' : '프로젝트 선택 필요',
                  style: AppTextStyles.caption.copyWith(
                    color: isRealEstateProject
                        ? AppColors.textMuted
                        : AppColors.warning,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // 모듈 1: 계약 관리 (Contract)
            _ModuleCard(
              title: '계약 관리',
              badgeText: 'CONTRACT',
              subtitle: '동·호수별 분양 계약 내역, 계약자 상세 정보, 권리의무 승계 및 계약 해지 이력 관리',
              tags: const ['분양 계약', '계약자 정보', '권리의무 승계', '계약 해지'],
              icon: Icons.assignment_outlined,
              accentColor: const Color(0xFF38BDF8), // Sky Blue
              isEnabled: isRealEstateProject,
              onTap: () => _openSubModule(ProjectActiveModule.contract),
            ),
            const SizedBox(height: 12),

            // 모듈 2: 대금 수납 관리 (Payment)
            _ModuleCard(
              title: '대금 수납 관리',
              badgeText: 'PAYMENT',
              subtitle: '계약금·중도금·잔금 차수별 납부 내역, 건별 입금 등록 및 미납금 현황 분석',
              tags: const ['회차별 납부', '건별 입금 등록', '미납금 관리', '수납 집계'],
              icon: Icons.payments_outlined,
              accentColor: const Color(0xFF34D399), // Emerald
              isEnabled: isRealEstateProject,
              onTap: () => _openSubModule(ProjectActiveModule.payment),
            ),
            const SizedBox(height: 12),

            // 모듈 3: 자금 / 캐시플로우 관리 (Ledger)
            _ModuleCard(
              title: '자금 / 재무 관리',
              badgeText: 'LEDGER',
              subtitle: '프로젝트 전용 계좌 거래 내역, 사업비/운영비 지출 정산 및 캐시플로우 흐름 집행',
              tags: const ['계좌 거래', '사업비 정산', '캐시플로우', '자금 집행'],
              icon: Icons.account_balance_wallet_outlined,
              accentColor: const Color(0xFFFBBF24), // Amber Gold
              isEnabled: isRealEstateProject,
              onTap: () => _openSubModule(ProjectActiveModule.ledger),
            ),
            const SizedBox(height: 12),

            // 모듈 4: 사업 부지 관리 (Site)
            _ModuleCard(
              title: '사업 부지 관리',
              badgeText: 'SITE',
              subtitle: '사업 대상지 필지·지번 현황, 토지 소유자 정보, 부지 매매계약 및 권리관계/협의 일지 관리',
              tags: const ['필지·지번 목록', '토지 소유자', '부지 매매계약', '협의 일지'],
              icon: Icons.map_outlined,
              accentColor: const Color(0xFF0D9488), // Teal Green
              isEnabled: isRealEstateProject,
              onTap: () => _openSubModule(ProjectActiveModule.site),
            ),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

/// radius = 0 이 적용된 정제된 모듈 카드 위젯
class _ModuleCard extends StatelessWidget {
  final String title;
  final String badgeText;
  final String subtitle;
  final List<String> tags;
  final IconData icon;
  final Color accentColor;
  final bool isEnabled;
  final VoidCallback onTap;

  const _ModuleCard({
    required this.title,
    required this.badgeText,
    required this.subtitle,
    required this.tags,
    required this.icon,
    required this.accentColor,
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
          color: isEnabled ? accentColor.withAlpha(65) : AppColors.border,
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
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── 상단 헤더: 아이콘 + 타이틀 + 영문 뱃지 ───────────────────────
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Container(
                      width: 38,
                      height: 38,
                      decoration: BoxDecoration(
                        color: effectiveColor.withAlpha(22),
                        borderRadius: BorderRadius.zero,
                        border: Border.all(
                          color: effectiveColor.withAlpha(60),
                          width: 0.8,
                        ),
                      ),
                      child: Icon(icon, size: 20, color: effectiveColor),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text(
                                title,
                                style: AppTextStyles.titleSm.copyWith(
                                  color: isEnabled
                                      ? AppColors.textPrimary
                                      : AppColors.textDisabled,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 15,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: effectiveColor.withAlpha(20),
                                  borderRadius: BorderRadius.zero,
                                  border: Border.all(
                                    color: effectiveColor.withAlpha(60),
                                    width: 0.8,
                                  ),
                                ),
                                child: Text(
                                  badgeText,
                                  style: AppTextStyles.caption.copyWith(
                                    color: effectiveColor,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 10,
                                    letterSpacing: 0.5,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    Icon(
                      Icons.chevron_right_rounded,
                      size: 20,
                      color: effectiveColor.withAlpha(150),
                    ),
                  ],
                ),
                const SizedBox(height: 10),

                // ── 설명 텍스트 ───────────────────────────────────────────────
                Text(
                  subtitle,
                  style: AppTextStyles.bodySecond.copyWith(
                    color: isEnabled
                        ? AppColors.textSecond
                        : AppColors.textDisabled,
                    fontSize: 12.5,
                    height: 1.38,
                  ),
                ),
                const SizedBox(height: 12),

                // ── 태그 칩스 목록 ────────────────────────────────────────────
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: tags.map((tag) {
                    return Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 7, vertical: 2.5),
                      decoration: BoxDecoration(
                        color: isEnabled
                            ? AppColors.bgSurface
                            : AppColors.bgSurface.withAlpha(100),
                        borderRadius: BorderRadius.zero,
                        border: Border.all(
                          color: isEnabled
                              ? AppColors.border
                              : AppColors.borderSubtle,
                          width: 0.8,
                        ),
                      ),
                      child: Text(
                        tag,
                        style: AppTextStyles.caption.copyWith(
                          color: isEnabled
                              ? AppColors.textMuted
                              : AppColors.textDisabled,
                          fontSize: 11,
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
