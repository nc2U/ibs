import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../data/models/sales_models.dart';
import '../data/sales_repository.dart';
import '../providers/sales_provider.dart';
import 'widgets/contract_agent_form_sheet.dart';
import 'widgets/person_form_sheet.dart';
import 'widgets/agency_team_manage_sheet.dart';
import 'widgets/policy_form_sheet.dart';
import 'widgets/period_form_sheet.dart';
import 'widgets/payout_detail_sheet.dart';
import 'widgets/banking_csv_helper.dart';
import 'widgets/person_document_sheet.dart';
import 'package:flutter/services.dart';

/// 🤝 분양 대행 관리 (Sales Agency) 서브 탭 구분
enum SalesSubTab {
  performance, // 계약 실적 관리
  settlement,  // 수수료 정산 관리
  payout,      // 수수료 지급 관리
  policy,      // 수수료 정책 관리
  organization,// 영업 조직 관리
}

/// 🤝 분양 대행 관리 (Sales) 메인 화면
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
  final TextEditingController _searchController = TextEditingController();
  Timer? _debounceTimer;

  final TextEditingController _orgSearchController = TextEditingController();
  Timer? _orgDebounceTimer;

  final TextEditingController _policySearchController = TextEditingController();
  Timer? _policyDebounceTimer;

  final TextEditingController _settlementSearchController = TextEditingController();
  Timer? _settlementDebounceTimer;

  final TextEditingController _payoutSearchController = TextEditingController();
  Timer? _payoutDebounceTimer;
  bool _isBatchProcessing = false;

  @override
  void dispose() {
    _searchController.dispose();
    _debounceTimer?.cancel();
    _orgSearchController.dispose();
    _orgDebounceTimer?.cancel();
    _policySearchController.dispose();
    _policyDebounceTimer?.cancel();
    _settlementSearchController.dispose();
    _settlementDebounceTimer?.cancel();
    _payoutSearchController.dispose();
    _payoutDebounceTimer?.cancel();
    super.dispose();
  }

  void _onSearchChanged(String value) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      ref.read(salesSearchQueryProvider.notifier).state = value.trim();
    });
  }

  void _onOrgSearchChanged(String value) {
    _orgDebounceTimer?.cancel();
    _orgDebounceTimer = Timer(const Duration(milliseconds: 300), () {
      ref.read(orgSearchQueryProvider.notifier).state = value.trim();
    });
  }

  void _onPolicySearchChanged(String value) {
    _policyDebounceTimer?.cancel();
    _policyDebounceTimer = Timer(const Duration(milliseconds: 300), () {
      ref.read(policySearchQueryProvider.notifier).state = value.trim();
    });
  }

  void _onSettlementSearchChanged(String value) {
    _settlementDebounceTimer?.cancel();
    _settlementDebounceTimer = Timer(const Duration(milliseconds: 300), () {
      ref.read(settlementSearchQueryProvider.notifier).state = value.trim();
    });
  }

  void _onPayoutSearchChanged(String value) {
    _payoutDebounceTimer?.cancel();
    _payoutDebounceTimer = Timer(const Duration(milliseconds: 300), () {
      ref.read(payoutTabSearchQueryProvider.notifier).state = value.trim();
    });
  }

  Future<void> _makePhoneCall(String phone, {String? targetName}) async {
    final cleanPhone = phone.replaceAll(RegExp(r'[^0-9]'), '');
    if (cleanPhone.isEmpty) return;

    final shouldCall = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        titlePadding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        actionsPadding: const EdgeInsets.all(12),
        title: Row(
          children: [
            const Icon(Icons.phone_in_talk, size: 20, color: Color(0xFF10B981)),
            const SizedBox(width: 8),
            Text(
              '통화 연결 확인',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Text(
          targetName != null && targetName.isNotEmpty
              ? '$targetName ($phone) 님에게 전화를 연결하시겠습니까?'
              : '$phone 로 전화를 연결하시겠습니까?',
          style: AppTextStyles.bodySecond.copyWith(
            color: context.colors.textSecond,
            height: 1.4,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(
              '취소',
              style: TextStyle(color: context.colors.textMuted),
            ),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: const Color(0xFF10B981),
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('통화 연결'),
          ),
        ],
      ),
    );

    if (shouldCall == true) {
      final uri = Uri.parse('tel:$cleanPhone');
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('통화 기능을 실행할 수 없습니다.')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
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
        return _buildPerformanceView(project);
      case SalesSubTab.settlement:
        return _buildSettlementView(project);
      case SalesSubTab.payout:
        return _buildPayoutView(project);
      case SalesSubTab.policy:
        return _buildPolicyView(project);
      case SalesSubTab.organization:
        return _buildOrganizationView(project);
    }
  }

  /// 1. 계약 실적 관리 뷰 (실제 API 연동 + 2×2 KPI + 카드 리스트 + 검색/필터 + 배정 모달)
  Widget _buildPerformanceView(SelectedProject project) {
    final summary = ref.watch(salesPerformanceSummaryProvider);
    final combinedAsync = ref.watch(combinedContractPerformanceProvider);
    final filteredItems = ref.watch(filteredContractPerformanceProvider);
    final persons = ref.watch(salesPersonsProvider).valueOrNull ?? [];

    return RefreshIndicator(
      color: const Color(0xFF8B5CF6),
      onRefresh: () async {
        ref.invalidate(simpleContractsProvider);
        ref.invalidate(rawContractSalesAgentsProvider);
        ref.invalidate(salesTeamsProvider);
        ref.invalidate(salesPersonsProvider);
        ref.invalidate(salesPoliciesProvider);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 1. 2×2 실시간 실적 KPI 대시보드
          _buildPerformanceKpiSection(summary),
          const SizedBox(height: 14),

          // 2. 검색 및 필터 바
          _buildFilterAndSearchBar(project, summary),
          const SizedBox(height: 14),

          // 3. 계약 실적 리스트
          combinedAsync.when(
            loading: () => Container(
              padding: const EdgeInsets.all(40),
              child: const Center(
                child: SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Color(0xFF8B5CF6),
                  ),
                ),
              ),
            ),
            error: (err, _) => Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.zero,
                border: Border.all(color: context.colors.error.withAlpha(80)),
              ),
              child: Row(
                children: [
                  Icon(Icons.error_outline_rounded, size: 18, color: context.colors.error),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '실적 데이터를 불러오지 못했습니다: $err',
                      style: AppTextStyles.caption.copyWith(color: context.colors.error),
                    ),
                  ),
                ],
              ),
            ),
            data: (_) {
              if (filteredItems.isEmpty) {
                return Container(
                  padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
                  decoration: BoxDecoration(
                    color: context.colors.bgCard,
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: context.colors.border),
                  ),
                  child: Column(
                    children: [
                      Icon(Icons.search_off_rounded, size: 32, color: context.colors.textMuted),
                      const SizedBox(height: 10),
                      Text(
                        '조건에 일치하는 계약 실적이 없습니다',
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        '검색어나 필터 조건을 변경해 보시거나, 상단 [배정] 버튼을 눌러 상담사를 배정해 보세요.',
                        textAlign: TextAlign.center,
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                      ),
                    ],
                  ),
                );
              }

              return Column(
                children: filteredItems.map((item) {
                  return _buildPerformanceCardItem(item, project, persons);
                }).toList(),
              );
            },
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  /// 2×2 실적 KPI 요약 대시보드
  Widget _buildPerformanceKpiSection(SalesPerformanceSummary summary) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _buildSingleKpiTile(
                label: '총 분양 계약',
                value: '${NumberFormat('#,###').format(summary.totalContracts)}건',
                subText: '프로젝트 전체 계약',
                accentColor: const Color(0xFF38BDF8), // Sky Blue
                icon: Icons.assignment_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildSingleKpiTile(
                label: '영업 배정 완료',
                value: '${NumberFormat('#,###').format(summary.mappedCount)}건 (${summary.mappingRate}%)',
                subText: '실적 매핑률',
                accentColor: const Color(0xFF10B981), // Emerald
                icon: Icons.account_circle_outlined,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _buildSingleKpiTile(
                label: '미배정 계약',
                value: '${NumberFormat('#,###').format(summary.unmappedCount)}건',
                subText: summary.unmappedCount > 0 ? '상담사 배정 필요' : '전건 배정 완료',
                accentColor: summary.unmappedCount > 0
                    ? const Color(0xFFF59E0B) // Amber
                    : context.colors.textMuted,
                icon: Icons.error_outline_rounded,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildSingleKpiTile(
                label: '1위 실적 상담사',
                value: summary.topAgentName ?? '-',
                subText: summary.topAgentCount > 0
                    ? '${summary.topAgentCount}건 달성 (${summary.topAgentTeam ?? ""})'
                    : 'MGM ${summary.mgmCount}건 연계',
                accentColor: const Color(0xFF8B5CF6), // Violet
                icon: Icons.emoji_events_outlined,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildSingleKpiTile({
    required String label,
    required String value,
    required String subText,
    required Color accentColor,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(
          color: accentColor.withAlpha(60),
          width: 0.8,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label,
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontSize: 11,
                ),
              ),
              Icon(icon, size: 14, color: accentColor),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: AppTextStyles.titleSm.copyWith(
              color: accentColor,
              fontWeight: FontWeight.bold,
              fontSize: 13.5,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 2),
          Text(
            subText,
            style: AppTextStyles.caption.copyWith(
              color: context.colors.textSecond,
              fontSize: 10,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  /// 검색창 & 필터 칩스 & 배정 버튼 바
  Widget _buildFilterAndSearchBar(SelectedProject project, SalesPerformanceSummary summary) {
    final canManage = ref.can(Perm.salesManage, projectSlug: project.slug);
    final statusFilter = ref.watch(salesMappingStatusFilterProvider);
    final teams = ref.watch(salesTeamsProvider).valueOrNull ?? [];
    final selectedTeamId = ref.watch(salesTeamFilterProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 검색창
        Container(
          height: 38,
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.zero,
            border: Border.all(color: context.colors.border, width: 0.8),
          ),
          child: Row(
            children: [
              const SizedBox(width: 10),
              Icon(Icons.search_rounded, size: 18, color: context.colors.textMuted),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _searchController,
                  onChanged: _onSearchChanged,
                  style: const TextStyle(fontSize: 12.5),
                  decoration: InputDecoration(
                    hintText: '계약자 / 동·호수 / 상담사 / MGM 검색',
                    hintStyle: TextStyle(fontSize: 12, color: context.colors.textMuted),
                    border: InputBorder.none,
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
              if (_searchController.text.isNotEmpty)
                IconButton(
                  icon: const Icon(Icons.clear_rounded, size: 16),
                  onPressed: () {
                    _searchController.clear();
                    ref.read(salesSearchQueryProvider.notifier).state = '';
                  },
                  color: context.colors.textMuted,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                ),
            ],
          ),
        ),
        const SizedBox(height: 10),

        // 필터 칩스 + 신규 배정 버튼
        Row(
          children: [
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildFilterChip(
                      label: '전체 ${summary.totalContracts}',
                      isSelected: statusFilter == SalesMappingStatusFilter.all,
                      onTap: () => ref.read(salesMappingStatusFilterProvider.notifier).state =
                          SalesMappingStatusFilter.all,
                    ),
                    const SizedBox(width: 6),
                    _buildFilterChip(
                      label: '배정 완료 ${summary.mappedCount}',
                      isSelected: statusFilter == SalesMappingStatusFilter.mapped,
                      onTap: () => ref.read(salesMappingStatusFilterProvider.notifier).state =
                          SalesMappingStatusFilter.mapped,
                      activeColor: const Color(0xFF10B981),
                    ),
                    const SizedBox(width: 6),
                    _buildFilterChip(
                      label: '미배정 ${summary.unmappedCount}',
                      isSelected: statusFilter == SalesMappingStatusFilter.unmapped,
                      onTap: () => ref.read(salesMappingStatusFilterProvider.notifier).state =
                          SalesMappingStatusFilter.unmapped,
                      activeColor: const Color(0xFFF59E0B),
                    ),
                    if (teams.isNotEmpty) ...[
                      const SizedBox(width: 8),
                      // 팀 드롭다운 필터
                      PopupMenuButton<int?>(
                        initialValue: selectedTeamId,
                        onSelected: (teamId) {
                          ref.read(salesTeamFilterProvider.notifier).state = teamId;
                        },
                        itemBuilder: (ctx) => [
                          const PopupMenuItem<int?>(
                            value: null,
                            child: Text('전체 팀', style: TextStyle(fontSize: 12)),
                          ),
                          ...teams.map((t) => PopupMenuItem<int?>(
                                value: t.id,
                                child: Text(t.name, style: const TextStyle(fontSize: 12)),
                              )),
                        ],
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
                          decoration: BoxDecoration(
                            color: selectedTeamId != null
                                ? const Color(0xFF8B5CF6).withAlpha(20)
                                : context.colors.bgCard,
                            border: Border.all(
                              color: selectedTeamId != null
                                  ? const Color(0xFF8B5CF6)
                                  : context.colors.border,
                              width: 0.8,
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                selectedTeamId != null
                                    ? teams.firstWhere((t) => t.id == selectedTeamId).name
                                    : '팀 필터',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: selectedTeamId != null ? FontWeight.bold : FontWeight.normal,
                                  color: selectedTeamId != null
                                      ? const Color(0xFF8B5CF6)
                                      : context.colors.textSecond,
                                ),
                              ),
                              const SizedBox(width: 3),
                              Icon(Icons.arrow_drop_down, size: 16, color: context.colors.textMuted),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            if (canManage) ...[
              const SizedBox(width: 8),
              // + 담당자 배정 버튼
              Material(
                color: const Color(0xFF8B5CF6),
                shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                child: InkWell(
                  onTap: () => showContractAgentFormSheet(
                    context,
                    projectId: project.realProjectId,
                  ),
                  child: const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.add, size: 14, color: Colors.white),
                        SizedBox(width: 4),
                        Text(
                          '배정',
                          style: TextStyle(
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
            ],
          ],
        ),
      ],
    );
  }

  Widget _buildFilterChip({
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
    Color activeColor = const Color(0xFF8B5CF6),
  }) {
    return Material(
      color: isSelected ? activeColor.withAlpha(25) : context.colors.bgCard,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.zero,
        side: BorderSide(
          color: isSelected ? activeColor : context.colors.border,
          width: 0.8,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          child: Text(
            label,
            style: TextStyle(
              fontSize: 11.5,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              color: isSelected ? activeColor : context.colors.textSecond,
            ),
          ),
        ),
      ),
    );
  }

  /// 계약 실적 개별 카드 위젯
  Widget _buildPerformanceCardItem(
    CombinedContractPerformanceItem item,
    SelectedProject project,
    List<SalesPersonModel> persons,
  ) {
    final canManage = ref.can(Perm.salesManage, projectSlug: project.slug);
    final isMapped = item.isMapped;
    SalesPersonModel? matchedPerson;
    if (isMapped && item.mapping?.salesPerson != null) {
      for (final p in persons) {
        if (p.id == item.mapping!.salesPerson) {
          matchedPerson = p;
          break;
        }
      }
    }

    final hasPersonPhone = matchedPerson?.phone != null && matchedPerson!.phone!.isNotEmpty;
    final hasMgmPhone = item.mgmPhone != null && item.mgmPhone!.isNotEmpty;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(
          color: isMapped
              ? const Color(0xFF8B5CF6).withAlpha(50)
              : const Color(0xFFF59E0B).withAlpha(60),
          width: 0.8,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 상단 행: 계약 라벨 + 상태 뱃지
            Row(
              children: [
                Icon(
                  Icons.assignment_outlined,
                  size: 15,
                  color: isMapped ? const Color(0xFF8B5CF6) : const Color(0xFFF59E0B),
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    item.contractLabel,
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: isMapped
                        ? const Color(0xFF8B5CF6).withAlpha(15)
                        : const Color(0xFFF59E0B).withAlpha(20),
                    border: Border.all(
                      color: isMapped
                          ? const Color(0xFF8B5CF6).withAlpha(70)
                          : const Color(0xFFF59E0B).withAlpha(80),
                      width: 0.8,
                    ),
                  ),
                  child: Text(
                    isMapped ? '배정완료' : '미배정',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: isMapped ? const Color(0xFF8B5CF6) : const Color(0xFFD97706),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Divider(color: context.colors.borderSubtle, height: 1),
            const SizedBox(height: 8),

            // 내용 영역
            if (isMapped) ...[
              // 담당 상담사 & 소속 팀
              Row(
                children: [
                  Icon(Icons.person_outline_rounded, size: 14, color: context.colors.textMuted),
                  const SizedBox(width: 5),
                  Text(
                    item.salesPersonName ?? '담당자 미지정',
                    style: AppTextStyles.bodySecond.copyWith(
                      color: const Color(0xFF8B5CF6),
                      fontWeight: FontWeight.bold,
                      fontSize: 12.5,
                    ),
                  ),
                  if (item.teamName != null && item.teamName!.isNotEmpty) ...[
                    const SizedBox(width: 6),
                    Text(
                      '(${item.teamName})',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                        fontSize: 11.5,
                      ),
                    ),
                  ],
                  if (item.policyName != null && item.policyName!.isNotEmpty) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                      decoration: BoxDecoration(
                        color: context.colors.bgSurface,
                        border: Border.all(color: context.colors.border, width: 0.7),
                      ),
                      child: Text(
                        item.policyName!,
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textSecond,
                          fontSize: 10,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
              if (item.contractDate != null && item.contractDate!.isNotEmpty) ...[
                const SizedBox(height: 4),
                Row(
                  children: [
                    Icon(Icons.event_available_outlined, size: 13, color: context.colors.textMuted),
                    const SizedBox(width: 5),
                    Text(
                      '성과인정일: ${item.contractDate}',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textSecond,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ],
              if (item.mgmName != null && item.mgmName!.isNotEmpty) ...[
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Icon(Icons.handshake_outlined, size: 13, color: Color(0xFF06B6D4)),
                    const SizedBox(width: 5),
                    Expanded(
                      child: Text(
                        'MGM: ${item.mgmName}'
                        '${item.mgmPhone != null && item.mgmPhone!.isNotEmpty ? ' (${item.mgmPhone})' : ''}'
                        '${item.mgmFee > 0 ? ' · 수수료: ${NumberFormat('#,###').format(item.mgmFee)}원' : ''}',
                        style: AppTextStyles.caption.copyWith(
                          color: const Color(0xFF0891B2),
                          fontSize: 11,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],
              if (item.note != null && item.note!.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  '비고: ${item.note}',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 11,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ] else ...[
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Text(
                  '영업 담당 상담사가 아직 배정되지 않은 분양 계약입니다.',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 11.5,
                  ),
                ),
              ),
            ],

            const SizedBox(height: 10),
            Divider(color: context.colors.borderSubtle, height: 1),
            const SizedBox(height: 6),

            // 하단 버튼 바: 전화걸기 & 배정/수정 버튼
            Row(
              children: [
                if (isMapped && hasPersonPhone)
                  InkWell(
                    onTap: () => _makePhoneCall(matchedPerson!.phone!, targetName: item.salesPersonName),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.phone_outlined, size: 14, color: Color(0xFF10B981)),
                          const SizedBox(width: 4),
                          Text(
                            '상담사 통화',
                            style: AppTextStyles.caption.copyWith(
                              color: const Color(0xFF10B981),
                              fontWeight: FontWeight.bold,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                if (isMapped && hasMgmPhone) ...[
                  const SizedBox(width: 8),
                  InkWell(
                    onTap: () => _makePhoneCall(item.mgmPhone!, targetName: 'MGM ${item.mgmName}'),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.phone_outlined, size: 14, color: Color(0xFF06B6D4)),
                          const SizedBox(width: 4),
                          Text(
                            'MGM 통화',
                            style: AppTextStyles.caption.copyWith(
                              color: const Color(0xFF06B6D4),
                              fontWeight: FontWeight.bold,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
                const Spacer(),
                if (canManage) ...[
                  if (isMapped)
                    OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: context.colors.textPrimary,
                        side: BorderSide(color: context.colors.border, width: 0.8),
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        minimumSize: Size.zero,
                      ),
                      icon: const Icon(Icons.edit_outlined, size: 12),
                      label: const Text('배정 수정', style: TextStyle(fontSize: 11.5)),
                      onPressed: () => showContractAgentFormSheet(
                        context,
                        projectId: project.realProjectId,
                        initialContractId: item.contractId,
                        initialContractLabel: item.contractLabel,
                        existingMapping: item.mapping,
                      ),
                    )
                  else
                    FilledButton.icon(
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFF8B5CF6),
                        foregroundColor: Colors.white,
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        minimumSize: Size.zero,
                      ),
                      icon: const Icon(Icons.person_add_alt_1_outlined, size: 12),
                      label: const Text('담당자 배정', style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.bold)),
                      onPressed: () => showContractAgentFormSheet(
                        context,
                        projectId: project.realProjectId,
                        initialContractId: item.contractId,
                        initialContractLabel: item.contractLabel,
                      ),
                    ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ═════════════════════════════════════════════════════════════════
  // 💰 2. 수수료 정산 관리 (Settlement)
  // ═════════════════════════════════════════════════════════════════

  Future<void> _handleGeneratePayouts(SettlementPeriodModel period) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Row(
          children: [
            const Icon(Icons.calculate_outlined, size: 20, color: Color(0xFF06B6D4)),
            const SizedBox(width: 8),
            Text(
              '수수료 정산 자동 계산',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Text(
          '【${period.title}】\n(대상 기간: ${period.startDate} ~ ${period.endDate})\n\n해당 기간 동안 발생한 계약 실적과 직책별 수수료 정책, 미상계 환수금을 집계하여 개인별 수수료 명세를 자동 산출하시겠습니까?\n\n※ 이미 산출된 명세가 있는 경우 최신 실적으로 재계산됩니다.',
          style: AppTextStyles.bodySm.copyWith(
            color: context.colors.textSecond,
            height: 1.4,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF06B6D4),
              foregroundColor: Colors.white,
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('정산 계산 실행'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    try {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('수수료 실적 및 정책을 집계하여 정산 계산 중입니다...'),
          duration: Duration(seconds: 1),
        ),
      );
      final repo = ref.read(salesRepositoryProvider);
      final res = await repo.generatePayouts(period.id);
      ref.invalidate(settlementPeriodsProvider);
      ref.invalidate(commissionPayoutsProvider);

      if (!mounted) return;
      final msg = res['message'] as String? ?? '수수료 정산 계산이 완료되었습니다.';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(msg),
          backgroundColor: const Color(0xFF10B981),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('정산 계산 실패: $e'),
          backgroundColor: context.colors.error,
        ),
      );
    }
  }

  Future<void> _handleConfirmSettlement(SettlementPeriodModel period) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Row(
          children: [
            const Icon(Icons.verified_outlined, size: 20, color: Color(0xFF10B981)),
            const SizedBox(width: 8),
            Text(
              '수수료 정산 확정',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Text(
          '【${period.title}】\n\n정산 내역을 확정하시겠습니까?\n\n확정 후에는 정산 재실행이 제한되며, 수수료 지급 집행 및 이체 대장 관리 단계로 전환됩니다.',
          style: AppTextStyles.bodySm.copyWith(
            color: context.colors.textSecond,
            height: 1.4,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF10B981),
              foregroundColor: Colors.white,
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('정산 확정하기'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    try {
      final repo = ref.read(salesRepositoryProvider);
      await repo.confirmSettlement(period.id);
      ref.invalidate(settlementPeriodsProvider);
      ref.invalidate(commissionPayoutsProvider);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('수수료 정산이 성공적으로 확정되었습니다.'),
          backgroundColor: Color(0xFF10B981),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('정산 확정 실패: $e'),
          backgroundColor: context.colors.error,
        ),
      );
    }
  }

  /// 2. 수수료 정산 관리 뷰 (회차별 실적 집계 + 2×2 KPI + 개인별 정산 명세 + 3.3% 원천세 계산 + 정산 실행/확정)
  Widget _buildSettlementView(SelectedProject project) {
    final periodsAsync = ref.watch(settlementPeriodsProvider);
    final currentPeriod = ref.watch(currentSettlementPeriodProvider);
    final payoutsAsync = ref.watch(commissionPayoutsProvider);
    final filteredPayouts = ref.watch(filteredCommissionPayoutsProvider);

    return RefreshIndicator(
      color: const Color(0xFF06B6D4),
      onRefresh: () async {
        ref.invalidate(settlementPeriodsProvider);
        ref.invalidate(commissionPayoutsProvider);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 1. 상단 안내 배너
          _buildInfoBanner(
            title: '수수료 정산 관리',
            subtitle: '정산 주기 회차별 계약 실적 집계, 3.3% 원천세(소득세+지방세) 계산 및 환수금 상계를 관리합니다.',
            icon: Icons.calculate_outlined,
            color: const Color(0xFF06B6D4),
          ),
          const SizedBox(height: 14),

          // 2. 정산 회차 선택기 & 관리 액션 바
          periodsAsync.when(
            loading: () => Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.zero,
                border: Border.all(color: context.colors.border),
              ),
              child: const Center(
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF06B6D4)),
                ),
              ),
            ),
            error: (err, _) => Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.zero,
                border: Border.all(color: context.colors.error.withAlpha(80)),
              ),
              child: Row(
                children: [
                  Icon(Icons.error_outline_rounded, size: 18, color: context.colors.error),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '정산 회차 데이터를 불러오지 못했습니다: $err',
                      style: AppTextStyles.caption.copyWith(color: context.colors.error),
                    ),
                  ),
                ],
              ),
            ),
            data: (periods) => _buildPeriodSection(project, periods, currentPeriod),
          ),
          const SizedBox(height: 14),

          // 3. 2×2 정산 KPI 요약 대시보드
          _buildSettlementKpiSection(currentPeriod),
          const SizedBox(height: 14),

          // 4. 검색 & 상태/직책 필터 바
          _buildSettlementFilterBar(currentPeriod),
          const SizedBox(height: 14),

          // 5. 개인별 수수료 지급 명세 카드 리스트
          _buildSettlementPayoutListSection(project, currentPeriod, payoutsAsync, filteredPayouts),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  /// 정산 회차 선택기 및 회차 정보 / 액션 바
  Widget _buildPeriodSection(
    SelectedProject project,
    List<SettlementPeriodModel> periods,
    SettlementPeriodModel? currentPeriod,
  ) {
    final canSettle = ref.can(Perm.salesSettle, projectSlug: project.slug);

    if (periods.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(color: const Color(0xFF06B6D4).withAlpha(80), width: 0.8),
        ),
        child: Column(
          children: [
            Icon(Icons.event_note_outlined, size: 36, color: context.colors.textMuted),
            const SizedBox(height: 10),
            Text(
              '등록된 정산 회차가 없습니다',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              '정산 대상 기간(시작/종료일)과 지급 예정일을 설정하여 첫 정산 회차를 생성하세요.',
              textAlign: TextAlign.center,
              style: AppTextStyles.caption.copyWith(color: context.colors.textSecond),
            ),
            if (canSettle) ...[
              const SizedBox(height: 14),
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF06B6D4),
                  side: const BorderSide(color: Color(0xFF06B6D4)),
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                ),
                icon: const Icon(Icons.add_rounded, size: 16),
                label: Text('새 정산 회차 등록', style: AppTextStyles.caption),
                onPressed: () => showPeriodFormSheet(context, projectId: project.realProjectId),
              ),
            ],
          ],
        ),
      );
    }

    final period = currentPeriod ?? periods.first;

    Color statusColor;
    if (period.isCompleted) {
      statusColor = const Color(0xFF10B981); // Emerald
    } else if (period.isConfirmed) {
      statusColor = const Color(0xFF0284C7); // Blue
    } else {
      statusColor = const Color(0xFFF59E0B); // Amber
    }

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 회차 헤더 & 선택기
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: context.colors.bgSurface,
              border: Border(
                bottom: BorderSide(color: context.colors.borderSubtle, width: 0.8),
              ),
            ),
            child: Row(
              children: [
                const Icon(Icons.calendar_month_outlined, size: 18, color: Color(0xFF06B6D4)),
                const SizedBox(width: 8),
                Expanded(
                  child: PopupMenuButton<int>(
                    tooltip: '정산 회차 전환',
                    padding: EdgeInsets.zero,
                    onSelected: (id) {
                      ref.read(selectedPeriodIdProvider.notifier).state = id;
                      ref.invalidate(commissionPayoutsProvider);
                    },
                    itemBuilder: (ctx) => periods.map((p) {
                      final isSelected = p.id == period.id;
                      Color pColor = p.isCompleted
                          ? const Color(0xFF10B981)
                          : p.isConfirmed
                              ? const Color(0xFF0284C7)
                              : const Color(0xFFF59E0B);
                      return PopupMenuItem<int>(
                        value: p.id,
                        child: Row(
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: BoxDecoration(color: pColor, shape: BoxShape.circle),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                p.title,
                                style: AppTextStyles.bodySm.copyWith(
                                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                  color: isSelected ? const Color(0xFF06B6D4) : context.colors.textPrimary,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                              decoration: BoxDecoration(
                                color: pColor.withAlpha(20),
                                borderRadius: BorderRadius.zero,
                                border: Border.all(color: pColor.withAlpha(60), width: 0.5),
                              ),
                              child: Text(
                                p.statusDisplay ?? '작성 중',
                                style: AppTextStyles.caption.copyWith(color: pColor, fontSize: 10),
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Flexible(
                          child: Text(
                            period.title,
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(Icons.arrow_drop_down, size: 20, color: context.colors.textMuted),
                      ],
                    ),
                  ),
                ),
                // 회차 상태 뱃지
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: statusColor.withAlpha(25),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: statusColor.withAlpha(100), width: 0.8),
                  ),
                  child: Text(
                    period.statusDisplay ?? '작성 중',
                    style: AppTextStyles.caption.copyWith(
                      color: statusColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                    ),
                  ),
                ),
                if (canSettle) ...[
                  const SizedBox(width: 6),
                  // 회차 정보 수정 버튼
                  IconButton(
                    icon: const Icon(Icons.edit_outlined, size: 16),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                    tooltip: '회차 설정 수정',
                    color: context.colors.textMuted,
                    onPressed: () => showPeriodFormSheet(
                      context,
                      projectId: project.realProjectId,
                      existingPeriod: period,
                    ),
                  ),
                ],
              ],
            ),
          ),

          // 회차 일자 정보 바
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 8),
            child: Row(
              children: [
                Expanded(
                  child: Row(
                    children: [
                      Icon(Icons.date_range, size: 14, color: context.colors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        '대상: ${period.startDate} ~ ${period.endDate}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textSecond,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                Row(
                  children: [
                    Icon(Icons.event_available, size: 14, color: context.colors.textMuted),
                    const SizedBox(width: 4),
                    Text(
                      '지급예정: ${period.payoutDate ?? '-'}',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textSecond,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          Divider(height: 1, thickness: 0.5, color: context.colors.borderSubtle),

          // 회차 액션 버튼 바
          Padding(
            padding: const EdgeInsets.all(10),
            child: Row(
              children: [
                // [+ 새 회차 등록]
                if (canSettle)
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: context.colors.textSecond,
                      side: BorderSide(color: context.colors.border),
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      minimumSize: Size.zero,
                    ),
                    icon: const Icon(Icons.add, size: 14),
                    label: const Text('회차 추가', style: TextStyle(fontSize: 12)),
                    onPressed: () => showPeriodFormSheet(context, projectId: project.realProjectId),
                  ),
                const Spacer(),

                // [⚡ 정산 계산 실행] 버튼 (작성 중일 때 활성화)
                if (canSettle && period.isDraft) ...[
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF06B6D4),
                      foregroundColor: Colors.white,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      minimumSize: Size.zero,
                    ),
                    icon: const Icon(Icons.auto_mode_rounded, size: 14),
                    label: const Text('정산 자동 계산', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    onPressed: () => _handleGeneratePayouts(period),
                  ),
                  const SizedBox(width: 8),
                ],

                // [✓ 정산 확정] 버튼 (작성 중이고 집계된 내역이 있을 때)
                if (canSettle && period.isDraft && (period.payoutCount > 0 || period.totalGrossAmount > 0)) ...[
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF10B981),
                      foregroundColor: Colors.white,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      minimumSize: Size.zero,
                    ),
                    icon: const Icon(Icons.check_circle_outline, size: 14),
                    label: const Text('정산 확정', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    onPressed: () => _handleConfirmSettlement(period),
                  ),
                ],

                // 확정 완료 안내 뱃지
                if (period.isConfirmed) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0284C7).withAlpha(20),
                      borderRadius: BorderRadius.zero,
                      border: Border.all(color: const Color(0xFF0284C7).withAlpha(80), width: 0.8),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.verified, size: 14, color: Color(0xFF0284C7)),
                        SizedBox(width: 4),
                        Text(
                          '정산 확정 완료 (지급 진행 가능)',
                          style: TextStyle(color: Color(0xFF0284C7), fontSize: 11, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ),
                ],

                // 지급 완료 안내 뱃지
                if (period.isCompleted) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF10B981).withAlpha(20),
                      borderRadius: BorderRadius.zero,
                      border: Border.all(color: const Color(0xFF10B981).withAlpha(80), width: 0.8),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.done_all_rounded, size: 14, color: Color(0xFF10B981)),
                        SizedBox(width: 4),
                        Text(
                          '지급 집행 완료',
                          style: TextStyle(color: Color(0xFF10B981), fontSize: 11, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 2×2 수수료 정산 KPI 요약 대시보드
  Widget _buildSettlementKpiSection(SettlementPeriodModel? currentPeriod) {
    if (currentPeriod == null) {
      return Column(
        children: [
          Row(
            children: [
              Expanded(
                child: _buildSingleKpiTile(
                  label: '정산 대상 실적',
                  value: '0건',
                  subText: '지급 대상자: 0명',
                  accentColor: const Color(0xFF06B6D4),
                  icon: Icons.assignment_turned_in_outlined,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildSingleKpiTile(
                  label: '총 지급액 (세전)',
                  value: '0원',
                  subText: '수수료+보너스+기본급-공제',
                  accentColor: const Color(0xFF8B5CF6),
                  icon: Icons.payments_outlined,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: _buildSingleKpiTile(
                  label: '원천징수 세액 (3.3%)',
                  value: '0원',
                  subText: '소득세 3% + 지방세 0.3%',
                  accentColor: const Color(0xFFEF4444),
                  icon: Icons.receipt_long_outlined,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildSingleKpiTile(
                  label: '총 실지급액 (세후)',
                  value: '0원',
                  subText: '실제 이체 필요 총액',
                  accentColor: const Color(0xFF10B981),
                  icon: Icons.account_balance_wallet_outlined,
                ),
              ),
            ],
          ),
        ],
      );
    }

    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _buildSingleKpiTile(
                label: '정산 대상 실적',
                value: '${NumberFormat('#,###').format(currentPeriod.totalContracts)}건',
                subText: '지급 대상자: ${NumberFormat('#,###').format(currentPeriod.payoutCount)}명',
                accentColor: const Color(0xFF06B6D4), // Sky / Cyan
                icon: Icons.assignment_turned_in_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildSingleKpiTile(
                label: '총 지급액 (세전)',
                value: '${NumberFormat('#,###').format(currentPeriod.totalGrossAmount)}원',
                subText: '수수료+보너스+기본급-공제',
                accentColor: const Color(0xFF8B5CF6), // Violet
                icon: Icons.payments_outlined,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _buildSingleKpiTile(
                label: '원천징수 세액 (3.3%)',
                value: '${NumberFormat('#,###').format(currentPeriod.totalTaxAmount)}원',
                subText: '소득세 3% + 지방세 0.3%',
                accentColor: const Color(0xFFEF4444), // Red
                icon: Icons.receipt_long_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildSingleKpiTile(
                label: '총 실지급액 (세후)',
                value: '${NumberFormat('#,###').format(currentPeriod.totalNetAmount)}원',
                subText: '실제 이체 필요 총액',
                accentColor: const Color(0xFF10B981), // Emerald
                icon: Icons.account_balance_wallet_outlined,
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// 검색창 & 상태/직책 필터 바
  Widget _buildSettlementFilterBar(SettlementPeriodModel? currentPeriod) {
    final payStatusFilter = ref.watch(settlementPayStatusFilterProvider);
    final dutyFilter = ref.watch(settlementDutyFilterProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 검색 필드
        Container(
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.zero,
            border: Border.all(color: context.colors.border, width: 0.8),
          ),
          child: TextField(
            controller: _settlementSearchController,
            onChanged: _onSettlementSearchChanged,
            style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
            decoration: InputDecoration(
              isDense: true,
              hintText: '성명, 소속팀, 예금주 검색...',
              hintStyle: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
              prefixIcon: Icon(Icons.search, size: 18, color: context.colors.textMuted),
              suffixIcon: _settlementSearchController.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear, size: 16),
                      onPressed: () {
                        _settlementSearchController.clear();
                        ref.read(settlementSearchQueryProvider.notifier).state = '';
                      },
                    )
                  : null,
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            ),
          ),
        ),
        const SizedBox(height: 8),

        // 상태 필터 & 직책 필터 칩 행
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              Text(
                '지급상태: ',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
              _buildFilterChip(
                label: '전체',
                isSelected: payStatusFilter.isEmpty,
                onTap: () => ref.read(settlementPayStatusFilterProvider.notifier).state = '',
              ),
              const SizedBox(width: 4),
              _buildFilterChip(
                label: '대기',
                isSelected: payStatusFilter == '1',
                onTap: () => ref.read(settlementPayStatusFilterProvider.notifier).state = '1',
                activeColor: const Color(0xFFF59E0B),
              ),
              const SizedBox(width: 4),
              _buildFilterChip(
                label: '승인',
                isSelected: payStatusFilter == '2',
                onTap: () => ref.read(settlementPayStatusFilterProvider.notifier).state = '2',
                activeColor: const Color(0xFF0284C7),
              ),
              const SizedBox(width: 4),
              _buildFilterChip(
                label: '완료',
                isSelected: payStatusFilter == '3',
                onTap: () => ref.read(settlementPayStatusFilterProvider.notifier).state = '3',
                activeColor: const Color(0xFF10B981),
              ),
              const SizedBox(width: 4),
              _buildFilterChip(
                label: '보류',
                isSelected: payStatusFilter == '4',
                onTap: () => ref.read(settlementPayStatusFilterProvider.notifier).state = '4',
                activeColor: const Color(0xFFEF4444),
              ),
              const SizedBox(width: 12),
              Container(width: 1, height: 14, color: context.colors.borderSubtle),
              const SizedBox(width: 12),
              Text(
                '직책: ',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
              _buildFilterChip(
                label: '전체',
                isSelected: dutyFilter.isEmpty,
                onTap: () => ref.read(settlementDutyFilterProvider.notifier).state = '',
              ),
              const SizedBox(width: 4),
              _buildFilterChip(
                label: '상담사',
                isSelected: dutyFilter == '상담사',
                onTap: () => ref.read(settlementDutyFilterProvider.notifier).state =
                    dutyFilter == '상담사' ? '' : '상담사',
                activeColor: const Color(0xFF10B981),
              ),
              const SizedBox(width: 4),
              _buildFilterChip(
                label: '팀장',
                isSelected: dutyFilter == '팀장',
                onTap: () => ref.read(settlementDutyFilterProvider.notifier).state =
                    dutyFilter == '팀장' ? '' : '팀장',
                activeColor: const Color(0xFF0284C7),
              ),
              const SizedBox(width: 4),
              _buildFilterChip(
                label: '본부장',
                isSelected: dutyFilter == '본부장',
                onTap: () => ref.read(settlementDutyFilterProvider.notifier).state =
                    dutyFilter == '본부장' ? '' : '본부장',
                activeColor: const Color(0xFF8B5CF6),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// 개인별 수수료 지급 명세 카드 리스트 (정산 탭)
  Widget _buildSettlementPayoutListSection(
    SelectedProject project,
    SettlementPeriodModel? currentPeriod,
    AsyncValue<List<CommissionPayoutModel>> payoutsAsync,
    List<CommissionPayoutModel> filteredPayouts,
  ) {
    if (currentPeriod == null) {
      return const SizedBox.shrink();
    }

    return payoutsAsync.when(
      loading: () => Container(
        padding: const EdgeInsets.all(40),
        child: const Center(
          child: SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: Color(0xFF06B6D4),
            ),
          ),
        ),
      ),
      error: (err, _) => Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(color: context.colors.error.withAlpha(80)),
        ),
        child: Row(
          children: [
            Icon(Icons.error_outline_rounded, size: 18, color: context.colors.error),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '수수료 정산 명세를 불러오지 못했습니다: $err',
                style: AppTextStyles.caption.copyWith(color: context.colors.error),
              ),
            ),
          ],
        ),
      ),
      data: (allPayouts) {
        if (allPayouts.isEmpty) {
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.zero,
              border: Border.all(color: context.colors.border),
            ),
            child: Column(
              children: [
                Icon(Icons.receipt_long_outlined, size: 40, color: context.colors.textMuted),
                const SizedBox(height: 12),
                Text(
                  '산출된 수수료 정산 명세가 없습니다',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  periodIsDraft(currentPeriod)
                      ? '[정산 자동 계산] 버튼을 누르면 해당 기간 내 계약 실적과 수수료 정책을 집계하여 개인별 수수료 명세가 자동 산출됩니다.'
                      : '해당 회차에 정산 대상 인원 또는 실적이 없습니다.',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.caption.copyWith(color: context.colors.textSecond),
                ),
                if (periodIsDraft(currentPeriod)) ...[
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF06B6D4),
                      foregroundColor: Colors.white,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    ),
                    icon: const Icon(Icons.auto_mode_rounded, size: 16),
                    label: const Text('지금 정산 계산 실행', style: TextStyle(fontWeight: FontWeight.bold)),
                    onPressed: () => _handleGeneratePayouts(currentPeriod),
                  ),
                ],
              ],
            ),
          );
        }

        if (filteredPayouts.isEmpty) {
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 20),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.zero,
              border: Border.all(color: context.colors.border),
            ),
            child: Column(
              children: [
                Icon(Icons.filter_list_off_outlined, size: 36, color: context.colors.textMuted),
                const SizedBox(height: 10),
                Text(
                  '조건에 일치하는 정산 명세가 없습니다',
                  style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: context.colors.textSecond,
                    side: BorderSide(color: context.colors.border),
                    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  ),
                  onPressed: () {
                    _settlementSearchController.clear();
                    ref.read(settlementSearchQueryProvider.notifier).state = '';
                    ref.read(settlementPayStatusFilterProvider.notifier).state = '';
                    ref.read(settlementDutyFilterProvider.notifier).state = '';
                  },
                  child: const Text('검색 및 필터 초기화'),
                ),
              ],
            ),
          );
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '개인별 정산 명세 (${filteredPayouts.length}명)',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  '카드를 누르면 상세/세금 공제 내역 확인',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: filteredPayouts.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (ctx, index) {
                final item = filteredPayouts[index];
                return _buildSettlementPayoutCard(context, item, project);
              },
            ),
          ],
        );
      },
    );
  }

  bool periodIsDraft(SettlementPeriodModel period) => period.isDraft || period.status == '1';

  /// 개인별 수수료 지급 명세 카드
  Widget _buildSettlementPayoutCard(BuildContext context, CommissionPayoutModel item, SelectedProject project) {
    Color statusColor;
    switch (item.payStatus) {
      case '2': // 승인 완료
        statusColor = const Color(0xFF0284C7);
        break;
      case '3': // 지급 완료
        statusColor = const Color(0xFF10B981);
        break;
      case '4': // 지급 보류
        statusColor = const Color(0xFFEF4444);
        break;
      case '1': // 지급 대기
      default:
        statusColor = const Color(0xFFF59E0B);
        break;
    }

    Color dutyColor;
    if (item.dutyDisplay?.contains('본부장') ?? false) {
      dutyColor = const Color(0xFF8B5CF6);
    } else if (item.dutyDisplay?.contains('팀장') ?? false) {
      dutyColor = const Color(0xFF0284C7);
    } else {
      dutyColor = const Color(0xFF10B981);
    }

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => showPayoutDetailSheet(context, payout: item, projectSlug: project.slug),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. 헤더: 성명 + 직책 + 소속팀 + 상태 뱃지
                Row(
                  children: [
                    Text(
                      item.salesPersonName ?? '미지정',
                      style: AppTextStyles.titleSm.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: dutyColor.withAlpha(20),
                        borderRadius: BorderRadius.zero,
                        border: Border.all(color: dutyColor.withAlpha(70), width: 0.5),
                      ),
                      child: Text(
                        item.dutyDisplay ?? '상담사',
                        style: AppTextStyles.caption.copyWith(
                          color: dutyColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 10,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        item.teamName ?? '-',
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                      decoration: BoxDecoration(
                        color: statusColor.withAlpha(25),
                        borderRadius: BorderRadius.zero,
                        border: Border.all(color: statusColor.withAlpha(90), width: 0.8),
                      ),
                      child: Text(
                        item.payStatusDisplay ?? '지급 대기',
                        style: AppTextStyles.caption.copyWith(
                          color: statusColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),

                // 2. 세후 실지급액 강조
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text(
                      '세후 실지급액',
                      style: AppTextStyles.caption.copyWith(color: context.colors.textSecond),
                    ),
                    Text(
                      '₩ ${NumberFormat('#,###').format(item.netAmount)}',
                      style: AppTextStyles.titleLg.copyWith(
                        color: const Color(0xFF10B981),
                        fontWeight: FontWeight.bold,
                        letterSpacing: -0.5,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                // 3. 정산 세부 요약 바
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: context.colors.bgSurface,
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildMiniMetric('계약 건수', '${item.contractCount}건', context.colors.textPrimary),
                      Container(width: 0.8, height: 16, color: context.colors.borderSubtle),
                      _buildMiniMetric('세전 총액', '₩${NumberFormat('#,###').format(item.grossAmount)}', context.colors.textPrimary),
                      Container(width: 0.8, height: 16, color: context.colors.borderSubtle),
                      _buildMiniMetric('원천세(3.3%)', '-₩${NumberFormat('#,###').format(item.totalTax)}', const Color(0xFFEF4444)),
                    ],
                  ),
                ),

                // 4. 보너스/공제/기본급 태그 (있을 때만)
                if (item.basePay > 0 || item.bonusAmount > 0 || item.deductionAmount > 0) ...[
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    children: [
                      if (item.basePay > 0)
                        _buildSubTag('기본급', '₩${NumberFormat('#,###').format(item.basePay)}', const Color(0xFF0284C7)),
                      if (item.bonusAmount > 0)
                        _buildSubTag('보너스', '+₩${NumberFormat('#,###').format(item.bonusAmount)}', const Color(0xFF10B981)),
                      if (item.deductionAmount > 0)
                        _buildSubTag('환수/공제', '-₩${NumberFormat('#,###').format(item.deductionAmount)}', const Color(0xFFEF4444)),
                    ],
                  ),
                ],
                const SizedBox(height: 8),

                // 5. 계좌 정보 및 상세 링크
                Row(
                  children: [
                    Icon(Icons.account_balance_rounded, size: 13, color: context.colors.textMuted),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        '${item.bankName ?? '-'} ${item.accountNumber ?? '-'} (${item.accountHolder ?? '-'})',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textSecond,
                          fontSize: 11,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '상세보기',
                          style: AppTextStyles.caption.copyWith(
                            color: const Color(0xFF06B6D4),
                            fontWeight: FontWeight.w600,
                            fontSize: 11,
                          ),
                        ),
                        const Icon(Icons.chevron_right, size: 14, color: Color(0xFF06B6D4)),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMiniMetric(String label, String value, Color valueColor) {
    return Column(
      children: [
        Text(
          label,
          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: AppTextStyles.caption.copyWith(
            color: valueColor,
            fontWeight: FontWeight.bold,
            fontSize: 11,
          ),
        ),
      ],
    );
  }

  Widget _buildSubTag(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
      decoration: BoxDecoration(
        color: color.withAlpha(15),
        borderRadius: BorderRadius.zero,
        border: Border.all(color: color.withAlpha(50), width: 0.5),
      ),
      child: Text(
        '$label: $value',
        style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w500),
      ),
    );
  }

  // ═════════════════════════════════════════════════════════════════
  // 💳 3. 수수료 지급 관리 (Payout & Banking Transfer)
  // ═════════════════════════════════════════════════════════════════

  Future<void> _handleCompletePeriod(SettlementPeriodModel period) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Row(
          children: [
            const Icon(Icons.done_all_rounded, size: 20, color: Color(0xFF10B981)),
            const SizedBox(width: 8),
            Text(
              '회차 지급 종결 처리',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Text(
          '【${period.title}】\n\n모든 대상자의 수수료 지급이 완료되었습니까?\n\n회차 상태를 [지급 완료] 상태로 종결 처리합니다.',
          style: AppTextStyles.bodySm.copyWith(
            color: context.colors.textSecond,
            height: 1.4,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF10B981),
              foregroundColor: Colors.white,
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('지급 종결'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    try {
      final repo = ref.read(salesRepositoryProvider);
      await repo.completeSettlementPeriod(period.id);
      ref.invalidate(settlementPeriodsProvider);
      ref.invalidate(payoutTabPayoutsProvider);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('정산 회차가 [지급 완료] 상태로 종결되었습니다.'),
          backgroundColor: Color(0xFF10B981),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('지급 종결 처리 실패: $e'),
          backgroundColor: context.colors.error,
        ),
      );
    }
  }

  Future<void> _handleBatchStatusUpdate(
    List<int> ids,
    String targetStatus,
    String statusLabel,
  ) async {
    if (ids.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('상태를 변경할 대상을 1명 이상 선택해 주세요.')),
      );
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Row(
          children: [
            const Icon(Icons.playlist_add_check, size: 20, color: Color(0xFF10B981)),
            const SizedBox(width: 8),
            Text(
              '일괄 상태 변경',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Text(
          '선택한 ${ids.length}명의 지급 상태를 [ $statusLabel ] 상태로 일괄 변경하시겠습니까?'
          '${targetStatus == '3' ? '\n(지급일자가 오늘 일자로 자동 기록됩니다.)' : ''}',
          style: AppTextStyles.bodySm.copyWith(
            color: context.colors.textSecond,
            height: 1.4,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF10B981),
              foregroundColor: Colors.white,
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('일괄 변경'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    setState(() => _isBatchProcessing = true);
    try {
      final repo = ref.read(salesRepositoryProvider);
      await repo.batchUpdatePayStatus(ids, targetStatus);
      ref.invalidate(payoutTabPayoutsProvider);
      ref.invalidate(settlementPeriodsProvider);
      ref.read(payoutTabSelectedIdsProvider.notifier).state = {};

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${ids.length}명의 지급 상태가 [$statusLabel] 상태로 변경되었습니다.'),
          backgroundColor: const Color(0xFF10B981),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('일괄 상태 변경 실패: $e'),
          backgroundColor: context.colors.error,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isBatchProcessing = false);
      }
    }
  }

  Future<void> _handleIndividualStatusUpdate(
    CommissionPayoutModel payout,
    String newStatus,
  ) async {
    if (payout.payStatus == newStatus) return;

    try {
      final repo = ref.read(salesRepositoryProvider);
      await repo.updatePayStatus(payout.id, newStatus);
      ref.invalidate(payoutTabPayoutsProvider);
      ref.invalidate(settlementPeriodsProvider);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('지급 상태가 업데이트되었습니다.'),
          backgroundColor: Color(0xFF10B981),
          duration: Duration(seconds: 1),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('지급 상태 변경 실패: $e'),
          backgroundColor: context.colors.error,
        ),
      );
    }
  }

  /// 3. 수수료 지급 관리 뷰 (지급 대장 & 은행 대량 이체 연동)
  Widget _buildPayoutView(SelectedProject project) {
    final periodsAsync = ref.watch(settlementPeriodsProvider);
    final currentPeriod = ref.watch(currentPayoutPeriodProvider);
    final payoutsAsync = ref.watch(payoutTabPayoutsProvider);
    final filteredList = ref.watch(payoutTabFilteredListProvider);
    final summary = ref.watch(payoutTabSummaryProvider);
    final selectedIds = ref.watch(payoutTabSelectedIdsProvider);

    return RefreshIndicator(
      color: const Color(0xFF10B981),
      onRefresh: () async {
        ref.invalidate(settlementPeriodsProvider);
        ref.invalidate(payoutTabPayoutsProvider);
        ref.read(payoutTabSelectedIdsProvider.notifier).state = {};
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 1. 상단 안내 배너
          _buildInfoBanner(
            title: '수수료 지급 대장 & 금융 이체',
            subtitle: '확정된 회차별 수수료 이체 집행, 지급 승인/완료 일괄 처리 및 은행 이체 파일(CSV) 연계를 관리합니다.',
            icon: Icons.account_balance_outlined,
            color: const Color(0xFF10B981),
          ),
          const SizedBox(height: 14),

          // 2. 정산 회차 선택기 & 회차 종결 관리 바
          periodsAsync.when(
            loading: () => Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.zero,
                border: Border.all(color: context.colors.border),
              ),
              child: const Center(
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF10B981)),
                ),
              ),
            ),
            error: (err, _) => Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.zero,
                border: Border.all(color: context.colors.error.withAlpha(80)),
              ),
              child: Row(
                children: [
                  Icon(Icons.error_outline_rounded, size: 18, color: context.colors.error),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '회차 데이터를 불러오지 못했습니다: $err',
                      style: AppTextStyles.caption.copyWith(color: context.colors.error),
                    ),
                  ),
                ],
              ),
            ),
            data: (periods) => _buildPayoutPeriodSection(project, periods, currentPeriod, summary),
          ),
          const SizedBox(height: 14),

          // 3. 2×2 지급 진행 현황 대시보드
          _buildPayoutSummaryKpi(summary),
          const SizedBox(height: 14),

          // 4. 검색 & 지급 상태 필터 바
          _buildPayoutFilterBar(),
          const SizedBox(height: 14),

          // 5. 다중 선택 & 일괄 상태 변경 & 이체 파일 다운로드 툴바
          _buildPayoutBatchActionBar(project, currentPeriod, filteredList, selectedIds),
          const SizedBox(height: 14),

          // 6. 개인별 지급 대장 카드 리스트
          _buildPayoutExecutionListSection(project, currentPeriod, payoutsAsync, filteredList, selectedIds),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  /// 지급 관리 전용 회차 선택기 & 종결 관리 바
  Widget _buildPayoutPeriodSection(
    SelectedProject project,
    List<SettlementPeriodModel> periods,
    SettlementPeriodModel? currentPeriod,
    PayoutStatusSummaryModel summary,
  ) {
    final canPayout = ref.can(Perm.salesPayout, projectSlug: project.slug);

    if (periods.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(color: const Color(0xFF10B981).withAlpha(80), width: 0.8),
        ),
        child: Column(
          children: [
            Icon(Icons.event_busy_outlined, size: 36, color: context.colors.textMuted),
            const SizedBox(height: 10),
            Text(
              '등록된 정산 회차가 없습니다',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              '[수수료 정산] 탭에서 정산 회차를 생성하고 정산을 확정한 후 지급 관리를 진행하세요.',
              textAlign: TextAlign.center,
              style: AppTextStyles.caption.copyWith(color: context.colors.textSecond),
            ),
          ],
        ),
      );
    }

    final period = currentPeriod ?? periods.first;

    Color statusColor;
    if (period.isCompleted) {
      statusColor = const Color(0xFF10B981); // Emerald
    } else if (period.isConfirmed) {
      statusColor = const Color(0xFF0284C7); // Blue
    } else {
      statusColor = const Color(0xFFF59E0B); // Amber
    }

    // 모든 인원이 지급 완료되었고, 회차가 확정 상태인 경우 종결 가능
    final canCompletePeriod = period.isConfirmed &&
        summary.totalCount > 0 &&
        summary.paidCount == summary.totalCount;

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 회차 헤더 & 선택기
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: context.colors.bgSurface,
              border: Border(
                bottom: BorderSide(color: context.colors.borderSubtle, width: 0.8),
              ),
            ),
            child: Row(
              children: [
                const Icon(Icons.account_balance_outlined, size: 18, color: Color(0xFF10B981)),
                const SizedBox(width: 8),
                Expanded(
                  child: PopupMenuButton<int>(
                    tooltip: '지급 회차 전환',
                    padding: EdgeInsets.zero,
                    onSelected: (id) {
                      ref.read(payoutTabPeriodIdProvider.notifier).state = id;
                      ref.read(payoutTabSelectedIdsProvider.notifier).state = {};
                      ref.invalidate(payoutTabPayoutsProvider);
                    },
                    itemBuilder: (ctx) => periods.map((p) {
                      final isSelected = p.id == period.id;
                      Color pColor = p.isCompleted
                          ? const Color(0xFF10B981)
                          : p.isConfirmed
                              ? const Color(0xFF0284C7)
                              : const Color(0xFFF59E0B);
                      return PopupMenuItem<int>(
                        value: p.id,
                        child: Row(
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: BoxDecoration(color: pColor, shape: BoxShape.circle),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                p.title,
                                style: AppTextStyles.bodySm.copyWith(
                                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                  color: isSelected ? const Color(0xFF10B981) : context.colors.textPrimary,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                              decoration: BoxDecoration(
                                color: pColor.withAlpha(20),
                                borderRadius: BorderRadius.zero,
                                border: Border.all(color: pColor.withAlpha(60), width: 0.5),
                              ),
                              child: Text(
                                p.statusDisplay ?? '작성 중',
                                style: AppTextStyles.caption.copyWith(color: pColor, fontSize: 10),
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Flexible(
                          child: Text(
                            period.title,
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(Icons.arrow_drop_down, size: 20, color: context.colors.textMuted),
                      ],
                    ),
                  ),
                ),
                // 회차 상태 뱃지
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: statusColor.withAlpha(25),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: statusColor.withAlpha(100), width: 0.8),
                  ),
                  child: Text(
                    period.statusDisplay ?? '작성 중',
                    style: AppTextStyles.caption.copyWith(
                      color: statusColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // 회차 세부 일자 & 종결 액션
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
            child: Row(
              children: [
                Expanded(
                  child: Row(
                    children: [
                      Icon(Icons.event_available, size: 14, color: context.colors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        '지급예정: ${period.payoutDate ?? '-'}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textSecond,
                          fontSize: 11,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '| 대상: ${period.startDate} ~ ${period.endDate}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                // 회차 완료 버튼 (조건 충족 시)
                if (canPayout && canCompletePeriod) ...[
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF10B981),
                      foregroundColor: Colors.white,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                    ),
                    icon: const Icon(Icons.done_all, size: 13),
                    label: const Text('회차 지급 종결', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                    onPressed: () => _handleCompletePeriod(period),
                  ),
                ] else if (period.isCompleted) ...[
                  const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.check_circle, size: 14, color: Color(0xFF10B981)),
                      SizedBox(width: 4),
                      Text(
                        '지급 완료 회차',
                        style: TextStyle(color: Color(0xFF10B981), fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ] else if (period.isDraft) ...[
                  Text(
                    '※ 정산 미확정 회차',
                    style: TextStyle(color: context.colors.textMuted, fontSize: 11),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 2×2 수수료 지급 진행 요약 대시보드
  Widget _buildPayoutSummaryKpi(PayoutStatusSummaryModel summary) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _buildSingleKpiTile(
                label: '총 실지급 대상액 (세후)',
                value: '₩ ${NumberFormat('#,###').format(summary.totalNetAmount)}',
                subText: '${summary.totalCount}명 지급 대상',
                accentColor: const Color(0xFF0284C7), // Blue
                icon: Icons.account_balance_wallet_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildSingleKpiTile(
                label: '지급 완료액 (이체완료)',
                value: '₩ ${NumberFormat('#,###').format(summary.paidNetAmount)}',
                subText: '${summary.completionRate}% 완료 (${summary.paidCount}명 완료)',
                accentColor: const Color(0xFF10B981), // Emerald
                icon: Icons.check_circle_outline,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _buildSingleKpiTile(
                label: '지급 잔액 (대기/보류)',
                value: '₩ ${NumberFormat('#,###').format(summary.unpaidNetAmount)}',
                subText: '${summary.unpaidCount}명 대기/보류 중',
                accentColor: summary.unpaidNetAmount > 0 ? const Color(0xFFF59E0B) : context.colors.textMuted,
                icon: Icons.pending_actions_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildSingleKpiTile(
                label: '원천세 예수금 (3.3%)',
                value: '₩ ${NumberFormat('#,###').format(summary.totalTaxAmount)}',
                subText: '익월 10일 세무 신고 납부 대상',
                accentColor: const Color(0xFFEF4444), // Red
                icon: Icons.receipt_long_outlined,
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// 검색 및 지급 상태 필터 바
  Widget _buildPayoutFilterBar() {
    final statusFilter = ref.watch(payoutTabStatusFilterProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.zero,
            border: Border.all(color: context.colors.border, width: 0.8),
          ),
          child: TextField(
            controller: _payoutSearchController,
            onChanged: _onPayoutSearchChanged,
            style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
            decoration: InputDecoration(
              isDense: true,
              hintText: '성명, 소속팀, 은행명, 계좌번호, 예금주 검색...',
              hintStyle: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
              prefixIcon: Icon(Icons.search, size: 18, color: context.colors.textMuted),
              suffixIcon: _payoutSearchController.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear, size: 16),
                      onPressed: () {
                        _payoutSearchController.clear();
                        ref.read(payoutTabSearchQueryProvider.notifier).state = '';
                      },
                    )
                  : null,
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            ),
          ),
        ),
        const SizedBox(height: 8),

        // 지급 상태 필터 칩
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              Text(
                '지급상태: ',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
              _buildFilterChip(
                label: '전체',
                isSelected: statusFilter.isEmpty,
                onTap: () => ref.read(payoutTabStatusFilterProvider.notifier).state = '',
                activeColor: const Color(0xFF10B981),
              ),
              const SizedBox(width: 4),
              _buildFilterChip(
                label: '대기',
                isSelected: statusFilter == '1',
                onTap: () => ref.read(payoutTabStatusFilterProvider.notifier).state = '1',
                activeColor: const Color(0xFFF59E0B),
              ),
              const SizedBox(width: 4),
              _buildFilterChip(
                label: '승인',
                isSelected: statusFilter == '2',
                onTap: () => ref.read(payoutTabStatusFilterProvider.notifier).state = '2',
                activeColor: const Color(0xFF0284C7),
              ),
              const SizedBox(width: 4),
              _buildFilterChip(
                label: '완료',
                isSelected: statusFilter == '3',
                onTap: () => ref.read(payoutTabStatusFilterProvider.notifier).state = '3',
                activeColor: const Color(0xFF10B981),
              ),
              const SizedBox(width: 4),
              _buildFilterChip(
                label: '보류',
                isSelected: statusFilter == '4',
                onTap: () => ref.read(payoutTabStatusFilterProvider.notifier).state = '4',
                activeColor: const Color(0xFFEF4444),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// 다중 선택 및 일괄 처리 & 이체 파일 다운로드 액션 바
  Widget _buildPayoutBatchActionBar(
    SelectedProject project,
    SettlementPeriodModel? currentPeriod,
    List<CommissionPayoutModel> filteredList,
    Set<int> selectedIds,
  ) {
    final canPayout = ref.can(Perm.salesPayout, projectSlug: project.slug);
    final isAllSelected = filteredList.isNotEmpty &&
        filteredList.every((item) => selectedIds.contains(item.id));

    final selectedTotalAmount = filteredList
        .where((item) => selectedIds.contains(item.id))
        .fold<int>(0, (sum, item) => sum + item.netAmount);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // 전체 선택 체크박스
              InkWell(
                onTap: () {
                  if (isAllSelected) {
                    ref.read(payoutTabSelectedIdsProvider.notifier).state = {};
                  } else {
                    ref.read(payoutTabSelectedIdsProvider.notifier).state =
                        filteredList.map((e) => e.id).toSet();
                  }
                },
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox(
                      width: 20,
                      height: 20,
                      child: Checkbox(
                        value: isAllSelected,
                        activeColor: const Color(0xFF10B981),
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        onChanged: (val) {
                          if (val == true) {
                            ref.read(payoutTabSelectedIdsProvider.notifier).state =
                                filteredList.map((e) => e.id).toSet();
                          } else {
                            ref.read(payoutTabSelectedIdsProvider.notifier).state = {};
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      '전체선택',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),

              // 선택된 인원 및 금액 요약
              Expanded(
                child: Text(
                  selectedIds.isNotEmpty
                      ? '선택 ${selectedIds.length}명 (₩${NumberFormat('#,###').format(selectedTotalAmount)})'
                      : '총 ${filteredList.length}건 조회됨',
                  style: AppTextStyles.caption.copyWith(
                    color: selectedIds.isNotEmpty ? const Color(0xFF10B981) : context.colors.textMuted,
                    fontWeight: selectedIds.isNotEmpty ? FontWeight.bold : FontWeight.normal,
                    fontSize: 11,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),

              // [은행 이체용 CSV 공유] 버튼
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF10B981),
                  side: const BorderSide(color: Color(0xFF10B981), width: 0.8),
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  minimumSize: Size.zero,
                ),
                icon: const Icon(Icons.file_download_outlined, size: 14),
                label: const Text('이체 CSV', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                onPressed: () {
                  final targets = selectedIds.isNotEmpty
                      ? filteredList.where((p) => selectedIds.contains(p.id)).toList()
                      : filteredList;
                  BankingCsvHelper.exportAndShareCsv(
                    context: context,
                    payouts: targets,
                    periodTitle: currentPeriod?.title ?? '수수료지급',
                  );
                },
              ),
            ],
          ),

          // 선택 항목이 있을 때 일괄 상태 변경 버튼 그룹 표출 (지급 권한 보유 시)
          if (canPayout && selectedIds.isNotEmpty) ...[
            const SizedBox(height: 8),
            Divider(height: 1, thickness: 0.5, color: context.colors.borderSubtle),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0284C7),
                      foregroundColor: Colors.white,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                    ),
                    icon: const Icon(Icons.check, size: 13),
                    label: const Text('선택 승인', style: TextStyle(fontSize: 11)),
                    onPressed: _isBatchProcessing
                        ? null
                        : () => _handleBatchStatusUpdate(selectedIds.toList(), '2', '승인 완료'),
                  ),
                  const SizedBox(width: 6),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF10B981),
                      foregroundColor: Colors.white,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                    ),
                    icon: const Icon(Icons.done_all, size: 13),
                    label: const Text('선택 지급완료', style: TextStyle(fontSize: 11)),
                    onPressed: _isBatchProcessing
                        ? null
                        : () => _handleBatchStatusUpdate(selectedIds.toList(), '3', '지급 완료'),
                  ),
                  const SizedBox(width: 6),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFEF4444),
                      foregroundColor: Colors.white,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                    ),
                    icon: const Icon(Icons.pause_circle_outline, size: 13),
                    label: const Text('선택 지급보류', style: TextStyle(fontSize: 11)),
                    onPressed: _isBatchProcessing
                        ? null
                        : () => _handleBatchStatusUpdate(selectedIds.toList(), '4', '지급 보류'),
                  ),
                  const SizedBox(width: 6),
                  TextButton(
                    style: TextButton.styleFrom(
                      foregroundColor: context.colors.textMuted,
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      minimumSize: Size.zero,
                    ),
                    onPressed: () => ref.read(payoutTabSelectedIdsProvider.notifier).state = {},
                    child: const Text('선택 해제', style: TextStyle(fontSize: 11)),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  /// 개인별 수수료 지급 대장 카드 리스트 (지급 탭)
  Widget _buildPayoutExecutionListSection(
    SelectedProject project,
    SettlementPeriodModel? currentPeriod,
    AsyncValue<List<CommissionPayoutModel>> payoutsAsync,
    List<CommissionPayoutModel> filteredList,
    Set<int> selectedIds,
  ) {
    if (currentPeriod == null) {
      return const SizedBox.shrink();
    }

    return payoutsAsync.when(
      loading: () => Container(
        padding: const EdgeInsets.all(40),
        child: const Center(
          child: SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: Color(0xFF10B981),
            ),
          ),
        ),
      ),
      error: (err, _) => Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(color: context.colors.error.withAlpha(80)),
        ),
        child: Row(
          children: [
            Icon(Icons.error_outline_rounded, size: 18, color: context.colors.error),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '지급 명세 목록을 불러오지 못했습니다: $err',
                style: AppTextStyles.caption.copyWith(color: context.colors.error),
              ),
            ),
          ],
        ),
      ),
      data: (allPayouts) {
        if (allPayouts.isEmpty) {
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.zero,
              border: Border.all(color: context.colors.border),
            ),
            child: Column(
              children: [
                Icon(Icons.payments_outlined, size: 40, color: context.colors.textMuted),
                const SizedBox(height: 12),
                Text(
                  '지급 대상 명세가 없습니다',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '[수수료 정산] 탭에서 정산 계산을 실행하고 정산을 확정해 주세요.',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.caption.copyWith(color: context.colors.textSecond),
                ),
              ],
            ),
          );
        }

        if (filteredList.isEmpty) {
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 20),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.zero,
              border: Border.all(color: context.colors.border),
            ),
            child: Column(
              children: [
                Icon(Icons.filter_list_off_outlined, size: 36, color: context.colors.textMuted),
                const SizedBox(height: 10),
                Text(
                  '조건에 일치하는 지급 명세가 없습니다',
                  style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: context.colors.textSecond,
                    side: BorderSide(color: context.colors.border),
                    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  ),
                  onPressed: () {
                    _payoutSearchController.clear();
                    ref.read(payoutTabSearchQueryProvider.notifier).state = '';
                    ref.read(payoutTabStatusFilterProvider.notifier).state = '';
                  },
                  child: const Text('검색 및 필터 초기화'),
                ),
              ],
            ),
          );
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '지급 대상 대장 (${filteredList.length}명)',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  '상태 뱃지를 눌러 즉시 변경 가능',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: filteredList.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (ctx, index) {
                final item = filteredList[index];
                final isSelected = selectedIds.contains(item.id);
                return _buildPayoutExecutionCard(context, item, isSelected, project);
              },
            ),
          ],
        );
      },
    );
  }

  /// 개인별 수수료 지급 대장 카드
  Widget _buildPayoutExecutionCard(
    BuildContext context,
    CommissionPayoutModel item,
    bool isSelected,
    SelectedProject project,
  ) {
    final canPayout = ref.can(Perm.salesPayout, projectSlug: project.slug);
    Color statusColor;
    switch (item.payStatus) {
      case '2': // 승인 완료
        statusColor = const Color(0xFF0284C7);
        break;
      case '3': // 지급 완료
        statusColor = const Color(0xFF10B981);
        break;
      case '4': // 지급 보류
        statusColor = const Color(0xFFEF4444);
        break;
      case '1': // 지급 대기
      default:
        statusColor = const Color(0xFFF59E0B);
        break;
    }

    Color dutyColor;
    if (item.dutyDisplay?.contains('본부장') ?? false) {
      dutyColor = const Color(0xFF8B5CF6);
    } else if (item.dutyDisplay?.contains('팀장') ?? false) {
      dutyColor = const Color(0xFF0284C7);
    } else {
      dutyColor = const Color(0xFF10B981);
    }

    return Container(
      decoration: BoxDecoration(
        color: isSelected ? const Color(0xFF10B981).withAlpha(10) : context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(
          color: isSelected ? const Color(0xFF10B981) : context.colors.border,
          width: isSelected ? 1.2 : 0.8,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => showPayoutDetailSheet(context, payout: item, projectSlug: project.slug),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. 헤더: 다중선택 체크박스 + 성명 + 직책 + 소속팀 + 상태 변경 팝업
                Row(
                  children: [
                    SizedBox(
                      width: 20,
                      height: 20,
                      child: Checkbox(
                        value: isSelected,
                        activeColor: const Color(0xFF10B981),
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        onChanged: (val) {
                          final currentSet = {...ref.read(payoutTabSelectedIdsProvider)};
                          if (val == true) {
                            currentSet.add(item.id);
                          } else {
                            currentSet.remove(item.id);
                          }
                          ref.read(payoutTabSelectedIdsProvider.notifier).state = currentSet;
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      item.salesPersonName ?? '미지정',
                      style: AppTextStyles.titleSm.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: dutyColor.withAlpha(20),
                        borderRadius: BorderRadius.zero,
                        border: Border.all(color: dutyColor.withAlpha(70), width: 0.5),
                      ),
                      child: Text(
                        item.dutyDisplay ?? '상담사',
                        style: AppTextStyles.caption.copyWith(
                          color: dutyColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 10,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        item.teamName ?? '-',
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),

                    // 원클릭 상태 전환 팝업 메뉴 (권한 보유 시 팝업, 미보유 시 단순 뱃지)
                    if (canPayout)
                      PopupMenuButton<String>(
                        tooltip: '지급 상태 변경',
                        padding: EdgeInsets.zero,
                        onSelected: (newStatus) => _handleIndividualStatusUpdate(item, newStatus),
                        itemBuilder: (ctx) => [
                          const PopupMenuItem(value: '1', child: Text('지급 대기')),
                          const PopupMenuItem(value: '2', child: Text('승인 완료')),
                          const PopupMenuItem(value: '3', child: Text('지급 완료 (오늘 일자)')),
                          const PopupMenuItem(value: '4', child: Text('지급 보류')),
                        ],
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                          decoration: BoxDecoration(
                            color: statusColor.withAlpha(25),
                            borderRadius: BorderRadius.zero,
                            border: Border.all(color: statusColor.withAlpha(90), width: 0.8),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                item.payStatusDisplay ?? '지급 대기',
                                style: AppTextStyles.caption.copyWith(
                                  color: statusColor,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 11,
                                ),
                              ),
                              const SizedBox(width: 2),
                              Icon(Icons.arrow_drop_down, size: 14, color: statusColor),
                            ],
                          ),
                        ),
                      )
                    else
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                        decoration: BoxDecoration(
                          color: statusColor.withAlpha(25),
                          borderRadius: BorderRadius.zero,
                          border: Border.all(color: statusColor.withAlpha(90), width: 0.8),
                        ),
                        child: Text(
                          item.payStatusDisplay ?? '지급 대기',
                          style: AppTextStyles.caption.copyWith(
                            color: statusColor,
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 10),

                // 2. 세후 실지급액 강조
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text(
                      '세후 실지급액 (이체 대상)',
                      style: AppTextStyles.caption.copyWith(color: context.colors.textSecond),
                    ),
                    Text(
                      '₩ ${NumberFormat('#,###').format(item.netAmount)}',
                      style: AppTextStyles.titleLg.copyWith(
                        color: const Color(0xFF10B981),
                        fontWeight: FontWeight.bold,
                        letterSpacing: -0.5,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                // 3. 은행 계좌 정보 박스 & 복사 버튼
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: context.colors.bgSurface,
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: context.colors.borderSubtle, width: 0.8),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.account_balance_rounded, size: 15, color: Color(0xFF10B981)),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          '${item.bankName ?? '-'} ${item.accountNumber ?? '-'} (예금주: ${item.accountHolder ?? '-'})',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.w600,
                            fontSize: 11.5,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      InkWell(
                        onTap: () {
                          final copyText = '${item.bankName ?? ''} ${item.accountNumber ?? ''} ${item.accountHolder ?? ''}'.trim();
                          if (copyText.isNotEmpty) {
                            Clipboard.setData(ClipboardData(text: copyText));
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('계좌 정보가 클립보드에 복사되었습니다.'),
                                duration: Duration(seconds: 1),
                              ),
                            );
                          }
                        },
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.copy_rounded, size: 13, color: context.colors.textMuted),
                              const SizedBox(width: 3),
                              Text(
                                '복사',
                                style: TextStyle(color: context.colors.textMuted, fontSize: 11),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 8),

                // 4. 하단 요약 (세전, 원천세, 지급일자) 및 상세 링크
                Row(
                  children: [
                    Text(
                      '세전 ₩${NumberFormat('#,###').format(item.grossAmount)} | 원천세 -₩${NumberFormat('#,###').format(item.totalTax)}',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                        fontSize: 11,
                      ),
                    ),
                    const Spacer(),
                    if (item.paidDate != null && item.paidDate!.isNotEmpty) ...[
                      Text(
                        '지급: ${item.paidDate}',
                        style: const TextStyle(
                          color: Color(0xFF10B981),
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(width: 8),
                    ],
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '상세보기',
                          style: AppTextStyles.caption.copyWith(
                            color: const Color(0xFF10B981),
                            fontWeight: FontWeight.w600,
                            fontSize: 11,
                          ),
                        ),
                        const Icon(Icons.chevron_right, size: 14, color: Color(0xFF10B981)),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// 4. 영업 조직 관리 뷰 (실시간 API 연동 + 2×2 KPI + 대행사/팀 계층 필터 + 인력 명부 + 원터치 통화/수정)
  Widget _buildOrganizationView(SelectedProject project) {
    final summary = ref.watch(salesOrganizationSummaryProvider);
    final agenciesAsync = ref.watch(salesAgenciesProvider);
    final teamsAsync = ref.watch(salesTeamsProvider);
    final personsAsync = ref.watch(salesPersonsProvider);
    final filteredPersons = ref.watch(filteredOrgPersonsProvider);

    return RefreshIndicator(
      color: const Color(0xFF6366F1),
      onRefresh: () async {
        ref.invalidate(salesAgenciesProvider);
        ref.invalidate(salesTeamsProvider);
        ref.invalidate(salesPersonsProvider);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 1. 2×2 조직 KPI 요약 대시보드
          _buildOrgKpiSection(summary),
          const SizedBox(height: 14),

          // 2. 대행사 & 팀 계층 가로 필터 바 + [⚙️ 조직 관리] 버튼
          _buildOrgHierarchyFilterBar(
            project,
            agenciesAsync.valueOrNull ?? [],
            teamsAsync.valueOrNull ?? [],
          ),
          const SizedBox(height: 12),

          // 3. 인력 검색창 & 직책/재직상태 필터 + [+ 인력 등록] 버튼
          _buildOrgPersonFilterBar(project),
          const SizedBox(height: 14),

          // 4. 인력 명부 리스트
          _buildOrgPersonListSection(
            project,
            personsAsync,
            filteredPersons,
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  /// 2×2 영업 조직 KPI 대시보드
  Widget _buildOrgKpiSection(SalesOrganizationSummary summary) {
    final direct = summary.directAgencyCount;
    final outsourced = summary.agencyCount - summary.directAgencyCount;

    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _buildSingleKpiTile(
                label: '분양 대행사',
                value: '${NumberFormat('#,###').format(summary.agencyCount)}개사',
                subText: '직영 $direct사 / 외주 ${outsourced > 0 ? outsourced : 0}사',
                accentColor: const Color(0xFF6366F1), // Indigo
                icon: Icons.corporate_fare_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildSingleKpiTile(
                label: '영업 본부/팀',
                value: '${NumberFormat('#,###').format(summary.teamCount)}개 팀',
                subText: '소속 팀 체계',
                accentColor: const Color(0xFF38BDF8), // Sky Blue
                icon: Icons.account_tree_outlined,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _buildSingleKpiTile(
                label: '총 등록 인력',
                value: '${NumberFormat('#,###').format(summary.totalPersons)}명',
                subText: '영업 인력 명부',
                accentColor: const Color(0xFF8B5CF6), // Violet
                icon: Icons.groups_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildSingleKpiTile(
                label: '활동(재직) 인력',
                value: '${NumberFormat('#,###').format(summary.activePersons)}명',
                subText: summary.totalPersons > 0
                    ? '재직률 ${((summary.activePersons / summary.totalPersons) * 100).toStringAsFixed(0)}%'
                    : '등록 인력 없음',
                accentColor: const Color(0xFF10B981), // Emerald
                icon: Icons.verified_user_outlined,
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// 대행사 및 팀 계층 가로 필터 바 + [⚙️ 조직 관리] 버튼
  Widget _buildOrgHierarchyFilterBar(
    SelectedProject project,
    List<SalesAgencyModel> agencies,
    List<SalesTeamModel> teams,
  ) {
    final canManage = ref.can(Perm.salesManage, projectSlug: project.slug);
    final selectedAgencyId = ref.watch(orgAgencyFilterProvider);
    final selectedTeamId = ref.watch(orgTeamFilterProvider);

    // 선택된 대행사에 속한 팀 목록 (대행사 미선택 시 전체 팀)
    final availableTeams = selectedAgencyId != null
        ? teams.where((t) => t.agency == selectedAgencyId).toList()
        : teams;

    return Row(
      children: [
        // 대행사 & 팀 가로 스크롤 필터
        Expanded(
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildFilterChip(
                  label: '대행사 전체',
                  isSelected: selectedAgencyId == null,
                  onTap: () {
                    ref.read(orgAgencyFilterProvider.notifier).state = null;
                    ref.read(orgTeamFilterProvider.notifier).state = null;
                  },
                  activeColor: const Color(0xFF6366F1),
                ),
                for (final agency in agencies) ...[
                  const SizedBox(width: 6),
                  _buildFilterChip(
                    label: agency.isDirectManaged
                        ? '[직영] ${agency.name}'
                        : agency.name,
                    isSelected: selectedAgencyId == agency.id,
                    onTap: () {
                      if (selectedAgencyId == agency.id) {
                        ref.read(orgAgencyFilterProvider.notifier).state = null;
                        ref.read(orgTeamFilterProvider.notifier).state = null;
                      } else {
                        ref.read(orgAgencyFilterProvider.notifier).state = agency.id;
                        ref.read(orgTeamFilterProvider.notifier).state = null;
                      }
                    },
                    activeColor: const Color(0xFF6366F1),
                  ),
                ],
                if (availableTeams.isNotEmpty) ...[
                  const SizedBox(width: 8),
                  // 팀 드롭다운 필터
                  PopupMenuButton<int?>(
                    initialValue: selectedTeamId,
                    onSelected: (teamId) {
                      ref.read(orgTeamFilterProvider.notifier).state = teamId;
                    },
                    itemBuilder: (ctx) => [
                      const PopupMenuItem<int?>(
                        value: null,
                        child: Text('전체 팀', style: TextStyle(fontSize: 12)),
                      ),
                      ...availableTeams.map(
                        (t) => PopupMenuItem<int?>(
                          value: t.id,
                          child: Text(t.name, style: const TextStyle(fontSize: 12)),
                        ),
                      ),
                    ],
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
                      decoration: BoxDecoration(
                        color: selectedTeamId != null
                            ? const Color(0xFF38BDF8).withAlpha(20)
                            : context.colors.bgCard,
                        border: Border.all(
                          color: selectedTeamId != null
                              ? const Color(0xFF38BDF8)
                              : context.colors.border,
                          width: 0.8,
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            selectedTeamId != null
                                ? (availableTeams
                                        .where((t) => t.id == selectedTeamId)
                                        .firstOrNull
                                        ?.name ??
                                    '팀 필터')
                                : '팀 선택',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: selectedTeamId != null
                                  ? FontWeight.bold
                                  : FontWeight.normal,
                              color: selectedTeamId != null
                                  ? const Color(0xFF0284C7)
                                  : context.colors.textSecond,
                            ),
                          ),
                          const SizedBox(width: 3),
                          Icon(Icons.arrow_drop_down,
                              size: 16, color: context.colors.textMuted),
                        ],
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
        if (canManage) ...[
          const SizedBox(width: 8),
          // [⚙️ 조직 관리] 버튼
          Material(
            color: const Color(0xFF6366F1),
            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            child: InkWell(
              onTap: () => showAgencyTeamManageSheet(
                context,
                projectId: project.realProjectId,
              ),
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.account_tree_outlined, size: 14, color: Colors.white),
                    SizedBox(width: 4),
                    Text(
                      '조직 관리',
                      style: TextStyle(
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
        ],
      ],
    );
  }

  /// 인력 검색창 & 직책/재직상태 필터 바 + [+ 인력 등록] 버튼
  Widget _buildOrgPersonFilterBar(SelectedProject project) {
    final canManage = ref.can(Perm.salesManage, projectSlug: project.slug);
    final statusFilter = ref.watch(orgStatusFilterProvider);
    final dutyFilter = ref.watch(orgDutyFilterProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 1. 검색창
        Container(
          height: 38,
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.zero,
            border: Border.all(color: context.colors.border, width: 0.8),
          ),
          child: Row(
            children: [
              const SizedBox(width: 10),
              Icon(Icons.search_rounded, size: 18, color: context.colors.textMuted),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _orgSearchController,
                  onChanged: _onOrgSearchChanged,
                  style: const TextStyle(fontSize: 12.5),
                  decoration: InputDecoration(
                    hintText: '성명 / 연락처 / 예금주 / 팀명 검색',
                    hintStyle: TextStyle(fontSize: 12, color: context.colors.textMuted),
                    border: InputBorder.none,
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
              if (_orgSearchController.text.isNotEmpty)
                IconButton(
                  icon: const Icon(Icons.clear_rounded, size: 16),
                  onPressed: () {
                    _orgSearchController.clear();
                    ref.read(orgSearchQueryProvider.notifier).state = '';
                  },
                  color: context.colors.textMuted,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                ),
            ],
          ),
        ),
        const SizedBox(height: 8),

        // 2. 재직상태/직책 필터 칩스 + [+ 인력 등록] 버튼
        Row(
          children: [
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildFilterChip(
                      label: '재직',
                      isSelected: statusFilter == '1',
                      onTap: () => ref.read(orgStatusFilterProvider.notifier).state = '1',
                      activeColor: const Color(0xFF10B981),
                    ),
                    const SizedBox(width: 6),
                    _buildFilterChip(
                      label: '전체 상태',
                      isSelected: statusFilter == '',
                      onTap: () => ref.read(orgStatusFilterProvider.notifier).state = '',
                      activeColor: const Color(0xFF8B5CF6),
                    ),
                    const SizedBox(width: 6),
                    _buildFilterChip(
                      label: '해촉',
                      isSelected: statusFilter == '2',
                      onTap: () => ref.read(orgStatusFilterProvider.notifier).state = '2',
                      activeColor: const Color(0xFFEF4444),
                    ),
                    const SizedBox(width: 8),
                    // 직책 필터 드롭다운
                    PopupMenuButton<String>(
                      initialValue: dutyFilter,
                      onSelected: (duty) {
                        ref.read(orgDutyFilterProvider.notifier).state = duty;
                      },
                      itemBuilder: (ctx) => [
                        const PopupMenuItem<String>(
                          value: '',
                          child: Text('전체 직책', style: TextStyle(fontSize: 12)),
                        ),
                        const PopupMenuItem<String>(
                          value: '1',
                          child: Text('상담사', style: TextStyle(fontSize: 12)),
                        ),
                        const PopupMenuItem<String>(
                          value: '2',
                          child: Text('팀장', style: TextStyle(fontSize: 12)),
                        ),
                        const PopupMenuItem<String>(
                          value: '3',
                          child: Text('본부장', style: TextStyle(fontSize: 12)),
                        ),
                        const PopupMenuItem<String>(
                          value: '4',
                          child: Text('총괄본부장', style: TextStyle(fontSize: 12)),
                        ),
                        const PopupMenuItem<String>(
                          value: '5',
                          child: Text('지원/기타', style: TextStyle(fontSize: 12)),
                        ),
                      ],
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
                        decoration: BoxDecoration(
                          color: dutyFilter.isNotEmpty
                              ? const Color(0xFF8B5CF6).withAlpha(20)
                              : context.colors.bgCard,
                          border: Border.all(
                            color: dutyFilter.isNotEmpty
                                ? const Color(0xFF8B5CF6)
                                : context.colors.border,
                            width: 0.8,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              dutyFilter.isNotEmpty
                                  ? _getDutyLabel(dutyFilter, null)
                                  : '직책',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: dutyFilter.isNotEmpty
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                                color: dutyFilter.isNotEmpty
                                    ? const Color(0xFF8B5CF6)
                                    : context.colors.textSecond,
                              ),
                            ),
                            const SizedBox(width: 3),
                            Icon(Icons.arrow_drop_down,
                                size: 16, color: context.colors.textMuted),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            if (canManage) ...[
              const SizedBox(width: 8),
              // [+ 인력 등록] 버튼
              Material(
                color: const Color(0xFF10B981),
                shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                child: InkWell(
                  onTap: () => showPersonFormSheet(
                    context,
                    projectId: project.realProjectId,
                  ),
                  child: const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.person_add_alt_1, size: 14, color: Colors.white),
                        SizedBox(width: 4),
                        Text(
                          '인력 등록',
                          style: TextStyle(
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
            ],
          ],
        ),
      ],
    );
  }

  /// 인력 명부 리스트 섹션 (로딩, 에러, 빈 상태, 카드 리스트)
  Widget _buildOrgPersonListSection(
    SelectedProject project,
    AsyncValue<List<SalesPersonModel>> personsAsync,
    List<SalesPersonModel> filteredPersons,
  ) {
    final canManage = ref.can(Perm.salesManage, projectSlug: project.slug);

    return personsAsync.when(
      loading: () => Container(
        padding: const EdgeInsets.all(40),
        child: const Center(
          child: SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: Color(0xFF6366F1),
            ),
          ),
        ),
      ),
      error: (err, _) => Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(color: context.colors.error.withAlpha(80)),
        ),
        child: Row(
          children: [
            Icon(Icons.error_outline_rounded, size: 18, color: context.colors.error),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '영업 인력 데이터를 불러오지 못했습니다: $err',
                style: AppTextStyles.caption.copyWith(color: context.colors.error),
              ),
            ),
          ],
        ),
      ),
      data: (_) {
        if (filteredPersons.isEmpty) {
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.zero,
              border: Border.all(color: context.colors.border),
            ),
            child: Column(
              children: [
                Icon(Icons.person_off_outlined,
                    size: 36, color: context.colors.textMuted),
                const SizedBox(height: 10),
                Text(
                  '조건에 일치하는 영업 인력이 없습니다',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '검색어나 소속/직책 필터를 변경하시거나, 상단 [+ 인력 등록] 버튼으로 새로운 상담사를 등록해 보세요.',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                ),
                if (canManage) ...[
                  const SizedBox(height: 14),
                  OutlinedButton.icon(
                    onPressed: () => showPersonFormSheet(
                      context,
                      projectId: project.realProjectId,
                    ),
                    icon: const Icon(Icons.person_add_alt_1, size: 14),
                    label: const Text('신규 인력 등록하기', style: TextStyle(fontSize: 12)),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF10B981),
                      side: const BorderSide(color: Color(0xFF10B981)),
                      shape: const RoundedRectangleBorder(
                          borderRadius: BorderRadius.zero),
                    ),
                  ),
                ],
              ],
            ),
          );
        }

        return Column(
          children: filteredPersons.map((person) {
            return _buildOrgPersonCardItem(person, project);
          }).toList(),
        );
      },
    );
  }

  /// 개별 영업 인력 카드 아이템
  Widget _buildOrgPersonCardItem(
    SalesPersonModel person,
    SelectedProject project,
  ) {
    final canManage = ref.can(Perm.salesManage, projectSlug: project.slug);
    final isActive = person.status == '1';
    final dutyColor = _getDutyColor(person.duty);
    final dutyText = _getDutyLabel(person.duty, person.dutyDisplay);
    final statusText = _getStatusLabel(person.status, person.statusDisplay);
    final hasPhone = person.phone != null && person.phone!.isNotEmpty;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(
          color: isActive
              ? const Color(0xFF6366F1).withAlpha(50)
              : context.colors.border,
          width: 0.8,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. 헤더: 성명 + 직책 뱃지 + 재직 뱃지 + 세무구분 + [수정] 버튼
            Row(
              children: [
                Icon(
                  Icons.person,
                  size: 16,
                  color: isActive ? const Color(0xFF6366F1) : context.colors.textMuted,
                ),
                const SizedBox(width: 6),
                Text(
                  person.name,
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                    fontSize: 13.5,
                  ),
                ),
                const SizedBox(width: 8),
                // 직책 뱃지
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: dutyColor.withAlpha(20),
                    border: Border.all(color: dutyColor.withAlpha(80), width: 0.8),
                  ),
                  child: Text(
                    dutyText,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: dutyColor,
                    ),
                  ),
                ),
                const SizedBox(width: 5),
                // 재직 상태 뱃지
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                  decoration: BoxDecoration(
                    color: isActive
                        ? const Color(0xFF10B981).withAlpha(20)
                        : context.colors.borderSubtle,
                    border: Border.all(
                      color: isActive
                          ? const Color(0xFF10B981).withAlpha(80)
                          : context.colors.textMuted.withAlpha(60),
                      width: 0.8,
                    ),
                  ),
                  child: Text(
                    statusText,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: isActive
                          ? const Color(0xFF10B981)
                          : context.colors.textMuted,
                    ),
                  ),
                ),
                if (person.taxTypeDisplay != null || person.taxType == '1') ...[
                  const SizedBox(width: 5),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                    decoration: BoxDecoration(
                      color: context.colors.bgSurface,
                      border: Border.all(color: context.colors.border, width: 0.7),
                    ),
                    child: Text(
                      person.taxTypeDisplay ??
                          (person.taxType == '1' ? '3.3%' : '일반'),
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textSecond,
                        fontSize: 9.5,
                      ),
                    ),
                  ),
                ],
                const Spacer(),
                // 수정 버튼
                if (canManage)
                  InkWell(
                    onTap: () => showPersonFormSheet(
                      context,
                      projectId: project.realProjectId,
                      existingPerson: person,
                    ),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.edit_outlined,
                              size: 13, color: context.colors.textMuted),
                          const SizedBox(width: 3),
                          Text(
                            '수정',
                            style: TextStyle(
                              fontSize: 11,
                              color: context.colors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Divider(color: context.colors.borderSubtle, height: 1),
            const SizedBox(height: 8),

            // 2. 소속 조직 (대행사 > 팀)
            Row(
              children: [
                Icon(Icons.domain_outlined,
                    size: 14, color: context.colors.textMuted),
                const SizedBox(width: 6),
                Text(
                  '소속:',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 11.5,
                  ),
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    person.agencyName != null && person.agencyName!.isNotEmpty
                        ? '${person.agencyName} > ${person.teamName ?? "소속팀 미지정"}'
                        : (person.teamName ?? '소속팀 미지정'),
                    style: AppTextStyles.bodySecond.copyWith(
                      color: context.colors.textPrimary,
                      fontSize: 12,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),

            // 3. 연락처 & 통화 버튼
            Row(
              children: [
                Icon(Icons.phone_outlined,
                    size: 14, color: context.colors.textMuted),
                const SizedBox(width: 6),
                Text(
                  '연락처:',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 11.5,
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  hasPhone ? person.phone! : '-',
                  style: AppTextStyles.bodySecond.copyWith(
                    color: hasPhone
                        ? context.colors.textPrimary
                        : context.colors.textMuted,
                    fontSize: 12,
                    fontWeight: hasPhone ? FontWeight.w500 : FontWeight.normal,
                  ),
                ),
                if (hasPhone) ...[
                  const SizedBox(width: 8),
                  InkWell(
                    onTap: () =>
                        _makePhoneCall(person.phone!, targetName: person.name),
                    child: Container(
                      padding:
                          const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFF10B981).withAlpha(20),
                        borderRadius: BorderRadius.zero,
                        border: Border.all(
                          color: const Color(0xFF10B981).withAlpha(70),
                          width: 0.8,
                        ),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.phone_in_talk,
                              size: 11, color: Color(0xFF10B981)),
                          SizedBox(width: 3),
                          Text(
                            '통화',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF10B981),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 6),

            // 4. 입금 계좌 정보
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.account_balance_outlined,
                    size: 14, color: context.colors.textMuted),
                const SizedBox(width: 6),
                Text(
                  '계좌:',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 11.5,
                  ),
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    person.accountNumber != null &&
                            person.accountNumber!.isNotEmpty
                        ? '${person.bankName ?? ""} ${person.accountNumber} (예금주: ${person.accountHolder ?? person.name})'
                        : '미등록',
                    style: AppTextStyles.bodySecond.copyWith(
                      color: person.accountNumber != null
                          ? context.colors.textSecond
                          : context.colors.textMuted,
                      fontSize: 11.5,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),

            // 5. 증빙 서류 (열람 및 공유 바로가기)
            Row(
              children: [
                Icon(Icons.attach_file,
                    size: 14, color: context.colors.textMuted),
                const SizedBox(width: 6),
                Text(
                  '증빙 서류:',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 11.5,
                  ),
                ),
                const SizedBox(width: 6),
                InkWell(
                  onTap: () => showPersonDocumentSheet(
                    context,
                    person: person,
                    projectSlug: project.slug,
                  ),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                    decoration: BoxDecoration(
                      color: person.documentsCount > 0
                          ? const Color(0xFF6366F1).withAlpha(15)
                          : context.colors.borderSubtle,
                      border: Border.all(
                        color: person.documentsCount > 0
                            ? const Color(0xFF6366F1).withAlpha(70)
                            : context.colors.border,
                        width: 0.8,
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          person.documentsCount > 0
                              ? Icons.description_outlined
                              : Icons.file_present_outlined,
                          size: 11,
                          color: person.documentsCount > 0
                              ? const Color(0xFF6366F1)
                              : context.colors.textMuted,
                        ),
                        const SizedBox(width: 3),
                        Text(
                          person.documentsCount > 0
                              ? '서류 ${person.documentsCount}건 열람/공유'
                              : '서류 미제출 (터치하여 확인)',
                          style: TextStyle(
                            fontSize: 10.5,
                            fontWeight: person.documentsCount > 0
                                ? FontWeight.bold
                                : FontWeight.normal,
                            color: person.documentsCount > 0
                                ? const Color(0xFF6366F1)
                                : context.colors.textMuted,
                          ),
                        ),
                        const SizedBox(width: 2),
                        Icon(
                          Icons.chevron_right,
                          size: 12,
                          color: person.documentsCount > 0
                              ? const Color(0xFF6366F1)
                              : context.colors.textMuted,
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),

            // 6. 위촉일/해촉일
            if (person.joinDate != null && person.joinDate!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Row(
                children: [
                  Icon(Icons.calendar_today_outlined,
                      size: 14, color: context.colors.textMuted),
                  const SizedBox(width: 6),
                  Text(
                    '위촉일:',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textMuted,
                      fontSize: 11.5,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    '${person.joinDate}${person.quitDate != null && person.quitDate!.isNotEmpty ? " (해촉: ${person.quitDate})" : ""}',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textSecond,
                      fontSize: 11.5,
                    ),
                  ),
                ],
              ),
            ],

            // 6. 비고
            if (person.notes != null && person.notes!.trim().isNotEmpty) ...[
              const SizedBox(height: 6),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.note_alt_outlined,
                      size: 14, color: context.colors.textMuted),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      person.notes!.trim(),
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                        fontSize: 11,
                        fontStyle: FontStyle.italic,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _getDutyLabel(String duty, String? dutyDisplay) {
    if (dutyDisplay != null && dutyDisplay.isNotEmpty) return dutyDisplay;
    switch (duty) {
      case '1':
        return '상담사';
      case '2':
        return '팀장';
      case '3':
        return '본부장';
      case '4':
        return '총괄본부장';
      case '5':
        return '지원/기타';
      default:
        return '상담사';
    }
  }

  Color _getDutyColor(String duty) {
    switch (duty) {
      case '1':
        return const Color(0xFF38BDF8); // Sky blue
      case '2':
        return const Color(0xFF8B5CF6); // Violet
      case '3':
        return const Color(0xFFF59E0B); // Amber
      case '4':
        return const Color(0xFFEC4899); // Rose
      default:
        return const Color(0xFF64748B); // Slate
    }
  }

  String _getStatusLabel(String status, String? statusDisplay) {
    if (statusDisplay != null && statusDisplay.isNotEmpty) return statusDisplay;
    switch (status) {
      case '1':
        return '재직';
      case '2':
        return '해촉';
      default:
        return '재직';
    }
  }

  /// 5. 수수료 정책 관리 뷰 (실시간 API 연동 + 2×2 KPI + 차수/타입 필터 + R값 기준 카드 + 분배 시각화 바)
  Widget _buildPolicyView(SelectedProject project) {
    final summary = ref.watch(salesPolicySummaryProvider);
    final policiesAsync = ref.watch(salesPoliciesProvider);
    final filteredPolicies = ref.watch(filteredSalesPoliciesProvider);
    final orderGroups = ref.watch(orderGroupsProvider).valueOrNull ?? [];
    final unitTypes = ref.watch(unitTypesProvider).valueOrNull ?? [];

    return RefreshIndicator(
      color: const Color(0xFFEC4899),
      onRefresh: () async {
        ref.invalidate(salesPoliciesProvider);
        ref.invalidate(orderGroupsProvider);
        ref.invalidate(unitTypesProvider);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 1. 2×2 수수료 정책 KPI 요약 대시보드
          _buildPolicyKpiSection(summary),
          const SizedBox(height: 14),

          // 2. 차수/타입 필터 & 검색창 + [+ 정책 등록] 버튼
          _buildPolicyFilterBar(project, orderGroups, unitTypes),
          const SizedBox(height: 14),

          // 3. 수수료 정책 리스트
          _buildPolicyListSection(project, policiesAsync, filteredPolicies),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  /// 2×2 수수료 정책 KPI 요약 대시보드
  Widget _buildPolicyKpiSection(SalesPolicySummary summary) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _buildSingleKpiTile(
                label: '수수료 정책',
                value: '${NumberFormat('#,###').format(summary.totalCount)}개 기준',
                subText: '활성 ${summary.activeCount}개 / 비활성 ${summary.totalCount - summary.activeCount}개',
                accentColor: const Color(0xFFEC4899), // Rose
                icon: Icons.rule_folder_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildSingleKpiTile(
                label: '활성 정책 비중',
                value: summary.totalCount > 0
                    ? '${((summary.activeCount / summary.totalCount) * 100).toStringAsFixed(0)}%'
                    : '0%',
                subText: '현재 실적 적용 대상',
                accentColor: const Color(0xFF10B981), // Emerald
                icon: Icons.check_circle_outline,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _buildSingleKpiTile(
                label: '최고 건당 수수료',
                value: summary.maxFee > 0
                    ? '${NumberFormat('#,###').format(summary.maxFee)}원'
                    : '-',
                subText: 'R값 기준표 최고액',
                accentColor: const Color(0xFF8B5CF6), // Violet
                icon: Icons.monetization_on_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildSingleKpiTile(
                label: '적용 유니트 타입',
                value: '${summary.coveredTypesCount}개 타입',
                subText: '평형별 기준표 설정',
                accentColor: const Color(0xFF38BDF8), // Sky Blue
                icon: Icons.apartment_outlined,
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// 차수/타입 필터 & 검색창 + [+ 정책 등록] 버튼
  Widget _buildPolicyFilterBar(
    SelectedProject project,
    List<OrderGroupOption> orderGroups,
    List<UnitTypeOption> unitTypes,
  ) {
    final canPolicy = ref.can(Perm.salesPolicy, projectSlug: project.slug);
    final activeFilter = ref.watch(policyActiveFilterProvider);
    final selectedOrderGroupId = ref.watch(policyOrderGroupFilterProvider);
    final selectedUnitTypeId = ref.watch(policyUnitTypeFilterProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 1. 검색창
        Container(
          height: 38,
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            borderRadius: BorderRadius.zero,
            border: Border.all(color: context.colors.border, width: 0.8),
          ),
          child: Row(
            children: [
              const SizedBox(width: 10),
              Icon(Icons.search_rounded, size: 18, color: context.colors.textMuted),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _policySearchController,
                  onChanged: _onPolicySearchChanged,
                  style: const TextStyle(fontSize: 12.5),
                  decoration: InputDecoration(
                    hintText: '정책명 / 적용 평형 / 차수 검색',
                    hintStyle: TextStyle(fontSize: 12, color: context.colors.textMuted),
                    border: InputBorder.none,
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
              if (_policySearchController.text.isNotEmpty)
                IconButton(
                  icon: const Icon(Icons.clear_rounded, size: 16),
                  onPressed: () {
                    _policySearchController.clear();
                    ref.read(policySearchQueryProvider.notifier).state = '';
                  },
                  color: context.colors.textMuted,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                ),
            ],
          ),
        ),
        const SizedBox(height: 8),

        // 2. 활성상태 칩 + 차수/타입 드롭다운 + [+ 정책 등록] 버튼
        Row(
          children: [
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildFilterChip(
                      label: '활성만',
                      isSelected: activeFilter == 'true',
                      onTap: () => ref.read(policyActiveFilterProvider.notifier).state = 'true',
                      activeColor: const Color(0xFF10B981),
                    ),
                    const SizedBox(width: 6),
                    _buildFilterChip(
                      label: '전체',
                      isSelected: activeFilter == '',
                      onTap: () => ref.read(policyActiveFilterProvider.notifier).state = '',
                      activeColor: const Color(0xFFEC4899),
                    ),
                    const SizedBox(width: 6),
                    _buildFilterChip(
                      label: '비활성',
                      isSelected: activeFilter == 'false',
                      onTap: () => ref.read(policyActiveFilterProvider.notifier).state = 'false',
                      activeColor: const Color(0xFF64748B),
                    ),
                    if (unitTypes.isNotEmpty) ...[
                      const SizedBox(width: 8),
                      // 유니트 타입 드롭다운 필터
                      PopupMenuButton<int?>(
                        initialValue: selectedUnitTypeId,
                        onSelected: (typeId) {
                          ref.read(policyUnitTypeFilterProvider.notifier).state = typeId;
                        },
                        itemBuilder: (ctx) => [
                          const PopupMenuItem<int?>(
                            value: null,
                            child: Text('전체 타입', style: TextStyle(fontSize: 12)),
                          ),
                          ...unitTypes.map(
                            (u) => PopupMenuItem<int?>(
                              value: u.id,
                              child: Text(u.name, style: const TextStyle(fontSize: 12)),
                            ),
                          ),
                        ],
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
                          decoration: BoxDecoration(
                            color: selectedUnitTypeId != null
                                ? const Color(0xFF38BDF8).withAlpha(20)
                                : context.colors.bgCard,
                            border: Border.all(
                              color: selectedUnitTypeId != null
                                  ? const Color(0xFF38BDF8)
                                  : context.colors.border,
                              width: 0.8,
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                selectedUnitTypeId != null
                                    ? (unitTypes.where((u) => u.id == selectedUnitTypeId).firstOrNull?.name ?? '타입')
                                    : '타입 필터',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: selectedUnitTypeId != null ? FontWeight.bold : FontWeight.normal,
                                  color: selectedUnitTypeId != null
                                      ? const Color(0xFF0284C7)
                                      : context.colors.textSecond,
                                ),
                              ),
                              const SizedBox(width: 3),
                              Icon(Icons.arrow_drop_down, size: 16, color: context.colors.textMuted),
                            ],
                          ),
                        ),
                      ),
                    ],
                    if (orderGroups.isNotEmpty) ...[
                      const SizedBox(width: 6),
                      // 공급 차수 드롭다운 필터
                      PopupMenuButton<int?>(
                        initialValue: selectedOrderGroupId,
                        onSelected: (ogId) {
                          ref.read(policyOrderGroupFilterProvider.notifier).state = ogId;
                        },
                        itemBuilder: (ctx) => [
                          const PopupMenuItem<int?>(
                            value: null,
                            child: Text('전체 차수', style: TextStyle(fontSize: 12)),
                          ),
                          ...orderGroups.map(
                            (og) => PopupMenuItem<int?>(
                              value: og.id,
                              child: Text(og.name, style: const TextStyle(fontSize: 12)),
                            ),
                          ),
                        ],
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
                          decoration: BoxDecoration(
                            color: selectedOrderGroupId != null
                                ? const Color(0xFF8B5CF6).withAlpha(20)
                                : context.colors.bgCard,
                            border: Border.all(
                              color: selectedOrderGroupId != null
                                  ? const Color(0xFF8B5CF6)
                                  : context.colors.border,
                              width: 0.8,
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                selectedOrderGroupId != null
                                    ? (orderGroups.where((og) => og.id == selectedOrderGroupId).firstOrNull?.name ?? '차수')
                                    : '차수 필터',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: selectedOrderGroupId != null ? FontWeight.bold : FontWeight.normal,
                                  color: selectedOrderGroupId != null
                                      ? const Color(0xFF8B5CF6)
                                      : context.colors.textSecond,
                                ),
                              ),
                              const SizedBox(width: 3),
                              Icon(Icons.arrow_drop_down, size: 16, color: context.colors.textMuted),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            if (canPolicy) ...[
              const SizedBox(width: 8),
              // [+ 정책 등록] 버튼
              Material(
                color: const Color(0xFFEC4899),
                shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                child: InkWell(
                  onTap: () => showPolicyFormSheet(
                    context,
                    projectId: project.realProjectId,
                  ),
                  child: const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.add, size: 14, color: Colors.white),
                        SizedBox(width: 4),
                        Text(
                          '정책 등록',
                          style: TextStyle(
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
            ],
          ],
        ),
      ],
    );
  }

  /// 수수료 정책 리스트 섹션 (로딩, 에러, 빈 상태, 카드 리스트)
  Widget _buildPolicyListSection(
    SelectedProject project,
    AsyncValue<List<CommissionPolicyModel>> policiesAsync,
    List<CommissionPolicyModel> filteredPolicies,
  ) {
    final canPolicy = ref.can(Perm.salesPolicy, projectSlug: project.slug);

    return policiesAsync.when(
      loading: () => Container(
        padding: const EdgeInsets.all(40),
        child: const Center(
          child: SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: Color(0xFFEC4899),
            ),
          ),
        ),
      ),
      error: (err, _) => Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(color: context.colors.error.withAlpha(80)),
        ),
        child: Row(
          children: [
            Icon(Icons.error_outline_rounded, size: 18, color: context.colors.error),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '수수료 정책 데이터를 불러오지 못했습니다: $err',
                style: AppTextStyles.caption.copyWith(color: context.colors.error),
              ),
            ),
          ],
        ),
      ),
      data: (_) {
        if (filteredPolicies.isEmpty) {
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.zero,
              border: Border.all(color: context.colors.border),
            ),
            child: Column(
              children: [
                Icon(Icons.rule_folder_outlined,
                    size: 36, color: context.colors.textMuted),
                const SizedBox(height: 10),
                Text(
                  '조건에 일치하는 수수료 정책이 없습니다',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '검색어나 차수/타입 필터를 변경하시거나, 상단 [+ 정책 등록] 버튼으로 신규 수수료 기준표를 등록해 보세요.',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                ),
                if (canPolicy) ...[
                  const SizedBox(height: 14),
                  OutlinedButton.icon(
                    onPressed: () => showPolicyFormSheet(
                      context,
                      projectId: project.realProjectId,
                    ),
                    icon: const Icon(Icons.add, size: 14),
                    label: const Text('신규 정책 등록하기', style: TextStyle(fontSize: 12)),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFFEC4899),
                      side: const BorderSide(color: Color(0xFFEC4899)),
                      shape: const RoundedRectangleBorder(
                          borderRadius: BorderRadius.zero),
                    ),
                  ),
                ],
              ],
            ),
          );
        }

        return Column(
          children: filteredPolicies.map((policy) {
            return _buildPolicyCardItem(policy, project);
          }).toList(),
        );
      },
    );
  }

  /// 개별 수수료 정책 카드 아이템
  Widget _buildPolicyCardItem(
    CommissionPolicyModel policy,
    SelectedProject project,
  ) {
    final canPolicy = ref.can(Perm.salesPolicy, projectSlug: project.slug);
    final isActive = policy.isActive;
    final total = policy.totalFee;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(
          color: isActive
              ? const Color(0xFFEC4899).withAlpha(50)
              : context.colors.border,
          width: 0.8,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. 헤더: 정책명 + 상태 뱃지 + 차수/타입 뱃지 + [수정] 버튼
            Row(
              children: [
                Icon(
                  Icons.rule_folder_outlined,
                  size: 16,
                  color: isActive ? const Color(0xFFEC4899) : context.colors.textMuted,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    policy.name,
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 6),
                // 활성 뱃지
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                  decoration: BoxDecoration(
                    color: isActive
                        ? const Color(0xFF10B981).withAlpha(20)
                        : context.colors.borderSubtle,
                    border: Border.all(
                      color: isActive
                          ? const Color(0xFF10B981).withAlpha(80)
                          : context.colors.textMuted.withAlpha(60),
                      width: 0.8,
                    ),
                  ),
                  child: Text(
                    isActive ? '활성' : '비활성',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: isActive ? const Color(0xFF10B981) : context.colors.textMuted,
                    ),
                  ),
                ),
                if (canPolicy) ...[
                  const SizedBox(width: 8),
                  // 수정 버튼
                  InkWell(
                    onTap: () => showPolicyFormSheet(
                      context,
                      projectId: project.realProjectId,
                      existingPolicy: policy,
                    ),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.edit_outlined, size: 13, color: context.colors.textMuted),
                          const SizedBox(width: 3),
                          Text(
                            '수정',
                            style: TextStyle(
                              fontSize: 11,
                              color: context.colors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 6),

            // 차수 및 유니트 타입 배지
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                  decoration: BoxDecoration(
                    color: context.colors.bgSurface,
                    border: Border.all(color: context.colors.border, width: 0.7),
                  ),
                  child: Text(
                    policy.orderGroupName ?? '전체 차수 공통',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textSecond,
                      fontSize: 10,
                    ),
                  ),
                ),
                const SizedBox(width: 4),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                  decoration: BoxDecoration(
                    color: const Color(0xFF38BDF8).withAlpha(15),
                    border: Border.all(
                      color: const Color(0xFF38BDF8).withAlpha(60),
                      width: 0.7,
                    ),
                  ),
                  child: Text(
                    policy.unitTypeName ?? '전체 타입 공통',
                    style: const TextStyle(
                      fontSize: 10,
                      color: Color(0xFF0284C7),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Divider(color: context.colors.borderSubtle, height: 1),
            const SizedBox(height: 8),

            // 2. 건당 총 수수료 하이라이트
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '건당 총 수수료 (R값)',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textSecond,
                    fontWeight: FontWeight.w600,
                    fontSize: 11.5,
                  ),
                ),
                Text(
                  '₩ ${NumberFormat('#,###').format(total)}원',
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFFDB2777),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),

            // 3. 직책별 분배 시각화 바
            if (total > 0) ...[
              ClipRRect(
                borderRadius: BorderRadius.zero,
                child: Row(
                  children: [
                    if (policy.agentFee > 0)
                      Expanded(
                        flex: policy.agentFee,
                        child: Container(
                          height: 5,
                          color: const Color(0xFF38BDF8),
                        ),
                      ),
                    if (policy.leaderFee > 0)
                      Expanded(
                        flex: policy.leaderFee,
                        child: Container(
                          height: 5,
                          color: const Color(0xFF8B5CF6),
                        ),
                      ),
                    if (policy.directorFee > 0)
                      Expanded(
                        flex: policy.directorFee,
                        child: Container(
                          height: 5,
                          color: const Color(0xFFF59E0B),
                        ),
                      ),
                    if (policy.agencyFee > 0)
                      Expanded(
                        flex: policy.agencyFee,
                        child: Container(
                          height: 5,
                          color: const Color(0xFF10B981),
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
            ],

            // 4. 직책별 수수료 상세 그리드 (4개 컬럼)
            Row(
              children: [
                _buildRoleFeeCol('상담사', policy.agentFee, total, const Color(0xFF38BDF8)),
                _buildRoleFeeCol('팀장', policy.leaderFee, total, const Color(0xFF8B5CF6)),
                _buildRoleFeeCol('본부장', policy.directorFee, total, const Color(0xFFF59E0B)),
                _buildRoleFeeCol('대행사', policy.agencyFee, total, const Color(0xFF10B981)),
              ],
            ),
            const SizedBox(height: 8),
            Divider(color: context.colors.borderSubtle, height: 1),
            const SizedBox(height: 8),

            // 5. 지급 조건 & 적용 기간
            Row(
              children: [
                Icon(Icons.payment_outlined, size: 13, color: context.colors.textMuted),
                const SizedBox(width: 5),
                Expanded(
                  child: Text(
                    policy.payConditionDisplay ?? _getPayConditionLabel(policy.payCondition),
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textSecond,
                      fontSize: 11,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(Icons.calendar_today_outlined, size: 13, color: context.colors.textMuted),
                const SizedBox(width: 5),
                Text(
                  '적용기간: ${policy.startDate} ~ ${policy.endDate ?? "종료일 없음 (상시)"}',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRoleFeeCol(String role, int fee, int total, Color color) {
    final pct = total > 0 ? ((fee / total) * 100).toStringAsFixed(0) : '0';
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(width: 5, height: 5, color: color),
              const SizedBox(width: 3),
              Text(
                role,
                style: TextStyle(fontSize: 10, color: context.colors.textMuted),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Text(
            '${NumberFormat('#,###').format(fee)}원',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: context.colors.textPrimary,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          Text(
            '$pct%',
            style: TextStyle(
              fontSize: 9.5,
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  String _getPayConditionLabel(String code) {
    switch (code) {
      case '1':
        return '계약금 100% 완납 시 전액 지급';
      case '2':
        return '계약금 1차 50%, 2차 완납 50% 분할 지급';
      case '3':
        return '공급계약 체결 시 전액 지급';
      case '4':
        return '청약/가계약금 납부 시 선지급';
      default:
        return '계약금 100% 완납 시 전액 지급';
    }
  }

  Widget _buildInfoBanner({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: color.withAlpha(70), width: 1),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color.withAlpha(25),
              borderRadius: BorderRadius.zero,
              border: Border.all(color: color.withAlpha(70), width: 0.8),
            ),
            child: Icon(icon, size: 20, color: color),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: AppTextStyles.bodySecond.copyWith(
                    color: context.colors.textSecond,
                    fontSize: 12,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
