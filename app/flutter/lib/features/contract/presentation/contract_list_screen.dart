import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../providers/contract_provider.dart';
import 'widgets/contract_action_sheet.dart';
import 'widgets/contract_card.dart';
import 'widgets/release_card.dart';
import 'widgets/succession_card.dart';
import 'widgets/unit_matrix_view.dart';

/// 계약 관리 (Contract) 메인 화면
class ContractListScreen extends ConsumerStatefulWidget {
  final VoidCallback onBackToMain;

  const ContractListScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  ConsumerState<ContractListScreen> createState() => _ContractListScreenState();
}

class _ContractListScreenState extends ConsumerState<ContractListScreen> {
  static final NumberFormat _currencyFormat = NumberFormat('#,###');

  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  Timer? _debounceTimer;
  bool _showUnitMatrix = false; // 🏢 동호수 배치도 뷰 토글 상태

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);

    // ── 화면 진입 시 현재 선택된 프로젝트 기준으로 최신 데이터 동기화 ──
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        _refreshAllData();
      }
    });
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (!_scrollController.hasClients) return;
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      final currentTab = ref.read(contractCurrentSubTabProvider);
      switch (currentTab) {
        case ContractSubTab.contracts:
          if (!_showUnitMatrix) {
            ref.read(validContractListProvider.notifier).fetchNextPage();
          }
          break;
        case ContractSubTab.successions:
          ref.read(successionListProvider.notifier).fetchNextPage();
          break;
        case ContractSubTab.releases:
          ref.read(contractorReleaseListProvider.notifier).fetchNextPage();
          break;
      }
    }
  }

  void _refreshAllData() {
    ref.invalidate(contractAggregateProvider);
    ref.invalidate(buildingUnitsProvider);
    ref.invalidate(unitTypesProvider);
    ref.invalidate(allHouseUnitsProvider);
    ref.read(validContractListProvider.notifier).fetchInitial();
    ref.read(successionListProvider.notifier).fetchInitial();
    ref.read(contractorReleaseListProvider.notifier).fetchInitial();
  }

  void _onSearchChanged(String value) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 350), () {
      if (!mounted) return;
      ref.read(contractSearchQueryProvider.notifier).state = value;
      ref.read(validContractListProvider.notifier).fetchInitial();
      ref.read(successionListProvider.notifier).fetchInitial();
      ref.read(contractorReleaseListProvider.notifier).fetchInitial();
    });
  }

  void _onClearSearch() {
    _debounceTimer?.cancel();
    _searchController.clear();
    ref.read(contractSearchQueryProvider.notifier).state = '';
    ref.read(validContractListProvider.notifier).fetchInitial();
    ref.read(successionListProvider.notifier).fetchInitial();
    ref.read(contractorReleaseListProvider.notifier).fetchInitial();
  }

  @override
  Widget build(BuildContext context) {
    // ── 🔄 프로젝트 변경 감지 리스너: 프로젝트가 변경되면 3대 탭 목록 및 종합 집계를 즉시 자동 갱신 ──
    ref.listen(selectedRealEstateProjectProvider, (previous, next) {
      if (previous?.realProjectId != next?.realProjectId) {
        _refreshAllData();
      }
    });

    final selectedProject = ref.watch(selectedRealEstateProjectProvider);
    final aggregateAsync = ref.watch(contractAggregateProvider);
    final currentTab = ref.watch(contractCurrentSubTabProvider);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: Column(
        children: [
          // ── 1. 계약 모듈 헤더 배너 (고정) ─────────────────────────────────
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: const Color(0xFF38BDF8).withAlpha(30),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: const Icon(Icons.assignment_outlined,
                      size: 20, color: Color(0xFF38BDF8)),
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
                            '계약 정보 관리',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                            decoration: BoxDecoration(
                              color: const Color(0xFF38BDF8).withAlpha(20),
                              border: Border.all(color: const Color(0xFF38BDF8).withAlpha(120), width: 0.8),
                              borderRadius: BorderRadius.circular(2),
                            ),
                            child: const Text(
                              'CONTRACT',
                              style: TextStyle(
                                fontSize: 9.5,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF38BDF8),
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
                  onPressed: _refreshAllData,
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

          // ── 아래부터 스크롤 가능한 본문 영역 (CustomScrollView) ───────────────
          Expanded(
            child: RefreshIndicator(
              color: context.colors.accentProject,
              onRefresh: () async => _refreshAllData(),
              child: CustomScrollView(
                controller: _scrollController,
                physics: const AlwaysScrollableScrollPhysics(),
                slivers: [
                  // A. KPI 대시보드 (분양 현황 요약 카드 - 스크롤 연동)
                  SliverToBoxAdapter(
                    child: aggregateAsync.when(
                      loading: () => const SizedBox(
                        height: 72,
                        child: Center(
                          child: SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                        ),
                      ),
                      error: (_, __) => const SizedBox.shrink(),
                      data: (aggregate) {
                        return Container(
                          color: context.colors.bgCard,
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                          child: Row(
                            children: [
                              _KpiItem(
                                label: '총 세대수',
                                value: '${_currencyFormat.format(aggregate.totalUnits)}세대',
                                color: context.colors.textPrimary,
                              ),
                              _divider(),
                              _KpiItem(
                                label: '계약 완료',
                                value: '${_currencyFormat.format(aggregate.contsNum)}세대',
                                color: const Color(0xFF38BDF8),
                              ),
                              _divider(),
                              _KpiItem(
                                label: '분양률',
                                value: '${aggregate.contractRate.toStringAsFixed(1)}%',
                                color: const Color(0xFF34D399),
                              ),
                              _divider(),
                              _KpiItem(
                                label: '청약(대기)',
                                value: '${_currencyFormat.format(aggregate.subsNum)}건',
                                color: const Color(0xFFFBBF24),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                  const SliverToBoxAdapter(
                    child: Divider(height: 1),
                  ),

                  // B. 3대 서브도메인 탭 (상단 고정 Sticky Header)
                  SliverPersistentHeader(
                    pinned: true,
                    delegate: _PinnedHeaderDelegate(
                      height: 52.0,
                      child: Container(
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          border: Border(
                            bottom: BorderSide(
                              color: context.colors.border,
                              width: 0.8,
                            ),
                          ),
                        ),
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                        child: Row(
                          children: [
                            _SubTabButton(
                              title: '계약 목록',
                              icon: Icons.assignment_outlined,
                              isSelected: currentTab == ContractSubTab.contracts,
                              onTap: () {
                                ref.read(contractCurrentSubTabProvider.notifier).state =
                                    ContractSubTab.contracts;
                              },
                            ),
                            const SizedBox(width: 6),
                            _SubTabButton(
                              title: '권리 의무 승계',
                              icon: Icons.swap_horiz_rounded,
                              isSelected: currentTab == ContractSubTab.successions,
                              onTap: () {
                                ref.read(contractCurrentSubTabProvider.notifier).state =
                                    ContractSubTab.successions;
                              },
                            ),
                            const SizedBox(width: 6),
                            _SubTabButton(
                              title: '계약 해지',
                              icon: Icons.cancel_outlined,
                              isSelected: currentTab == ContractSubTab.releases,
                              onTap: () {
                                ref.read(contractCurrentSubTabProvider.notifier).state =
                                    ContractSubTab.releases;
                              },
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  // C. 검색창 & 유효 계약 탭 전용 [동호수 배치도 / 목록형] 토글 버튼
                  SliverToBoxAdapter(
                    child: Container(
                      color: context.colors.bgCard,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: Row(
                        children: [
                          // 검색 입력 필드
                          Expanded(
                            child: Container(
                              height: 38,
                              decoration: BoxDecoration(
                                color: (currentTab == ContractSubTab.contracts && _showUnitMatrix)
                                    ? context.colors.bgPrimary
                                    : context.colors.bgSurface,
                                borderRadius: BorderRadius.zero,
                                border: Border.all(color: context.colors.border, width: 0.8),
                              ),
                              child: TextField(
                                controller: _searchController,
                                enabled: !(currentTab == ContractSubTab.contracts && _showUnitMatrix),
                                onChanged: _onSearchChanged,
                                style: AppTextStyles.bodySecond.copyWith(
                                  color: context.colors.textPrimary,
                                  fontSize: 13,
                                ),
                                decoration: InputDecoration(
                                  isDense: true,
                                  hintText: currentTab == ContractSubTab.contracts
                                      ? (_showUnitMatrix
                                          ? '배치도 모드 (상단 동 탭으로 탐색)'
                                          : '계약자명, 동·호수, 연락처, 일련번호 검색...')
                                      : (currentTab == ContractSubTab.successions
                                          ? '양도인, 양수인, 일련번호 검색...'
                                          : '해약 신청자명 검색...'),
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

                          // 🏢 유효 계약 탭일 때만 검색창 오른쪽에 '동호수 배치도' 토글 버튼 제공
                          if (currentTab == ContractSubTab.contracts) ...[
                            const SizedBox(width: 8),
                            Material(
                              color: _showUnitMatrix
                                  ? context.colors.accentProject
                                  : context.colors.bgSurface,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.zero,
                                side: BorderSide(
                                  color: _showUnitMatrix
                                      ? context.colors.accentProject
                                      : context.colors.border,
                                  width: 0.8,
                                ),
                              ),
                              child: InkWell(
                                onTap: () {
                                  setState(() {
                                    _showUnitMatrix = !_showUnitMatrix;
                                  });
                                },
                                borderRadius: BorderRadius.zero,
                                child: Container(
                                  height: 38,
                                  padding: const EdgeInsets.symmetric(horizontal: 10),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(
                                        _showUnitMatrix
                                            ? Icons.view_list_rounded
                                            : Icons.grid_view_rounded,
                                        size: 16,
                                        color: _showUnitMatrix
                                            ? Colors.white
                                            : context.colors.accentProject,
                                      ),
                                      const SizedBox(width: 5),
                                      Text(
                                        _showUnitMatrix ? '목록 보기' : '동호수 배치도',
                                        style: TextStyle(
                                          fontSize: 12,
                                          fontWeight: FontWeight.bold,
                                          color: _showUnitMatrix
                                              ? Colors.white
                                              : context.colors.textPrimary,
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
                    ),
                  ),
                  const SliverToBoxAdapter(
                    child: Divider(height: 1),
                  ),

                  // D. 탭별 맞춤 리스트 (Slivers)
                  Builder(
                    builder: (context) {
                      switch (currentTab) {
                        case ContractSubTab.contracts:
                          return _showUnitMatrix
                              ? const SliverFillRemaining(child: UnitMatrixView())
                              : _buildContractsSliver();
                        case ContractSubTab.successions:
                          return _buildSuccessionsSliver();
                        case ContractSubTab.releases:
                          return _buildReleasesSliver();
                      }
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 1. 유효 계약 목록 Sliver 뷰
  Widget _buildContractsSliver() {
    final state = ref.watch(validContractListProvider);

    if (state.isLoading) {
      return const _SliverLoadingView();
    }

    if (state.error != null && state.items.isEmpty) {
      return _SliverErrorView(message: '데이터 로드 실패: ${state.error}');
    }

    if (state.items.isEmpty) {
      return const _SliverEmptyView(
        icon: Icons.search_off_rounded,
        message: '일치하는 유효 계약 정보가 없습니다.',
      );
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      sliver: SliverList(
        delegate: SliverChildBuilderDelegate(
          (ctx, index) {
            if (index == state.items.length) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 14),
                child: Center(
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              );
            }

            final item = state.items[index];
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: ContractCard(
                contract: item,
                onMoreTap: () => ContractActionSheet.show(context, contract: item),
              ),
            );
          },
          childCount: itemCount,
        ),
      ),
    );
  }

  /// 2. 권리의무 승계 목록 Sliver 뷰
  Widget _buildSuccessionsSliver() {
    final state = ref.watch(successionListProvider);

    if (state.isLoading) {
      return const _SliverLoadingView();
    }

    if (state.error != null && state.items.isEmpty) {
      return _SliverErrorView(message: '승계 내역 로드 실패: ${state.error}');
    }

    if (state.items.isEmpty) {
      return const _SliverEmptyView(
        icon: Icons.swap_horiz_rounded,
        message: '등록된 권리의무 승계 내역이 없습니다.',
      );
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      sliver: SliverList(
        delegate: SliverChildBuilderDelegate(
          (ctx, index) {
            if (index == state.items.length) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 14),
                child: Center(
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              );
            }

            final item = state.items[index];
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: SuccessionCard(
                succession: item,
                onCallBuyer: () => makeContractPhoneCall(
                  context,
                  item.buyerCellPhone,
                  contractorName: item.buyerName,
                ),
              ),
            );
          },
          childCount: itemCount,
        ),
      ),
    );
  }

  /// 3. 계약 해약/해지 목록 Sliver 뷰
  Widget _buildReleasesSliver() {
    final state = ref.watch(contractorReleaseListProvider);

    if (state.isLoading) {
      return const _SliverLoadingView();
    }

    if (state.error != null && state.items.isEmpty) {
      return _SliverErrorView(message: '해약 내역 로드 실패: ${state.error}');
    }

    if (state.items.isEmpty) {
      return const _SliverEmptyView(
        icon: Icons.cancel_outlined,
        message: '등록된 계약 해약 내역이 없습니다.',
      );
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      sliver: SliverList(
        delegate: SliverChildBuilderDelegate(
          (ctx, index) {
            if (index == state.items.length) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 14),
                child: Center(
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              );
            }

            final item = state.items[index];
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: ReleaseCard(release: item),
            );
          },
          childCount: itemCount,
        ),
      ),
    );
  }

  Widget _divider() {
    return Container(
      width: 1,
      height: 24,
      color: context.colors.border,
      margin: const EdgeInsets.symmetric(horizontal: 4),
    );
  }
}

class _SliverLoadingView extends StatelessWidget {
  const _SliverLoadingView();

  @override
  Widget build(BuildContext context) {
    return SliverFillRemaining(
      hasScrollBody: false,
      child: Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: context.colors.accentProject,
        ),
      ),
    );
  }
}

class _SliverErrorView extends StatelessWidget {
  final String message;
  const _SliverErrorView({required this.message});

  @override
  Widget build(BuildContext context) {
    return SliverFillRemaining(
      hasScrollBody: false,
      child: Center(
        child: Text(
          message,
          style: TextStyle(color: context.colors.error),
        ),
      ),
    );
  }
}

class _SliverEmptyView extends StatelessWidget {
  final IconData icon;
  final String message;
  const _SliverEmptyView({required this.icon, required this.message});

  @override
  Widget build(BuildContext context) {
    return SliverFillRemaining(
      hasScrollBody: false,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 40, color: context.colors.textDisabled),
            const SizedBox(height: 12),
            Text(
              message,
              style: AppTextStyles.bodySecond.copyWith(
                color: context.colors.textMuted,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SubTabButton extends StatelessWidget {
  final String title;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  const _SubTabButton({
    required this.title,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Material(
        color: isSelected
            ? context.colors.accentProject.withAlpha(25)
            : context.colors.bgCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.zero,
          side: BorderSide(
            color: isSelected ? context.colors.accentProject : context.colors.border,
            width: isSelected ? 1 : 0.8,
          ),
        ),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.zero,
          child: Container(
            height: 38,
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  icon,
                  size: 14,
                  color: isSelected
                      ? context.colors.accentProject
                      : context.colors.textSecond,
                ),
                const SizedBox(width: 4),
                Flexible(
                  child: Text(
                    title,
                    style: AppTextStyles.caption.copyWith(
                      color: isSelected
                          ? context.colors.accentProject
                          : context.colors.textSecond,
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                      fontSize: 12,
                      height: 1.15,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
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

class _KpiItem extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _KpiItem({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            label,
            style: AppTextStyles.caption.copyWith(
              color: context.colors.textMuted,
              fontSize: 10.5,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            value,
            style: AppTextStyles.titleSm.copyWith(
              color: color,
              fontSize: 13,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

class _PinnedHeaderDelegate extends SliverPersistentHeaderDelegate {
  final Widget child;
  final double height;

  _PinnedHeaderDelegate({required this.child, required this.height});

  @override
  double get minExtent => height;

  @override
  double get maxExtent => height;

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    return SizedBox.expand(child: child);
  }

  @override
  bool shouldRebuild(covariant _PinnedHeaderDelegate oldDelegate) {
    return height != oldDelegate.height || child != oldDelegate.child;
  }
}
