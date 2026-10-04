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
  final ScrollController _tabScrollController = ScrollController();
  bool _canScrollLeft = false;
  bool _canScrollRight = false;

  @override
  void initState() {
    super.initState();
    _tabScrollController.addListener(_updateScrollIndicators);
    WidgetsBinding.instance.addPostFrameCallback((_) => _updateScrollIndicators());
  }

  @override
  void dispose() {
    _tabScrollController.removeListener(_updateScrollIndicators);
    _tabScrollController.dispose();
    super.dispose();
  }

  void _updateScrollIndicators() {
    if (!_tabScrollController.hasClients) return;
    final maxScroll = _tabScrollController.position.maxScrollExtent;
    final currentScroll = _tabScrollController.offset;
    final canLeft = currentScroll > 4;
    final canRight = currentScroll < maxScroll - 4 && maxScroll > 0;

    if (canLeft != _canScrollLeft || canRight != _canScrollRight) {
      if (mounted) {
        setState(() {
          _canScrollLeft = canLeft;
          _canScrollRight = canRight;
        });
      }
    }
  }

  void _scrollTo(bool right) {
    if (!_tabScrollController.hasClients) return;
    final current = _tabScrollController.offset;
    final target = right ? current + 140.0 : current - 140.0;
    _tabScrollController.animateTo(
      target.clamp(0.0, _tabScrollController.position.maxScrollExtent),
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
    );
  }

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

  /// 현재 선택된 탭의 데이터 새로고침
  Future<void> _refreshCurrentTab() async {
    switch (_currentTab) {
      case SalesSubTab.performance:
        await Future.wait([
          ref.refresh(simpleContractsProvider.future),
          ref.refresh(rawContractSalesAgentsProvider.future),
          ref.refresh(salesTeamsProvider.future),
          ref.refresh(salesPersonsProvider.future),
          ref.refresh(salesPoliciesProvider.future),
        ]);
        break;
      case SalesSubTab.settlement:
        await Future.wait([
          ref.refresh(settlementPeriodsProvider.future),
          ref.refresh(commissionPayoutsProvider.future),
          ref.refresh(agencyPayoutsProvider.future),
        ]);
        break;
      case SalesSubTab.payout:
        await Future.wait([
          ref.refresh(settlementPeriodsProvider.future),
          ref.refresh(payoutTabPayoutsProvider.future),
          ref.refresh(payoutTabAgencyPayoutsProvider.future),
        ]);
        break;
      case SalesSubTab.policy:
        await Future.wait([
          ref.refresh(salesPoliciesProvider.future),
          ref.refresh(orderGroupsProvider.future),
          ref.refresh(unitTypesProvider.future),
        ]);
        break;
      case SalesSubTab.organization:
        await Future.wait([
          ref.refresh(salesAgenciesProvider.future),
          ref.refresh(salesTeamsProvider.future),
          ref.refresh(salesPersonsProvider.future),
        ]);
        break;
    }
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
          // ── 상단 글로벌 헤더 배너 (뒤로가기 연동 & 프로젝트 명 표기) ───
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back_rounded, size: 20),
                  tooltip: '뒤로가기',
                  color: context.colors.textPrimary,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                  onPressed: () {
                    if (Navigator.of(context).canPop()) {
                      Navigator.of(context).pop();
                    } else {
                      widget.onBackToMain();
                    }
                  },
                ),
                const SizedBox(width: 8),
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: const Color(0xFF8B5CF6).withAlpha(30),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.real_estate_agent_outlined,
                    size: 20,
                    color: Color(0xFF8B5CF6),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Text(
                            '분양 대행 관리',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 5,
                              vertical: 1.5,
                            ),
                            decoration: BoxDecoration(
                              color: const Color(0xFF8B5CF6).withAlpha(20),
                              border: Border.all(
                                color: const Color(0xFF8B5CF6).withAlpha(120),
                                width: 0.8,
                              ),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Text(
                              'SALES',
                              style: TextStyle(
                                fontSize: 9.5,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF8B5CF6),
                                letterSpacing: 0.6,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        selectedProject?.name ?? '부동산 개발 프로젝트',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: _refreshCurrentTab,
                  icon: const Icon(Icons.refresh_rounded, size: 18),
                  tooltip: '새로고침',
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  color: context.colors.textSecond,
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 상단 서브 탭 바 ──────────────────────────────────────
          if (availableTabs.isNotEmpty)
            LayoutBuilder(
              builder: (context, constraints) {
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  if (mounted) _updateScrollIndicators();
                });

                return Container(
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: context.colors.bgSurface,
                    border: Border(
                      bottom: BorderSide(color: context.colors.border, width: 1),
                    ),
                  ),
                  child: Stack(
                    children: [
                      NotificationListener<ScrollNotification>(
                        onNotification: (notification) {
                          _updateScrollIndicators();
                          return false;
                        },
                        child: SingleChildScrollView(
                          controller: _tabScrollController,
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
                      if (_canScrollLeft)
                        _buildScrollHintButton(isRight: false),
                      if (_canScrollRight)
                        _buildScrollHintButton(isRight: true),
                    ],
                  ),
                );
              },
            ),

          // ── 본문 영역 ──────────────────────────────────────────
          Expanded(
            child: selectedProject == null
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.folder_open_outlined,
                          size: 48,
                          color: context.colors.textDisabled,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          '선택된 프로젝트가 없습니다.',
                          style: AppTextStyles.bodyMd.copyWith(
                            color: context.colors.textMuted,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          '상단에서 프로젝트를 먼저 선택해 주세요.',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textDisabled,
                          ),
                        ),
                      ],
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
        borderRadius: BorderRadius.circular(6),
        side: BorderSide(
          color: isSelected ? primaryColor : context.colors.border,
          width: 0.8,
        ),
      ),
      child: InkWell(
        onTap: () => setState(() => _currentTab = tab),
        borderRadius: BorderRadius.circular(6),
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

  /// 탭 바 좌우 스크롤 힌트 및 버튼 위젯
  Widget _buildScrollHintButton({required bool isRight}) {
    final bgColor = context.colors.bgSurface;
    const primaryColor = Color(0xFF8B5CF6);

    return Positioned(
      left: isRight ? null : 0,
      right: isRight ? 0 : null,
      top: 0,
      bottom: 1, // 하단 테두리 선 바로 위
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () => _scrollTo(isRight),
        child: Container(
          width: 44,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: isRight ? Alignment.centerRight : Alignment.centerLeft,
              end: isRight ? Alignment.centerLeft : Alignment.centerRight,
              colors: [
                bgColor,
                bgColor.withAlpha(220),
                bgColor.withAlpha(0),
              ],
              stops: const [0.0, 0.45, 1.0],
            ),
          ),
          child: Align(
            alignment: isRight ? Alignment.centerRight : Alignment.centerLeft,
            child: Padding(
              padding: EdgeInsets.only(
                right: isRight ? 6 : 0,
                left: isRight ? 0 : 6,
              ),
              child: Container(
                width: 22,
                height: 22,
                decoration: BoxDecoration(
                  color: bgColor,
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: primaryColor.withAlpha(140),
                    width: 0.8,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withAlpha(20),
                      blurRadius: 4,
                      offset: const Offset(0, 1),
                    ),
                  ],
                ),
                child: Icon(
                  isRight
                      ? Icons.chevron_right_rounded
                      : Icons.chevron_left_rounded,
                  size: 16,
                  color: primaryColor,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
