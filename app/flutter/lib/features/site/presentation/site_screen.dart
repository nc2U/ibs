import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/constants/permissions.dart';
import '../../../core/providers/permission_provider.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../data/models/site_models.dart';
import '../providers/site_provider.dart';
import 'views/site_contract_tab_view.dart';
import 'views/site_owner_tab_view.dart';
import 'views/site_parcel_tab_view.dart';
import 'widgets/site_common_widgets.dart';
import 'widgets/site_file_helper.dart';

/// 🗺️ 사업 부지 관리 (Site) 메인 화면 컨테이너
///
/// 3개 서브 탭 뷰를 라우팅/스위칭하며 권한별 접근 제어 및 프로젝트 변경 상태 초기화를 총괄합니다:
/// 1. [SiteParcelTabView]: 지번별 사업부지 필지 관리
/// 2. [SiteOwnerTabView]: 토지 소유자 및 상담일지 관리
/// 3. [SiteContractTabView]: 사업부지 매입계약 관리
class SiteScreen extends ConsumerStatefulWidget {
  final VoidCallback onBackToMain;

  const SiteScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  ConsumerState<SiteScreen> createState() => _SiteScreenState();
}

class _SiteScreenState extends ConsumerState<SiteScreen> {
  final TextEditingController _searchController = TextEditingController();
  Timer? _debounceTimer;

  @override
  void dispose() {
    _searchController.dispose();
    _debounceTimer?.cancel();
    super.dispose();
  }

  /// 프로젝트 변경 시 검색어 및 필터 초기화
  void _resetAllFiltersAndSearch() {
    _searchController.clear();
    ref.read(siteSearchQueryProvider.notifier).state = '';
    ref.read(siteOwnSortFilterProvider.notifier).state = '';
    ref.invalidate(siteOverallAggregateProvider);
    ref.invalidate(siteListProvider);
    ref.invalidate(siteOwnerListProvider);
    ref.invalidate(siteContractListProvider);
  }

  /// 검색어 변경 (300ms 디바운스)
  void _onSearchChanged(String query) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      ref.read(siteSearchQueryProvider.notifier).state = query.trim();
      final currentTab = ref.read(siteCurrentSubTabProvider);
      switch (currentTab) {
        case SiteSubTab.sites:
          ref.invalidate(siteListProvider);
          break;
        case SiteSubTab.owners:
          ref.invalidate(siteOwnerListProvider);
          break;
        case SiteSubTab.contracts:
          ref.invalidate(siteContractListProvider);
          break;
      }
    });
  }

  void _onClearSearch() {
    _searchController.clear();
    _onSearchChanged('');
  }

  void _refreshAll() {
    ref.invalidate(siteOverallAggregateProvider);
    final currentTab = ref.read(siteCurrentSubTabProvider);
    switch (currentTab) {
      case SiteSubTab.sites:
        ref.invalidate(siteListProvider);
        break;
      case SiteSubTab.owners:
        ref.invalidate(siteOwnerListProvider);
        break;
      case SiteSubTab.contracts:
        ref.invalidate(siteContractListProvider);
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    // ── 🔄 프로젝트 변경 감지 리스너 ──
    ref.listen(selectedRealEstateProjectProvider, (previous, next) {
      if (previous?.realProjectId != next?.realProjectId) {
        _resetAllFiltersAndSearch();
      }
    });

    final selectedProject = ref.watch(selectedRealEstateProjectProvider);
    final projectSlug = selectedProject?.slug;
    final canRead = ref.can(Perm.siteRead, projectSlug: projectSlug);

    // 1. 프로젝트 미선택 시
    if (selectedProject == null) {
      return Scaffold(
        backgroundColor: context.colors.bgPrimary,
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.terrain_outlined, size: 48, color: context.colors.textMuted),
              const SizedBox(height: 12),
              Text(
                '선택된 프로젝트가 없습니다.',
                style: AppTextStyles.titleSm.copyWith(color: context.colors.textSecond),
              ),
              const SizedBox(height: 6),
              Text(
                '상단에서 프로젝트를 먼저 선택해주세요.',
                style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
              ),
            ],
          ),
        ),
      );
    }

    // 2. 권한 미보유 시
    if (!canRead) {
      return Scaffold(
        backgroundColor: context.colors.bgPrimary,
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.lock_outline_rounded, size: 48, color: Color(0xFFEF4444)),
              const SizedBox(height: 12),
              Text(
                '사업부지 관리 접근 권한이 없습니다.',
                style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary),
              ),
              const SizedBox(height: 6),
              Text(
                '프로젝트 관리자에게 권한(site.read)을 요청하세요.',
                style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
              ),
            ],
          ),
        ),
      );
    }

    final aggregateAsync = ref.watch(siteOverallAggregateProvider);
    final currentTab = ref.watch(siteCurrentSubTabProvider);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: Column(
        children: [
          // ── A. 부지 관리 상단 헤더 ──
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
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
                    color: const Color(0xFF0D9488).withAlpha(26),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.map_outlined,
                    size: 20,
                    color: Color(0xFF0D9488),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Text(
                            '부지 정보 관리',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                            decoration: BoxDecoration(
                              color: const Color(0xFF0D9488).withAlpha(20),
                              border: Border.all(color: const Color(0xFF0D9488).withAlpha(120), width: 0.8),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Text(
                              'SITE',
                              style: TextStyle(
                                fontSize: 9.5,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF0D9488),
                                letterSpacing: 0.6,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        selectedProject.name,
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                // 📊 Excel 다운로드 버튼
                IconButton(
                  onPressed: () => SiteFileHelper.downloadAndShareCurrentTabExcel(
                    context: context,
                    ref: ref,
                  ),
                  icon: const Icon(Icons.file_download_outlined, size: 20),
                  tooltip: '엑셀 다운로드',
                  color: context.colors.textSecond,
                ),
                // 🔄 새로고침 버튼
                IconButton(
                  onPressed: _refreshAll,
                  icon: const Icon(Icons.refresh_rounded, size: 20),
                  tooltip: '새로고침',
                  color: context.colors.textSecond,
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── B. 부지 종합 집계 대시보드 (KPI) ──
          aggregateAsync.when(
            loading: () => const SizedBox(
              height: 70,
              child: Center(
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            ),
            error: (_, __) => const SizedBox.shrink(),
            data: (aggregate) => _buildAggregateDashboard(aggregate),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── C. 3대 서브 탭 바 ──
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
            child: Row(
              children: [
                SiteSubTabButton(
                  title: '지번별 토지',
                  icon: Icons.pin_drop_outlined,
                  isSelected: currentTab == SiteSubTab.sites,
                  onTap: () {
                    ref.read(siteCurrentSubTabProvider.notifier).state = SiteSubTab.sites;
                  },
                ),
                const SizedBox(width: 6),
                SiteSubTabButton(
                  title: '소유자별',
                  icon: Icons.person_outline_rounded,
                  isSelected: currentTab == SiteSubTab.owners,
                  onTap: () {
                    ref.read(siteCurrentSubTabProvider.notifier).state = SiteSubTab.owners;
                  },
                ),
                const SizedBox(width: 6),
                SiteSubTabButton(
                  title: '매입 계약',
                  icon: Icons.receipt_long_outlined,
                  isSelected: currentTab == SiteSubTab.contracts,
                  onTap: () {
                    ref.read(siteCurrentSubTabProvider.notifier).state = SiteSubTab.contracts;
                  },
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── D. 통합 검색창 ──
          Container(
            color: context.colors.bgCard,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Container(
              height: 38,
              decoration: BoxDecoration(
                color: context.colors.bgSurface,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: TextField(
                controller: _searchController,
                onChanged: _onSearchChanged,
                style: AppTextStyles.bodySecond.copyWith(
                  color: context.colors.textPrimary,
                  fontSize: 13,
                ),
                decoration: InputDecoration(
                  isDense: true,
                  hintText: currentTab == SiteSubTab.sites
                      ? '지번, 행정동, 지목, 소유자 검색...'
                      : (currentTab == SiteSubTab.owners
                          ? '소유자명, 연락처, 지번, 비고 검색...'
                          : '매도인(소유자), 은행, 계좌, 메모 검색...'),
                  hintStyle: AppTextStyles.bodySecond.copyWith(
                    color: context.colors.textMuted,
                    fontSize: 12.5,
                  ),
                  prefixIcon: Icon(
                    Icons.search_rounded,
                    size: 18,
                    color: context.colors.textMuted,
                  ),
                  suffixIcon: _searchController.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear_rounded, size: 16),
                          color: context.colors.textMuted,
                          onPressed: _onClearSearch,
                        )
                      : null,
                  border: InputBorder.none,
                  contentPadding: const EdgeInsets.symmetric(vertical: 9),
                ),
              ),
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── E. 서브 탭 본문 뷰 (독립된 스크롤 및 상태 관리) ──
          Expanded(
            child: _buildCurrentTabView(currentTab),
          ),
        ],
      ),
    );
  }

  /// 종합 집계 현황 카드 위젯
  Widget _buildAggregateDashboard(SiteAggregateModel aggregate) {
    return Container(
      color: context.colors.bgCard,
      padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 헤더: 총 대상부지 면적 및 필지수
          Row(
            children: [
              Icon(Icons.terrain_outlined, size: 13, color: context.colors.textMuted),
              const SizedBox(width: 5),
              Text(
                aggregate.isReturnedArea ? '사업대상 면적(환지)' : '총 대상부지 면적',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontSize: 10.5,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                '${NumberFormat('#,###.#').format(aggregate.targetTotalArea)}㎡ (${NumberFormat('#,###.#').format(aggregate.targetTotalPyung)}평)',
                style: AppTextStyles.titleSm.copyWith(
                  color: context.colors.textPrimary,
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Spacer(),
              Text(
                '총 ${aggregate.totalSitesCount}필지 / ${aggregate.totalOwnersCount}명',
                style: AppTextStyles.caption.copyWith(
                  color: const Color(0xFF0D9488),
                  fontWeight: FontWeight.bold,
                  fontSize: 11,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Divider(color: context.colors.border, height: 1),
          const SizedBox(height: 7),

          // 하단 KPI 3종: 계약면적 | 미계약면적 | 확보율(계약율)
          Row(
            children: [
              SiteKpiItem(
                label: '계약면적',
                value: '${NumberFormat('#,###.#').format(aggregate.totalContractedArea)}㎡ (${NumberFormat('#,###.#').format(aggregate.totalContractedPyung)}평)',
                color: const Color(0xFF10B981),
              ),
              _divider(),
              SiteKpiItem(
                label: '미계약면적',
                value: '${NumberFormat('#,###.#').format(aggregate.uncontractedArea)}㎡',
                color: context.colors.textSecond,
              ),
              _divider(),
              SiteKpiItem(
                label: '확보율(계약율)',
                value: '${aggregate.securedAreaRate.toStringAsFixed(1)}%',
                color: aggregate.securedAreaRate >= 100
                    ? const Color(0xFF10B981)
                    : const Color(0xFF0D9488),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _divider() => Container(width: 1, height: 26, color: context.colors.border);

  Widget _buildCurrentTabView(SiteSubTab tab) {
    switch (tab) {
      case SiteSubTab.sites:
        return const SiteParcelTabView();
      case SiteSubTab.owners:
        return const SiteOwnerTabView();
      case SiteSubTab.contracts:
        return const SiteContractTabView();
    }
  }
}
