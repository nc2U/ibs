import 'dart:async';
import 'package:dio/dio.dart';
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
/// - SafeArea 적용 및 뒤로가기 버튼, URL 쿼리(?q=) 연동 지원
/// - 350ms 입력 디바운스 (실시간 검색) 및 확정 검색 시에만 최근 검색어 저장
/// - 사용자별 최근 검색어(Recent Searches) 로컬 영속화, 삭제, 원터치 재검색
/// - 검색 범위 ('all': 전체, 'my': 내 워크스페이스, 'project': 선택된 워크스페이스) 및 상세 필터 지원
/// - 검색 결과 카테고리 탭 및 0건 시 'all' 자동 폴백
/// - 제목 및 본문 요약 검색어 하이라이팅(Highlighting) 지원
/// - 상세 조회/복귀 시 자동 갱신 및 당겨서 새로고침(Pull-to-Refresh) 지원
class SearchResultsScreen extends ConsumerStatefulWidget {
  final String? initialQuery;

  const SearchResultsScreen({super.key, this.initialQuery});

  @override
  ConsumerState<SearchResultsScreen> createState() => _SearchResultsScreenState();
}

class _SearchResultsScreenState extends ConsumerState<SearchResultsScreen> {
  late final TextEditingController _controller;
  late final bool _shouldAutofocus;
  Timer? _debounceTimer;
  bool _isLoadingDetail = false;

  @override
  void initState() {
    super.initState();
    final incomingQuery = widget.initialQuery?.trim();
    final currentQuery = ref.read(searchQueryProvider);
    final effectiveInitial =
        (incomingQuery != null && incomingQuery.isNotEmpty) ? incomingQuery : currentQuery;

    _controller = TextEditingController(text: effectiveInitial);
    _shouldAutofocus = effectiveInitial.trim().isEmpty;

    if (incomingQuery != null && incomingQuery.length >= 2 && incomingQuery != currentQuery) {
      Future.microtask(() {
        if (!mounted) return;
        ref.read(searchQueryProvider.notifier).state = incomingQuery;
        ref.read(recentSearchesProvider.notifier).addSearch(incomingQuery);
      });
    }
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  /// 명시적 검색 실행 (키보드 완료 버튼, 검색 버튼 클릭, 최근 검색어 탭)
  void _onSearchSubmit(String text) {
    _debounceTimer?.cancel();
    FocusScope.of(context).unfocus();
    final query = text.trim();
    if (query.length >= 2) {
      ref.read(recentSearchesProvider.notifier).addSearch(query);
      ref.read(searchQueryProvider.notifier).state = query;
    } else {
      ref.read(searchQueryProvider.notifier).state = '';
      ref.read(searchTargetTabProvider.notifier).state = 'all';
    }
  }

  /// 실시간 타이핑 디바운스 (미완성 검색어가 최근 검색어에 오염되지 않도록 쿼리 상태만 갱신)
  void _onSearchChanged(String val) {
    _debounceTimer?.cancel();
    final trimmed = val.trim();
    if (trimmed.length < 2) {
      // 2자 미만이면 즉시 검색 결과 및 탭 초기화하여 이전 결과 잔존 방지
      ref.read(searchQueryProvider.notifier).state = '';
      ref.read(searchTargetTabProvider.notifier).state = 'all';
      return;
    }

    _debounceTimer = Timer(const Duration(milliseconds: 350), () {
      if (!mounted) return;
      ref.read(searchQueryProvider.notifier).state = trimmed;
    });
  }

  void _onClearSearch() {
    _debounceTimer?.cancel();
    _controller.clear();
    ref.read(searchQueryProvider.notifier).state = '';
    ref.read(searchTargetTabProvider.notifier).state = 'all';
  }

  /// 검색 결과 항목을 탭할 때 현재 검색어를 최근 검색어에 기록
  void _recordCurrentQueryToRecent() {
    final q = ref.read(searchQueryProvider).trim();
    if (q.length >= 2) {
      ref.read(recentSearchesProvider.notifier).addSearch(q);
    }
  }

  String _getErrorMessage(Object err, {String fallback = '검색 결과를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'}) {
    if (err is DioException) {
      if (err.type == DioExceptionType.connectionTimeout ||
          err.type == DioExceptionType.receiveTimeout ||
          err.type == DioExceptionType.sendTimeout ||
          err.type == DioExceptionType.connectionError) {
        return '서버와 연결할 수 없습니다. 네트워크 연결을 확인해 주세요.';
      }
      final data = err.response?.data;
      if (data is Map) {
        if (data['detail'] != null) return data['detail'].toString();
        if (data['error'] != null) return data['error'].toString();
      }
      if (err.response?.statusCode != null) {
        return '$fallback (오류 코드: ${err.response!.statusCode})';
      }
    }
    return fallback;
  }

  Future<void> _openIssueDetail(int pk) async {
    _recordCurrentQueryToRecent();
    await context.push('/work/issues/$pk');
    if (mounted) {
      ref.invalidate(searchResultsProvider);
    }
  }

  Future<void> _openMeetingDetail(int pk) async {
    _recordCurrentQueryToRecent();
    await context.push('/work/meetings/$pk');
    if (mounted) {
      ref.invalidate(searchResultsProvider);
    }
  }

  Future<void> _openDocumentDetail(int pk) async {
    if (_isLoadingDetail) return;
    _recordCurrentQueryToRecent();
    setState(() => _isLoadingDetail = true);
    try {
      final doc = await ref.read(docsRepositoryProvider).fetchDocumentDetail(pk);
      if (mounted) {
        setState(() => _isLoadingDetail = false);
        await showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.transparent,
          builder: (ctx) => DocumentDetailSheet(doc: doc),
        );
        if (mounted) {
          ref.invalidate(searchResultsProvider);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_getErrorMessage(e, fallback: '문서 정보를 불러오지 못했습니다.')),
          ),
        );
      }
    } finally {
      if (mounted && _isLoadingDetail) {
        setState(() => _isLoadingDetail = false);
      }
    }
  }

  Future<void> _openNoticeDetail(int pk) async {
    if (_isLoadingDetail) return;
    _recordCurrentQueryToRecent();
    setState(() => _isLoadingDetail = true);
    try {
      final notice = await ref.read(noticeRepositoryProvider).fetchNoticeDetail(pk);
      if (mounted) {
        setState(() => _isLoadingDetail = false);
        await showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.transparent,
          builder: (ctx) => NoticeDetailSheet(notice: notice),
        );
        if (mounted) {
          ref.invalidate(searchResultsProvider);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_getErrorMessage(e, fallback: '공지사항 정보를 불러오지 못했습니다.')),
          ),
        );
      }
    } finally {
      if (mounted && _isLoadingDetail) {
        setState(() => _isLoadingDetail = false);
      }
    }
  }

  Future<void> _openPostDetail(int pk) async {
    if (_isLoadingDetail) return;
    _recordCurrentQueryToRecent();
    setState(() => _isLoadingDetail = true);
    try {
      final post = await ref.read(forumRepositoryProvider).fetchPostDetail(pk);
      if (mounted) {
        setState(() => _isLoadingDetail = false);
        await showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.transparent,
          builder: (ctx) => PostDetailSheet(post: post),
        );
        if (mounted) {
          ref.invalidate(searchResultsProvider);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_getErrorMessage(e, fallback: '게시글 정보를 불러오지 못했습니다.')),
          ),
        );
      }
    } finally {
      if (mounted && _isLoadingDetail) {
        setState(() => _isLoadingDetail = false);
      }
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
    final effectiveScope = ref.watch(effectiveSearchScopeProvider);
    final selectedTab = ref.watch(searchTargetTabProvider);
    final selectedProj = ref.watch(selectedProjectProvider);
    final titleOnly = ref.watch(searchTitleOnlyProvider);
    final openedOnly = ref.watch(searchOpenedOnlyProvider);
    final attachMode = ref.watch(searchAttachModeProvider);
    final searchResultsAsync = ref.watch(searchResultsProvider);
    final canPop = context.canPop();

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: SafeArea(
        child: Column(
          children: [
            // ── A. 상단 검색 입력창 및 범위·상세 필터 바 ─────────────────────────
            Container(
              color: context.colors.bgSurface,
              padding: const EdgeInsets.fromLTRB(8, 8, 16, 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
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
                            autofocus: _shouldAutofocus,
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
                              suffixIcon: ValueListenableBuilder<TextEditingValue>(
                                valueListenable: _controller,
                                builder: (context, value, _) {
                                  if (value.text.isEmpty) return const SizedBox.shrink();
                                  return IconButton(
                                    icon: Icon(Icons.clear_rounded, size: 16, color: context.colors.textMuted),
                                    onPressed: _onClearSearch,
                                  );
                                },
                              ),
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

                  // ── 범위 및 상세 옵션 필터 (가로 스크롤 지원) ─────────
                  Padding(
                    padding: EdgeInsets.only(left: canPop ? 8 : 4),
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          Text(
                            '범위:',
                            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                          ),
                          const SizedBox(width: 6),
                          _ScopeChip(
                            label: '🌐 전체 워크스페이스',
                            selected: effectiveScope == 'all',
                            onTap: () => ref.read(searchScopeProvider.notifier).state = 'all',
                          ),
                          const SizedBox(width: 6),
                          _ScopeChip(
                            label: '👤 내 워크스페이스',
                            selected: effectiveScope == 'my',
                            onTap: () => ref.read(searchScopeProvider.notifier).state = 'my',
                          ),
                          if (selectedProj != null) ...[
                            const SizedBox(width: 6),
                            _ScopeChip(
                              label: '📁 ${selectedProj.name}',
                              selected: effectiveScope == 'project',
                              onTap: () => ref.read(searchScopeProvider.notifier).state = 'project',
                            ),
                          ],
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 8),
                            child: SizedBox(
                              height: 14,
                              child: VerticalDivider(color: context.colors.border, width: 1),
                            ),
                          ),
                          _ScopeChip(
                            label: '제목만',
                            selected: titleOnly,
                            onTap: () => ref.read(searchTitleOnlyProvider.notifier).state = !titleOnly,
                          ),
                          const SizedBox(width: 6),
                          _ScopeChip(
                            label: '열린 업무만',
                            selected: openedOnly,
                            onTap: () => ref.read(searchOpenedOnlyProvider.notifier).state = !openedOnly,
                          ),
                          const SizedBox(width: 6),
                          _ScopeChip(
                            label: '📎 첨부파일 포함',
                            selected: attachMode == '2',
                            onTap: () => ref.read(searchAttachModeProvider.notifier).state =
                                attachMode == '2' ? '1' : '2',
                          ),
                        ],
                      ),
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
                            message: _getErrorMessage(err),
                            subMessage: '네트워크 연결 상태나 검색어 조건을 확인해 주세요.',
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
                _controller.selection = TextSelection.fromPosition(
                  TextPosition(offset: keyword.length),
                );
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
        final prefix = item.isPrivate ? '🔒 ' : '';
        final statusText = item.statusClosed ? '${item.statusName}(완료)' : item.statusName;
        list.add(_ResultCard(
          badgeText: item.trackerName.isNotEmpty ? item.trackerName : '업무',
          badgeColor: item.statusClosed ? const Color(0xFF64748B) : const Color(0xFF2563EB),
          title: '$prefix#${item.pk} ${item.subject}',
          query: query,
          project: item.project.name,
          subInfo: _joinSubInfo([
            statusText,
            item.creator?.username ?? '작성자 미상',
            _safeFormatDate(item.created),
          ]),
          onTap: () => _openIssueDetail(item.pk),
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
          badgeText: item.statusLabel,
          badgeColor: const Color(0xFF0D9488),
          title: item.title,
          query: query,
          project: item.project.name,
          subInfo: _joinSubInfo([
            _safeFormatDate(item.meetingDate),
            item.creator?.username ?? '작성자 미상',
          ]),
          onTap: () => _openMeetingDetail(item.pk),
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
          subInfo: _joinSubInfo([
            item.description.isNotEmpty ? _sanitizeSnippet(item.description) : null,
            item.creator?.username,
            _safeFormatDate(item.created),
          ]),
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
          subInfo: _joinSubInfo([
            item.summary.isNotEmpty ? _sanitizeSnippet(item.summary) : null,
            item.author?.username,
            _safeFormatDate(item.created),
          ]),
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
          subInfo: _joinSubInfo([
            item.creator?.username ?? '작성자 미상',
            _safeFormatDate(item.created),
          ]),
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
          title: _sanitizeSnippet(item.content),
          query: query,
          project: _joinSubInfo([
            item.project.name,
            '#${item.issuePk} ${item.issueSubject}',
          ]),
          subInfo: _joinSubInfo([
            item.creator?.username ?? '작성자 미상',
            _safeFormatDate(item.created),
          ]),
          onTap: () => _openIssueDetail(item.issuePk),
        ));
      }
    }

    return RefreshIndicator(
      color: context.colors.accentWork,
      onRefresh: () async {
        ref.invalidate(searchResultsProvider);
        await ref.read(searchResultsProvider.future);
      },
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        children: list,
      ),
    );
  }

  /// 빈 문자열을 제외하고 ' · ' 구분자로 안전하게 결합
  static String _joinSubInfo(List<String?> parts) {
    return parts
        .where((p) => p != null && p.trim().isNotEmpty)
        .map((p) => p!.trim())
        .join(' · ');
  }

  /// 마크다운 기호 및 다중 개행을 카드 스니펫용 단일 라인 텍스트로 정제
  static String _sanitizeSnippet(String raw) {
    if (raw.isEmpty) return '';
    return raw
        .replaceAll(RegExp(r'<[^>]*>'), ' ')
        .replaceAll(RegExp(r'[#*`>~]+'), '')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
  }

  static String _safeFormatDate(String? raw) {
    if (raw == null || raw.trim().isEmpty) return '';
    final parsed = DateTime.tryParse(raw.trim());
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
    if (trimmedQuery.length < 2 || text.isEmpty) {
      return Text(text, style: style, maxLines: maxLines, overflow: overflow);
    }

    final textLower = text.toLowerCase();
    final qLower = trimmedQuery.toLowerCase();
    if (!textLower.contains(qLower)) {
      return Text(text, style: style, maxLines: maxLines, overflow: overflow);
    }

    final spans = <TextSpan>[];
    int start = 0;

    while (start < text.length) {
      final index = textLower.indexOf(qLower, start);
      if (index == -1) {
        spans.add(TextSpan(text: text.substring(start)));
        break;
      }
      if (index > start) {
        spans.add(TextSpan(text: text.substring(start, index)));
      }
      final matchEnd = (index + trimmedQuery.length).clamp(0, text.length);
      spans.add(TextSpan(
        text: text.substring(index, matchEnd),
        style: (style ?? const TextStyle()).copyWith(
          color: highlightColor,
          fontWeight: FontWeight.bold,
          backgroundColor: highlightColor.withAlpha(25),
        ),
      ));
      start = matchEnd;
      if (start >= text.length) break;
    }

    return Text.rich(
      TextSpan(style: style, children: spans),
      maxLines: maxLines,
      overflow: overflow,
    );
  }
}

// ── 범위 및 상세 필터 칩 ──────────────────────────────────────────────────────
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
              if (subInfo.isNotEmpty) ...[
                const SizedBox(height: 4),
                _HighlightText(
                  text: subInfo,
                  query: query,
                  highlightColor: badgeColor,
                  style: AppTextStyles.caption.copyWith(color: context.colors.textDisabled),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
