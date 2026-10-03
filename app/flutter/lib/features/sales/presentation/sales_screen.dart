import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../providers/sales_provider.dart';
import 'views/sales_organization_tab_view.dart';
import 'views/sales_payout_tab_view.dart';
import 'views/sales_performance_tab_view.dart';
import 'views/sales_policy_tab_view.dart';
import 'views/sales_settlement_tab_view.dart';
import 'widgets/sales_common_widgets.dart';

/// 🤝 분양 대행 관리 (Sales) 메인 화면 컨테이너
///
/// 5개 서브 탭 뷰를 라우팅/스위칭하며 권한별 접근 제어 및 프로젝트 변경 상태 초기화를 총괄합니다:
/// 1. [SalesPerformanceTabView]: 계약 실적 관리
/// 2. [SalesSettlementTabView]: 수수료 정산 관리
/// 3. [SalesPayoutTabView]: 수수료 지급 관리 & 금융 이체
/// 4. [SalesPolicyTabView]: 수수료 정책 관리
/// 5. [SalesOrganizationTabView]: 영업 조직 관리
class SalesScreen extends ConsumerStatefulWidget {
  final VoidCallback onBackToMain;

  const SalesScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  ConsumerState<SalesScreen> createState() => _SalesScreenState();
}

class _SalesScreenState extends ConsumerState<SalesScreen> {
  SalesSubTab _currentTab = SalesSubTab.performance;

  /// 프로젝트 변경 시 이전 프로젝트의 모든 검색어와 필터 프로바이더 상태를 초기화
  void _resetAllFiltersAndSearch() {
    // 실적 탭
    ref.read(salesSearchQueryProvider.notifier).state = '';
    ref.read(salesMappingStatusFilterProvider.notifier).state = SalesMappingStatusFilter.all;
    ref.read(salesTeamFilterProvider.notifier).state = null;
    ref.read(salesPersonFilterProvider.notifier).state = null;

    // 정산 탭
    ref.read(selectedPeriodIdProvider.notifier).state = null;
    ref.read(settlementSearchQueryProvider.notifier).state = '';
    ref.read(settlementDutyFilterProvider.notifier).state = '';
    ref.read(settlementPayStatusFilterProvider.notifier).state = '';

    // 지급 탭
    ref.read(payoutTabPeriodIdProvider.notifier).state = null;
    ref.read(payoutTabSearchQueryProvider.notifier).state = '';
    ref.read(payoutTabStatusFilterProvider.notifier).state = '';
    ref.read(payoutTabSelectedIdsProvider.notifier).state = {};
    ref.read(payoutTabModeProvider.notifier).state = 'person';
    ref.read(payoutTabAgencyStatusFilterProvider.notifier).state = '';
    ref.read(payoutTabAgencySearchQueryProvider.notifier).state = '';

    // 조직 탭
    ref.read(orgAgencyFilterProvider.notifier).state = null;
    ref.read(orgTeamFilterProvider.notifier).state = null;
    ref.read(orgDutyFilterProvider.notifier).state = '';
    ref.read(orgStatusFilterProvider.notifier).state = '1';
    ref.read(orgSearchQueryProvider.notifier).state = '';

    // 정책 탭
    ref.read(policyOrderGroupFilterProvider.notifier).state = null;
    ref.read(policyUnitTypeFilterProvider.notifier).state = null;
    ref.read(policyActiveFilterProvider.notifier).state = 'true';
    ref.read(policySearchQueryProvider.notifier).state = '';
  }

  @override
  Widget build(BuildContext context) {
    // ── 🔄 프로젝트 변경 감지 리스너: 프로젝트 변경 시 5개 탭의 모든 검색어와 필터 초기화 ──
    ref.listen(selectedRealEstateProjectProvider, (previous, next) {
      if (previous?.realProjectId != next?.realProjectId) {
        _resetAllFiltersAndSearch();
      }
    });

    final selectedProject = ref.watch(selectedRealEstateProjectProvider);
    final projectSlug = selectedProject?.slug;

    final canPerformance = ref.can(Perm.salesRead, projectSlug: projectSlug);
    final canSettlement = ref.can(Perm.salesSettle, projectSlug: projectSlug);
    final canPayout = ref.can(Perm.salesPayout, projectSlug: projectSlug);
    final canOrganization = ref.can(Perm.salesManage, projectSlug: projectSlug);
    final canPolicy = ref.can(Perm.salesPolicy, projectSlug: projectSlug);

    final availableTabs = <SalesSubTab>[];
    if (canPerformance) availableTabs.add(SalesSubTab.performance);
    if (canSettlement) availableTabs.add(SalesSubTab.settlement);
    if (canPayout) availableTabs.add(SalesSubTab.payout);
    if (canPolicy) availableTabs.add(SalesSubTab.policy);
    if (canOrganization) availableTabs.add(SalesSubTab.organization);

    if (availableTabs.isNotEmpty && !availableTabs.contains(_currentTab)) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted && availableTabs.isNotEmpty && !availableTabs.contains(_currentTab)) {
          setState(() => _currentTab = availableTabs.first);
        }
      });
    }

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: Column(
        children: [
          // ── 상단 서브 탭 바 (IBS Global Flat radius=0) ─────────────────
          if (availableTabs.isNotEmpty)
            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: context.colors.bgSurface,
                border: Border(
                  bottom: BorderSide(color: context.colors.border, width: 1),
                ),
              ),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                child: Row(
                  children: [
                    if (canPerformance) ...[
                      _buildSubTabButton(
                        tab: SalesSubTab.performance,
                        label: '계약 실적',
                        icon: Icons.assignment_turned_in_outlined,
                      ),
                      const SizedBox(width: 8),
                    ],
                    if (canSettlement) ...[
                      _buildSubTabButton(
                        tab: SalesSubTab.settlement,
                        label: '수수료 정산',
                        icon: Icons.calculate_outlined,
                      ),
                      const SizedBox(width: 8),
                    ],
                    if (canPayout) ...[
                      _buildSubTabButton(
                        tab: SalesSubTab.payout,
                        label: '수수료 지급',
                        icon: Icons.account_balance_outlined,
                      ),
                      const SizedBox(width: 8),
                    ],
                    if (canPolicy) ...[
                      _buildSubTabButton(
                        tab: SalesSubTab.policy,
                        label: '수수료 정책',
                        icon: Icons.rule_folder_outlined,
                      ),
                      const SizedBox(width: 8),
                    ],
                    if (canOrganization) ...[
                      _buildSubTabButton(
                        tab: SalesSubTab.organization,
                        label: '영업 조직',
                        icon: Icons.groups_outlined,
                      ),
                    ],
                  ],
                ),
              ),
            ),

          // ── 본문 영역 ──────────────────────────────────────────
          Expanded(
            child: selectedProject == null
                ? Center(
                    child: Text(
                      '프로젝트를 먼저 선택해 주세요.',
                      style: AppTextStyles.bodySecond.copyWith(
                        color: context.colors.textMuted,
                      ),
                    ),
                  )
                : availableTabs.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.lock_outline, size: 48, color: context.colors.textMuted),
                            const SizedBox(height: 12),
                            Text(
                              '분양 대행 관리 열람 권한이 없습니다.',
                              style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '관리자에게 분양 대행 관련 권한(sales.*)을 요청해 주세요.',
                              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                            ),
                          ],
                        ),
                      )
                    : _buildTabContent(selectedProject),
          ),
        ],
      ),
    );
  }

  Widget _buildSubTabButton({
    required SalesSubTab tab,
    required String label,
    required IconData icon,
  }) {
    final isSelected = _currentTab == tab;
    const primaryColor = Color(0xFF8B5CF6); // Violet

    return Material(
      color: isSelected ? primaryColor : context.colors.bgCard,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.zero,
        side: BorderSide(
          color: isSelected ? primaryColor : context.colors.border,
          width: 0.8,
        ),
      ),
      child: InkWell(
        onTap: () => setState(() => _currentTab = tab),
        borderRadius: BorderRadius.zero,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                size: 14,
                color: isSelected ? Colors.white : context.colors.textSecond,
              ),
              const SizedBox(width: 6),
              Text(
                label,
                style: AppTextStyles.label.copyWith(
                  color: isSelected ? Colors.white : context.colors.textSecond,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTabContent(SelectedProject project) {
    switch (_currentTab) {
      case SalesSubTab.performance:
        return SalesPerformanceTabView(project: project);
      case SalesSubTab.settlement:
        return SalesSettlementTabView(project: project);
      case SalesSubTab.payout:
        return SalesPayoutTabView(project: project);
      case SalesSubTab.policy:
        return SalesPolicyTabView(project: project);
      case SalesSubTab.organization:
        return SalesOrganizationTabView(project: project);
    }
  }
}
