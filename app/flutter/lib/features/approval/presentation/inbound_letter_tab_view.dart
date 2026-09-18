import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:open_filex/open_filex.dart';
import 'package:share_plus/share_plus.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_router.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../data/inbound_letter_repository.dart';
import '../data/models/inbound_letter_model.dart';
import '../providers/inbound_letter_providers.dart';
import 'widgets/inbound_letter_card.dart';

class InboundLetterTabView extends ConsumerStatefulWidget {
  const InboundLetterTabView({super.key});

  @override
  ConsumerState<InboundLetterTabView> createState() => _InboundLetterTabViewState();
}

class _InboundLetterTabViewState extends ConsumerState<InboundLetterTabView> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _quickViewScanPdf(InboundLetterModel letter) async {
    if (letter.scanFile == null || letter.scanFile!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('등록된 원본 스캔본 파일이 없습니다.')),
      );
      return;
    }

    try {
      final repo = ref.read(inboundLetterRepositoryProvider);
      final filePath = await repo.downloadScanPdf(
        letter.id,
        letter.receiptNumber,
        scanUrl: letter.scanFile,
      );

      if (!mounted) return;

      final openResult = await OpenFilex.open(filePath);
      if (openResult.type != ResultType.done && mounted) {
        final docNum = letter.receiptNumber.isNotEmpty ? letter.receiptNumber : '수신공문_${letter.id}';
        final file = XFile(filePath, name: '$docNum.pdf');
        await Share.shareXFiles(
          [file],
          subject: '[수신공문] ${letter.title} ($docNum)',
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('스캔 파일 열람 실패: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final currentStatus = ref.watch(inboundLetterFilterStatusProvider);
    final lettersAsync = ref.watch(inboundLettersProvider);

    return Column(
      children: [
        // ── 상단 검색 및 상태 필터 칩 영역 ──
        Container(
          color: colors.bgSurface,
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 10),
          child: Column(
            children: [
              // 검색 입력창
              Container(
                height: 38,
                decoration: BoxDecoration(
                  color: colors.bgInput,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: colors.borderSubtle, width: 0.8),
                ),
                child: TextField(
                  controller: _searchController,
                  style: TextStyle(fontSize: 13, color: colors.textPrimary),
                  decoration: InputDecoration(
                    hintText: '공문 제목, 발신처, 접수번호 검색',
                    hintStyle: TextStyle(fontSize: 12.5, color: colors.textMuted),
                    prefixIcon: Icon(Icons.search_rounded, size: 18, color: colors.textMuted),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 16),
                            onPressed: () {
                              _searchController.clear();
                              ref.read(inboundLetterSearchQueryProvider.notifier).state = '';
                            },
                          )
                        : null,
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                  onSubmitted: (val) {
                    ref.read(inboundLetterSearchQueryProvider.notifier).state = val.trim();
                  },
                ),
              ),
              const SizedBox(height: 10),

              // 상태 필터 칩: [전체] [접수] [처리중] [회신완료] [종결]
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildFilterChip(
                      label: '전체',
                      isSelected: currentStatus == null,
                      onTap: () {
                        ref.read(inboundLetterFilterStatusProvider.notifier).state = null;
                      },
                    ),
                    const SizedBox(width: 8),
                    _buildFilterChip(
                      label: '접수',
                      isSelected: currentStatus == 'received',
                      onTap: () {
                        ref.read(inboundLetterFilterStatusProvider.notifier).state = 'received';
                      },
                    ),
                    const SizedBox(width: 8),
                    _buildFilterChip(
                      label: '처리중',
                      isSelected: currentStatus == 'in_progress',
                      onTap: () {
                        ref.read(inboundLetterFilterStatusProvider.notifier).state = 'in_progress';
                      },
                    ),
                    const SizedBox(width: 8),
                    _buildFilterChip(
                      label: '회신완료',
                      isSelected: currentStatus == 'replied',
                      onTap: () {
                        ref.read(inboundLetterFilterStatusProvider.notifier).state = 'replied';
                      },
                    ),
                    const SizedBox(width: 8),
                    _buildFilterChip(
                      label: '종결',
                      isSelected: currentStatus == 'closed',
                      onTap: () {
                        ref.read(inboundLetterFilterStatusProvider.notifier).state = 'closed';
                      },
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        Divider(color: colors.border, height: 1),

        // ── 수신 공문 목록 리스트뷰 ──
        Expanded(
          child: lettersAsync.when(
            loading: () => const Center(
              child: LoadingShimmer(itemHeight: 120, itemCount: 5),
            ),
            error: (err, stack) => ErrorView(
              message: err.toString(),
              onRetry: () => ref.refresh(inboundLettersProvider),
            ),
            data: (res) {
              final letters = res.results;
              if (letters.isEmpty) {
                return RefreshIndicator(
                  onRefresh: () async => ref.refresh(inboundLettersProvider.future),
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      SizedBox(height: MediaQuery.of(context).size.height * 0.2),
                      Center(
                        child: Column(
                          children: [
                            Icon(Icons.inbox_outlined,
                                size: 48, color: colors.textMuted.withAlpha(100)),
                            const SizedBox(height: 12),
                            Text(
                              '등록된 수신 공문이 없습니다.',
                              style: AppTextStyles.bodyMd.copyWith(color: colors.textMuted),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              }

              return RefreshIndicator(
                onRefresh: () async => ref.refresh(inboundLettersProvider.future),
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: letters.length,
                  itemBuilder: (ctx, idx) {
                    final item = letters[idx];
                    return InboundLetterCard(
                      letter: item,
                      onTap: () async {
                        await context.push('${AppRoutes.approval}/letters/inbound/${item.id}');
                        ref.invalidate(inboundLettersProvider);
                      },
                      onPdfTap: item.hasScan ? () => _quickViewScanPdf(item) : null,
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildFilterChip({
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    final colors = context.colors;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? colors.accentApproval : colors.bgCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? colors.accentApproval : colors.border,
            width: 0.8,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            color: isSelected ? Colors.white : colors.textSecond,
          ),
        ),
      ),
    );
  }
}
