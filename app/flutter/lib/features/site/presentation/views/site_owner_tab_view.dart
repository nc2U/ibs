import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/site_models.dart';
import '../../providers/site_provider.dart';
import '../widgets/site_common_widgets.dart';
import '../widgets/site_detail_sheets.dart';

/// 👤 소유자별 토지 탭 뷰
class SiteOwnerTabView extends ConsumerStatefulWidget {
  const SiteOwnerTabView({super.key});

  @override
  ConsumerState<SiteOwnerTabView> createState() => _SiteOwnerTabViewState();
}

class _SiteOwnerTabViewState extends ConsumerState<SiteOwnerTabView> {
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
      ref.read(siteOwnerListProvider.notifier).fetchNextPage();
    }
  }

  Future<void> _refresh() async {
    ref.invalidate(siteOwnerListProvider);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(siteOwnerListProvider);
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
                  ref.invalidate(siteOwnerListProvider);
                },
              ),
              const SizedBox(width: 4),
              SiteFilterChipBtn(
                label: '개인',
                isSelected: ownSortFilter == '1',
                onTap: () {
                  ref.read(siteOwnSortFilterProvider.notifier).state = '1';
                  ref.invalidate(siteOwnerListProvider);
                },
              ),
              const SizedBox(width: 4),
              SiteFilterChipBtn(
                label: '법인',
                isSelected: ownSortFilter == '2',
                onTap: () {
                  ref.read(siteOwnSortFilterProvider.notifier).state = '2';
                  ref.invalidate(siteOwnerListProvider);
                },
              ),
              const SizedBox(width: 4),
              SiteFilterChipBtn(
                label: '국공유지',
                isSelected: ownSortFilter == '3',
                onTap: () {
                  ref.read(siteOwnSortFilterProvider.notifier).state = '3';
                  ref.invalidate(siteOwnerListProvider);
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

  Widget _buildBody(SitePaginationState<SiteOwnerItemModel> state) {
    if (state.isLoading) {
      return const Center(
        child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF38BDF8)),
      );
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              '데이터 로드 실패: ${state.error}',
              style: TextStyle(color: context.colors.error),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: _refresh,
              style: OutlinedButton.styleFrom(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
              ),
              child: const Text('다시 시도'),
            ),
          ],
        ),
      );
    }

    if (state.items.isEmpty) {
      return Center(
        child: Text(
          '등록된 토지 소유자가 없습니다.',
          style: TextStyle(color: context.colors.textMuted),
        ),
      );
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return RefreshIndicator(
      color: const Color(0xFF38BDF8),
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
          return _buildOwnerCard(item);
        },
      ),
    );
  }

  Widget _buildOwnerCard(SiteOwnerItemModel item) {
    return Card(
      margin: EdgeInsets.zero,
      color: context.colors.bgCard,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      clipBehavior: Clip.antiAlias,
      elevation: 0,
      child: InkWell(
        onTap: () => showSiteOwnerDetailBottomSheet(
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
                        color: const Color(0xFF38BDF8).withAlpha(20),
                        border: Border.all(color: const Color(0xFF38BDF8).withAlpha(80), width: 0.6),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        item.ownSortDesc ?? '개인',
                        style: const TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF38BDF8),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        item.owner,
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                          fontSize: 13.5,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                      decoration: BoxDecoration(
                        color: item.useConsent
                            ? const Color(0xFF10B981).withAlpha(20)
                            : context.colors.border.withAlpha(50),
                        border: Border.all(
                          color: item.useConsent
                              ? const Color(0xFF10B981).withAlpha(80)
                              : context.colors.border,
                          width: 0.6,
                        ),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        item.useConsent ? '동의완료' : '미동의',
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.bold,
                          color: item.useConsent ? const Color(0xFF10B981) : context.colors.textMuted,
                        ),
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
                        Icon(Icons.pin_drop_outlined, size: 13, color: context.colors.textMuted),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            item.displaySiteSummary,
                            style: AppTextStyles.bodySecond.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                              fontSize: 12.5,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Text(
                          '총 ${item.totalOwnedArea.toStringAsFixed(1)}㎡',
                          style: AppTextStyles.caption.copyWith(
                            color: const Color(0xFF0D9488),
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    if (item.phone1.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Icon(Icons.phone_outlined, size: 13, color: context.colors.textMuted),
                          const SizedBox(width: 4),
                          Text(
                            item.phone1,
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textSecond,
                              fontSize: 11.5,
                            ),
                          ),
                          const Spacer(),
                          InkWell(
                            onTap: () => makeSitePhoneCall(
                              context,
                              item.phone1,
                              targetName: item.owner,
                            ),
                            child: const Padding(
                              padding: EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                              child: Icon(Icons.call, size: 15, color: Color(0xFF10B981)),
                            ),
                          ),
                          const SizedBox(width: 6),
                          InkWell(
                            onTap: () => sendSiteSms(item.phone1),
                            child: const Padding(
                              padding: EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                              child: Icon(Icons.sms_outlined, size: 15, color: Color(0xFF38BDF8)),
                            ),
                          ),
                        ],
                      ),
                    ],
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
