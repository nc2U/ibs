import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/widgets/error_view.dart';
import '../../../core/widgets/loading_shimmer.dart';
import '../data/issue_repository.dart';
import '../data/models/issue_model.dart';
import '../providers/issue_provider.dart';
import 'issue_form_screen.dart';
import 'widgets/done_ratio_bottom_sheet.dart';
import 'widgets/issue_comment_tile.dart';


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
          .addComment(content);
      _commentController.clear();
      _commentFocus.unfocus();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('댓글 등록에 실패했습니다.'),
            backgroundColor: AppColors.error,
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
            data: (issue) => IconButton(
              icon: const Icon(Icons.edit_outlined, size: 22),
              tooltip: '수정',
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => IssueFormScreen(initialIssue: issue),
                ),
              ),
            ),
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
                    child: Text(issue.description, style: AppTextStyles.bodyMd),
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

                // ── 댓글 ────────────────────────────────────────────────────
                _SectionLabel(label: '댓글'),
                _CommentSection(issueId: issue.pk),
                const SizedBox(height: 80), // 하단 입력창 여백
              ],
            ),
          ),
        ),

        // ── 하단 댓글 입력창 (고정) ─────────────────────────────────────────
        _CommentInputBar(
          controller: _commentController,
          focusNode: _commentFocus,
          isSending: _isSendingComment,
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
          if (issue.startDate.isNotEmpty)
            _InfoRow(
              label: '시작일',
              value: _fmt(issue.startDate),
              icon: Icons.calendar_today_outlined,
            ),
          if (issue.dueDate != null)
            _InfoRow(
              label: '완료기한',
              value: _fmt(issue.dueDate!),
              icon: Icons.event_outlined,
              valueColor: _dueDateColor(issue.dueDate!),
            ),
          // 진척률 (탭 → 바텀시트)
          const Divider(height: 1, color: AppColors.border),
          const SizedBox(height: 10),
          GestureDetector(
            onTap: () => showDoneRatioBottomSheet(
              context: context,
              ref: ref,
              issueId: issue.pk,
              currentRatio: issue.doneRatio,
            ),
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
                const SizedBox(width: 8),
                Icon(Icons.edit_outlined, size: 14, color: doneColor),
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

  Color _dueDateColor(String dueDate) {
    try {
      final due = DateTime.parse(dueDate);
      final now = DateTime.now();
      if (due.isBefore(now)) return AppColors.error;
      if (due.difference(now).inDays <= 3) return AppColors.warning;
    } catch (_) {}
    return AppColors.textSecond;
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
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        children: [
          Icon(icon, size: 16, color: AppColors.textMuted),
          const SizedBox(width: 8),
          SizedBox(
            width: 72,
            child: Text(label, style: AppTextStyles.bodyMuted),
          ),
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
    return Container(
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
    final issue = relation.issue!;
    final isPrec = direction == '선행';
    final color = isPrec ? AppColors.accentApproval : AppColors.accentProject;

    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
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
                '#${issue.pk} ${issue.subject}',
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

// ── 댓글 섹션 ──────────────────────────────────────────────────────────────────
class _CommentSection extends ConsumerWidget {
  final int issueId;
  const _CommentSection({required this.issueId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final commentsState = ref.watch(issueCommentProvider(issueId));
    return commentsState.when(
      loading: () =>
          const LoadingShimmer(itemCount: 2, itemHeight: 80),
      error: (e, _) => const ErrorView.empty(message: '댓글을 불러오지 못했습니다.'),
      data: (comments) {
        if (comments.isEmpty) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Text('첫 번째 댓글을 작성해 보세요.',
                style: AppTextStyles.bodyMuted),
          );
        }
        return Column(
          children: comments
              .map((c) => IssueCommentTile(comment: c))
              .toList(),
        );
      },
    );
  }
}

// ── 하단 댓글 입력창 ────────────────────────────────────────────────────────────
class _CommentInputBar extends StatelessWidget {
  final TextEditingController controller;
  final FocusNode focusNode;
  final bool isSending;
  final VoidCallback onSend;
  final VoidCallback onAttachPhoto;

  const _CommentInputBar({
    required this.controller,
    required this.focusNode,
    required this.isSending,
    required this.onSend,
    required this.onAttachPhoto,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(
        left: 12,
        right: 12,
        top: 8,
        bottom: MediaQuery.of(context).viewInsets.bottom + 8,
      ),
      decoration: const BoxDecoration(
        color: AppColors.bgSurface,
        border: Border(top: BorderSide(color: AppColors.border, width: 0.8)),
      ),
      child: Row(
        children: [
          // 카메라 버튼
          IconButton(
            icon: const Icon(Icons.camera_alt_outlined,
                color: AppColors.textMuted, size: 22),
            tooltip: '사진 첨부',
            onPressed: onAttachPhoto,
          ),
          // 텍스트 입력
          Expanded(
            child: TextField(
              controller: controller,
              focusNode: focusNode,
              style: AppTextStyles.bodyMd,
              maxLines: 4,
              minLines: 1,
              decoration: InputDecoration(
                hintText: '댓글을 입력하세요...',
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
          const SizedBox(width: 8),
          // 전송 버튼
          SizedBox(
            width: 44,
            height: 44,
            child: isSending
                ? const Center(
                    child: SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: AppColors.accentWork),
                    ),
                  )
                : IconButton(
                    icon: const Icon(Icons.send_rounded,
                        color: AppColors.accentWork, size: 22),
                    tooltip: '전송',
                    onPressed: onSend,
                  ),
          ),
        ],
      ),
    );
  }
}
