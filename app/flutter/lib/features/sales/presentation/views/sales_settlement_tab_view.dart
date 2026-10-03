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
import '../widgets/payout_detail_sheet.dart';
import '../widgets/period_form_sheet.dart';
import '../widgets/person_payout_history_sheet.dart';
import '../widgets/sales_common_widgets.dart';

/// 2. 수수료 정산 관리 탭 뷰 (회차별 실적 집계, 2×2 KPI, 정산 명세, 3.3% 원천세, 대행사 정산, 환수금)
class SalesSettlementTabView extends ConsumerStatefulWidget {
  final SelectedProject project;

  const SalesSettlementTabView({
    super.key,
    required this.project,
  });

  @override
  ConsumerState<SalesSettlementTabView> createState() => _SalesSettlementTabViewState();
}

class _SalesSettlementTabViewState extends ConsumerState<SalesSettlementTabView> {
  final TextEditingController _settlementSearchController = TextEditingController();
  Timer? _settlementDebounceTimer;

  @override
  void initState() {
    super.initState();
    final currentQuery = ref.read(settlementSearchQueryProvider);
    if (currentQuery.isNotEmpty) {
      _settlementSearchController.text = currentQuery;
    }
  }

  @override
  void dispose() {
    _settlementSearchController.dispose();
    _settlementDebounceTimer?.cancel();
    super.dispose();
  }

  void _onSettlementSearchChanged(String value) {
    _settlementDebounceTimer?.cancel();
    _settlementDebounceTimer = Timer(const Duration(milliseconds: 300), () {
      if (!mounted) return;
      ref.read(settlementSearchQueryProvider.notifier).state = value.trim();
    });
  }

  Future<void> _handleGeneratePayouts(SettlementPeriodModel period) async {
    final repo = ref.read(salesRepositoryProvider);

    // 정산 실행 전 조직 건강성 사전 진단
    OrgHealthCheckResult? healthResult;
    try {
      healthResult = await repo.validateOrgHealth(period.project);
    } catch (_) {}

    if (!mounted) return;

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
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '【${period.title}】\n(대상 기간: ${period.startDate} ~ ${period.endDate})\n\n해당 기간 동안 발생한 계약 실적과 직책별 수수료 정책, 미상계 환수금을 집계하여 개인별 수수료 명세를 자동 산출하시겠습니까?',
                style: AppTextStyles.bodySm.copyWith(
                  color: context.colors.textSecond,
                  height: 1.4,
                ),
              ),
              if (healthResult != null && !healthResult.isHealthy) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFEF3C7),
                    border: Border.all(color: const Color(0xFFF59E0B), width: 0.8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.warning_amber_rounded, size: 16, color: Color(0xFFD97706)),
                          const SizedBox(width: 6),
                          Text(
                            '조직 구조 사전 점검 (주의 ${healthResult.warningCount}건 / 오류 ${healthResult.errorCount}건)',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF92400E),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      ...healthResult.items.map((item) {
                        return Padding(
                          padding: const EdgeInsets.only(top: 3),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                item.isError ? '• [오류] ' : '• [주의] ',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: item.isError ? const Color(0xFFDC2626) : const Color(0xFFD97706),
                                ),
                              ),
                              Expanded(
                                child: Text(
                                  item.message,
                                  style: const TextStyle(fontSize: 11, color: Color(0xFF78350F)),
                                ),
                              ),
                            ],
                          ),
                        );
                      }),
                      const SizedBox(height: 4),
                      const Text(
                        '* 팀장 부재 등 주의 항목은 상위 본부장 합산 또는 대행사 귀속 이익으로 자동 처리됩니다.',
                        style: TextStyle(fontSize: 10.5, color: Color(0xFFB45309)),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 10),
              Text(
                '※ 이미 산출된 명세가 있는 경우 최신 실적으로 재계산됩니다.',
                style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
              ),
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
      final res = await repo.generatePayouts(period.id);
      ref.invalidate(settlementPeriodsProvider);
      ref.invalidate(commissionPayoutsProvider);
      ref.invalidate(agencyPayoutsProvider);
      ref.invalidate(payoutTabPayoutsProvider);
      ref.invalidate(payoutTabAgencyPayoutsProvider);
      ref.invalidate(projectClawbacksProvider);

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
      ref.invalidate(agencyPayoutsProvider);
      ref.invalidate(payoutTabPayoutsProvider);
      ref.invalidate(payoutTabAgencyPayoutsProvider);

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

  bool periodIsDraft(SettlementPeriodModel period) => period.isDraft || period.status == '1';

  @override
  Widget build(BuildContext context) {
    // 프로젝트 변경 감지 시 검색어 및 필터 초기화
    ref.listen(selectedRealEstateProjectProvider, (previous, next) {
      if (previous?.realProjectId != next?.realProjectId) {
        _settlementDebounceTimer?.cancel();
        _settlementSearchController.clear();
        ref.read(settlementSearchQueryProvider.notifier).state = '';
        ref.read(settlementPayStatusFilterProvider.notifier).state = '';
        ref.read(settlementDutyFilterProvider.notifier).state = '';
      }
    });

    final periodsAsync = ref.watch(settlementPeriodsProvider);
    final currentPeriod = ref.watch(currentSettlementPeriodProvider);
    final payoutsAsync = ref.watch(commissionPayoutsProvider);
    final filteredPayouts = ref.watch(filteredCommissionPayoutsProvider);
    final agencyPayoutsAsync = ref.watch(agencyPayoutsProvider);
    final clawbacksAsync = ref.watch(projectClawbacksProvider);

    return RefreshIndicator(
      color: const Color(0xFF06B6D4),
      onRefresh: () async {
        await Future.wait([
          ref.refresh(settlementPeriodsProvider.future),
          ref.refresh(commissionPayoutsProvider.future),
          ref.refresh(agencyPayoutsProvider.future),
          ref.refresh(projectClawbacksProvider.future),
        ]);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 1. 상단 안내 배너
          buildInfoBanner(
            context: context,
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
            error: (err, _) => buildErrorBanner(
              context: context,
              message: '정산 회차 데이터를 불러오지 못했습니다: $err',
              onRetry: () => ref.invalidate(settlementPeriodsProvider),
            ),
            data: (periods) => _buildPeriodSection(widget.project, periods, currentPeriod),
          ),
          const SizedBox(height: 14),

          // 3. 2×2 정산 KPI 요약 대시보드
          _buildSettlementKpiSection(currentPeriod),
          const SizedBox(height: 14),

          // 4. 검색 & 상태/직책 필터 바
          _buildSettlementFilterBar(currentPeriod),
          const SizedBox(height: 14),

          // 5. 개인별 정산 명세 리스트
          _buildSettlementPayoutListSection(
            widget.project,
            currentPeriod,
            payoutsAsync,
            filteredPayouts,
          ),
          const SizedBox(height: 20),

          // 6. 대행사별 정산 명세 섹션 (외주/직영 포함)
          _buildSettlementAgencyPayoutSection(widget.project, currentPeriod, agencyPayoutsAsync),
          const SizedBox(height: 20),

          // 7. 프로젝트 수수료 환수(Clawback) 이력 섹션
          _buildSettlementClawbackSection(widget.project, currentPeriod, clawbacksAsync),
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
                child: buildSingleKpiTile(
                  context: context,
                  label: '정산 대상 실적',
                  value: '0건',
                  subText: '지급 대상자: 0명',
                  accentColor: const Color(0xFF06B6D4),
                  icon: Icons.assignment_turned_in_outlined,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: buildSingleKpiTile(
                  context: context,
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
                child: buildSingleKpiTile(
                  context: context,
                  label: '원천징수 세액 (3.3%)',
                  value: '0원',
                  subText: '소득세 3% + 지방세 0.3%',
                  accentColor: const Color(0xFFEF4444),
                  icon: Icons.receipt_long_outlined,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: buildSingleKpiTile(
                  context: context,
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
              child: buildSingleKpiTile(
                context: context,
                label: '운영인력 지급 총액 (세전)',
                value: '${NumberFormat('#,###').format(currentPeriod.totalGrossAmount)}원',
                subText: '정산 대상자: ${NumberFormat('#,###').format(currentPeriod.payoutCount)}명',
                accentColor: const Color(0xFF8B5CF6), // Violet
                icon: Icons.payments_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: buildSingleKpiTile(
                context: context,
                label: '원천징수 세액 (3.3%)',
                value: '${NumberFormat('#,###').format(currentPeriod.totalTaxAmount)}원',
                subText: '소득세 3% + 지방세 0.3%',
                accentColor: const Color(0xFFEF4444), // Red
                icon: Icons.receipt_long_outlined,
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
                label: '인력 총 실지급액 (세후)',
                value: '${NumberFormat('#,###').format(currentPeriod.totalNetAmount)}원',
                subText: currentPeriod.payoutDate != null
                    ? '지급 예정일: ${currentPeriod.payoutDate}'
                    : '실제 이체 필요 총액',
                accentColor: const Color(0xFF10B981), // Emerald
                icon: Icons.account_balance_wallet_outlined,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Builder(
                builder: (context) {
                  final agencyPayouts = ref.watch(agencyPayoutsProvider).valueOrNull ?? [];
                  final totalUnallocated = agencyPayouts.fold<int>(
                    0,
                    (sum, ap) => sum + ap.unallocatedFee,
                  );

                  final subText = totalUnallocated > 0
                      ? '총 ${NumberFormat('#,###').format(currentPeriod.totalContracts)}건 · 귀속이익: ${NumberFormat('#,###').format(totalUnallocated)}원'
                      : '총 ${NumberFormat('#,###').format(currentPeriod.totalContracts)}건 (공급가: ${NumberFormat('#,###').format(currentPeriod.billingSupplyPrice > 0 ? currentPeriod.billingSupplyPrice : currentPeriod.totalGrossAmount)}원)';

                  return buildSingleKpiTile(
                    context: context,
                    label: '시행사 청구 금액 (VAT포함)',
                    value: '${NumberFormat('#,###').format(currentPeriod.billingTotalAmount > 0 ? currentPeriod.billingTotalAmount : (currentPeriod.totalGrossAmount * 1.1).floor())}원',
                    subText: subText,
                    accentColor: const Color(0xFFF59E0B), // Amber
                    icon: Icons.request_quote_outlined,
                  );
                },
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
          child: ValueListenableBuilder<TextEditingValue>(
            valueListenable: _settlementSearchController,
            builder: (context, value, _) => TextField(
              controller: _settlementSearchController,
              onChanged: _onSettlementSearchChanged,
              style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
              decoration: InputDecoration(
                isDense: true,
                hintText: '성명, 소속팀, 예금주 검색...',
                hintStyle: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                prefixIcon: Icon(Icons.search, size: 18, color: context.colors.textMuted),
                suffixIcon: value.text.isNotEmpty
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
              buildFilterChip(
                context: context,
                label: '전체',
                isSelected: payStatusFilter.isEmpty,
                onTap: () => ref.read(settlementPayStatusFilterProvider.notifier).state = '',
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '대기',
                isSelected: payStatusFilter == '1',
                onTap: () => ref.read(settlementPayStatusFilterProvider.notifier).state = '1',
                activeColor: const Color(0xFFF59E0B),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '승인',
                isSelected: payStatusFilter == '2',
                onTap: () => ref.read(settlementPayStatusFilterProvider.notifier).state = '2',
                activeColor: const Color(0xFF0284C7),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '완료',
                isSelected: payStatusFilter == '3',
                onTap: () => ref.read(settlementPayStatusFilterProvider.notifier).state = '3',
                activeColor: const Color(0xFF10B981),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '보류',
                isSelected: payStatusFilter == '4',
                onTap: () => ref.read(settlementPayStatusFilterProvider.notifier).state = '4',
                activeColor: const Color(0xFFEF4444),
              ),

              const SizedBox(width: 14),
              Container(width: 1, height: 16, color: context.colors.borderSubtle),
              const SizedBox(width: 14),

              Text(
                '직책: ',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
              buildFilterChip(
                context: context,
                label: '전체',
                isSelected: dutyFilter.isEmpty,
                onTap: () => ref.read(settlementDutyFilterProvider.notifier).state = '',
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '본부장',
                isSelected: dutyFilter == '본부장',
                onTap: () => ref.read(settlementDutyFilterProvider.notifier).state =
                    dutyFilter == '본부장' ? '' : '본부장',
                activeColor: const Color(0xFF8B5CF6),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '팀장',
                isSelected: dutyFilter == '팀장',
                onTap: () => ref.read(settlementDutyFilterProvider.notifier).state =
                    dutyFilter == '팀장' ? '' : '팀장',
                activeColor: const Color(0xFF0284C7),
              ),
              const SizedBox(width: 4),
              buildFilterChip(
                context: context,
                label: '상담사',
                isSelected: dutyFilter == '상담사',
                onTap: () => ref.read(settlementDutyFilterProvider.notifier).state =
                    dutyFilter == '상담사' ? '' : '상담사',
                activeColor: const Color(0xFF10B981),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// 개인별 수수료 정산 명세 목록 섹션
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
      error: (err, _) => buildErrorBanner(
        context: context,
        message: '수수료 정산 명세를 불러오지 못했습니다: $err',
        onRetry: () => ref.invalidate(commissionPayoutsProvider),
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
                    InkWell(
                      onTap: () {
                        showPersonPayoutHistorySheet(
                          context,
                          salesPersonId: item.salesPerson,
                          salesPersonName: item.salesPersonName ?? '미지정',
                          teamName: item.teamName,
                          dutyDisplay: item.dutyDisplay,
                        );
                      },
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            item.salesPersonName ?? '미지정',
                            style: AppTextStyles.titleSm.copyWith(
                              color: const Color(0xFF06B6D4),
                              fontWeight: FontWeight.bold,
                              decoration: TextDecoration.underline,
                            ),
                          ),
                          const SizedBox(width: 3),
                          const Icon(Icons.history_rounded, size: 14, color: Color(0xFF06B6D4)),
                        ],
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

  // ── 대행사별 정산 명세 섹션 (외주 대행사 직배정 수수료 포함) ──
  Widget _buildSettlementAgencyPayoutSection(
    SelectedProject project,
    SettlementPeriodModel? currentPeriod,
    AsyncValue<List<AgencyPayoutModel>> agencyPayoutsAsync,
  ) {
    return agencyPayoutsAsync.when(
      loading: () => const SizedBox.shrink(),
      error: (err, _) => buildErrorBanner(
        context: context,
        message: '대행사 정산 명세를 불러오지 못했습니다: $err',
        onRetry: () => ref.invalidate(agencyPayoutsProvider),
      ),
      data: (agencyPayouts) {
        if (agencyPayouts.isEmpty) return const SizedBox.shrink();

        return Container(
          decoration: BoxDecoration(
            color: context.colors.bgCard,
            border: Border.all(color: context.colors.border, width: 0.8),
          ),
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.business_center_outlined, size: 18, color: Color(0xFF06B6D4)),
                      const SizedBox(width: 6),
                      Text(
                        '대행사 정산 명세 (${agencyPayouts.length}개사)',
                        style: AppTextStyles.titleSm.copyWith(
                          fontWeight: FontWeight.bold,
                          color: context.colors.textPrimary,
                        ),
                      ),
                    ],
                  ),
                  Text(
                    '외주 대행사 총액 정산 포함',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textMuted,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              ...agencyPayouts.map((ap) {
                final fmt = NumberFormat('#,###');
                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: context.colors.bgSurface,
                    border: Border.all(color: context.colors.border, width: 0.5),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Text(
                                ap.agencyName ?? '대행사',
                                style: AppTextStyles.bodySm.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: context.colors.textPrimary,
                                ),
                              ),
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                                decoration: BoxDecoration(
                                  color: ap.isDirectManaged
                                      ? const Color(0xFF0284C7).withAlpha(25)
                                      : const Color(0xFF8B5CF6).withAlpha(25),
                                ),
                                child: Text(
                                  ap.isDirectManaged ? '직영' : '외주',
                                  style: TextStyle(
                                    fontSize: 9.5,
                                    fontWeight: FontWeight.bold,
                                    color: ap.isDirectManaged
                                        ? const Color(0xFF0284C7)
                                        : const Color(0xFF8B5CF6),
                                  ),
                                ),
                              ),
                            ],
                          ),
                          Text(
                            '${fmt.format(ap.totalAmount)}원 (VAT포함)',
                            style: AppTextStyles.bodySm.copyWith(
                              fontWeight: FontWeight.bold,
                              color: const Color(0xFF06B6D4),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '계약: ${ap.contractCount}건 | 공급가액: ${fmt.format(ap.agencyFeeSum)}원',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textSecond,
                              fontSize: 10.5,
                            ),
                          ),
                          if (ap.unallocatedFee > 0)
                            Text(
                              '시행사 귀속: ${fmt.format(ap.unallocatedFee)}원',
                              style: AppTextStyles.caption.copyWith(
                                color: const Color(0xFF10B981),
                                fontSize: 10.5,
                              ),
                            ),
                        ],
                      ),
                    ],
                  ),
                );
              }),
            ],
          ),
        );
      },
    );
  }

  // ── 수수료 환수(Clawback) 이력 섹션 ───────────────────────
  Widget _buildSettlementClawbackSection(
    SelectedProject project,
    SettlementPeriodModel? currentPeriod,
    AsyncValue<List<CommissionClawbackModel>> clawbacksAsync,
  ) {
    return clawbacksAsync.when(
      loading: () => const SizedBox.shrink(),
      error: (err, _) => buildErrorBanner(
        context: context,
        message: '환수금 목록을 불러오지 못했습니다: $err',
        onRetry: () => ref.invalidate(projectClawbacksProvider),
      ),
      data: (clawbacks) {
        if (clawbacks.isEmpty) return const SizedBox.shrink();

        final fmt = NumberFormat('#,###');
        final totalAmount = clawbacks.fold<int>(0, (sum, c) => sum + c.amount);
        final unsettledCount = clawbacks.where((c) => !c.isSettled).length;

        return Container(
          decoration: BoxDecoration(
            color: const Color(0xFFEF4444).withAlpha(10),
            border: Border.all(color: const Color(0xFFEF4444).withAlpha(60), width: 0.8),
          ),
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.currency_exchange_rounded, size: 18, color: Color(0xFFEF4444)),
                      const SizedBox(width: 6),
                      Text(
                        '수수료 환수(Clawback) 이력 (${clawbacks.length}건)',
                        style: AppTextStyles.titleSm.copyWith(
                          fontWeight: FontWeight.bold,
                          color: const Color(0xFFEF4444),
                        ),
                      ),
                    ],
                  ),
                  Text(
                    '미상계 $unsettledCount건',
                    style: AppTextStyles.caption.copyWith(
                      fontWeight: FontWeight.bold,
                      color: const Color(0xFFEF4444),
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                '해지 계약에 의해 발생한 환수금으로 차기 정산 시 자동 상계 처리됩니다. 총 환수: ${fmt.format(totalAmount)}원',
                style: AppTextStyles.caption.copyWith(color: context.colors.textSecond, fontSize: 11),
              ),
              const SizedBox(height: 10),
              ...clawbacks.map((c) {
                return Container(
                  margin: const EdgeInsets.only(bottom: 6),
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: context.colors.bgCard,
                    border: Border.all(color: context.colors.border, width: 0.5),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                        decoration: BoxDecoration(
                          color: c.isSettled
                              ? const Color(0xFF10B981).withAlpha(20)
                              : const Color(0xFFEF4444).withAlpha(20),
                        ),
                        child: Text(
                          c.isSettled ? '상계완료' : '미상계',
                          style: TextStyle(
                            fontSize: 9.5,
                            fontWeight: FontWeight.bold,
                            color: c.isSettled ? const Color(0xFF10B981) : const Color(0xFFEF4444),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${c.salesPersonName ?? "인력"} • 계약 ${c.contractSerial ?? "#${c.contract}"}',
                              style: AppTextStyles.bodySm.copyWith(
                                fontWeight: FontWeight.w600,
                                color: context.colors.textPrimary,
                                fontSize: 11.5,
                              ),
                            ),
                            Text(
                              c.reason.isNotEmpty ? c.reason : '해약에 따른 수수료 환수',
                              style: AppTextStyles.caption.copyWith(
                                color: context.colors.textMuted,
                                fontSize: 10.5,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                      Text(
                        '-${fmt.format(c.amount)}원',
                        style: AppTextStyles.bodySm.copyWith(
                          fontWeight: FontWeight.bold,
                          color: const Color(0xFFEF4444),
                        ),
                      ),
                    ],
                  ),
                );
              }),
            ],
          ),
        );
      },
    );
  }
}
