import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../../core/widgets/error_view.dart';
import '../../../core/widgets/loading_shimmer.dart';
import '../../channel/data/forum_repository.dart';
import '../../channel/data/notice_repository.dart';
import '../../channel/presentation/widgets/notice_detail_sheet.dart';
import '../../channel/presentation/widgets/post_detail_sheet.dart';
import '../../docs/data/docs_repository.dart';
import '../../docs/presentation/widgets/document_detail_sheet.dart';
import '../data/models/search_model.dart';
import '../providers/search_provider.dart';

/// 🔍 통합 검색 결과 화면 (/search)
/// - SafeArea 적용 및 뒤로가기 버튼 지원
/// - 350ms 입력 디바운스 및 2자 미만 시 즉시 상태 초기화
/// - 최근 검색어(Recent Searches) 저장, 삭제, 원터치 재검색
/// - 검색 결과 카테고리 탭 및 0건 시 'all' 자동 폴백
/// - 검색어 하이라이팅(Highlighting) 지원
/// - 문서/공지/게시글 상세 조회 시 로딩 인디케이터 제공
class SearchResultsScreen extends ConsumerStatefulWidget {
  const SearchResultsScreen({super.key});

  @override
  ConsumerState<SearchResultsScreen> createState() => _SearchResultsScreenState();
}

class _SearchResultsScreenState extends ConsumerState<SearchResultsScreen> {
  late final TextEditingController _controller;
  Timer? _debounceTimer;
  bool _isLoadingDetail = false;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: ref.read(searchQueryProvider));
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onSearchSubmit(String text) {
    _debounceTimer?.cancel();
    final query = text.trim();
    if (query.length >= 2) {
      ref.read(recentSearchesProvider.notifier).addSearch(query);
      ref.read(searchQueryProvider.notifier).state = query;
    } else {
      ref.read(searchQueryProvider.notifier).state = '';
    }
  }

  void _onSearchChanged(String val) {
    setState(() {});
    _debounceTimer?.cancel();
    final trimmed = val.trim();
    if (trimmed.length < 2) {
      // 2자 미만이면 즉시 검색 결과 초기화하여 이전 결과 잔존 방지
      ref.read(searchQueryProvider.notifier).state = '';
      return;
    }

    _debounceTimer = Timer(const Duration(milliseconds: 350), () {
      _onSearchSubmit(trimmed);
    });
  }

  void _onClearSearch() {
    _debounceTimer?.cancel();
    _controller.clear();
    ref.read(searchQueryProvider.notifier).state = '';
    setState(() {});
  }

  Future<void> _openDocumentDetail(int pk) async {
    if (_isLoadingDetail) return;
    setState(() => _isLoadingDetail = true);
    try {
      final doc = await ref.read(docsRepositoryProvider).fetchDocumentDetail(pk);
      if (mounted) {
        showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.transparent,
          builder: (ctx) => DocumentDetailSheet(doc: doc),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('문서 정보를 불러오지 못했습니다: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoadingDetail = false);
    }
  }

  Future<void> _openNoticeDetail(int pk) async {
    if (_isLoadingDetail) return;
    setState(() => _isLoadingDetail = true);
    try {
      final notice = await ref.read(noticeRepositoryProvider).fetchNoticeDetail(pk);
      if (mounted) {
        showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.transparent,
          builder: (ctx) => NoticeDetailSheet(notice: notice),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('공지사항 정보를 불러오지 못했습니다: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoadingDetail = false);
    }
  }

  Future<void> _openPostDetail(int pk) async {
    if (_isLoadingDetail) return;
    setState(() => _isLoadingDetail = true);
    try {
      final post = await ref.read(forumRepositoryProvider).fetchPostDetail(pk);
      if (mounted) {
        showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.transparent,
          builder: (ctx) => PostDetailSheet(post: post),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('게시글 정보를 불러오지 못했습니다: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoadingDetail = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // ── 🔄 검색 결과 변경 시, 현재 선택된 탭이 비어있으면 'all'로 자동 복귀 ──
    ref.listen<AsyncValue<UnifiedSearchResponse?>>(searchResultsProvider, (prev, next) {
      final res = next.valueOrNull;
      if (res != null) {
        final currentTab = ref.read(searchTargetTabProvider);
        if (currentTab == 'issues' && res.issues.isEmpty) {
          ref.read(searchTargetTabProvider.notifier).state = 'all';
        } else if (currentTab == 'meetings' && res.meetings.isEmpty) {
          ref.read(searchTargetTabProvider.notifier).state = 'all';
        } else if (currentTab == 'documents' && res.documents.isEmpty) {
          ref.read(searchTargetTabProvider.notifier).state = 'all';
        } else if (currentTab == 'news' && res.news.isEmpty) {
          ref.read(searchTargetTabProvider.notifier).state = 'all';
        } else if (currentTab == 'posts' && res.posts.isEmpty) {
          ref.read(searchTargetTabProvider.notifier).state = 'all';
        } else if (currentTab == 'comments' && res.comments.isEmpty) {
          ref.read(searchTargetTabProvider.notifier).state = 'all';
        }
      }
    });

    final query = ref.watch(searchQueryProvider);
    final scope = ref.watch(searchScopeProvider);
    final selectedTab = ref.watch(searchTargetTabProvider);
    final selectedProj = ref.watch(selectedProjectProvider);
    final searchResultsAsync = ref.watch(searchResultsProvider);
    final canPop = context.canPop();

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: SafeArea(
        child: Column(
          children: [
            // ── A. 상단 검색 입력창 및 범위 필터 바 ─────────────────────────
            Container(
              color: context.colors.bgSurface,
              padding: const EdgeInsets.fromLTRB(8, 8, 16, 10),
              child: Column(
                children: [
                  Row(
                    children: [
                      if (canPop)
                        IconButton(
                          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18),
                          color: context.colors.textPrimary,
                          tooltip: '뒤로가기',
                          onPressed: () => context.pop(),
                        )
                      else
                        const SizedBox(width: 8),
                      Expanded(
                        child: Container(
                          height: 42,
                          decoration: BoxDecoration(
                            color: context.colors.bgInput,
                            borderRadius: BorderRadius.zero,
                            border: Border.all(color: context.colors.border, width: 0.8),
                          ),
                          child: TextField(
                            controller: _controller,
                            textInputAction: TextInputAction.search,
                            style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                            decoration: InputDecoration(
                              hintText: '통합 검색 (2자 이상 입력)...',
                              hintStyle: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                              prefixIcon: Icon(
                                Icons.search_rounded,
                                size: 20,
                                color: context.colors.accentWork,
                              ),
                              suffixIcon: _controller.text.isNotEmpty
                                  ? IconButton(
                                      icon: Icon(Icons.clear_rounded, size: 16, color: context.colors.textMuted),
                                      onPressed: _onClearSearch,
                                    )
                                  : null,
                              border: InputBorder.none,
                              contentPadding: const EdgeInsets.symmetric(vertical: 11),
                            ),
                            onSubmitted: _onSearchSubmit,
                            onChanged: _onSearchChanged,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: context.colors.accentWork,
                          foregroundColor: Colors.white,
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                          padding: const EdgeInsets.symmetric(horizontal: 14),
                          minimumSize: const Size(60, 42),
                          elevation: 0,
                        ),
                        onPressed: () => _onSearchSubmit(_controller.text),
                        child: const Text('검색', style: TextStyle(fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  // ── 범위 필터: 전체 워크스페이스 vs 현재 워크스페이스 ─────────
                  Padding(
                    padding: EdgeInsets.only(left: canPop ? 8 : 4),
                    child: Row(
                      children: [
                        Text(
                          '검색 범위:',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                        const SizedBox(width: 8),
                        _ScopeChip(
                          label: '🌐 전체 워크스페이스',
                          selected: scope == 'all',
                          onTap: () => ref.read(searchScopeProvider.notifier).state = 'all',
                        ),
                        const SizedBox(width: 6),
                        if (selectedProj != null)
                          _ScopeChip(
                            label: '📁 ${selectedProj.name}',
                            selected: scope == 'project',
                            onTap: () => ref.read(searchScopeProvider.notifier).state = 'project',
                          ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // ── B. 카테고리별 탭 바 ─────────────────────────────────────
            searchResultsAsync.maybeWhen(
              data: (res) {
                if (res == null || res.isEmpty) return const SizedBox.shrink();
                return Container(
                  color: context.colors.bgSurface,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        _CategoryTabChip(
                          label: '전체',
                          count: res.totalCount,
                          selected: selectedTab == 'all',
                          color: context.colors.textPrimary,
                          onTap: () => ref.read(searchTargetTabProvider.notifier).state = 'all',
                        ),
                        const SizedBox(width: 6),
                        if (res.issues.isNotEmpty) ...[
                          _CategoryTabChip(
                            label: '📋 업무',
                            count: res.issues.length,
                            selected: selectedTab == 'issues',
                            color: const Color(0xFF2563EB),
                            onTap: () => ref.read(searchTargetTabProvider.notifier).state = 'issues',
                          ),
                          const SizedBox(width: 6),
                        ],
                        if (res.meetings.isNotEmpty) ...[
                          _CategoryTabChip(
                            label: '👥 회의',
                            count: res.meetings.length,
                            selected: selectedTab == 'meetings',
                            color: const Color(0xFF0D9488),
                            onTap: () => ref.read(searchTargetTabProvider.notifier).state = 'meetings',
                          ),
                          const SizedBox(width: 6),
                        ],
                        if (res.documents.isNotEmpty) ...[
                          _CategoryTabChip(
                            label: '📄 문서',
                            count: res.documents.length,
                            selected: selectedTab == 'documents',
                            color: const Color(0xFF7C3AED),
                            onTap: () => ref.read(searchTargetTabProvider.notifier).state = 'documents',
                          ),
                          const SizedBox(width: 6),
                        ],
                        if (res.news.isNotEmpty) ...[
                          _CategoryTabChip(
                            label: '📢 공지',
                            count: res.news.length,
                            selected: selectedTab == 'news',
                            color: const Color(0xFF1565C0),
                            onTap: () => ref.read(searchTargetTabProvider.notifier).state = 'news',
                          ),
                          const SizedBox(width: 6),
                        ],
                        if (res.posts.isNotEmpty) ...[
                          _CategoryTabChip(
                            label: '💬 게시판',
                            count: res.posts.length,
                            selected: selectedTab == 'posts',
                            color: const Color(0xFF00695C),
                            onTap: () => ref.read(searchTargetTabProvider.notifier).state = 'posts',
                          ),
                          const SizedBox(width: 6),
                        ],
                        if (res.comments.isNotEmpty) ...[
                          _CategoryTabChip(
                            label: '🗨️ 댓글',
                            count: res.comments.length,
                            selected: selectedTab == 'comments',
                            color: Colors.amber.shade800,
                            onTap: () => ref.read(searchTargetTabProvider.notifier).state = 'comments',
                          ),
                        ],
                      ],
                    ),
                  ),
                );
              },
              orElse: () => const SizedBox.shrink(),
            ),
            Divider(color: context.colors.border, height: 1),

            // ── C. 본문 검색 결과 영역 (스택으로 상세 로딩 인디케이터 처리) ──
            Expanded(
              child: Stack(
                children: [
                  query.length < 2
                      ? _buildInitialOrRecentSearches()
                      : searchResultsAsync.when(
                          loading: () => const LoadingShimmer(itemCount: 5, itemHeight: 90),
                          error: (err, _) => ErrorView(
                            message: '$err',
                            onRetry: () => ref.invalidate(searchResultsProvider),
                          ),
                          data: (response) {
                            if (response == null || response.isEmpty) {
                              return Center(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(
                                      Icons.search_off_rounded,
                                      size: 48,
                                      color: context.colors.textDisabled,
                                    ),
                                    const SizedBox(height: 12),
                                    Text(
                                      '\'$query\'에 대한 검색 결과가 없습니다.',
                                      style: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                                    ),
                                  ],
                                ),
                              );
                            }

                            return _buildResultList(context, response, selectedTab, query);
                          },
                        ),
                  if (_isLoadingDetail)
                    Container(
                      color: Colors.black26,
                      child: const Center(
                        child: CircularProgressIndicator(strokeWidth: 2.5),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 검색어 미입력 시 최근 검색어 및 가이드 UI
  Widget _buildInitialOrRecentSearches() {
    final recentSearches = ref.watch(recentSearchesProvider);

    if (recentSearches.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.manage_search_rounded, size: 54, color: context.colors.textDisabled),
            const SizedBox(height: 12),
            Text(
              '검색어를 2자 이상 입력하세요.',
              style: AppTextStyles.bodyMd.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              '업무, 회의록, 문서, 공지사항, 게시글을 통합 검색합니다.',
              style: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
            ),
          ],
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      children: [
        Row(
          children: [
            const Icon(Icons.history_rounded, size: 16, color: Color(0xFF64748B)),
            const SizedBox(width: 6),
            Text(
              '최근 검색어',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const Spacer(),
            TextButton(
              onPressed: () => ref.read(recentSearchesProvider.notifier).clearAll(),
              style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(50, 30)),
              child: Text(
                '전체 삭제',
                style: TextStyle(color: context.colors.textMuted, fontSize: 12),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: recentSearches.map((keyword) {
            return InkWell(
              onTap: () {
                _controller.text = keyword;
                _onSearchSubmit(keyword);
              },
              child: Container(
                padding: const EdgeInsets.fromLTRB(10, 5, 6, 5),
                decoration: BoxDecoration(
                  color: context.colors.bgSurface,
                  border: Border.all(color: context.colors.border, width: 0.8),
                  borderRadius: BorderRadius.zero,
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      keyword,
                      style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
                    ),
                    const SizedBox(width: 4),
                    InkWell(
                      onTap: () => ref.read(recentSearchesProvider.notifier).removeSearch(keyword),
                      child: Padding(
                        padding: const EdgeInsets.all(2),
                        child: Icon(Icons.close_rounded, size: 13, color: context.colors.textMuted),
                      ),
                    ),
                  ],
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildResultList(
    BuildContext context,
    UnifiedSearchResponse response,
    String activeTab,
    String query,
  ) {
    final list = <Widget>[];

    // 1. 업무 결과
    if ((activeTab == 'all' || activeTab == 'issues') && response.issues.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
          title: '📋 업무 이슈 (${response.issues.length})',
          color: const Color(0xFF2563EB),
        ));
      }
      for (final item in response.issues) {
        list.add(_ResultCard(
          badgeText: item.trackerName,
          badgeColor: const Color(0xFF2563EB),
          title: '#${item.pk} ${item.subject}',
          query: query,
          project: item.project.name,
          subInfo: '${item.statusName} · ${item.creator?.username ?? "작성자 미상"} · ${_safeFormatDate(item.created)}',
          onTap: () => context.push('/work/issues/${item.pk}'),
        ));
      }
    }

    // 2. 회의 결과
    if ((activeTab == 'all' || activeTab == 'meetings') && response.meetings.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
          title: '👥 회의록 (${response.meetings.length})',
          color: const Color(0xFF0D9488),
        ));
      }
      for (final item in response.meetings) {
        list.add(_ResultCard(
          badgeText: '회의록',
          badgeColor: const Color(0xFF0D9488),
          title: item.title,
          query: query,
          project: item.project.name,
          subInfo: '${item.meetingDate} · ${item.creator?.username ?? "작성자 미상"}',
          onTap: () => context.push('/work/meetings/${item.pk}'),
        ));
      }
    }

    // 3. 문서 결과
    if ((activeTab == 'all' || activeTab == 'documents') && response.documents.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
          title: '📄 공용 문서 (${response.documents.length})',
          color: const Color(0xFF7C3AED),
        ));
      }
      for (final item in response.documents) {
        list.add(_ResultCard(
          badgeText: '문서',
          badgeColor: const Color(0xFF7C3AED),
          title: item.title,
          query: query,
          project: item.project.name,
          subInfo: '${item.description.isNotEmpty ? item.description : "설명 없음"} · ${_safeFormatDate(item.created)}',
          onTap: () => _openDocumentDetail(item.pk),
        ));
      }
    }

    // 4. 공지사항 결과
    if ((activeTab == 'all' || activeTab == 'news') && response.news.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
          title: '📢 공지사항 (${response.news.length})',
          color: const Color(0xFF1565C0),
        ));
      }
      for (final item in response.news) {
        list.add(_ResultCard(
          badgeText: '공지',
          badgeColor: const Color(0xFF1565C0),
          title: item.title,
          query: query,
          project: item.project.name,
          subInfo: '${item.summary} · ${item.author?.username ?? ""} · ${_safeFormatDate(item.created)}',
          onTap: () => _openNoticeDetail(item.pk),
        ));
      }
    }

    // 5. 게시판 결과
    if ((activeTab == 'all' || activeTab == 'posts') && response.posts.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
          title: '💬 게시판 (${response.posts.length})',
          color: const Color(0xFF00695C),
        ));
      }
      for (final item in response.posts) {
        list.add(_ResultCard(
          badgeText: '게시글',
          badgeColor: const Color(0xFF00695C),
          title: item.title,
          query: query,
          project: item.project.name,
          subInfo: '${item.creator?.username ?? ""} · ${_safeFormatDate(item.created)}',
          onTap: () => _openPostDetail(item.pk),
        ));
      }
    }

    // 6. 댓글 결과
    if ((activeTab == 'all' || activeTab == 'comments') && response.comments.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
          title: '🗨️ 댓글 (${response.comments.length})',
          color: Colors.amber.shade800,
        ));
      }
      for (final item in response.comments) {
        list.add(_ResultCard(
          badgeText: '업무댓글',
          badgeColor: Colors.amber.shade800,
          title: item.content,
          query: query,
          project: '${item.project.name} · #${item.issuePk} ${item.issueSubject}',
          subInfo: '${item.creator?.username ?? ""} · ${_safeFormatDate(item.created)}',
          onTap: () => context.push('/work/issues/${item.issuePk}'),
        ));
      }
    }

    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      children: list,
    );
  }

  static String _safeFormatDate(String? raw) {
    if (raw == null || raw.isEmpty) return '';
    final parsed = DateTime.tryParse(raw);
    if (parsed != null) {
      return DateFormat('yyyy-MM-dd').format(parsed);
    }
    return raw.split('T').first;
  }
}

// ── 검색어 하이라이팅 텍스트 위젯 ─────────────────────────────────────────────
class _HighlightText extends StatelessWidget {
  final String text;
  final String query;
  final TextStyle? style;
  final Color highlightColor;
  final int? maxLines;
  final TextOverflow? overflow;

  const _HighlightText({
    required this.text,
    required this.query,
    this.style,
    this.highlightColor = const Color(0xFF2563EB),
    this.maxLines,
    this.overflow,
  });

  @override
  Widget build(BuildContext context) {
    final trimmedQuery = query.trim();
    if (trimmedQuery.length < 2 || !text.toLowerCase().contains(trimmedQuery.toLowerCase())) {
      return Text(text, style: style, maxLines: maxLines, overflow: overflow);
    }

    final spans = <TextSpan>[];
    final qLower = trimmedQuery.toLowerCase();
    int start = 0;

    while (true) {
      final index = text.toLowerCase().indexOf(qLower, start);
      if (index == -1) {
        spans.add(TextSpan(text: text.substring(start)));
        break;
      }
      if (index > start) {
        spans.add(TextSpan(text: text.substring(start, index)));
      }
      spans.add(TextSpan(
        text: text.substring(index, index + trimmedQuery.length),
        style: (style ?? const TextStyle()).copyWith(
          color: highlightColor,
          fontWeight: FontWeight.bold,
          backgroundColor: highlightColor.withAlpha(25),
        ),
      ));
      start = index + trimmedQuery.length;
    }

    return Text.rich(
      TextSpan(style: style, children: spans),
      maxLines: maxLines,
      overflow: overflow,
    );
  }
}

// ── 범위 필터 칩 ─────────────────────────────────────────────────────────────
class _ScopeChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _ScopeChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: selected ? context.colors.accentWork.withAlpha(40) : context.colors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(
            color: selected ? context.colors.accentWork : context.colors.border,
            width: 0.8,
          ),
        ),
        child: Text(
          label,
          style: AppTextStyles.caption.copyWith(
            color: selected ? context.colors.accentWork : context.colors.textMuted,
            fontWeight: selected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }
}

// ── 카테고리 탭 칩 ───────────────────────────────────────────────────────────
class _CategoryTabChip extends StatelessWidget {
  final String label;
  final int count;
  final bool selected;
  final Color color;
  final VoidCallback onTap;

  const _CategoryTabChip({
    required this.label,
    required this.count,
    required this.selected,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: selected ? color.withAlpha(35) : context.colors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(
            color: selected ? color : context.colors.border,
            width: selected ? 1.2 : 0.8,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: AppTextStyles.caption.copyWith(
                color: selected ? color : context.colors.textSecond,
                fontWeight: selected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
            const SizedBox(width: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
              decoration: BoxDecoration(
                color: selected ? color : context.colors.border,
                borderRadius: BorderRadius.zero,
              ),
              child: Text(
                '$count',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: selected ? Colors.white : context.colors.textSecond,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 섹션 헤더 ─────────────────────────────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  final String title;
  final Color color;

  const _SectionHeader({required this.title, required this.color});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 14, bottom: 8),
      child: Row(
        children: [
          Container(
            width: 3,
            height: 14,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.zero,
            ),
          ),
          const SizedBox(width: 6),
          Text(title, style: AppTextStyles.titleSm.copyWith(color: color)),
        ],
      ),
    );
  }
}

// ── 통합 검색 결과 개별 카드 위젯 (플랫 직각 스타일) ───────────────────────────
class _ResultCard extends StatelessWidget {
  final String badgeText;
  final Color badgeColor;
  final String title;
  final String query;
  final String project;
  final String subInfo;
  final VoidCallback onTap;

  const _ResultCard({
    required this.badgeText,
    required this.badgeColor,
    required this.title,
    required this.query,
    required this.project,
    required this.subInfo,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: badgeColor.withAlpha(25),
                      borderRadius: BorderRadius.zero,
                      border: Border.all(color: badgeColor.withAlpha(100), width: 0.8),
                    ),
                    child: Text(
                      badgeText,
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: badgeColor,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      project,
                      style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              _HighlightText(
                text: title,
                query: query,
                highlightColor: badgeColor,
                style: AppTextStyles.titleSm.copyWith(
                  color: context.colors.textPrimary,
                  fontWeight: FontWeight.w600,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 4),
              Text(
                subInfo,
                style: AppTextStyles.caption.copyWith(color: context.colors.textDisabled),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
