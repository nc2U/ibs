import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/router/app_router.dart';
import '../../../core/widgets/error_view.dart';
import '../../../core/widgets/loading_shimmer.dart';
import '../../docs/data/docs_repository.dart';
import '../../docs/presentation/widgets/document_detail_sheet.dart';
import '../data/models/search_model.dart';
import '../providers/search_provider.dart';

/// 통합 검색 결과 화면 (/search)
/// - 하단 MainShell 탭바가 유지되는 상태에서 표시
/// - 상단 검색창 + 프로젝트 범위 선택 + 카테고리별 결과 탭
/// - 결과 클릭 시 각 도메인 상세 페이지/바텀시트로 연결
class SearchResultsScreen extends ConsumerStatefulWidget {
  const SearchResultsScreen({super.key});

  @override
  ConsumerState<SearchResultsScreen> createState() => _SearchResultsScreenState();
}

class _SearchResultsScreenState extends ConsumerState<SearchResultsScreen> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: ref.read(searchQueryProvider));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onSearchSubmit(String text) {
    ref.read(searchQueryProvider.notifier).state = text.trim();
  }

  @override
  Widget build(BuildContext context) {
    final query = ref.watch(searchQueryProvider);
    final scope = ref.watch(searchScopeProvider);
    final selectedTab = ref.watch(searchTargetTabProvider);
    final selectedProj = ref.watch(selectedProjectProvider);
    final searchResultsAsync = ref.watch(searchResultsProvider);

    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      body: Column(
        children: [
          // ── 상단 검색 입력창 바 ─────────────────────────────────────────
          Container(
            color: AppColors.bgSurface,
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Container(
                        height: 42,
                        decoration: BoxDecoration(
                          color: AppColors.bgInput,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: AppColors.border, width: 0.8),
                        ),
                        child: TextField(
                          controller: _controller,
                          textInputAction: TextInputAction.search,
                          style: AppTextStyles.bodyMd,
                          decoration: InputDecoration(
                            hintText: '통합 검색 (2자 이상 입력)...',
                            hintStyle: AppTextStyles.bodyMuted,
                            prefixIcon: const Icon(Icons.search,
                                size: 20, color: AppColors.accentWork),
                            suffixIcon: _controller.text.isNotEmpty
                                ? IconButton(
                                    icon: const Icon(Icons.clear,
                                        size: 16, color: AppColors.textMuted),
                                    onPressed: () {
                                      _controller.clear();
                                      ref.read(searchQueryProvider.notifier).state = '';
                                    },
                                  )
                                : null,
                            border: InputBorder.none,
                            contentPadding:
                                const EdgeInsets.symmetric(vertical: 11),
                          ),
                          onSubmitted: _onSearchSubmit,
                          onChanged: (val) {
                            setState(() {});
                            if (val.trim().length >= 2) {
                              _onSearchSubmit(val);
                            }
                          },
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.accentWork,
                        foregroundColor: Colors.white,
                        shape: const RoundedRectangleBorder(
                            borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(horizontal: 14),
                        minimumSize: const Size(60, 42),
                      ),
                      onPressed: () => _onSearchSubmit(_controller.text),
                      child: const Text('검색',
                          style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
                const SizedBox(height: 10),

                // ── 범위 필터: 전체 워크스페이스 vs 현재 워크스페이스 ─────────
                Row(
                  children: [
                    Text('검색 범위:',
                        style: AppTextStyles.caption
                            .copyWith(color: AppColors.textMuted)),
                    const SizedBox(width: 8),
                    _ScopeChip(
                      label: '🌐 전체 워크스페이스',
                      selected: scope == 'all',
                      onTap: () =>
                          ref.read(searchScopeProvider.notifier).state = 'all',
                    ),
                    const SizedBox(width: 6),
                    if (selectedProj != null)
                      _ScopeChip(
                        label: '📁 ${selectedProj.name}',
                        selected: scope == 'project',
                        onTap: () => ref
                            .read(searchScopeProvider.notifier)
                            .state = 'project',
                      ),
                  ],
                ),
              ],
            ),
          ),

          // ── 카테고리별 탭 바 (전체 / 업무 / 회의 / 문서 / 공지 / 게시판) ────
          searchResultsAsync.maybeWhen(
            data: (res) {
              if (res == null || res.isEmpty) return const SizedBox.shrink();
              return Container(
                color: AppColors.bgSurface,
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _CategoryTabChip(
                        label: '전체',
                        count: res.totalCount,
                        selected: selectedTab == 'all',
                        color: AppColors.textPrimary,
                        onTap: () => ref
                            .read(searchTargetTabProvider.notifier)
                            .state = 'all',
                      ),
                      const SizedBox(width: 6),
                      if (res.issues.isNotEmpty) ...[
                        _CategoryTabChip(
                          label: '📋 업무',
                          count: res.issues.length,
                          selected: selectedTab == 'issues',
                          color: const Color(0xFF2563EB),
                          onTap: () => ref
                              .read(searchTargetTabProvider.notifier)
                              .state = 'issues',
                        ),
                        const SizedBox(width: 6),
                      ],
                      if (res.meetings.isNotEmpty) ...[
                        _CategoryTabChip(
                          label: '👥 회의',
                          count: res.meetings.length,
                          selected: selectedTab == 'meetings',
                          color: const Color(0xFF0D9488),
                          onTap: () => ref
                              .read(searchTargetTabProvider.notifier)
                              .state = 'meetings',
                        ),
                        const SizedBox(width: 6),
                      ],
                      if (res.documents.isNotEmpty) ...[
                        _CategoryTabChip(
                          label: '📄 문서',
                          count: res.documents.length,
                          selected: selectedTab == 'documents',
                          color: const Color(0xFF7C3AED),
                          onTap: () => ref
                              .read(searchTargetTabProvider.notifier)
                              .state = 'documents',
                        ),
                        const SizedBox(width: 6),
                      ],
                      if (res.news.isNotEmpty) ...[
                        _CategoryTabChip(
                          label: '📢 공지',
                          count: res.news.length,
                          selected: selectedTab == 'news',
                          color: const Color(0xFF1565C0),
                          onTap: () => ref
                              .read(searchTargetTabProvider.notifier)
                              .state = 'news',
                        ),
                        const SizedBox(width: 6),
                      ],
                      if (res.posts.isNotEmpty) ...[
                        _CategoryTabChip(
                          label: '💬 게시판',
                          count: res.posts.length,
                          selected: selectedTab == 'posts',
                          color: const Color(0xFF00695C),
                          onTap: () => ref
                              .read(searchTargetTabProvider.notifier)
                              .state = 'posts',
                        ),
                        const SizedBox(width: 6),
                      ],
                      if (res.comments.isNotEmpty) ...[
                        _CategoryTabChip(
                          label: '🗨️ 댓글',
                          count: res.comments.length,
                          selected: selectedTab == 'comments',
                          color: Colors.amber.shade700,
                          onTap: () => ref
                              .read(searchTargetTabProvider.notifier)
                              .state = 'comments',
                        ),
                      ],
                    ],
                  ),
                ),
              );
            },
            orElse: () => const SizedBox.shrink(),
          ),
          const Divider(color: AppColors.border, height: 1),

          // ── 본문 검색 결과 목록 ─────────────────────────────────────────
          Expanded(
            child: query.length < 2
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.search, size: 48, color: AppColors.textDisabled),
                        const SizedBox(height: 12),
                        Text('검색어를 2자 이상 입력하세요.',
                            style: AppTextStyles.bodyMuted),
                      ],
                    ),
                  )
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
                              const Icon(Icons.search_off_rounded,
                                  size: 48, color: AppColors.textDisabled),
                              const SizedBox(height: 12),
                              Text('\'$query\'에 대한 검색 결과가 없습니다.',
                                  style: AppTextStyles.bodyMuted),
                            ],
                          ),
                        );
                      }

                      return _buildResultList(context, ref, response, selectedTab);
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultList(BuildContext context, WidgetRef ref,
      UnifiedSearchResponse response, String activeTab) {
    final list = <Widget>[];

    // 1. 업무 결과
    if ((activeTab == 'all' || activeTab == 'issues') &&
        response.issues.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
            title: '📋 업무 이슈 (${response.issues.length})',
            color: const Color(0xFF2563EB)));
      }
      for (final item in response.issues) {
        list.add(_ResultCard(
          badgeText: item.trackerName,
          badgeColor: const Color(0xFF2563EB),
          title: '#${item.pk} ${item.subject}',
          project: item.project.name,
          subInfo: '${item.statusName} · ${item.creator?.username ?? "작성자 미상"} · ${item.created.split("T").first}',
          onTap: () => context.push('/work/issues/${item.pk}'),
        ));
      }
    }

    // 2. 회의 결과
    if ((activeTab == 'all' || activeTab == 'meetings') &&
        response.meetings.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
            title: '👥 회의록 (${response.meetings.length})',
            color: const Color(0xFF0D9488)));
      }
      for (final item in response.meetings) {
        list.add(_ResultCard(
          badgeText: '회의록',
          badgeColor: const Color(0xFF0D9488),
          title: item.title,
          project: item.project.name,
          subInfo: '${item.meetingDate} · ${item.creator?.username ?? "작성자 미상"}',
          onTap: () => context.push('/work/meetings/${item.pk}'),
        ));
      }
    }

    // 3. 문서 결과
    if ((activeTab == 'all' || activeTab == 'documents') &&
        response.documents.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
            title: '📄 공용 문서 (${response.documents.length})',
            color: const Color(0xFF7C3AED)));
      }
      for (final item in response.documents) {
        list.add(_ResultCard(
          badgeText: '문서',
          badgeColor: const Color(0xFF7C3AED),
          title: item.title,
          project: item.project.name,
          subInfo: '${item.description.isNotEmpty ? item.description : "설명 없음"} · ${item.created.split("T").first}',
          onTap: () async {
            try {
              final doc = await ref
                  .read(docsRepositoryProvider)
                  .fetchDocumentDetail(item.pk);
              if (context.mounted) {
                showModalBottomSheet(
                  context: context,
                  isScrollControlled: true,
                  backgroundColor: Colors.transparent,
                  builder: (ctx) => DocumentDetailSheet(doc: doc),
                );
              }
            } catch (e) {
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('문서 정보를 불러오지 못했습니다: $e')),
                );
              }
            }
          },
        ));
      }
    }

    // 4. 공지사항 결과
    if ((activeTab == 'all' || activeTab == 'news') && response.news.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
            title: '📢 공지사항 (${response.news.length})',
            color: const Color(0xFF1565C0)));
      }
      for (final item in response.news) {
        list.add(_ResultCard(
          badgeText: '공지',
          badgeColor: const Color(0xFF1565C0),
          title: item.title,
          project: item.project.name,
          subInfo: '${item.summary} · ${item.author?.username ?? ""} · ${item.created.split("T").first}',
          onTap: () => context.go(AppRoutes.channel),
        ));
      }
    }

    // 5. 게시판 결과
    if ((activeTab == 'all' || activeTab == 'posts') &&
        response.posts.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
            title: '💬 게시판 (${response.posts.length})',
            color: const Color(0xFF00695C)));
      }
      for (final item in response.posts) {
        list.add(_ResultCard(
          badgeText: '게시글',
          badgeColor: const Color(0xFF00695C),
          title: item.title,
          project: item.project.name,
          subInfo: '${item.creator?.username ?? ""} · ${item.created.split("T").first}',
          onTap: () => context.go(AppRoutes.channel),
        ));
      }
    }

    // 6. 댓글 결과
    if ((activeTab == 'all' || activeTab == 'comments') &&
        response.comments.isNotEmpty) {
      if (activeTab == 'all') {
        list.add(_SectionHeader(
            title: '🗨️ 댓글 (${response.comments.length})',
            color: Colors.amber.shade700));
      }
      for (final item in response.comments) {
        list.add(_ResultCard(
          badgeText: '업무댓글',
          badgeColor: Colors.amber.shade700,
          title: item.content,
          project: '${item.project.name} · #${item.issuePk} ${item.issueSubject}',
          subInfo: '${item.creator?.username ?? ""} · ${item.created.split("T").first}',
          onTap: () => context.push('/work/issues/${item.issuePk}'),
        ));
      }
    }

    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      children: list,
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
          color: selected ? AppColors.accentWork.withAlpha(40) : AppColors.bgCard,
          borderRadius: BorderRadius.circular(4),
          border: Border.all(
            color: selected ? AppColors.accentWork : AppColors.border,
            width: 0.8,
          ),
        ),
        child: Text(
          label,
          style: AppTextStyles.caption.copyWith(
            color: selected ? AppColors.accentWork : AppColors.textMuted,
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
          color: selected ? color.withAlpha(45) : AppColors.bgCard,
          borderRadius: BorderRadius.circular(4),
          border: Border.all(
            color: selected ? color : AppColors.border,
            width: selected ? 1.2 : 0.8,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: AppTextStyles.caption.copyWith(
                color: selected ? color : AppColors.textSecond,
                fontWeight: selected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
            const SizedBox(width: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
              decoration: BoxDecoration(
                color: selected ? color : AppColors.border,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '$count',
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
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
              borderRadius: BorderRadius.circular(1.5),
            ),
          ),
          const SizedBox(width: 6),
          Text(title, style: AppTextStyles.titleSm.copyWith(color: color)),
        ],
      ),
    );
  }
}

// ── 통합 검색 결과 개별 카드 위젯 (radius = 0 모던 스타일) ─────────────────
class _ResultCard extends StatelessWidget {
  final String badgeText;
  final Color badgeColor;
  final String title;
  final String project;
  final String subInfo;
  final VoidCallback onTap;

  const _ResultCard({
    required this.badgeText,
    required this.badgeColor,
    required this.title,
    required this.project,
    required this.subInfo,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: AppColors.border, width: 0.8),
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
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: badgeColor.withAlpha(35),
                      borderRadius: BorderRadius.circular(2),
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
                      style: AppTextStyles.caption
                          .copyWith(color: AppColors.textMuted),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                title,
                style: AppTextStyles.titleSm.copyWith(fontWeight: FontWeight.w600),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 4),
              Text(
                subInfo,
                style: AppTextStyles.caption.copyWith(color: AppColors.textDisabled),
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
