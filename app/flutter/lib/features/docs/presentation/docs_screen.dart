import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/docs_context_provider.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../../../../core/widgets/project_selector_bottom_sheet.dart';

import '../providers/docs_provider.dart';
import 'widgets/document_card.dart';
import 'widgets/document_detail_sheet.dart';
import 'widgets/document_form_sheet.dart';

/// 공용 문서함 메인 화면 (/docs)
class DocsScreen extends ConsumerStatefulWidget {
  final bool showScopeHeader;
  const DocsScreen({super.key, this.showScopeHeader = false});

  @override
  ConsumerState<DocsScreen> createState() => _DocsScreenState();
}

class _DocsScreenState extends ConsumerState<DocsScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _onSearch(String query) {
    ref.read(docsSearchProvider.notifier).state = query.trim();
  }

  @override
  Widget build(BuildContext context) {
    final canRead = ref.can(Perm.docsRead);
    if (!canRead) {
      return const Scaffold(
        backgroundColor: AppColors.bgPrimary,
        body: Center(
          child: Padding(
            padding: EdgeInsets.all(24.0),
            child: ErrorView.empty(
              message: '공용문서함을 조회할 권한이 없습니다.',
              subMessage: '관리자에게 [공용문서 열람] 권한(docs.read)을 요청해 주세요.',
            ),
          ),
        ),
      );
    }

    final docsContext = ref.watch(docsContextProvider);
    final docsListAsync = ref.watch(docsListProvider);

    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      body: Column(
        children: [
          // ── 1. 선택적 컨텍스트 선택바 (showScopeHeader == true 일 때만 표시) ──
          if (widget.showScopeHeader) ...[
            Container(
              color: AppColors.bgSurface,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: Row(
                children: [
                  if (Navigator.canPop(context) ||
                      docsContext.scopeType != DocsScopeType.all) ...[
                    IconButton(
                      icon: const Icon(Icons.arrow_back_rounded, size: 20),
                      color: AppColors.textPrimary,
                      tooltip: '돌아가기',
                      onPressed: () {
                        if (Navigator.canPop(context)) {
                          Navigator.pop(context);
                        } else {
                          ref.read(docsContextProvider.notifier).state =
                              DocsContext.all();
                        }
                      },
                    ),
                    const SizedBox(width: 4),
                  ],
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '문서 조회 범위',
                          style: AppTextStyles.caption
                              .copyWith(color: AppColors.textMuted),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          docsContext.displayName,
                          style: AppTextStyles.titleSm.copyWith(
                            color: docsContext.scopeType == DocsScopeType.all
                                ? AppColors.textPrimary
                                : (docsContext.scopeType ==
                                        DocsScopeType.project
                                    ? AppColors.accentProject
                                    : const Color(0xFF1565C0)),
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => showProjectSelectorBottomSheet(context),
                    icon: const Icon(Icons.tune_rounded, size: 15),
                    label: Text(
                      docsContext.scopeType == DocsScopeType.all
                          ? '범위 선택'
                          : '범위 변경',
                    ),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.accentWork,
                      side: const BorderSide(color: AppColors.accentWork),
                      shape: const RoundedRectangleBorder(
                          borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                  if (docsContext.scopeType != DocsScopeType.all) ...[
                    const SizedBox(width: 6),
                    IconButton(
                      icon: const Icon(Icons.clear_rounded, size: 18),
                      color: AppColors.textMuted,
                      tooltip: '전체 문서로 리셋',
                      onPressed: () {
                        ref.read(docsContextProvider.notifier).state =
                            DocsContext.all();
                      },
                    ),
                  ],
                ],
              ),
            ),
            const Divider(color: AppColors.border, height: 1),
          ],

          // ── 2. 검색바 ────────────────────────────────────────────────────
          Container(
            color: AppColors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextField(
              controller: _searchController,
              onSubmitted: _onSearch,
              style: AppTextStyles.bodyMd,
              decoration: InputDecoration(
                hintText: '문서 제목 검색...',
                prefixIcon: const Icon(Icons.search_rounded,
                    size: 18, color: AppColors.textMuted),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.close_rounded, size: 18),
                        onPressed: () {
                          _searchController.clear();
                          _onSearch('');
                        },
                      )
                    : null,
                contentPadding: const EdgeInsets.symmetric(vertical: 8),
              ),
            ),
          ),
          const Divider(color: AppColors.border, height: 1),

          // ── 3. 문서 유형 필터 탭 (일반 문서 | 소송 기록) ──────────────────
          Builder(
            builder: (ctx) {
              final selectedDocType = ref.watch(docTypeFilterProvider);
              return Container(
                color: AppColors.bgSurface,
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                child: Row(
                  children: [
                    Expanded(
                      child: _DocTypeFilterChip(
                        label: '📄 일반 문서',
                        isSelected: selectedDocType == '1',
                        onTap: () {
                          ref.read(docTypeFilterProvider.notifier).state = '1';
                          ref.read(docCategoryFilterProvider.notifier).state =
                              null;
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _DocTypeFilterChip(
                        label: '⚖️ 소송 기록',
                        isSelected: selectedDocType == '2',
                        onTap: () {
                          ref.read(docTypeFilterProvider.notifier).state = '2';
                          ref.read(docCategoryFilterProvider.notifier).state =
                              null;
                        },
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
          const Divider(color: AppColors.border, height: 1),

          // ── 4. 카테고리 셀렉트(드롭다운) 필터 바 ──────────────────────────────
          Consumer(
            builder: (ctx, ref, child) {
              final selectedDocType = ref.watch(docTypeFilterProvider);
              final selectedCategory = ref.watch(docCategoryFilterProvider);
              final categoriesAsync = ref.watch(docCategoriesProvider);

              return categoriesAsync.when(
                data: (allCategories) {
                  // 현재 선택된 docType ('1' 일반, '2' 소송)에 해당하는 카테고리만 추출
                  final categories = allCategories
                      .where((c) =>
                          c.docType == null || c.docType == selectedDocType)
                      .toList();

                  return Container(
                    color: AppColors.bgSurface,
                    padding:
                        const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                    child: Row(
                      children: [
                        const Icon(Icons.filter_list_rounded,
                            size: 16, color: AppColors.accentWork),
                        const SizedBox(width: 8),
                        Text('카테고리:',
                            style: AppTextStyles.caption
                                .copyWith(color: AppColors.textMuted)),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Container(
                            height: 34,
                            padding: const EdgeInsets.symmetric(horizontal: 10),
                            decoration: BoxDecoration(
                              color: AppColors.bgCard,
                              borderRadius: BorderRadius.zero,
                              border: Border.all(
                                color: selectedCategory != null
                                    ? AppColors.accentWork.withAlpha(120)
                                    : AppColors.border,
                              ),
                            ),
                            child: DropdownButtonHideUnderline(
                              child: DropdownButton<int?>(
                                value: selectedCategory,
                                isExpanded: true,
                                icon: const Icon(
                                    Icons.keyboard_arrow_down_rounded,
                                    size: 18,
                                    color: AppColors.textSecond),
                                style: AppTextStyles.bodySm.copyWith(
                                  color: selectedCategory != null
                                      ? AppColors.accentWork
                                      : AppColors.textPrimary,
                                  fontWeight: selectedCategory != null
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                ),
                                dropdownColor: AppColors.bgCard,
                                items: [
                                  DropdownMenuItem<int?>(
                                    value: null,
                                    child: Text(
                                        '전체 카테고리 (${categories.length}개)',
                                        style: AppTextStyles.bodySm),
                                  ),
                                  ...categories.map(
                                    (c) => DropdownMenuItem<int?>(
                                      value: c.pk,
                                      child: Text(c.name,
                                          style: AppTextStyles.bodySm),
                                    ),
                                  ),
                                ],
                                onChanged: (val) {
                                  ref
                                      .read(docCategoryFilterProvider.notifier)
                                      .state = val;
                                },
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                },
                loading: () => const SizedBox.shrink(),
                error: (e, s) => const SizedBox.shrink(),
              );
            },
          ),
          const Divider(color: AppColors.border, height: 1),

          // ── 5. 문서 목록 ──────────────────────────────────────────────────
          Expanded(
            child: docsListAsync.when(
              data: (data) {
                if (data.results.isEmpty) {
                  return const ErrorView(
                    message: '등록된 문서가 없습니다.',
                    icon: Icons.folder_open_rounded,
                  );
                }
                return RefreshIndicator(
                  onRefresh: () =>
                      ref.read(docsListProvider.notifier).refresh(),
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: data.results.length,
                    itemBuilder: (ctx, index) {
                      final doc = data.results[index];
                      return DocumentCard(
                        doc: doc,
                        onTap: () {
                          showModalBottomSheet(
                            context: context,
                            isScrollControlled: true,
                            backgroundColor: Colors.transparent,
                            builder: (bCtx) => DocumentDetailSheet(doc: doc),
                          );
                        },
                      );
                    },
                  ),
                );
              },
              loading: () => const LoadingShimmer(),
              error: (err, stack) => ErrorView(
                message: '$err',
                onRetry: () => ref.read(docsListProvider.notifier).refresh(),
              ),
            ),
          ),
        ],
      ),

      // ── 문서 생성 FAB (radius = 0, 바이올렛/퍼플 테마, docs.create 권한 체크) ───────────
      floatingActionButton: ref.can(Perm.docsCreate)
          ? FloatingActionButton.extended(
              onPressed: () {
                showModalBottomSheet(
                  context: context,
                  isScrollControlled: true,
                  backgroundColor: Colors.transparent,
                  builder: (ctx) => const DocumentFormSheet(),
                );
              },
              elevation: 4,
              highlightElevation: 8,
              backgroundColor: const Color(0xFF7C3AED),
              foregroundColor: Colors.white,
              shape:
                  const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
              icon: const Icon(Icons.add_rounded, size: 20),
              label: const Text(
                '문서 등록',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.2,
                ),
              ),
            )
          : null,
    );
  }
}

/// 문서 유형 필터 칩 (radius = 0)
class _DocTypeFilterChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _DocTypeFilterChip({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.zero,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
        decoration: BoxDecoration(
          color: isSelected
              ? AppColors.accentWork
              : AppColors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(
            color: isSelected ? AppColors.accentWork : AppColors.border,
          ),
        ),
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: AppTextStyles.label.copyWith(
            color: isSelected ? Colors.white : AppColors.textSecond,
            fontSize: 11.5,
          ),
        ),
      ),
    );
  }
}

