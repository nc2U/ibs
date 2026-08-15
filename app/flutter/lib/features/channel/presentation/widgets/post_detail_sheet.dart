import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_widget_from_html/flutter_widget_from_html.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../data/models/forum_model.dart';
import '../../data/forum_repository.dart';
import '../../providers/forum_provider.dart';
import 'post_form_sheet.dart';

/// 게시글 상세 보기 바텀시트 (radius = 0)
class PostDetailSheet extends ConsumerStatefulWidget {
  final PostModel post;

  const PostDetailSheet({super.key, required this.post});

  @override
  ConsumerState<PostDetailSheet> createState() => _PostDetailSheetState();
}

class _PostDetailSheetState extends ConsumerState<PostDetailSheet> {
  final TextEditingController _commentController = TextEditingController();
  bool _isSubmittingComment = false;
  bool _isDownloadingFile = false;
  int? _replyParentId;

  @override
  void initState() {
    super.initState();
    // 조회수 카운트 증가
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(forumRepositoryProvider).hitPost(widget.post.pk);
    });
  }

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _handleDeletePost(BuildContext context) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Text('게시글 삭제', style: AppTextStyles.titleLg),
        content: Text(
          '\'${widget.post.title}\' 게시글을 정말 삭제하시겠습니까?',
          style: AppTextStyles.bodySecond,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: AppTextStyles.bodyMuted),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.error,
              shape: const RoundedRectangleBorder(
                  borderRadius: BorderRadius.zero),
            ),
            child: const Text('삭제'),
          ),
        ],
      ),
    );

    if (confirm != true || !mounted) return;

    try {
      final repo = ref.read(forumRepositoryProvider);
      await repo.deletePost(widget.post.pk);
      ref.read(postListProvider.notifier).refresh();
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('게시글이 삭제되었습니다.')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('삭제 실패: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Future<void> _handleLike() async {
    try {
      final repo = ref.read(forumRepositoryProvider);
      await repo.likePost(widget.post.pk);
      ref.invalidate(postDetailProvider(widget.post.pk));
      ref.read(postListProvider.notifier).refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: AppColors.error),
        );
      }
    }
  }

  Future<void> _handleBlame() async {
    try {
      final repo = ref.read(forumRepositoryProvider);
      await repo.blamePost(widget.post.pk);
      ref.invalidate(postDetailProvider(widget.post.pk));
      ref.read(postListProvider.notifier).refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: AppColors.error),
        );
      }
    }
  }

  Future<void> _handleAddComment() async {
    final text = _commentController.text.trim();
    if (text.isEmpty) return;

    final selectedProject = ref.read(selectedProjectProvider);

    setState(() => _isSubmittingComment = true);
    try {
      final repo = ref.read(forumRepositoryProvider);
      await repo.createComment(
        postId: widget.post.pk,
        content: text,
        parent: _replyParentId,
        projectSlug: selectedProject?.slug,
        projectId: selectedProject?.pk,
      );
      _commentController.clear();
      setState(() => _replyParentId = null);
      ref.invalidate(postCommentsProvider(widget.post.pk));
      ref.invalidate(postDetailProvider(widget.post.pk));
      ref.read(postListProvider.notifier).refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('댓글 작성 실패: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmittingComment = false);
    }
  }

  Future<void> _handleDeleteComment(int commentId) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Text('댓글 삭제', style: AppTextStyles.titleLg),
        content: const Text('댓글을 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: AppTextStyles.bodyMuted),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.error,
              shape: const RoundedRectangleBorder(
                  borderRadius: BorderRadius.zero),
            ),
            child: const Text('삭제'),
          ),
        ],
      ),
    );

    if (confirm != true || !mounted) return;

    try {
      final repo = ref.read(forumRepositoryProvider);
      await repo.deleteComment(commentId);
      ref.invalidate(postCommentsProvider(widget.post.pk));
      ref.invalidate(postDetailProvider(widget.post.pk));
      ref.read(postListProvider.notifier).refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('댓글 삭제 실패: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Future<void> _downloadAndOpenFile(PostFileModel file) async {
    setState(() => _isDownloadingFile = true);
    try {
      final dio = ref.read(dioProvider);
      final tempDir = await getTemporaryDirectory();
      final savePath = '${tempDir.path}/${file.fileName}';

      await dio.download(file.file, savePath);

      final result = await OpenFilex.open(savePath);
      if (result.type != ResultType.done && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('파일 열기 상태: ${result.message}')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('파일 다운로드 실패: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isDownloadingFile = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(postDetailProvider(widget.post.pk));
    final post = detailAsync.value ?? widget.post;
    final commentsAsync = ref.watch(postCommentsProvider(widget.post.pk));

    final currentUser = ref.watch(currentUserProvider).valueOrNull;
    final isAuthor = currentUser != null &&
        post.creator != null &&
        (currentUser.pk == post.creator!.pk ||
            currentUser.username == post.creator!.username);

    final canUpdate = isAuthor
        ? ref.can(Perm.forumOwnUpdate) || ref.can(Perm.forumUpdate) || ref.can(Perm.forumManage)
        : ref.can(Perm.forumUpdate) || ref.can(Perm.forumManage);

    final canDelete = isAuthor
        ? ref.can(Perm.forumOwnDelete) || ref.can(Perm.forumDelete) || ref.can(Perm.forumManage)
        : ref.can(Perm.forumDelete) || ref.can(Perm.forumManage);

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.9,
      ),
      decoration: const BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.zero,
      ),
      child: Column(
        children: [
          // ── 1. 상단 바 (배지 + 수정/삭제/닫기) ─────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.border, width: 0.8)),
            ),
            child: Row(
              children: [
                if (post.isNotice) ...[
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE5A93C).withAlpha(28),
                      borderRadius: BorderRadius.zero,
                      border: Border.all(
                          color: const Color(0xFFE5A93C).withAlpha(120), width: 0.8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.campaign_rounded,
                            size: 13, color: Color(0xFFE5A93C)),
                        const SizedBox(width: 4),
                        Text(
                          '공지',
                          style: AppTextStyles.caption.copyWith(
                            color: const Color(0xFFE5A93C),
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                ],
                if (post.cateName != null && post.cateName!.isNotEmpty) ...[
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.accentWork.withAlpha(20),
                      borderRadius: BorderRadius.zero,
                      border: Border.all(
                        color: AppColors.accentWork.withAlpha(60),
                        width: 0.8,
                      ),
                    ),
                    child: Text(
                      post.cateName!,
                      style: AppTextStyles.caption.copyWith(
                        color: AppColors.accentWork,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                ],
                if (post.forumName.isNotEmpty) ...[
                  Text(
                    post.forumName,
                    style: AppTextStyles.caption.copyWith(
                      color: AppColors.textSecond,
                    ),
                  ),
                ],
                const Spacer(),
                if (canUpdate)
                  IconButton(
                    icon: const Icon(Icons.edit_outlined, size: 20),
                    color: AppColors.textSecond,
                    onPressed: () {
                      Navigator.pop(context);
                      showModalBottomSheet(
                        context: context,
                        isScrollControlled: true,
                        backgroundColor: Colors.transparent,
                        builder: (ctx) => PostFormSheet(post: post),
                      );
                    },
                  ),
                if (canDelete)
                  IconButton(
                    icon: const Icon(Icons.delete_outline_rounded, size: 20),
                    color: AppColors.error,
                    onPressed: () => _handleDeletePost(context),
                  ),
                IconButton(
                  icon: const Icon(Icons.close_rounded, size: 20),
                  color: AppColors.textPrimary,
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),

          // ── 2. 본문 스크롤 영역 ──────────────────────────────────────────
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 제목
                  Text(post.title, style: AppTextStyles.titleLg),
                  const SizedBox(height: 10),

                  // 메타 정보 (작성자 + 등록일 + 조회수 + 추천수)
                  Row(
                    children: [
                      const Icon(Icons.person_outline_rounded,
                          size: 15, color: AppColors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        post.creator?.username ?? '익명',
                        style: AppTextStyles.bodySm.copyWith(
                          fontWeight: FontWeight.w600,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Icon(Icons.access_time_rounded,
                          size: 13, color: AppColors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        post.created?.substring(0, 16).replaceAll('T', ' ') ??
                            '',
                        style: AppTextStyles.caption
                            .copyWith(color: AppColors.textMuted),
                      ),
                      const Spacer(),
                      const Icon(Icons.visibility_outlined,
                          size: 13, color: AppColors.textMuted),
                      const SizedBox(width: 3),
                      Text('${post.hit}',
                          style: AppTextStyles.caption
                              .copyWith(color: AppColors.textMuted)),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // 본문 HTML 렌더링
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppColors.bgSurface,
                      borderRadius: BorderRadius.zero,
                      border: Border.all(color: AppColors.border, width: 0.8),
                    ),
                    child: post.content.isNotEmpty
                        ? HtmlWidget(
                            post.content,
                            textStyle: AppTextStyles.bodyMd.copyWith(
                              color: AppColors.textPrimary,
                              height: 1.5,
                            ),
                            customStylesBuilder: (element) {
                              if (element.localName == 'table') {
                                return {
                                  'border-collapse': 'collapse',
                                  'width': '100%',
                                };
                              }
                              if (element.localName == 'th' ||
                                  element.localName == 'td') {
                                return {
                                  'border': '1px solid #444',
                                  'padding': '6px 8px',
                                };
                              }
                              if (element.localName == 'img') {
                                return {
                                  'max-width': '100%',
                                  'height': 'auto',
                                };
                              }
                              return null;
                            },
                          )
                        : Text(
                            '본문 내용이 없습니다.',
                            style: AppTextStyles.bodyMd.copyWith(
                              color: AppColors.textMuted,
                            ),
                          ),
                  ),
                  const SizedBox(height: 16),

                  // 좋아요 / 비추천 버튼 바
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      OutlinedButton.icon(
                        onPressed: _handleLike,
                        icon: Icon(
                          post.myLike
                              ? Icons.thumb_up_alt_rounded
                              : Icons.thumb_up_alt_outlined,
                          size: 16,
                          color: post.myLike
                              ? AppColors.accentProject
                              : AppColors.textSecond,
                        ),
                        label: Text(
                          '추천 ${post.like}',
                          style: TextStyle(
                            color: post.myLike
                                ? AppColors.accentProject
                                : AppColors.textPrimary,
                            fontWeight: post.myLike
                                ? FontWeight.bold
                                : FontWeight.normal,
                          ),
                        ),
                        style: OutlinedButton.styleFrom(
                          side: BorderSide(
                            color: post.myLike
                                ? AppColors.accentProject
                                : AppColors.border,
                          ),
                          shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero),
                        ),
                      ),
                      const SizedBox(width: 12),
                      OutlinedButton.icon(
                        onPressed: _handleBlame,
                        icon: Icon(
                          post.myBlame
                              ? Icons.thumb_down_alt_rounded
                              : Icons.thumb_down_alt_outlined,
                          size: 16,
                          color: post.myBlame
                              ? AppColors.error
                              : AppColors.textSecond,
                        ),
                        label: Text(
                          '비추천 ${post.blame}',
                          style: TextStyle(
                            color: post.myBlame
                                ? AppColors.error
                                : AppColors.textPrimary,
                            fontWeight: post.myBlame
                                ? FontWeight.bold
                                : FontWeight.normal,
                          ),
                        ),
                        style: OutlinedButton.styleFrom(
                          side: BorderSide(
                            color: post.myBlame
                                ? AppColors.error
                                : AppColors.border,
                          ),
                          shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // 첨부파일 목록
                  if (post.files.isNotEmpty) ...[
                    Text(
                      '첨부파일 (${post.files.length})',
                      style: AppTextStyles.titleSm
                          .copyWith(color: AppColors.textSecond),
                    ),
                    const SizedBox(height: 8),
                    ...post.files.map((file) => Container(
                          margin: const EdgeInsets.only(bottom: 6),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 10),
                          decoration: BoxDecoration(
                            color: AppColors.bgSurface,
                            borderRadius: BorderRadius.zero,
                            border:
                                Border.all(color: AppColors.border, width: 0.8),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.attach_file_rounded,
                                  size: 16, color: AppColors.accentWork),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  file.fileName,
                                  style: AppTextStyles.bodySm,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.download_rounded,
                                    size: 18, color: AppColors.accentWork),
                                onPressed: _isDownloadingFile
                                    ? null
                                    : () => _downloadAndOpenFile(file),
                              ),
                            ],
                          ),
                        )),
                    const SizedBox(height: 20),
                  ],

                  // 댓글 섹션
                  commentsAsync.when(
                    data: (comments) {
                      final totalCount = comments.fold<int>(
                        comments.length,
                        (sum, c) => sum + c.replies.length,
                      );
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.chat_bubble_outline_rounded,
                                  size: 16, color: AppColors.accentWork),
                              const SizedBox(width: 6),
                              Text(
                                '댓글 ($totalCount)',
                                style: AppTextStyles.titleSm
                                    .copyWith(color: AppColors.textPrimary),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          if (comments.isEmpty)
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.symmetric(vertical: 20),
                              alignment: Alignment.center,
                              child: Text(
                                '등록된 댓글이 없습니다. 첫 번째 댓글을 남겨보세요!',
                                style: AppTextStyles.caption
                                    .copyWith(color: AppColors.textMuted),
                              ),
                            )
                          else
                            ...comments.map(
                              (c) => _buildCommentTile(c, currentUser),
                            ),
                        ],
                      );
                    },
                    loading: () => const Center(
                      child: Padding(
                        padding: EdgeInsets.all(16.0),
                        child: SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      ),
                    ),
                    error: (e, _) => Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Text('댓글 로드 실패: $e',
                          style: AppTextStyles.caption
                              .copyWith(color: AppColors.error)),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // ── 3. 하단 댓글 입력 바 ─────────────────────────────────────
          Container(
            decoration: const BoxDecoration(
              color: AppColors.bgSurface,
              border: Border(top: BorderSide(color: AppColors.border, width: 0.8)),
            ),
            child: SafeArea(
              top: false,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (_replyParentId != null)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 6),
                      color: AppColors.accentWork.withAlpha(25),
                      child: Row(
                        children: [
                          const Icon(Icons.reply_rounded,
                              size: 14, color: AppColors.accentWork),
                          const SizedBox(width: 6),
                          Text(
                            '답글 작성 중...',
                            style: AppTextStyles.caption.copyWith(
                              color: AppColors.accentWork,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const Spacer(),
                          GestureDetector(
                            onTap: () =>
                                setState(() => _replyParentId = null),
                            child: const Icon(Icons.close_rounded,
                                size: 14, color: AppColors.textMuted),
                          ),
                        ],
                      ),
                    ),
                  Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 10),
                    child: Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _commentController,
                            decoration: InputDecoration(
                              hintText: _replyParentId != null
                                  ? '답글을 입력해 주세요...'
                                  : '댓글을 입력해 주세요...',
                              hintStyle: AppTextStyles.bodyMuted,
                              filled: true,
                              fillColor: AppColors.bgCard,
                              isDense: true,
                              contentPadding: const EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 10),
                              border: const OutlineInputBorder(
                                borderRadius: BorderRadius.zero,
                                borderSide: BorderSide(color: AppColors.border),
                              ),
                              enabledBorder: const OutlineInputBorder(
                                borderRadius: BorderRadius.zero,
                                borderSide: BorderSide(color: AppColors.border),
                              ),
                              focusedBorder: const OutlineInputBorder(
                                borderRadius: BorderRadius.zero,
                                borderSide:
                                    BorderSide(color: AppColors.accentWork),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        FilledButton(
                          onPressed: _isSubmittingComment
                              ? null
                              : _handleAddComment,
                          style: FilledButton.styleFrom(
                            backgroundColor: AppColors.accentWork,
                            shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.zero),
                            padding: const EdgeInsets.symmetric(
                                horizontal: 16, vertical: 12),
                          ),
                          child: _isSubmittingComment
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Text('등록'),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCommentTile(PostCommentModel c, dynamic currentUser,
      {bool isReply = false}) {
    final isCommentAuthor = currentUser != null &&
        c.creator != null &&
        (currentUser.pk == c.creator!.pk ||
            currentUser.username == c.creator!.username);
    final canDeleteThisComment = ref.can(Perm.forumDelete) ||
        ref.can(Perm.forumManage) ||
        (ref.can(Perm.forumOwnDelete) && isCommentAuthor);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          margin: EdgeInsets.only(
            bottom: 8,
            left: isReply ? 20 : 0,
          ),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: isReply
                ? AppColors.bgSurface.withAlpha(160)
                : AppColors.bgSurface,
            borderRadius: BorderRadius.zero,
            border: Border.all(color: AppColors.border, width: 0.8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  if (isReply) ...[
                    const Icon(Icons.subdirectory_arrow_right_rounded,
                        size: 14, color: AppColors.textMuted),
                    const SizedBox(width: 4),
                  ],
                  Text(
                    c.creator?.username ?? '사용자',
                    style: AppTextStyles.label.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    c.created?.substring(0, 16).replaceAll('T', ' ') ?? '',
                    style: AppTextStyles.caption
                        .copyWith(color: AppColors.textMuted),
                  ),
                  const Spacer(),
                  if (!isReply)
                    GestureDetector(
                      onTap: () {
                        setState(() {
                          _replyParentId =
                              (_replyParentId == c.pk) ? null : c.pk;
                        });
                      },
                      child: Text(
                        _replyParentId == c.pk ? '답글취소' : '답글',
                        style: AppTextStyles.caption.copyWith(
                          color: _replyParentId == c.pk
                              ? AppColors.error
                              : AppColors.accentWork,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  if (canDeleteThisComment) ...[
                    const SizedBox(width: 10),
                    IconButton(
                      icon: const Icon(Icons.close_rounded,
                          size: 14, color: AppColors.textMuted),
                      onPressed: () => _handleDeleteComment(c.pk),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 6),
              Text(
                c.content,
                style: AppTextStyles.bodySm
                    .copyWith(color: AppColors.textPrimary),
              ),
            ],
          ),
        ),
        if (c.replies.isNotEmpty)
          ...c.replies.map(
            (r) => _buildCommentTile(r, currentUser, isReply: true),
          ),
      ],
    );
  }
}
