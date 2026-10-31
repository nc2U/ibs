import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/share_payload_provider.dart';
import '../../../../core/router/app_router.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/issue_repository.dart';
import '../../data/models/issue_model.dart';
import '../../providers/issue_provider.dart';

/// 외부 공유된 파일들을 기존 업무(Issue)에 첨부하기 위해 업무를 검색·선택하는 바텀시트
class IssueShareTargetSheet extends ConsumerStatefulWidget {
  final SharePayload payload;

  const IssueShareTargetSheet({
    super.key,
    required this.payload,
  });

  static Future<void> show(BuildContext context, SharePayload payload) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useRootNavigator: true,
      backgroundColor: Colors.transparent,
      builder: (_) => IssueShareTargetSheet(payload: payload),
    );
  }

  @override
  ConsumerState<IssueShareTargetSheet> createState() => _IssueShareTargetSheetState();
}

class _IssueShareTargetSheetState extends ConsumerState<IssueShareTargetSheet> {
  final TextEditingController _searchController = TextEditingController();
  Timer? _debounceTimer;
  String _searchQuery = '';

  List<IssueModel> _issues = [];
  bool _isLoading = true;
  bool _isLoadingMore = false;
  bool _hasMore = false;
  int _page = 1;
  bool _isUploading = false;
  String? _uploadProgressText;

  @override
  void initState() {
    super.initState();
    _fetchIssues();
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      if (mounted) {
        setState(() {
          _searchQuery = query.trim();
        });
        _fetchIssues();
      }
    });
  }

  Future<void> _fetchIssues() async {
    final requestQuery = _searchQuery;
    setState(() {
      _isLoading = true;
      _page = 1;
      _hasMore = false;
    });
    try {
      final repo = ref.read(issueRepositoryProvider);
      final resp = await repo.fetchIssues(IssueFilterModel(
        search: requestQuery.isEmpty ? null : requestQuery,
        page: 1,
        ordering: '-id',
      ));
      if (mounted && requestQuery == _searchQuery) {
        setState(() {
          _issues = resp.results;
          _hasMore = resp.next != null;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _fetchMore() async {
    if (_isLoading || _isLoadingMore || !_hasMore) return;
    final requestQuery = _searchQuery;
    setState(() => _isLoadingMore = true);
    try {
      final resp = await ref.read(issueRepositoryProvider).fetchIssues(
            IssueFilterModel(
              search: requestQuery.isEmpty ? null : requestQuery,
              page: _page + 1,
              ordering: '-id',
            ),
          );
      if (mounted && requestQuery == _searchQuery) {
        setState(() {
          _issues = [..._issues, ...resp.results];
          _page += 1;
          _hasMore = resp.next != null;
          _isLoadingMore = false;
        });
      } else if (mounted) {
        setState(() => _isLoadingMore = false);
      }
    } catch (_) {
      if (mounted) setState(() => _isLoadingMore = false);
    }
  }

  bool _canAttach(IssueModel issue) {
    if (issue.status.closed) return false;
    final currentUser = ref.read(currentUserProvider).valueOrNull;
    final isCreator = currentUser != null && currentUser.pk == issue.creator?.pk;
    final isAssignee = currentUser != null && currentUser.pk == issue.assignedTo?.pk;
    return ref.can(Perm.issueUpdate, projectSlug: issue.project.slug) ||
        (ref.can(Perm.issueOwnUpdate, projectSlug: issue.project.slug) && (isCreator || isAssignee));
  }

  Future<void> _handleIssueTap(IssueModel issue) async {
    if (!_canAttach(issue)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(issue.status.closed
              ? '완료(종결)된 업무에는 파일을 첨부할 수 없습니다.'
              : '해당 업무에 파일을 첨부할 권한이 없습니다.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }
    await _attachFilesToIssue(issue);
  }

  String _formatFileSize(int bytes) {
    if (bytes <= 0) return '';
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  /// 업무 선택 후 파일 첨부 실행
  Future<void> _attachFilesToIssue(IssueModel issue) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('업무 파일 첨부'),
        content: Text(
          '[#${issue.pk} ${issue.subject}] 업무에 공유받은 ${widget.payload.files.length}개 파일을 첨부하시겠습니까?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('첨부하기'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() {
      _isUploading = true;
    });

    final repo = ref.read(issueRepositoryProvider);
    int successCount = 0;
    String? errorMessage;

    try {
      for (int i = 0; i < widget.payload.files.length; i++) {
        final file = widget.payload.files[i];
        setState(() {
          _uploadProgressText = '파일 업로드 중 (${i + 1}/${widget.payload.files.length})...';
        });

        await repo.uploadIssueFile(
          issue.pk,
          filePath: file.path,
          bytes: file.bytes,
          fileName: file.name,
        );
        successCount++;
      }

      if (!mounted) return;

      Navigator.pop(context); // 시트 닫기
      ref.read(pendingSharePayloadProvider.notifier).clear();

      final currentCtx = rootNavigatorKey.currentContext;
      if (currentCtx != null && currentCtx.mounted) {
        ScaffoldMessenger.of(currentCtx).showSnackBar(
          SnackBar(
            content: Text('[#${issue.pk}]에 $successCount개 파일이 성공적으로 첨부되었습니다.'),
            backgroundColor: currentCtx.colors.success,
            duration: const Duration(seconds: 4),
            action: SnackBarAction(
              label: '업무 보기',
              textColor: Colors.white,
              onPressed: () {
                currentCtx.push('/work/issues/${issue.pk}');
              },
            ),
          ),
        );
      }
    } catch (e) {
      errorMessage = e.toString();
    } finally {
      if (successCount > 0) {
        ref.invalidate(issueDetailProvider(issue.pk));
        ref.invalidate(issueLogProvider(issue.pk));
        ref.invalidate(issueListProvider);
      }
      if (mounted) {
        setState(() {
          _isUploading = false;
          _uploadProgressText = null;
        });

        if (errorMessage != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('파일 첨부 실패 ($successCount건 완료 후 중단): $errorMessage'),
              backgroundColor: context.colors.error,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final totalSize = widget.payload.files.fold<int>(0, (sum, f) => sum + f.size);

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: BoxDecoration(
        color: context.colors.bgSurface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Stack(
        children: [
          Column(
            children: [
              // ── 상단 드래그 핸들 ──────────────────────────────────
              const SizedBox(height: 12),
              Center(
                child: Container(
                  width: 36,
                  height: 4,
                  decoration: BoxDecoration(
                    color: context.colors.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // ── 헤더 ──────────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Row(
                  children: [
                    Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: const Color(0xFF0284C7).withAlpha(30),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.task_alt_rounded,
                        color: Color(0xFF0284C7),
                        size: 20,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '업무(Issue) 선택 및 파일 첨부',
                            style: AppTextStyles.titleMd.copyWith(
                              fontWeight: FontWeight.bold,
                              color: context.colors.textPrimary,
                            ),
                          ),
                          Text(
                            '첨부할 대상 업무를 선택해 주세요.',
                            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: Icon(Icons.close_rounded, color: context.colors.textMuted),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 10),

              // ── 수신 파일 요약 칩 ─────────────────────────────────
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: context.colors.bgPrimary,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: context.colors.border, width: 0.8),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.attach_file_rounded, size: 16, color: context.colors.accentWork),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          widget.payload.files.map((f) => f.name).join(', '),
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.w600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (totalSize > 0)
                        Text(
                          _formatFileSize(totalSize),
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // ── 검색 입력창 ───────────────────────────────────────
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: TextField(
                  controller: _searchController,
                  onChanged: _onSearchChanged,
                  decoration: InputDecoration(
                    hintText: '업무 제목, 번호 또는 내용 검색...',
                    prefixIcon: Icon(Icons.search_rounded, size: 20, color: context.colors.textMuted),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear_rounded, size: 18),
                            onPressed: () {
                              _searchController.clear();
                              _onSearchChanged('');
                            },
                          )
                        : null,
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                    filled: true,
                    fillColor: context.colors.bgPrimary,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide(color: context.colors.border),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide(color: context.colors.border),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 10),

              // ── 업무 목록 ─────────────────────────────────────────
              Expanded(
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : _issues.isEmpty
                        ? Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.search_off_rounded, size: 40, color: context.colors.textMuted),
                                const SizedBox(height: 8),
                                Text(
                                  _searchQuery.isEmpty ? '등록된 업무가 없습니다.' : '검색 결과가 없습니다.',
                                  style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
                                ),
                              ],
                            ),
                          )
                        : NotificationListener<ScrollNotification>(
                            onNotification: (notification) {
                              if (notification.metrics.pixels >=
                                  notification.metrics.maxScrollExtent - 200) {
                                _fetchMore();
                              }
                              return false;
                            },
                            child: ListView.separated(
                              padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
                              itemCount: _issues.length + (_isLoadingMore ? 1 : 0),
                              separatorBuilder: (_, __) => const SizedBox(height: 8),
                              itemBuilder: (ctx, index) {
                                if (index >= _issues.length) {
                                  return const Padding(
                                    padding: EdgeInsets.symmetric(vertical: 12),
                                    child: Center(
                                      child: SizedBox(
                                        width: 20,
                                        height: 20,
                                        child: CircularProgressIndicator(strokeWidth: 2),
                                      ),
                                    ),
                                  );
                                }
                                final issue = _issues[index];
                                return _IssuePickTile(
                                  issue: issue,
                                  canAttach: _canAttach(issue),
                                  onTap: () => _handleIssueTap(issue),
                                );
                              },
                            ),
                          ),
              ),
            ],
          ),

          // ── 업로드 로딩 오버레이 ──────────────────────────────────
          if (_isUploading)
            Container(
              color: Colors.black.withAlpha(120),
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
                  decoration: BoxDecoration(
                    color: context.colors.bgSurface,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const CircularProgressIndicator(),
                      const SizedBox(height: 16),
                      Text(
                        _uploadProgressText ?? '파일 첨부 중...',
                        style: AppTextStyles.bodyMd.copyWith(
                          fontWeight: FontWeight.bold,
                          color: context.colors.textPrimary,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _IssuePickTile extends StatelessWidget {
  final IssueModel issue;
  final bool canAttach;
  final VoidCallback onTap;

  const _IssuePickTile({
    required this.issue,
    required this.canAttach,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: canAttach ? 1.0 : 0.45,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: context.colors.bgPrimary,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: context.colors.border, width: 0.8),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFF0284C7).withAlpha(25),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            '#${issue.pk} · ${issue.tracker.name}',
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF0284C7),
                            ),
                          ),
                        ),
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: issue.status.closed
                                ? context.colors.textMuted.withAlpha(20)
                                : context.colors.success.withAlpha(20),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            issue.status.name,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: issue.status.closed
                                  ? context.colors.textMuted
                                  : context.colors.success,
                            ),
                          ),
                        ),
                        const Spacer(),
                        if (issue.assignedTo != null)
                          Text(
                            issue.assignedTo!.username,
                            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                          ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      issue.subject,
                      style: AppTextStyles.bodyMd.copyWith(
                        fontWeight: FontWeight.bold,
                        color: context.colors.textPrimary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (issue.files.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Icon(Icons.attachment_rounded, size: 14, color: context.colors.textMuted),
                          const SizedBox(width: 4),
                          Text(
                            '기존 첨부 ${issue.files.length}개',
                            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Icon(Icons.add_circle_outline_rounded, color: context.colors.accentWork, size: 22),
            ],
          ),
        ),
      ),
    ),
  );
}
}
