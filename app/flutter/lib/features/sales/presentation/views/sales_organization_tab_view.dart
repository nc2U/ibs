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
import '../widgets/agency_team_manage_sheet.dart';
import '../widgets/person_document_sheet.dart';
import '../widgets/person_form_sheet.dart';
import '../widgets/sales_common_widgets.dart';

/// 4. 영업 조직 관리 탭 뷰 (실시간 API 연동 + 2×2 KPI + 대행사/팀 계층 필터 + 인력 명부 + 원터치 통화/수정)
class SalesOrganizationTabView extends ConsumerStatefulWidget {
  final SelectedProject project;

  const SalesOrganizationTabView({
    super.key,
    required this.project,
  });

  @override
  ConsumerState<SalesOrganizationTabView> createState() => _SalesOrganizationTabViewState();
}

class _SalesOrganizationTabViewState extends ConsumerState<SalesOrganizationTabView> {
  final TextEditingController _orgSearchController = TextEditingController();
  Timer? _orgDebounceTimer;

  @override
  void dispose() {
    _orgSearchController.dispose();
    _orgDebounceTimer?.cancel();
    super.dispose();
  }

  void _onOrgSearchChanged(String value) {
    _orgDebounceTimer?.cancel();
    _orgDebounceTimer = Timer(const Duration(milliseconds: 300), () {
      if (!mounted) return;
      ref.read(orgSearchQueryProvider.notifier).state = value.trim();
    });
  }

  @override
  Widget build(BuildContext context) {
    final summary = ref.watch(salesOrganizationSummaryProvider);
    final agenciesAsync = ref.watch(salesAgenciesProvider);
    final teamsAsync = ref.watch(salesTeamsProvider);
    final personsAsync = ref.watch(salesPersonsProvider);
    final filteredPersons = ref.watch(filteredOrgPersonsProvider);

    return RefreshIndicator(
      color: const Color(0xFF6366F1),
      onRefresh: () async {
        await Future.wait([
          ref.refresh(salesAgenciesProvider.future),
          ref.refresh(salesTeamsProvider.future),
          ref.refresh(salesPersonsProvider.future),
        ]);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 1. 2×2 조직 KPI 요약 대시보드
          _buildOrgKpiSection(summary),
          const SizedBox(height: 14),

          // 2. 대행사 & 팀 계층 가로 필터 바 + [⚙️ 조직 관리] 버튼
          _buildOrgHierarchyFilterBar(
            widget.project,
            agenciesAsync.valueOrNull ?? [],
            teamsAsync.valueOrNull ?? [],
          ),
          const SizedBox(height: 12),

          // 3. 인력 검색창 & 직책/재직상태 필터 + [+ 인력 등록] 버튼
          _buildOrgPersonFilterBar(widget.project),
          const SizedBox(height: 14),

          // 4. 인력 명부 리스트
          _buildOrgPersonListSection(
            widget.project,
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
              child: buildSingleKpiTile(
                context: context,
                label: '분양 대행사',
                value: '${NumberFormat('#,###').format(summary.agencyCount)}개사',
                subText: '직영 $direct사 / 외주 ${outsourced > 0 ? outsourced : 0}사',
                accentColor: const Color(0xFF6366F1), // Indigo
                icon: Icons.corporate_fare_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: buildSingleKpiTile(
                context: context,
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
              child: buildSingleKpiTile(
                context: context,
                label: '총 등록 인력',
                value: '${NumberFormat('#,###').format(summary.totalPersons)}명',
                subText: '영업 인력 명부',
                accentColor: const Color(0xFF8B5CF6), // Violet
                icon: Icons.groups_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: buildSingleKpiTile(
                context: context,
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
                buildFilterChip(
                  context: context,
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
                  buildFilterChip(
                    context: context,
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
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
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
              ValueListenableBuilder<TextEditingValue>(
                valueListenable: _orgSearchController,
                builder: (context, value, _) {
                  if (value.text.isEmpty) return const SizedBox.shrink();
                  return IconButton(
                    icon: const Icon(Icons.clear_rounded, size: 16),
                    onPressed: () {
                      _orgSearchController.clear();
                      ref.read(orgSearchQueryProvider.notifier).state = '';
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

        // 2. 재직상태/직책 필터 칩스 + [+ 인력 등록] 버튼
        Row(
          children: [
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    buildFilterChip(
                      context: context,
                      label: '재직',
                      isSelected: statusFilter == '1',
                      onTap: () => ref.read(orgStatusFilterProvider.notifier).state = '1',
                      activeColor: const Color(0xFF10B981),
                    ),
                    const SizedBox(width: 6),
                    buildFilterChip(
                      context: context,
                      label: '전체 상태',
                      isSelected: statusFilter == '',
                      onTap: () => ref.read(orgStatusFilterProvider.notifier).state = '',
                      activeColor: const Color(0xFF8B5CF6),
                    ),
                    const SizedBox(width: 6),
                    buildFilterChip(
                      context: context,
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
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
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
      error: (err, _) => buildErrorBanner(
        context: context,
        message: '영업 인력 데이터를 불러오지 못했습니다: $err',
        onRetry: () => ref.invalidate(salesPersonsProvider),
      ),
      data: (_) {
        if (filteredPersons.isEmpty) {
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.circular(8),
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
        borderRadius: BorderRadius.circular(8),
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
                Flexible(
                  child: Text(
                    person.name,
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
                        makePhoneCall(context, person.phone!, targetName: person.name),
                    child: Container(
                      padding:
                          const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFF10B981).withAlpha(20),
                        borderRadius: BorderRadius.circular(4),
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
                Expanded(
                  child: InkWell(
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
                          Expanded(
                            child: Text(
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
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
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

            // 7. 비고
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
}
