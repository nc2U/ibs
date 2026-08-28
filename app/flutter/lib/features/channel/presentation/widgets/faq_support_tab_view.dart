import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_widget_from_html/flutter_widget_from_html.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../../data/forum_repository.dart';
import '../../data/models/forum_model.dart';
import '../../providers/forum_provider.dart';

/// 신입사원 FAQ (아코디언) & 기술지원 탭 뷰 (본사 1번 포럼 is_faq=true 실시간 API 연동)
class FaqSupportTabView extends ConsumerStatefulWidget {
  const FaqSupportTabView({super.key});

  @override
  ConsumerState<FaqSupportTabView> createState() => _FaqSupportTabViewState();
}

class _FaqSupportTabViewState extends ConsumerState<FaqSupportTabView> {
  // 선택된 카테고리: 0 = '전체 FAQ', -1 = '🛠️ 기술지원 문의', 그 외 = PostCategory pk
  int _selectedCategoryId = 0;

  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  int? _selectedSupportCategory;
  bool _isSubmitting = false;

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    super.dispose();
  }

  Future<void> _submitTechSupport() async {
    final title = _titleController.text.trim();
    final content = _contentController.text.trim();

    if (title.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('문의 제목을 입력해주세요.'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: Colors.redAccent,
        ),
      );
      return;
    }
    if (content.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('상세 문의 내용을 입력해주세요.'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: Colors.redAccent,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      final repo = ref.read(forumRepositoryProvider);
      await repo.createPost(
        forumId: kTechSupportForumId,
        title: title,
        content: content,
        categoryId: _selectedSupportCategory,
      );

      _titleController.clear();
      _contentController.clear();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('기술지원 문의가 등록되었습니다 (전산팀 접수 완료).'),
            backgroundColor: context.colors.success,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('문의 등록 중 오류가 발생했습니다: $e'),
            backgroundColor: context.colors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final categoriesAsync = ref.watch(faqCategoriesProvider);
    final faqPostsAsync = ref.watch(faqPostsProvider);
    final faqNoticesAsync = ref.watch(faqNoticesProvider);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(faqCategoriesProvider);
          ref.invalidate(faqPostsProvider);
          ref.invalidate(faqNoticesProvider);
        },
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            // ── 1. 상단 카테고리 필터 칩 ──────────────────────────────────
            SliverToBoxAdapter(
              child: Container(
                color: context.colors.bgCard,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                child: categoriesAsync.when(
                  loading: () => const SizedBox(
                    height: 38,
                    child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
                  ),
                  error: (_, __) => _buildStaticCategoryBar(),
                  data: (categories) {
                    // 전체 FAQ(0) + 서버 카테고리들 + 기술지원 문의(-1)
                    final chipList = [
                      {'id': 0, 'name': '전체 FAQ'},
                      ...categories.map((c) => {'id': c.pk, 'name': c.name}),
                      {'id': -1, 'name': '🛠️ 기술지원'},
                    ];

                    return SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: chipList.map((chip) {
                          final chipId = chip['id'] as int;
                          final chipName = chip['name'] as String;
                          final isSelected = _selectedCategoryId == chipId;

                          return Padding(
                            padding: const EdgeInsets.only(right: 8),
                            child: ChoiceChip(
                              label: Text(chipName),
                              selected: isSelected,
                              onSelected: (_) => setState(() => _selectedCategoryId = chipId),
                              selectedColor: context.colors.accentTech,
                              backgroundColor: context.colors.bgSurface,
                              labelStyle: TextStyle(
                                color: isSelected ? Colors.white : context.colors.textSecond,
                                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                fontSize: 13,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(20),
                                side: BorderSide(
                                  color: isSelected ? context.colors.accentTech : context.colors.border,
                                  width: 0.8,
                                ),
                              ),
                              showCheckmark: false,
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            ),
                          );
                        }).toList(),
                      ),
                    );
                  },
                ),
              ),
            ),

            // ── 2. 본문 섹션 ────────────────────────────────────────────────
            SliverPadding(
              padding: const EdgeInsets.all(16),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  if (_selectedCategoryId == -1) ...[
                    // 🛠️ 기술지원 / IT 헬프데스크 전용 폼 & 안내 (공지글이 있으면 상단에 렌더링)
                    _buildTechSupportSection(
                      context,
                      categoriesAsync.valueOrNull ?? [],
                      faqNoticesAsync.valueOrNull ?? [],
                    ),
                  ] else ...[
                    // ❓ FAQ 아코디언 리스트 (is_faq=true API 데이터 기반 - 순수 FAQ 아코디언만 렌더링)
                    faqPostsAsync.when(
                      loading: () => const Padding(
                        padding: EdgeInsets.symmetric(vertical: 12),
                        child: LoadingShimmer(itemHeight: 92, itemCount: 4),
                      ),
                      error: (err, _) => ErrorView(
                        message: 'FAQ 목록을 불러오지 못했습니다.',
                        onRetry: () => ref.invalidate(faqPostsProvider),
                      ),
                      data: (allFaqPosts) {
                        final filteredFaqs = _selectedCategoryId == 0
                            ? allFaqPosts
                            : allFaqPosts.where((p) => p.category == _selectedCategoryId).toList();

                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  '신입사원 자주 묻는 질문 (FAQ)',
                                  style: AppTextStyles.titleMd.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: context.colors.textPrimary,
                                  ),
                                ),
                                Text(
                                  '총 ${filteredFaqs.length}건',
                                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),

                            if (filteredFaqs.isEmpty)
                              Container(
                                width: double.infinity,
                                padding: const EdgeInsets.symmetric(vertical: 40),
                                decoration: BoxDecoration(
                                  color: context.colors.bgCard,
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: context.colors.border, width: 0.8),
                                ),
                                child: Center(
                                  child: Column(
                                    children: [
                                      Icon(Icons.help_outline_rounded, size: 36, color: context.colors.textMuted),
                                      const SizedBox(height: 8),
                                      Text(
                                        '등록된 FAQ 항목이 없습니다.',
                                        style: TextStyle(color: context.colors.textMuted, fontSize: 13),
                                      ),
                                    ],
                                  ),
                                ),
                              )
                            else
                              ...filteredFaqs.map((faq) => _buildFaqItem(context, faq)),

                            const SizedBox(height: 24),
                            // 하단 헬프데스크 바로가기 배너
                            _buildHelpBanner(context),
                            const SizedBox(height: 32),
                          ],
                        );
                      },
                    ),
                  ],
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 개별 FAQ 아코디언 아이템 (HTML 렌더링 지원)
  Widget _buildFaqItem(BuildContext context, PostModel faq) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
          childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
          leading: Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: context.colors.accentTech.withAlpha(30),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              'Q',
              style: TextStyle(
                color: context.colors.accentTech,
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
          ),
          title: Text(
            faq.title,
            style: AppTextStyles.bodyMd.copyWith(
              fontWeight: FontWeight.w600,
              color: context.colors.textPrimary,
            ),
          ),
          subtitle: faq.cateName != null
              ? Text(
                  faq.cateName!,
                  style: TextStyle(fontSize: 11.5, color: context.colors.accentTech),
                )
              : null,
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: context.colors.bgSurface,
                borderRadius: BorderRadius.circular(6),
              ),
              child: faq.content.isNotEmpty
                  ? HtmlWidget(
                      faq.content,
                      textStyle: AppTextStyles.bodySecond.copyWith(
                        color: context.colors.textSecond,
                        height: 1.45,
                      ),
                      customStylesBuilder: (element) {
                        if (element.localName == 'p') {
                          return {'margin': '0 0 4px 0', 'padding': '0'};
                        }
                        if (element.localName == 'a') {
                          return {'color': '#0ea5e9', 'text-decoration': 'none'};
                        }
                        return null;
                      },
                    )
                  : Text(
                      '내용이 없습니다.',
                      style: AppTextStyles.bodySecond.copyWith(
                        color: context.colors.textMuted,
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  /// 로딩 에러 시 fallback 카테고리 바
  Widget _buildStaticCategoryBar() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          ChoiceChip(
            label: const Text('전체 FAQ'),
            selected: true,
            onSelected: (_) {},
            selectedColor: context.colors.accentTech,
          ),
        ],
      ),
    );
  }

  /// 🛠️ 기술지원 / IT 헬프데스크 접수 폼 (공지사항이 있을 경우 상단 안내 배너로 렌더링)
  Widget _buildTechSupportSection(
    BuildContext context,
    List<PostCategoryModel> categories,
    List<PostModel> notices,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 📢 기술지원 이용안내 공지글이 있으면 동적으로 상단 배너 표시, 없으면 기본 안내 카드 표시
        if (notices.isNotEmpty)
          ...notices.map((notice) => Container(
                margin: const EdgeInsets.only(bottom: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: context.colors.bgCard,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: context.colors.accentTech.withAlpha(60), width: 0.8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.campaign_rounded, color: context.colors.accentTech, size: 22),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            notice.title,
                            style: AppTextStyles.titleSm.copyWith(
                              fontWeight: FontWeight.bold,
                              color: context.colors.textPrimary,
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (notice.content.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      HtmlWidget(
                        notice.content,
                        textStyle: AppTextStyles.caption.copyWith(
                          color: context.colors.textSecond,
                          height: 1.45,
                        ),
                        customStylesBuilder: (element) {
                          if (element.localName == 'p') {
                            return {'margin': '0 0 4px 0', 'padding': '0'};
                          }
                          return null;
                        },
                      ),
                    ],
                  ],
                ),
              ))
        else
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: context.colors.border, width: 0.8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.support_agent_rounded, color: Colors.deepOrangeAccent, size: 24),
                    const SizedBox(width: 8),
                    Text(
                      'IT 기술지원 & 전산 문의 접수',
                      style: AppTextStyles.titleSm.copyWith(
                        fontWeight: FontWeight.bold,
                        color: context.colors.textPrimary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'IBS 시스템 오류, 권한 요청, 사내 네트워크 및 PC 장비 관련 문의를 남겨주시면 전산팀에서 신속하게 처리해 드립니다.',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        const SizedBox(height: 16),
        Text(
          '문의 작성하기 (게시판 연동)',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        const SizedBox(height: 10),

        if (categories.isNotEmpty) ...[
          DropdownButtonFormField<int>(
            initialValue: _selectedSupportCategory,
            decoration: InputDecoration(
              hintText: '문의 분류 선택 (선택 사항)',
              hintStyle: TextStyle(color: context.colors.textMuted, fontSize: 13),
              filled: true,
              fillColor: context.colors.bgCard,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: BorderSide(color: context.colors.border),
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            ),
            items: categories.map((c) {
              return DropdownMenuItem<int>(
                value: c.pk,
                child: Text(c.name, style: TextStyle(fontSize: 13, color: context.colors.textPrimary)),
              );
            }).toList(),
            onChanged: (val) => setState(() => _selectedSupportCategory = val),
          ),
          const SizedBox(height: 10),
        ],

        TextField(
          controller: _titleController,
          decoration: InputDecoration(
            hintText: '문의 제목을 입력하세요 (예: 00현장 워크스페이스 권한 요청)',
            hintStyle: TextStyle(color: context.colors.textMuted, fontSize: 13),
            filled: true,
            fillColor: context.colors.bgCard,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: context.colors.border),
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          ),
        ),
        const SizedBox(height: 10),
        TextField(
          controller: _contentController,
          maxLines: 4,
          decoration: InputDecoration(
            hintText: '상세 문의 내용 및 발생 화면을 구체적으로 적어주세요.',
            hintStyle: TextStyle(color: context.colors.textMuted, fontSize: 13),
            filled: true,
            fillColor: context.colors.bgCard,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: context.colors.border),
            ),
            contentPadding: const EdgeInsets.all(14),
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          height: 46,
          child: ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: context.colors.accentTech,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            onPressed: _isSubmitting ? null : _submitTechSupport,
            icon: _isSubmitting
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.send_rounded, size: 18),
            label: Text(
              _isSubmitting ? '등록 중...' : '문의 등록하기',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            ),
          ),
        ),
        const SizedBox(height: 32),
      ],
    );
  }

  /// 💬 하단 배너
  Widget _buildHelpBanner(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Row(
        children: [
          const Icon(Icons.help_center_outlined, color: Colors.amber, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '원하는 답변을 찾지 못하셨나요?',
                  style: AppTextStyles.bodyMd.copyWith(
                    fontWeight: FontWeight.w600,
                    color: context.colors.textPrimary,
                  ),
                ),
                Text(
                  'IT 기술지원 탭에서 직접 문의를 남기실 수 있습니다.',
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                ),
              ],
            ),
          ),
          OutlinedButton(
            style: OutlinedButton.styleFrom(
              side: BorderSide(color: context.colors.accentTech),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
            ),
            onPressed: () => setState(() => _selectedCategoryId = -1),
            child: Text(
              '문의하기',
              style: TextStyle(
                color: context.colors.accentTech,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
