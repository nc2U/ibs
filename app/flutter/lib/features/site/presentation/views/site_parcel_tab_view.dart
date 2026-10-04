import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/site_models.dart';
import '../../providers/site_provider.dart';
import '../widgets/site_detail_sheets.dart';

/// 📌 지번별 토지(사업부지) 탭 뷰
class SiteParcelTabView extends ConsumerStatefulWidget {
  const SiteParcelTabView({super.key});

  @override
  ConsumerState<SiteParcelTabView> createState() => _SiteParcelTabViewState();
}

class _SiteParcelTabViewState extends ConsumerState<SiteParcelTabView> {
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
      ref.read(siteListProvider.notifier).fetchNextPage();
    }
  }

  Future<void> _refresh() async {
    ref.invalidate(siteListProvider);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(siteListProvider);

    if (state.isLoading) {
      return const Center(
        child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF0D9488)),
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
          '등록된 사업부지 필지가 없습니다.',
          style: TextStyle(color: context.colors.textMuted),
        ),
      );
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return RefreshIndicator(
      color: const Color(0xFF0D9488),
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
          return _buildParcelCard(item);
        },
      ),
    );
  }

  Widget _buildParcelCard(SiteItemModel item) {
    return Card(
      margin: EdgeInsets.zero,
      color: context.colors.bgCard,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      clipBehavior: Clip.antiAlias,
      elevation: 0,
      child: InkWell(
        onTap: () => showSiteDetailBottomSheet(
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
                        color: const Color(0xFF0D9488).withAlpha(20),
                        border: Border.all(color: const Color(0xFF0D9488).withAlpha(80), width: 0.6),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        '순번 #${item.order}',
                        style: const TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF0D9488),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '${item.district} ${item.lotNumber}',
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
                        color: context.colors.border.withAlpha(50),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        item.sitePurpose,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: context.colors.textSecond,
                        ),
                      ),
                    ),
                    const SizedBox(width: 5),
                    // 📄 등기부등본 등록 상태 배지 (상시 노출)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                      decoration: BoxDecoration(
                        color: item.hasRegisterFile
                            ? const Color(0xFF0D9488).withAlpha(20)
                            : context.colors.border.withAlpha(40),
                        border: Border.all(
                          color: item.hasRegisterFile
                              ? const Color(0xFF0D9488).withAlpha(80)
                              : context.colors.border.withAlpha(80),
                          width: 0.6,
                        ),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            item.hasRegisterFile
                                ? Icons.picture_as_pdf
                                : Icons.picture_as_pdf_outlined,
                            size: 11,
                            color: item.hasRegisterFile
                                ? const Color(0xFF0D9488)
                                : context.colors.textMuted,
                          ),
                          const SizedBox(width: 2.5),
                          Text(
                            item.hasRegisterFile ? '등본' : '미등록',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: item.hasRegisterFile
                                  ? FontWeight.bold
                                  : FontWeight.normal,
                              color: item.hasRegisterFile
                                  ? const Color(0xFF0D9488)
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
                          '공부면적: ',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                        Text(
                          '${item.officialArea.toStringAsFixed(2)}㎡',
                          style: AppTextStyles.bodySecond.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '(${item.pyungArea.toStringAsFixed(1)}평)',
                          style: AppTextStyles.caption.copyWith(color: const Color(0xFF0D9488)),
                        ),
                        const Spacer(),
                        if (item.noticePrice != null)
                          Text(
                            '공시: ${NumberFormat('#,###').format(item.noticePrice)}원/㎡',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textMuted,
                              fontSize: 11,
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Icon(Icons.person_outline, size: 13, color: context.colors.textMuted),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            '소유자: ${item.displayOwnerSummary}',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textSecond,
                              fontSize: 11.5,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (item.rightsA.isNotEmpty || item.rightsB.isNotEmpty) ...[
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                            decoration: BoxDecoration(
                              color: const Color(0xFFEF4444).withAlpha(20),
                              border: Border.all(color: const Color(0xFFEF4444).withAlpha(80), width: 0.5),
                            ),
                            child: const Text(
                              '권리제한',
                              style: TextStyle(
                                fontSize: 9.5,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFFEF4444),
                              ),
                            ),
                          ),
                        ],
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
