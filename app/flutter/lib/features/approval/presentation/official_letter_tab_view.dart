import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_router.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../providers/letter_providers.dart';
import 'inbound_letter_tab_view.dart';
import 'widgets/letter_card.dart';

class OfficialLetterTabView extends ConsumerStatefulWidget {
  const OfficialLetterTabView({super.key});

  @override
  ConsumerState<OfficialLetterTabView> createState() => _OfficialLetterTabViewState();
}

class _OfficialLetterTabViewState extends ConsumerState<OfficialLetterTabView> {
  int _subMode = 0; // 0: 발신 공문, 1: 수신 공문
  final TextEditingController _outboundSearchController = TextEditingController();

  @override
  void dispose() {
    _outboundSearchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;

    return Column(
      children: [
        // ── [ 발신 공문 | 수신 공문 ] 서브 세그먼트 바 ──
        Container(
          color: colors.bgSurface,
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 8),
          child: Container(
            height: 38,
            decoration: BoxDecoration(
              color: colors.bgInput,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: colors.borderSubtle, width: 0.8),
            ),
            padding: const EdgeInsets.all(2),
            child: Row(
              children: [
                Expanded(
                  child: InkWell(
                    onTap: () {
                      if (_subMode != 0) setState(() => _subMode = 0);
                    },
                    borderRadius: BorderRadius.circular(6),
                    child: Container(
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: _subMode == 0 ? colors.accentApproval : Colors.transparent,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.outbox_rounded,
                            size: 15,
                            color: _subMode == 0 ? Colors.white : colors.textMuted,
                          ),
                          const SizedBox(width: 5),
                          Text(
                            '발신 공문',
                            style: TextStyle(
                              fontSize: 12.5,
                              fontWeight: _subMode == 0 ? FontWeight.bold : FontWeight.w500,
                              color: _subMode == 0 ? Colors.white : colors.textSecond,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: InkWell(
                    onTap: () {
                      if (_subMode != 1) setState(() => _subMode = 1);
                    },
                    borderRadius: BorderRadius.circular(6),
                    child: Container(
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: _subMode == 1 ? colors.accentApproval : Colors.transparent,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.move_to_inbox_rounded,
                            size: 15,
                            color: _subMode == 1 ? Colors.white : colors.textMuted,
                          ),
                          const SizedBox(width: 5),
                          Text(
                            '수신 공문',
                            style: TextStyle(
                              fontSize: 12.5,
                              fontWeight: _subMode == 1 ? FontWeight.bold : FontWeight.w500,
                              color: _subMode == 1 ? Colors.white : colors.textSecond,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),

        // ── 선택된 모드에 따른 뷰 표시 ──
        Expanded(
          child: _subMode == 0 ? _buildOutboundView(context) : const InboundLetterTabView(),
        ),
      ],
    );
  }

  /// ── [0: 발신 공문] 서브 뷰 ──
  Widget _buildOutboundView(BuildContext context) {
    final colors = context.colors;
    final currentStatus = ref.watch(letterFilterStatusProvider);
    final lettersAsync = ref.watch(officialLettersProvider);

    return Column(
      children: [
        // 상단 검색 및 상태 필터 칩
        Container(
          color: colors.bgSurface,
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 10),
          child: Column(
            children: [
              // 검색창
              Container(
                height: 38,
                decoration: BoxDecoration(
                  color: colors.bgInput,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: colors.borderSubtle, width: 0.8),
                ),
                child: TextField(
                  controller: _outboundSearchController,
                  style: TextStyle(fontSize: 13, color: colors.textPrimary),
                  decoration: InputDecoration(
                    hintText: '공문 제목, 수신처, 문서번호 검색',
                    hintStyle: TextStyle(fontSize: 12.5, color: colors.textMuted),
                    prefixIcon: Icon(Icons.search_rounded, size: 18, color: colors.textMuted),
                    suffixIcon: _outboundSearchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 16),
                            onPressed: () {
                              _outboundSearchController.clear();
                              ref.read(letterSearchQueryProvider.notifier).state = '';
                            },
                          )
                        : null,
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                  onSubmitted: (val) {
                    ref.read(letterSearchQueryProvider.notifier).state = val.trim();
                  },
                ),
              ),
              const SizedBox(height: 10),

              // 상태 필터 칩: [전체] [결재대기] [결재승인] [발송완료]
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildFilterChip(
                      label: '전체',
                      isSelected: currentStatus == null,
                      onTap: () {
                        ref.read(letterFilterStatusProvider.notifier).state = null;
                      },
                    ),
                    const SizedBox(width: 8),
                    _buildFilterChip(
                      label: '결재대기',
                      isSelected: currentStatus == 'pending',
                      onTap: () {
                        ref.read(letterFilterStatusProvider.notifier).state = 'pending';
                      },
                    ),
                    const SizedBox(width: 8),
                    _buildFilterChip(
                      label: '결재승인',
                      isSelected: currentStatus == 'approved',
                      onTap: () {
                        ref.read(letterFilterStatusProvider.notifier).state = 'approved';
                      },
                    ),
                    const SizedBox(width: 8),
                    _buildFilterChip(
                      label: '발송완료',
                      isSelected: currentStatus == 'dispatched',
                      onTap: () {
                        ref.read(letterFilterStatusProvider.notifier).state = 'dispatched';
                      },
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        Divider(color: colors.border, height: 1),

        // 발신 공문 목록 리스트뷰
        Expanded(
          child: lettersAsync.when(
            loading: () => const Center(
              child: LoadingShimmer(itemHeight: 120, itemCount: 5),
            ),
            error: (err, stack) => ErrorView(
              message: err.toString(),
              onRetry: () => ref.refresh(officialLettersProvider),
            ),
            data: (res) {
              final letters = res.results;
              if (letters.isEmpty) {
                return RefreshIndicator(
                  onRefresh: () async => ref.refresh(officialLettersProvider.future),
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      SizedBox(height: MediaQuery.of(context).size.height * 0.2),
                      Center(
                        child: Column(
                          children: [
                            Icon(Icons.mark_email_read_outlined,
                                size: 48, color: colors.textMuted.withAlpha(100)),
                            const SizedBox(height: 12),
                            Text(
                              '등록된 발신 공문이 없습니다.',
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
                onRefresh: () async => ref.refresh(officialLettersProvider.future),
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: letters.length,
                  itemBuilder: (context, index) {
                    final letter = letters[index];
                    return LetterCard(
                      letter: letter,
                      onTap: () async {
                        await context.push('${AppRoutes.approval}/letters/${letter.id}');
                        ref.invalidate(officialLettersProvider);
                      },
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
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
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
            fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
            color: isSelected ? Colors.white : colors.textSecond,
          ),
        ),
      ),
    );
  }
}
