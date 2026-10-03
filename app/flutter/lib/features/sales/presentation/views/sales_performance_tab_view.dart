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
import '../../data/sales_repository.dart';
import '../../providers/sales_provider.dart';
import '../widgets/contract_agent_form_sheet.dart';
import '../widgets/sales_common_widgets.dart';

/// 1. 계약 실적 관리 탭 뷰 (계약별 실적, 2×2 KPI, 필터/검색, 상담사 배정, 정산 승인 토글)
class SalesPerformanceTabView extends ConsumerStatefulWidget {
  final SelectedProject project;

  const SalesPerformanceTabView({
    super.key,
    required this.project,
  });

  @override
  ConsumerState<SalesPerformanceTabView> createState() => _SalesPerformanceTabViewState();
}

class _SalesPerformanceTabViewState extends ConsumerState<SalesPerformanceTabView> {
  final TextEditingController _searchController = TextEditingController();
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    final currentQuery = ref.read(salesSearchQueryProvider);
    if (currentQuery.isNotEmpty) {
      _searchController.text = currentQuery;
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    _debounceTimer?.cancel();
    super.dispose();
  }

  void _onSearchChanged(String value) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      if (!mounted) return;
      ref.read(salesSearchQueryProvider.notifier).state = value.trim();
    });
  }

  @override
  Widget build(BuildContext context) {
    // 프로젝트 변경 감지 시 검색어 및 필터 초기화
    ref.listen(selectedRealEstateProjectProvider, (previous, next) {
      if (previous?.realProjectId != next?.realProjectId) {
        _debounceTimer?.cancel();
        _searchController.clear();
        ref.read(salesSearchQueryProvider.notifier).state = '';
        ref.read(salesMappingStatusFilterProvider.notifier).state = SalesMappingStatusFilter.all;
        ref.read(salesTeamFilterProvider.notifier).state = null;
      }
    });

    final summary = ref.watch(salesPerformanceSummaryProvider);
    final combinedAsync = ref.watch(combinedContractPerformanceProvider);
    final filteredItems = ref.watch(filteredContractPerformanceProvider);
    final persons = ref.watch(salesPersonsProvider).valueOrNull ?? [];

    return RefreshIndicator(
      color: const Color(0xFF8B5CF6),
      onRefresh: () async {
        await Future.wait([
          ref.refresh(simpleContractsProvider.future),
          ref.refresh(rawContractSalesAgentsProvider.future),
          ref.refresh(salesTeamsProvider.future),
          ref.refresh(salesPersonsProvider.future),
          ref.refresh(salesPoliciesProvider.future),
        ]);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 1. 2×2 실시간 실적 KPI 대시보드
          _buildPerformanceKpiSection(summary),
          const SizedBox(height: 14),

          // 2. 검색 및 필터 바
          _buildFilterAndSearchBar(widget.project, summary),
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
            error: (err, _) => buildErrorBanner(
              context: context,
              message: '실적 데이터를 불러오지 못했습니다: $err',
              onRetry: () {
                ref.invalidate(simpleContractsProvider);
                ref.invalidate(rawContractSalesAgentsProvider);
                ref.invalidate(salesTeamsProvider);
                ref.invalidate(salesPersonsProvider);
                ref.invalidate(salesPoliciesProvider);
              },
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
                      Icon(Icons.assignment_late_outlined, size: 40, color: context.colors.textMuted),
                      const SizedBox(height: 12),
                      Text(
                        '조건에 일치하는 계약 실적 내역이 없습니다',
                        style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '검색어나 선택된 필터 조건을 변경해 보세요.',
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                      ),
                    ],
                  ),
                );
              }

              return Column(
                children: filteredItems.map((item) {
                  return _buildPerformanceCardItem(item, widget.project, persons);
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
              child: buildSingleKpiTile(
                context: context,
                label: '총 분양 계약',
                value: '${NumberFormat('#,###').format(summary.totalContracts)}건',
                subText: '프로젝트 전체 계약',
                accentColor: const Color(0xFF38BDF8), // Sky Blue
                icon: Icons.assignment_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: buildSingleKpiTile(
                context: context,
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
              child: buildSingleKpiTile(
                context: context,
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
              child: buildSingleKpiTile(
                context: context,
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
              ValueListenableBuilder<TextEditingValue>(
                valueListenable: _searchController,
                builder: (context, value, _) {
                  if (value.text.isEmpty) return const SizedBox.shrink();
                  return IconButton(
                    icon: const Icon(Icons.clear_rounded, size: 16),
                    onPressed: () {
                      _searchController.clear();
                      ref.read(salesSearchQueryProvider.notifier).state = '';
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
        const SizedBox(height: 10),

        // 필터 칩스 + 신규 배정 버튼
        Row(
          children: [
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    buildFilterChip(
                      context: context,
                      label: '전체 ${summary.totalContracts}',
                      isSelected: statusFilter == SalesMappingStatusFilter.all,
                      onTap: () => ref.read(salesMappingStatusFilterProvider.notifier).state =
                          SalesMappingStatusFilter.all,
                    ),
                    const SizedBox(width: 6),
                    buildFilterChip(
                      context: context,
                      label: '배정 완료 ${summary.mappedCount}',
                      isSelected: statusFilter == SalesMappingStatusFilter.mapped,
                      onTap: () => ref.read(salesMappingStatusFilterProvider.notifier).state =
                          SalesMappingStatusFilter.mapped,
                      activeColor: const Color(0xFF10B981),
                    ),
                    const SizedBox(width: 6),
                    buildFilterChip(
                      context: context,
                      label: '미배정 ${summary.unmappedCount}',
                      isSelected: statusFilter == SalesMappingStatusFilter.unmapped,
                      onTap: () => ref.read(salesMappingStatusFilterProvider.notifier).state =
                          SalesMappingStatusFilter.unmapped,
                      activeColor: const Color(0xFFF59E0B),
                    ),
                    const SizedBox(width: 6),
                    buildFilterChip(
                      context: context,
                      label: '정산 승인',
                      isSelected: statusFilter == SalesMappingStatusFilter.approved,
                      onTap: () => ref.read(salesMappingStatusFilterProvider.notifier).state =
                          SalesMappingStatusFilter.approved,
                      activeColor: const Color(0xFF10B981),
                    ),
                    const SizedBox(width: 6),
                    buildFilterChip(
                      context: context,
                      label: '정산 보류',
                      isSelected: statusFilter == SalesMappingStatusFilter.pending,
                      onTap: () => ref.read(salesMappingStatusFilterProvider.notifier).state =
                          SalesMappingStatusFilter.pending,
                      activeColor: const Color(0xFFEF4444),
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
                if (isMapped) ...[
                  // 정산 확정 반영 뱃지
                  if (item.isSettled) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFF6366F1).withAlpha(15),
                        border: Border.all(color: const Color(0xFF6366F1).withAlpha(70), width: 0.8),
                      ),
                      child: Text(
                        item.settledPeriodTitle != null && item.settledPeriodTitle!.isNotEmpty
                            ? '정산: ${item.settledPeriodTitle}'
                            : '기정산',
                        style: const TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF6366F1),
                        ),
                      ),
                    ),
                    const SizedBox(width: 4),
                  ],

                  // 정산 승인 / 보류 뱃지 (관리 권한 시 클릭 토글 가능)
                  InkWell(
                    onTap: canManage ? () => _showSettlementApprovalDialog(item) : null,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: item.isSettlementApproved
                            ? const Color(0xFF10B981).withAlpha(15)
                            : const Color(0xFFEF4444).withAlpha(15),
                        border: Border.all(
                          color: item.isSettlementApproved
                              ? const Color(0xFF10B981).withAlpha(70)
                              : const Color(0xFFEF4444).withAlpha(70),
                          width: 0.8,
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            item.isSettlementApproved ? Icons.check_circle_outline : Icons.error_outline,
                            size: 11,
                            color: item.isSettlementApproved ? const Color(0xFF10B981) : const Color(0xFFEF4444),
                          ),
                          const SizedBox(width: 3),
                          Text(
                            item.isSettlementApproved ? '정산 승인' : '정산 보류',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: item.isSettlementApproved ? const Color(0xFF10B981) : const Color(0xFFEF4444),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 4),
                ],
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
              // 담당 상담사 & 소속 팀 (또는 외주 대행사)
              Row(
                children: [
                  if (!item.isDirectManaged || item.salesPersonName == null) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFFD1FAE5),
                        border: Border.all(color: const Color(0xFF10B981), width: 0.8),
                      ),
                      child: const Text(
                        '외주 대행',
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF047857),
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      item.agencyName ?? '외주 대행사',
                      style: AppTextStyles.bodySecond.copyWith(
                        color: const Color(0xFF047857),
                        fontWeight: FontWeight.bold,
                        fontSize: 12.5,
                      ),
                    ),
                  ] else ...[
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
              if (!item.isSettlementApproved && item.approvalNote != null && item.approvalNote!.isNotEmpty) ...[
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Icon(Icons.info_outline, size: 12, color: Color(0xFFEF4444)),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        '정산 보류 사유: ${item.approvalNote}',
                        style: AppTextStyles.caption.copyWith(
                          color: const Color(0xFFEF4444),
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
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
                    onTap: () => makePhoneCall(context, matchedPerson!.phone!, targetName: item.salesPersonName),
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
                    onTap: () => makePhoneCall(context, item.mgmPhone!, targetName: 'MGM ${item.mgmName}'),
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

  /// 계약 영업 담당자의 수수료 정산 승인 / 보류 설정 다이얼로그
  Future<void> _showSettlementApprovalDialog(CombinedContractPerformanceItem item) async {
    if (item.mapping == null) return;
    final mapping = item.mapping!;
    bool isApproved = mapping.isSettlementApproved;
    final noteController = TextEditingController(text: mapping.approvalNote ?? '');

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModalState) {
          return AlertDialog(
            backgroundColor: context.colors.bgCard,
            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            title: Row(
              children: [
                Icon(
                  Icons.verified_outlined,
                  size: 20,
                  color: isApproved ? const Color(0xFF10B981) : const Color(0xFFEF4444),
                ),
                const SizedBox(width: 8),
                Text(
                  '수수료 정산 승인 / 보류 설정',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            content: SizedBox(
              width: 400,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 계약 및 담당자 요약
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: context.colors.bgSurface,
                      border: Border.all(color: context.colors.border, width: 0.8),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.contractLabel,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12.5),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '담당 상담사: ${item.salesPersonName ?? '미지정'} (${item.teamName ?? '소속 팀 없음'})',
                          style: TextStyle(fontSize: 11.5, color: context.colors.textSecond),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // 상태 토글 스위치/라디오
                  Text(
                    '정산 대상 승인 상태',
                    style: AppTextStyles.caption.copyWith(
                      fontWeight: FontWeight.bold,
                      color: context.colors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Expanded(
                        child: InkWell(
                          onTap: () => setModalState(() => isApproved = true),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
                            decoration: BoxDecoration(
                              color: isApproved
                                  ? const Color(0xFF10B981).withAlpha(20)
                                  : context.colors.bgSurface,
                              border: Border.all(
                                color: isApproved ? const Color(0xFF10B981) : context.colors.border,
                                width: isApproved ? 1.5 : 0.8,
                              ),
                            ),
                            child: const Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.check_circle, size: 14, color: Color(0xFF10B981)),
                                SizedBox(width: 4),
                                Text(
                                  '정산 승인',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFF10B981),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: InkWell(
                          onTap: () => setModalState(() => isApproved = false),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
                            decoration: BoxDecoration(
                              color: !isApproved
                                  ? const Color(0xFFEF4444).withAlpha(20)
                                  : context.colors.bgSurface,
                              border: Border.all(
                                color: !isApproved ? const Color(0xFFEF4444) : context.colors.border,
                                width: !isApproved ? 1.5 : 0.8,
                              ),
                            ),
                            child: const Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.error_outline, size: 14, color: Color(0xFFEF4444)),
                                SizedBox(width: 4),
                                Text(
                                  '정산 보류 (미승인)',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFFEF4444),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    isApproved
                        ? '※ 정산 회차 자동 계산 시 수수료 대상에 정상 반영됩니다.'
                        : '※ 서류 미비/분납 등으로 이번 정산 회차에서 자동으로 제외됩니다.',
                    style: TextStyle(fontSize: 10.5, color: context.colors.textMuted),
                  ),

                  // 보류 사유 입력창
                  if (!isApproved) ...[
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: noteController,
                      maxLines: 2,
                      decoration: InputDecoration(
                        labelText: '정산 보류 사유',
                        hintText: '예: 계약금 2차 분납 500만원 미납, 서류 미비 등',
                        hintStyle: TextStyle(fontSize: 11, color: context.colors.textMuted),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: const Color(0xFFEF4444).withAlpha(80)),
                        ),
                      ),
                      style: const TextStyle(fontSize: 12),
                    ),
                  ],
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
              ),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: isApproved ? const Color(0xFF10B981) : const Color(0xFFEF4444),
                  foregroundColor: Colors.white,
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                ),
                onPressed: () => Navigator.pop(ctx, true),
                child: Text(isApproved ? '승인으로 저장' : '보류로 저장'),
              ),
            ],
          );
        },
      ),
    );

    if (result != true || !mounted) return;

    try {
      final repo = ref.read(salesRepositoryProvider);
      await repo.toggleSettlementApproval(
        mapping.id,
        isApproved: isApproved,
        approvalNote: noteController.text.trim(),
      );
      ref.invalidate(rawContractSalesAgentsProvider);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            isApproved ? '정산 승인 상태로 변경되었습니다.' : '정산 보류 상태로 변경되었습니다.',
          ),
          backgroundColor: isApproved ? const Color(0xFF10B981) : const Color(0xFFEF4444),
          duration: const Duration(seconds: 1),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('정산 승인 상태 변경 실패: $e'),
          backgroundColor: context.colors.error,
        ),
      );
    }
  }
}
