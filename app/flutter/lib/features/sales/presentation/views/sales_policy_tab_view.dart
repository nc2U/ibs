import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/sales_models.dart';
import '../../providers/sales_provider.dart';
import '../widgets/policy_form_sheet.dart';
import '../widgets/sales_common_widgets.dart';

/// 5. 수수료 정책 관리 탭 뷰 (실시간 API 연동 + 2×2 KPI + 차수/타입 필터 + R값 기준 카드 + 분배 시각화 바)
class SalesPolicyTabView extends ConsumerStatefulWidget {
  final SelectedProject project;

  const SalesPolicyTabView({
    super.key,
    required this.project,
  });

  @override
  ConsumerState<SalesPolicyTabView> createState() => _SalesPolicyTabViewState();
}

class _SalesPolicyTabViewState extends ConsumerState<SalesPolicyTabView> {
  final TextEditingController _policySearchController = TextEditingController();
  Timer? _policyDebounceTimer;

  @override
  void dispose() {
    _policySearchController.dispose();
    _policyDebounceTimer?.cancel();
    super.dispose();
  }

  void _onPolicySearchChanged(String value) {
    _policyDebounceTimer?.cancel();
    _policyDebounceTimer = Timer(const Duration(milliseconds: 300), () {
      if (!mounted) return;
      ref.read(policySearchQueryProvider.notifier).state = value.trim();
    });
  }

  @override
  Widget build(BuildContext context) {
    final summary = ref.watch(salesPolicySummaryProvider);
    final policiesAsync = ref.watch(salesPoliciesProvider);
    final filteredPolicies = ref.watch(filteredSalesPoliciesProvider);
    final orderGroups = ref.watch(orderGroupsProvider).valueOrNull ?? [];
    final unitTypes = ref.watch(unitTypesProvider).valueOrNull ?? [];

    return RefreshIndicator(
      color: const Color(0xFFEC4899),
      onRefresh: () async {
        await Future.wait([
          ref.refresh(salesPoliciesProvider.future),
          ref.refresh(orderGroupsProvider.future),
          ref.refresh(unitTypesProvider.future),
        ]);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 1. 2×2 수수료 정책 KPI 요약 대시보드
          _buildPolicyKpiSection(summary),
          const SizedBox(height: 14),

          // 2. 차수/타입 필터 & 검색창 + [+ 정책 등록] 버튼
          _buildPolicyFilterBar(widget.project, orderGroups, unitTypes),
          const SizedBox(height: 14),

          // 3. 수수료 정책 리스트
          _buildPolicyListSection(widget.project, policiesAsync, filteredPolicies),
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
              child: buildSingleKpiTile(
                context: context,
                label: '수수료 정책',
                value: '${NumberFormat('#,###').format(summary.totalCount)}개 기준',
                subText: '활성 ${summary.activeCount}개 / 비활성 ${summary.totalCount - summary.activeCount}개',
                accentColor: const Color(0xFFEC4899), // Rose
                icon: Icons.rule_folder_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: buildSingleKpiTile(
                context: context,
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
              child: buildSingleKpiTile(
                context: context,
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
              child: buildSingleKpiTile(
                context: context,
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
            borderRadius: BorderRadius.circular(6),
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
              ValueListenableBuilder<TextEditingValue>(
                valueListenable: _policySearchController,
                builder: (context, value, _) {
                  if (value.text.isEmpty) return const SizedBox.shrink();
                  return IconButton(
                    icon: const Icon(Icons.clear_rounded, size: 16),
                    onPressed: () {
                      _policySearchController.clear();
                      ref.read(policySearchQueryProvider.notifier).state = '';
                    },
                    color: context.colors.textMuted,
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                  );
                },
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
                    buildFilterChip(
                      context: context,
                      label: '활성만',
                      isSelected: activeFilter == 'true',
                      onTap: () => ref.read(policyActiveFilterProvider.notifier).state = 'true',
                      activeColor: const Color(0xFF10B981),
                    ),
                    const SizedBox(width: 6),
                    buildFilterChip(
                      context: context,
                      label: '전체',
                      isSelected: activeFilter == '',
                      onTap: () => ref.read(policyActiveFilterProvider.notifier).state = '',
                      activeColor: const Color(0xFFEC4899),
                    ),
                    const SizedBox(width: 6),
                    buildFilterChip(
                      context: context,
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
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
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
      error: (err, _) => buildErrorBanner(
        context: context,
        message: '수수료 정책 데이터를 불러오지 못했습니다: $err',
        onRetry: () => ref.invalidate(salesPoliciesProvider),
      ),
      data: (_) {
        if (filteredPolicies.isEmpty) {
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.circular(8),
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
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(6)),
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
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(8),
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
                    borderRadius: BorderRadius.circular(4),
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
                    borderRadius: BorderRadius.circular(4),
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
                    borderRadius: BorderRadius.circular(4),
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

            // 2. 건당 총 수수료 하이라이트 (VAT 별도 및 청구액)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '건당 공급가 (VAT 별도)',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textSecond,
                        fontWeight: FontWeight.w600,
                        fontSize: 11.5,
                      ),
                    ),
                    const SizedBox(height: 1),
                    Text(
                      '청구: ₩ ${NumberFormat('#,###').format(policy.totalBillingAmount)} (VAT 10% 포함)',
                      style: const TextStyle(
                        fontSize: 11,
                        color: Color(0xFFF59E0B),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
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
                borderRadius: BorderRadius.circular(3),
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
                    policy.payConditionDisplay ?? getPayConditionLabel(policy.payCondition),
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
}
