import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../data/models/site_models.dart';
import '../../providers/site_provider.dart';
import '../widgets/site_common_widgets.dart';
import '../widgets/site_detail_sheets.dart';

/// 📑 사업부지 매입계약 탭 뷰
class SiteContractTabView extends ConsumerStatefulWidget {
  const SiteContractTabView({super.key});

  @override
  ConsumerState<SiteContractTabView> createState() => _SiteContractTabViewState();
}

class _SiteContractTabViewState extends ConsumerState<SiteContractTabView> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (!_scrollController.hasClients) return;
    if (_scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 200) {
      ref.read(siteContractListProvider.notifier).fetchNextPage();
    }
  }

  Future<void> _refresh() async {
    ref.invalidate(siteContractListProvider);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(siteContractListProvider);
    final ownSortFilter = ref.watch(siteOwnSortFilterProvider);

    return Column(
      children: [
        // 상단 소유구분 필터 바
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          color: context.colors.bgSurface,
          child: Row(
            children: [
              Text(
                '소유구분:',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(width: 8),
              SiteFilterChipBtn(
                label: '전체',
                isSelected: ownSortFilter == '',
                onTap: () {
                  ref.read(siteOwnSortFilterProvider.notifier).state = '';
                },
              ),
              const SizedBox(width: 4),
              SiteFilterChipBtn(
                label: '개인',
                isSelected: ownSortFilter == '1',
                onTap: () {
                  ref.read(siteOwnSortFilterProvider.notifier).state = '1';
                },
              ),
              const SizedBox(width: 4),
              SiteFilterChipBtn(
                label: '법인',
                isSelected: ownSortFilter == '2',
                onTap: () {
                  ref.read(siteOwnSortFilterProvider.notifier).state = '2';
                },
              ),
              const SizedBox(width: 4),
              SiteFilterChipBtn(
                label: '국공유지',
                isSelected: ownSortFilter == '3',
                onTap: () {
                  ref.read(siteOwnSortFilterProvider.notifier).state = '3';
                },
              ),
            ],
          ),
        ),
        Divider(color: context.colors.border, height: 1),

        // 본문 리스트 영역
        Expanded(
          child: _buildBody(state),
        ),
      ],
    );
  }

  Widget _buildBody(SitePaginationState<SiteContractItemModel> state) {
    final numFormat = NumberFormat('#,###');

    if (state.isLoading) {
      return const Center(
        child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFF59E0B)),
      );
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: ErrorView(
          message: '계약 데이터를 불러오지 못했습니다.',
          subMessage: state.error,
          onRetry: _refresh,
        ),
      );
    }

    if (state.items.isEmpty) {
      return const Center(
        child: ErrorView.empty(
          message: '체결된 사업부지 매입 계약이 없습니다.',
        ),
      );
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return RefreshIndicator(
      color: const Color(0xFFF59E0B),
      onRefresh: _refresh,
      child: ListView.separated(
        controller: _scrollController,
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(12),
        itemCount: itemCount,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (ctx, idx) {
          if (idx == state.items.length) {
            return const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
            );
          }

          final item = state.items[idx];
          return _buildContractCard(item, numFormat);
        },
      ),
    );
  }

  Widget _buildContractCard(SiteContractItemModel item, NumberFormat numFormat) {
    return Card(
      margin: EdgeInsets.zero,
      color: context.colors.bgCard,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      clipBehavior: Clip.antiAlias,
      elevation: 0,
      child: InkWell(
        onTap: () => showSiteContractDetailBottomSheet(
          context: context,
          ref: ref,
          item: item,
        ),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: context.colors.border, width: 0.8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 카드 헤더
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                color: context.colors.bgSurface,
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF59E0B).withAlpha(20),
                        border: Border.all(color: const Color(0xFFF59E0B).withAlpha(80), width: 0.6),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        '매도: ${item.ownerName}',
                        style: const TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFFF59E0B),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '계약일: ${item.contractDate}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11.5,
                        ),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                      decoration: BoxDecoration(
                        color: item.ownershipCompletion
                            ? const Color(0xFF10B981).withAlpha(20)
                            : const Color(0xFF38BDF8).withAlpha(20),
                        border: Border.all(
                          color: item.ownershipCompletion
                              ? const Color(0xFF10B981).withAlpha(80)
                              : const Color(0xFF38BDF8).withAlpha(80),
                          width: 0.6,
                        ),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        item.ownershipCompletion ? '소유권확보' : '진행중',
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.bold,
                          color: item.ownershipCompletion ? const Color(0xFF10B981) : const Color(0xFF38BDF8),
                        ),
                      ),
                    ),
                    const SizedBox(width: 5),
                    // 📑 매매계약서 등록 상태 배지 (상시 노출)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                      decoration: BoxDecoration(
                        color: item.hasContractFile
                            ? const Color(0xFFF59E0B).withAlpha(20)
                            : context.colors.border.withAlpha(40),
                        border: Border.all(
                          color: item.hasContractFile
                              ? const Color(0xFFF59E0B).withAlpha(80)
                              : context.colors.border.withAlpha(80),
                          width: 0.6,
                        ),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            item.hasContractFile
                                ? Icons.description
                                : Icons.description_outlined,
                            size: 11,
                            color: item.hasContractFile
                                ? const Color(0xFFF59E0B)
                                : context.colors.textMuted,
                          ),
                          const SizedBox(width: 2.5),
                          Text(
                            item.hasContractFile ? '계약서' : '미등록',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: item.hasContractFile
                                  ? FontWeight.bold
                                  : FontWeight.normal,
                              color: item.hasContractFile
                                  ? const Color(0xFFF59E0B)
                                  : context.colors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              Divider(color: context.colors.border, height: 1),

              // 카드 본문
              Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          '매매대금: ',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                        Text(
                          '${numFormat.format(item.totalPrice)}원',
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                            fontSize: 13.5,
                          ),
                        ),
                        const Spacer(),
                        Text(
                          '지급률 ${item.paymentRate.toStringAsFixed(0)}%',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: item.paymentRate >= 100 ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Text(
                          '계약면적: ${item.contractArea.toStringAsFixed(1)}㎡ (${item.contractPyung.toStringAsFixed(1)}평)',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textSecond,
                            fontSize: 11.5,
                          ),
                        ),
                        const Spacer(),
                        Text(
                          '평당 ${numFormat.format(item.pricePerPyung)}원',
                          style: AppTextStyles.caption.copyWith(
                            color: const Color(0xFF0D9488),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
