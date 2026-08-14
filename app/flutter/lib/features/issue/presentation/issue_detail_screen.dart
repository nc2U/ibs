import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/constants/permissions.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/permission_provider.dart';
import '../../../core/widgets/error_view.dart';
import '../../../core/widgets/loading_shimmer.dart';
import '../data/issue_repository.dart';
import '../data/models/issue_model.dart';
import '../providers/issue_provider.dart';
import 'issue_form_screen.dart';
import 'widgets/done_ratio_bottom_sheet.dart';
import 'widgets/issue_comment_tile.dart';
import 'widgets/issue_log_tile.dart';


/// 업무 상세 화면
class IssueDetailScreen extends ConsumerStatefulWidget {
  final int issueId;
  const IssueDetailScreen({super.key, required this.issueId});

  @override
  ConsumerState<IssueDetailScreen> createState() =>
      _IssueDetailScreenState();
}

class _IssueDetailScreenState extends ConsumerState<IssueDetailScreen> {
  final _commentController = TextEditingController();
  final _commentFocus = FocusNode();
  bool _isSendingComment = false;
  bool _isPrivateComment = false;

  @override
  void dispose() {
    _commentController.dispose();
    _commentFocus.dispose();
    super.dispose();
  }

  Future<void> _sendComment() async {
    final content = _commentController.text.trim();
    if (content.isEmpty) return;

    setState(() => _isSendingComment = true);
    try {
      await ref
          .read(issueCommentProvider(widget.issueId).notifier)
          .addComment(content, isPrivate: _isPrivateComment);
      ref.invalidate(issueLogProvider(widget.issueId));
      ref.invalidate(issueDetailProvider(widget.issueId));
      _commentController.clear();
      _commentFocus.unfocus();
      setState(() => _isPrivateComment = false);
    } catch (e) {
      if (mounted) {
        String msg = '댓글 등록에 실패했습니다.';
        if (e is DioException) {
          final res = e.response;
          if (res != null) {
            if (res.statusCode == 403) {
              msg = '댓글 작성 권한이 없습니다 (403 Forbidden).';
            } else if (res.data is Map) {
              final entries = (res.data as Map).entries;
              if (entries.isNotEmpty) {
                msg = '${entries.first.key}: ${entries.first.value}';
              }
            } else if (res.data is String && (res.data as String).isNotEmpty) {
              msg = res.data as String;
            }
          }
        }
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(msg),
            backgroundColor: AppColors.error,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSendingComment = false);
    }
  }

  Future<void> _attachPhoto() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.camera);
    if (picked == null) return;

    try {
      await ref
          .read(issueRepositoryProvider)
          .uploadFile(widget.issueId, File(picked.path));
      ref.invalidate(issueDetailProvider(widget.issueId));
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('사진이 첨부되었습니다.'),
            backgroundColor: AppColors.success,
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('파일 업로드에 실패했습니다.'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final detailState = ref.watch(issueDetailProvider(widget.issueId));

    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      appBar: AppBar(
        backgroundColor: AppColors.bgPrimary,
        foregroundColor: AppColors.textPrimary,
        elevation: 0,
        title: detailState.maybeWhen(
          data: (issue) => Row(
            children: [
              if (issue.isPrivate)
                const Padding(
                  padding: EdgeInsets.only(right: 6),
                  child: Icon(Icons.lock_outline_rounded,
                      size: 16, color: AppColors.textMuted),
                ),
              Expanded(
                child: Text(
                  '#${issue.pk} ${issue.subject}',
                  style: AppTextStyles.titleMd,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          orElse: () => Text('업무 상세', style: AppTextStyles.titleMd),
        ),
        actions: [
          detailState.maybeWhen(
            data: (issue) {
              final currentUser = ref.watch(currentUserProvider).valueOrNull;
              final isCreator =
                  currentUser != null && currentUser.pk == issue.creator?.pk;
              final isAssignee = currentUser != null &&
                  currentUser.pk == issue.assignedTo?.pk;

              final canUpdate = ref.can(Perm.issueUpdate,
                      projectSlug: issue.project.slug) ||
                  (ref.can(Perm.issueOwnUpdate,
                          projectSlug: issue.project.slug) &&
                      (isCreator || isAssignee));

              final isMyWatching = currentUser != null &&
                  issue.watchers.any((w) => w.pk == currentUser.pk);

              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: Icon(
                      isMyWatching
                          ? Icons.star_rounded
                          : Icons.star_outline_rounded,
                      color: isMyWatching
                          ? AppColors.warning
                          : AppColors.textMuted,
                      size: 24,
                    ),
                    tooltip: isMyWatching ? '관심끄기' : '지켜보기',
                    onPressed: () async {
                      try {
                        await ref
                            .read(issueDetailProvider(widget.issueId).notifier)
                            .toggleWatch();
                        if (context.mounted) {
                          final currentIssue = ref
                              .read(issueDetailProvider(widget.issueId))
                              .valueOrNull;
                          final nowWatching = currentUser != null &&
                              (currentIssue?.watchers
                                      .any((w) => w.pk == currentUser.pk) ??
                                  false);
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(nowWatching
                                  ? '이 업무를 지켜봅니다.'
                                  : '관심을 껐습니다.'),
                              duration: const Duration(seconds: 2),
                            ),
                          );
                        }
                      } catch (_) {
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('지켜보기 설정 변경에 실패했습니다.'),
                              backgroundColor: AppColors.error,
                            ),
                          );
                        }
                      }
                    },
                  ),
                  if (canUpdate)
                    IconButton(
                      icon: const Icon(Icons.edit_outlined, size: 22),
                      tooltip: '수정',
                      onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => IssueFormScreen(initialIssue: issue),
                        ),
                      ),
                    ),
                ],
              );
            },
            orElse: () => const SizedBox.shrink(),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded, size: 22),
            tooltip: '새로고침',
            onPressed: () => ref
                .read(issueDetailProvider(widget.issueId).notifier)
                .refresh(),
          ),
        ],
      ),
      body: detailState.when(
        loading: () => const LoadingShimmer(itemCount: 4, itemHeight: 120),
        error: (e, _) => ErrorView.network(
          onRetry: () => ref.invalidate(issueDetailProvider(widget.issueId)),
        ),
        data: (issue) => _buildBody(issue),
      ),
    );
  }

  Widget _buildBody(IssueModel issue) {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── 핵심 정보 카드 ──────────────────────────────────────────
                _InfoSection(issue: issue, ref: ref),
                const SizedBox(height: 12),

                // ── 설명 ────────────────────────────────────────────────────
                if (issue.description.isNotEmpty) ...[
                  _SectionLabel(label: '설명'),
                  _Card(
                    child: MarkdownBody(
                      data: issue.description,
                      selectable: true,
                      styleSheet: MarkdownStyleSheet(
                        p: AppTextStyles.bodyMd,
                        strong: AppTextStyles.bodyMd.copyWith(
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                        ),
                        blockquote: AppTextStyles.bodyMd.copyWith(
                          color: AppColors.textMuted,
                        ),
                        blockquoteDecoration: BoxDecoration(
                          color: AppColors.bgSurface,
                          border: const Border(
                            left: BorderSide(
                                color: AppColors.accentWork, width: 3),
                          ),
                        ),
                        code: const TextStyle(
                          backgroundColor: AppColors.bgSurface,
                          color: AppColors.accentWork,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                ],

                // ── 하위 업무 ────────────────────────────────────────────────
                if (issue.subIssues.isNotEmpty) ...[
                  _SectionLabel(
                      label: '하위 업무', count: issue.subIssues.length),
                  ...issue.subIssues.map((sub) => Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: _SubIssueRow(sub: sub),
                      )),
                  const SizedBox(height: 12),
                ],

                // ── 연결 업무 ────────────────────────────────────────────────
                if (issue.outgoingRelations.isNotEmpty ||
                    issue.incomingRelation != null) ...[
                  _SectionLabel(label: '연결 업무'),
                  if (issue.incomingRelation?.issue != null)
                    _RelationRow(
                      relation: issue.incomingRelation!,
                      direction: '선행',
                    ),
                  ...issue.outgoingRelations
                      .where((r) => r.issue != null)
                      .map((r) => _RelationRow(relation: r, direction: '후행')),
                  const SizedBox(height: 12),
                ],

                // ── 첨부 파일 ────────────────────────────────────────────────
                if (issue.files.isNotEmpty) ...[
                  _SectionLabel(label: '첨부 파일', count: issue.files.length),
                  ...issue.files
                      .map((f) => _FileRow(file: f)),
                  const SizedBox(height: 12),
                ],

                // ── 변경 이력 및 댓글 ───────────────────────────────────────
                _SectionLabel(label: '이력 및 댓글'),
                _HistoryAndCommentSection(issueId: issue.pk),
                const SizedBox(height: 80), // 하단 입력창 여백
              ],
            ),
          ),
        ),

        // ── 하단 댓글 입력창 (고정) ─────────────────────────────────────────
        if (ref.can(Perm.issueCommentCreate, projectSlug: issue.project.slug))
          _CommentInputBar(
            controller: _commentController,
            focusNode: _commentFocus,
            isSending: _isSendingComment,
            isPrivate: _isPrivateComment,
            canSetPrivate: ref.can(Perm.issuePrivateCommentSet,
                projectSlug: issue.project.slug),
            onTogglePrivate: () =>
                setState(() => _isPrivateComment = !_isPrivateComment),
            onSend: _sendComment,
            onAttachPhoto: _attachPhoto,
          ),
      ],
    );
  }
}

// ── 핵심 정보 섹션 ──────────────────────────────────────────────────────────────
class _InfoSection extends StatelessWidget {
  final IssueModel issue;
  final WidgetRef ref;
  const _InfoSection({required this.issue, required this.ref});

  @override
  Widget build(BuildContext context) {
    final currentUser = ref.watch(currentUserProvider).valueOrNull;
    final isCreator =
        currentUser != null && currentUser.pk == issue.creator?.pk;
    final isAssignee =
        currentUser != null && currentUser.pk == issue.assignedTo?.pk;
    final canUpdate = ref.can(Perm.issueUpdate,
            projectSlug: issue.project.slug) ||
        (ref.can(Perm.issueOwnUpdate, projectSlug: issue.project.slug) &&
            (isCreator || isAssignee));

    final doneColor =
        issue.doneRatio == 100 ? AppColors.success : AppColors.accentWork;

    return _Card(
      child: Column(
        children: [
          _InfoRow(
            label: '프로젝트',
            value: issue.project.name,
            icon: Icons.business_center_outlined,
          ),
          _InfoRow(
            label: '상태',
            value: issue.status.name,
            icon: Icons.flag_outlined,
            valueColor: issue.status.closed
                ? AppColors.textDisabled
                : AppColors.success,
          ),
          _InfoRow(
            label: '우선순위',
            value: issue.priority.name,
            icon: Icons.priority_high_rounded,
          ),
          _InfoRow(
            label: '담당자',
            value: issue.assignedTo?.username ?? '미배정',
            icon: Icons.person_outline_rounded,
          ),
          if (issue.expectedDurationDisplay.isNotEmpty)
            _InfoRow(
              label: '예상 처리기간',
              value: issue.expectedDurationDisplay,
              icon: Icons.timer_outlined,
            ),
          if (issue.startDate.isNotEmpty)
            _InfoRow(
              label: '시작일',
              value: _fmt(issue.startDate),
              icon: Icons.calendar_today_outlined,
            ),
          if (issue.dueDate != null)
            _buildDueDateRow(issue.dueDate!, issue.status.closed),
          _InfoRow(
            label: '업무 관람자',
            value: issue.watchers.isNotEmpty
                ? '${issue.watchers.map((w) => w.username).join(', ')} (${issue.watchers.length}명)'
                : '없음',
            icon: Icons.visibility_outlined,
          ),
          // 진척률 (탭 → 바텀시트)
          const Divider(height: 1, color: AppColors.border),
          const SizedBox(height: 10),
          GestureDetector(
            onTap: canUpdate
                ? () => showDoneRatioBottomSheet(
                      context: context,
                      ref: ref,
                      issueId: issue.pk,
                      currentRatio: issue.doneRatio,
                    )
                : null,
            child: Row(
              children: [
                Icon(Icons.percent_rounded, size: 16, color: doneColor),
                const SizedBox(width: 8),
                Text('진척률', style: AppTextStyles.bodyMuted),
                const Spacer(),
                Text(
                  '${issue.doneRatio}%',
                  style: AppTextStyles.titleSm.copyWith(color: doneColor),
                ),
                if (canUpdate) ...[
                  const SizedBox(width: 8),
                  Icon(Icons.edit_outlined, size: 14, color: doneColor),
                ],
              ],
            ),
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(3),
            child: LinearProgressIndicator(
              value: issue.doneRatio / 100.0,
              minHeight: 6,
              backgroundColor: AppColors.bgSurface,
              valueColor: AlwaysStoppedAnimation<Color>(doneColor),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDueDateRow(String dueDateStr, bool isClosed) {
    String formattedDate = _fmt(dueDateStr);
    String badgeText = '';
    Color statusColor = AppColors.textPrimary;
    Color badgeBgColor = Colors.transparent;
    Color badgeTextColor = Colors.transparent;
    bool hasBadge = false;

    if (!isClosed) {
      try {
        final now = DateTime.now();
        final today = DateTime(now.year, now.month, now.day);
        final due = DateTime.parse(dueDateStr);
        final dueDay = DateTime(due.year, due.month, due.day);
        final diffDays = dueDay.difference(today).inDays;

        if (diffDays < 0) {
          // 기한 초과 (Overdue) - Danger
          statusColor = AppColors.error;
          badgeText = '기한초과 (${-diffDays}일)';
          badgeBgColor = AppColors.error.withAlpha(30);
          badgeTextColor = AppColors.error;
          hasBadge = true;
        } else if (diffDays == 0) {
          // 오늘 마감 (D-Day) - Danger
          statusColor = AppColors.error;
          badgeText = '오늘 마감 (D-Day)';
          badgeBgColor = AppColors.error.withAlpha(30);
          badgeTextColor = AppColors.error;
          hasBadge = true;
        } else if (diffDays <= 3) {
          // 임박 (D-1 ~ D-3) - Warning
          statusColor = AppColors.warning;
          badgeText = 'D-$diffDays 임박';
          badgeBgColor = AppColors.warning.withAlpha(30);
          badgeTextColor = AppColors.warning;
          hasBadge = true;
        }
      } catch (_) {}
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        children: [
          const Icon(Icons.event_outlined, size: 16, color: AppColors.textMuted),
          const SizedBox(width: 10),
          SizedBox(
            width: 115,
            child: Text('완료기한', style: AppTextStyles.bodyMuted),
          ),
          const Spacer(),
          if (hasBadge) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: badgeBgColor,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: badgeTextColor, width: 0.8),
              ),
              child: Text(
                badgeText,
                style: AppTextStyles.caption.copyWith(
                  color: badgeTextColor,
                  fontWeight: FontWeight.bold,
                  fontSize: 11,
                ),
              ),
            ),
            const SizedBox(width: 6),
          ],
          Text(
            formattedDate,
            style: AppTextStyles.bodyMd.copyWith(
              color: isClosed ? AppColors.textDisabled : statusColor,
              fontWeight: hasBadge ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }

  String _fmt(String iso) {
    try {
      final dt = DateTime.parse(iso);
      return '${dt.year}.${dt.month.toString().padLeft(2, '0')}.${dt.day.toString().padLeft(2, '0')}';
    } catch (_) {
      return iso;
    }
  }
}

// ── 공통 카드 컨테이너 ─────────────────────────────────────────────────────────
class _Card extends StatelessWidget {
  final Widget child;
  const _Card({required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        border: Border.all(color: AppColors.border, width: 0.8),
      ),
      child: child,
    );
  }
}

// ── 섹션 레이블 ────────────────────────────────────────────────────────────────
class _SectionLabel extends StatelessWidget {
  final String label;
  final int? count;
  const _SectionLabel({required this.label, this.count});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          Text(label, style: AppTextStyles.titleSm.copyWith(color: AppColors.textMuted)),
          if (count != null) ...[
            const SizedBox(width: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
              decoration: BoxDecoration(
                color: AppColors.accentWork.withAlpha(40),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text('$count',
                  style: AppTextStyles.label.copyWith(
                      color: AppColors.accentWork)),
            ),
          ],
        ],
      ),
    );
  }
}

// ── 정보 행 ────────────────────────────────────────────────────────────────────
class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color? valueColor;
  const _InfoRow(
      {required this.label,
      required this.value,
      required this.icon,
      this.valueColor});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        children: [
          Icon(icon, size: 16, color: AppColors.textMuted),
          const SizedBox(width: 10),
          SizedBox(
            width: 115,
            child: Text(label, style: AppTextStyles.bodyMuted),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              value,
              style: AppTextStyles.bodyMd.copyWith(color: valueColor),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

// ── 하위 업무 행 ───────────────────────────────────────────────────────────────
class _SubIssueRow extends StatelessWidget {
  final SubIssueModel sub;
  const _SubIssueRow({required this.sub});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => context.push('/work/issues/${sub.pk}'),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          border: Border.all(color: AppColors.border, width: 0.8),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.accentWork.withAlpha(30),
                borderRadius: BorderRadius.circular(3),
              ),
              child: Text(sub.tracker.name,
                  style: AppTextStyles.label
                      .copyWith(color: AppColors.accentWork)),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text('#${sub.pk} ${sub.subject}',
                  style: AppTextStyles.bodyMd, overflow: TextOverflow.ellipsis),
            ),
            Text('${sub.doneRatio}%',
                style: AppTextStyles.caption.copyWith(
                    color: sub.doneRatio == 100
                        ? AppColors.success
                        : AppColors.textMuted)),
          ],
        ),
      ),
    );
  }
}

// ── 연결 업무 행 ───────────────────────────────────────────────────────────────
class _RelationRow extends StatelessWidget {
  final IssueRelationModel relation;
  final String direction;
  const _RelationRow({required this.relation, required this.direction});

  @override
  Widget build(BuildContext context) {
    final relIssue = relation.issue!;
    final isPrec = direction == '선행';
    final color = isPrec ? AppColors.accentApproval : AppColors.accentProject;

    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: InkWell(
        onTap: () => context.push('/work/issues/${relIssue.pk}'),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: AppColors.bgCard,
            border: Border.all(color: color.withAlpha(80), width: 0.8),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: color.withAlpha(30),
                  borderRadius: BorderRadius.circular(3),
                ),
                child: Text(direction,
                    style:
                        AppTextStyles.label.copyWith(color: color)),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '#${relIssue.pk} ${relIssue.subject}',
                  style: AppTextStyles.bodyMd,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (relation.delay != null && relation.delay! > 0)
                Text('+${relation.delay}일',
                    style: AppTextStyles.caption),
            ],
          ),
        ),
      ),
    );
  }
}

// ── 첨부 파일 행 ───────────────────────────────────────────────────────────────
class _FileRow extends StatelessWidget {
  final IssueFileModel file;
  const _FileRow({required this.file});

  IconData _icon() {
    final t = file.fileType.toLowerCase();
    if (t.contains('image')) return Icons.image_outlined;
    if (t.contains('pdf')) return Icons.picture_as_pdf_outlined;
    return Icons.attach_file_rounded;
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: InkWell(
        onTap: () async {
          final uri = Uri.parse(file.file);
          if (await canLaunchUrl(uri)) launchUrl(uri);
        },
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: AppColors.bgCard,
            border: Border.all(color: AppColors.border, width: 0.8),
          ),
          child: Row(
            children: [
              Icon(_icon(), size: 20, color: AppColors.accentWork),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(file.fileName,
                        style: AppTextStyles.bodyMd,
                        overflow: TextOverflow.ellipsis),
                    if (file.description.isNotEmpty)
                      Text(file.description, style: AppTextStyles.caption),
                  ],
                ),
              ),
              Icon(Icons.open_in_new_rounded,
                  size: 16, color: AppColors.textMuted),
            ],
          ),
        ),
      ),
    );
  }
}

// ── 변경 이력 & 댓글 통합 섹션 ──────────────────────────────────────────
class _HistoryAndCommentSection extends StatefulWidget {
  final int issueId;
  const _HistoryAndCommentSection({required this.issueId});

  @override
  State<_HistoryAndCommentSection> createState() =>
      _HistoryAndCommentSectionState();
}

class _HistoryAndCommentSectionState
    extends State<_HistoryAndCommentSection> {
  int _activeTab = 0; // 0: 전체 로그, 1: 댓글, 2: 항목 변경

  @override
  Widget build(BuildContext context) {
    return Consumer(
      builder: (context, ref, child) {
        final logsState = ref.watch(issueLogProvider(widget.issueId));

        return logsState.when(
          loading: () => const LoadingShimmer(itemCount: 2, itemHeight: 80),
          error: (e, _) => const ErrorView.empty(message: '이력을 불러오지 못했습니다.'),
          data: (logs) {
            final commentLogs = logs.where((l) => l.comment != null).toList();
            final historyLogs = logs.where((l) => l.comment == null).toList();

            if (logs.isEmpty) {
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Text('등록된 변경 이력 및 댓글이 없습니다.',
                    style: AppTextStyles.bodyMuted),
              );
            }

            List<IssueLogEntryModel> displayLogs;
            if (_activeTab == 1) {
              displayLogs = commentLogs;
            } else if (_activeTab == 2) {
              displayLogs = historyLogs;
            } else {
              displayLogs = logs;
            }

            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── 탭 버튼 바 ───────────────────────────────────────────
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: [
                      _HistoryTabChip(
                        label: '전체 로그',
                        count: logs.length,
                        selected: _activeTab == 0,
                        onTap: () => setState(() => _activeTab = 0),
                      ),
                      const SizedBox(width: 6),
                      if (commentLogs.isNotEmpty) ...[
                        _HistoryTabChip(
                          label: '댓글',
                          count: commentLogs.length,
                          selected: _activeTab == 1,
                          onTap: () => setState(() => _activeTab = 1),
                        ),
                        const SizedBox(width: 6),
                      ],
                      if (historyLogs.isNotEmpty) ...[
                        _HistoryTabChip(
                          label: '변경 이력',
                          count: historyLogs.length,
                          selected: _activeTab == 2,
                          onTap: () => setState(() => _activeTab = 2),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 8),

                // ── 로그 타일 목록 ─────────────────────────────────────────
                if (displayLogs.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    child: Center(
                      child: Text('해당 탭의 내역이 없습니다.',
                          style: AppTextStyles.caption),
                    ),
                  )
                else
                  ...displayLogs.map((log) => IssueLogTile(log: log)),
              ],
            );
          },
        );
      },
    );
  }
}

class _HistoryTabChip extends StatelessWidget {
  final String label;
  final int count;
  final bool selected;
  final VoidCallback onTap;

  const _HistoryTabChip({
    required this.label,
    required this.count,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: selected
              ? AppColors.accentWork.withAlpha(35)
              : AppColors.bgCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: selected ? AppColors.accentWork : AppColors.border,
            width: selected ? 1.2 : 0.8,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: AppTextStyles.label.copyWith(
                color: selected ? AppColors.accentWork : AppColors.textMuted,
                fontWeight: selected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              '$count',
              style: AppTextStyles.caption.copyWith(
                color: selected ? AppColors.accentWork : AppColors.textDisabled,
                fontWeight: FontWeight.bold,
                fontSize: 10.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 하단 댓글 입력창 ────────────────────────────────────────────────────────────
class _CommentInputBar extends StatelessWidget {
  final TextEditingController controller;
  final FocusNode focusNode;
  final bool isSending;
  final bool isPrivate;
  final bool canSetPrivate;
  final VoidCallback onTogglePrivate;
  final VoidCallback onSend;
  final VoidCallback onAttachPhoto;

  const _CommentInputBar({
    required this.controller,
    required this.focusNode,
    required this.isSending,
    required this.isPrivate,
    required this.canSetPrivate,
    required this.onTogglePrivate,
    required this.onSend,
    required this.onAttachPhoto,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(
        left: 8,
        right: 10,
        top: 6,
        bottom: MediaQuery.of(context).viewInsets.bottom + 8,
      ),
      decoration: const BoxDecoration(
        color: AppColors.bgSurface,
        border: Border(top: BorderSide(color: AppColors.border, width: 0.8)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (isPrivate)
            Padding(
              padding: const EdgeInsets.only(left: 12, bottom: 4),
              child: Row(
                children: [
                  const Icon(Icons.lock_rounded,
                      size: 13, color: AppColors.warning),
                  const SizedBox(width: 4),
                  Text('비밀 댓글로 등록됩니다 (관리자 및 작성자만 조회 가능)',
                      style: AppTextStyles.caption
                          .copyWith(color: AppColors.warning)),
                ],
              ),
            ),
          Row(
            children: [
              // 카메라/사진 첨부 버튼
              IconButton(
                icon: const Icon(Icons.camera_alt_outlined,
                    color: AppColors.textMuted, size: 20),
                tooltip: '사진 첨부',
                onPressed: onAttachPhoto,
                padding: const EdgeInsets.all(8),
                constraints: const BoxConstraints(),
              ),
              // 비밀 댓글 토글 (권한이 있는 경우)
              if (canSetPrivate)
                IconButton(
                  icon: Icon(
                    isPrivate
                        ? Icons.lock_rounded
                        : Icons.lock_open_outlined,
                    color:
                        isPrivate ? AppColors.warning : AppColors.textMuted,
                    size: 20,
                  ),
                  tooltip: isPrivate ? '비밀 댓글 해제' : '비밀 댓글 설정',
                  onPressed: onTogglePrivate,
                  padding: const EdgeInsets.all(8),
                  constraints: const BoxConstraints(),
                ),
              const SizedBox(width: 4),
              // 텍스트 입력
              Expanded(
                child: TextField(
                  controller: controller,
                  focusNode: focusNode,
                  style: AppTextStyles.bodyMd,
                  maxLines: 4,
                  minLines: 1,
                  decoration: InputDecoration(
                    hintText: isPrivate ? '비밀 댓글을 입력하세요...' : '댓글을 입력하세요...',
                    hintStyle: AppTextStyles.bodyMuted,
                    filled: true,
                    fillColor: AppColors.bgCard,
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 8),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide:
                          const BorderSide(color: AppColors.border, width: 0.8),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide:
                          const BorderSide(color: AppColors.border, width: 0.8),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide:
                          const BorderSide(color: AppColors.accentWork, width: 1.5),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 6),
              // 전송 버튼
              SizedBox(
                width: 40,
                height: 40,
                child: isSending
                    ? const Center(
                        child: SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: AppColors.accentWork),
                        ),
                      )
                    : IconButton(
                        icon: const Icon(Icons.send_rounded,
                            color: AppColors.accentWork, size: 20),
                        tooltip: '전송',
                        padding: EdgeInsets.zero,
                        onPressed: onSend,
                      ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
