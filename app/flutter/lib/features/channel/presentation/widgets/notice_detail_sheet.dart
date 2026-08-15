import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:dio/dio.dart';
import 'package:flutter_widget_from_html/flutter_widget_from_html.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../data/models/notice_model.dart';
import '../../data/notice_repository.dart';
import '../../providers/notice_provider.dart';
import 'notice_form_sheet.dart';

/// 공지사항 상세 보기 바텀시트 (radius = 0)
class NoticeDetailSheet extends ConsumerStatefulWidget {
  final NoticeModel notice;

  const NoticeDetailSheet({super.key, required this.notice});

  @override
  ConsumerState<NoticeDetailSheet> createState() => _NoticeDetailSheetState();
}

class _NoticeDetailSheetState extends ConsumerState<NoticeDetailSheet> {
  final TextEditingController _commentController = TextEditingController();
  bool _isSubmittingComment = false;
  bool _isDownloadingFile = false;

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _handleDelete(BuildContext context) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Text('공지사항 삭제', style: AppTextStyles.titleLg),
        content: Text(
          '\'${widget.notice.title}\' 공지사항을 삭제하시겠습니까?',
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
              shape:
                  const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            ),
            child: const Text('삭제'),
          ),
        ],
      ),
    );

    if (confirm != true || !mounted) return;

    try {
      final repo = ref.read(noticeRepositoryProvider);
      await repo.deleteNotice(widget.notice.pk);
      ref.read(noticeListProvider.notifier).refresh();
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('공지사항이 삭제되었습니다.')),
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

  Future<void> _handleAddComment() async {
    final text = _commentController.text.trim();
    if (text.isEmpty) return;

    setState(() => _isSubmittingComment = true);
    try {
      final repo = ref.read(noticeRepositoryProvider);
      await repo.createComment(newsId: widget.notice.pk, content: text);
      _commentController.clear();
      // 공지 상세 및 목록 새로고침
      ref.invalidate(noticeDetailProvider(widget.notice.pk));
      ref.read(noticeListProvider.notifier).refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('댓글 등록 실패: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmittingComment = false);
    }
  }

  Future<void> _handleDeleteComment(int commentId) async {
    try {
      final repo = ref.read(noticeRepositoryProvider);
      await repo.deleteComment(commentId);
      ref.invalidate(noticeDetailProvider(widget.notice.pk));
      ref.read(noticeListProvider.notifier).refresh();
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

  Future<void> _downloadAndOpenFile(NoticeFileModel file) async {
    setState(() => _isDownloadingFile = true);
    try {
      final dio = ref.read(dioProvider);
      final dir = await getApplicationDocumentsDirectory();
      final savePath = '${dir.path}/${file.fileName}';

      await dio.download(file.file, savePath);
      await OpenFilex.open(savePath);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('파일 열기 실패: $e'),
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
    final detailAsync = ref.watch(noticeDetailProvider(widget.notice.pk));
    final notice = detailAsync.value ?? widget.notice;

    final canManage = ref.can(Perm.newsManage);
    final canComment = ref.can(Perm.newsComment);
    final currentUser = ref.watch(currentUserProvider).valueOrNull;

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.88,
      ),
      decoration: const BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.zero,
      ),
      child: Column(
        children: [
          // ── 상단 드래그 핸들 & 액션 바 ─────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.border, width: 0.8)),
            ),
            child: Row(
              children: [
                if (notice.isImportant) ...[
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.error.withAlpha(25),
                      borderRadius: BorderRadius.zero,
                      border: Border.all(color: AppColors.error, width: 0.8),
                    ),
                    child: Text(
                      '중요 공지',
                      style: AppTextStyles.caption.copyWith(
                        color: AppColors.error,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                ],
                if (notice.project != null) ...[
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.accentWork.withAlpha(20),
                      borderRadius: BorderRadius.zero,
                      border:
                          Border.all(color: AppColors.accentWork, width: 0.8),
                    ),
                    child: Text(
                      notice.project!.name,
                      style: AppTextStyles.caption.copyWith(
                        color: AppColors.accentWork,
                      ),
                    ),
                  ),
                ],
                const Spacer(),
                if (canManage) ...[
                  IconButton(
                    icon: const Icon(Icons.edit_outlined, size: 20),
                    color: AppColors.textSecond,
                    onPressed: () {
                      Navigator.pop(context);
                      showModalBottomSheet(
                        context: context,
                        isScrollControlled: true,
                        backgroundColor: Colors.transparent,
                        builder: (ctx) => NoticeFormSheet(notice: notice),
                      );
                    },
                  ),
                  IconButton(
                    icon: const Icon(Icons.delete_outline_rounded, size: 20),
                    color: AppColors.error,
                    onPressed: () => _handleDelete(context),
                  ),
                ],
                IconButton(
                  icon: const Icon(Icons.close_rounded, size: 20),
                  color: AppColors.textPrimary,
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),

          // ── 본문 스크롤 영역 ──────────────────────────────────────────
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 1. 공지 제목
                  Text(notice.title, style: AppTextStyles.titleLg),
                  const SizedBox(height: 8),

                  // 2. 작성자 및 작성일시
                  Row(
                    children: [
                      const Icon(Icons.person_outline_rounded,
                          size: 14, color: AppColors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        notice.author?.username ?? '작성자 미상',
                        style: AppTextStyles.caption
                            .copyWith(color: AppColors.textSecond),
                      ),
                      const SizedBox(width: 12),
                      const Icon(Icons.access_time_rounded,
                          size: 14, color: AppColors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        notice.created?.substring(0, 16).replaceAll('T', ' ') ??
                            '',
                        style: AppTextStyles.caption
                            .copyWith(color: AppColors.textMuted),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // 3. 요약문 (있을 경우)
                  if (notice.summary.isNotEmpty) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.bgSurface,
                        borderRadius: BorderRadius.zero,
                        border: Border.all(color: AppColors.border, width: 0.8),
                      ),
                      child: Text(
                        notice.summary,
                        style: AppTextStyles.bodyMd.copyWith(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // 4. 공지 본문 (HTML 파싱 렌더링)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppColors.bgSurface,
                      borderRadius: BorderRadius.zero,
                      border: Border.all(color: AppColors.border, width: 0.8),
                    ),
                    child: notice.content.isNotEmpty
                        ? HtmlWidget(
                            notice.content,
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

                  // 5. 첨부파일 목록
                  if (notice.files.isNotEmpty) ...[
                    Text(
                      '첨부파일 (${notice.files.length})',
                      style: AppTextStyles.titleSm
                          .copyWith(color: AppColors.textSecond),
                    ),
                    const SizedBox(height: 8),
                    ...notice.files.map((file) => Container(
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
                    const SizedBox(height: 16),
                  ],

                  // 6. 댓글 섹션
                  Row(
                    children: [
                      const Icon(Icons.chat_bubble_outline_rounded,
                          size: 16, color: AppColors.accentWork),
                      const SizedBox(width: 6),
                      Text(
                        '댓글 (${notice.comments.length})',
                        style: AppTextStyles.titleSm
                            .copyWith(color: AppColors.textPrimary),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  if (notice.comments.isEmpty)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 20),
                      alignment: Alignment.center,
                      child: Text(
                        '등록된 댓글이 없습니다.',
                        style: AppTextStyles.caption
                            .copyWith(color: AppColors.textMuted),
                      ),
                    )
                  else
                    ...notice.comments.map(
                      (c) {
                        final isAuthor = currentUser != null &&
                            c.creator != null &&
                            (currentUser.pk == c.creator!.pk ||
                                currentUser.username == c.creator!.username);
                        final canDeleteComment = canManage || (canComment && isAuthor);

                        return Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.bgSurface,
                            borderRadius: BorderRadius.zero,
                            border:
                                Border.all(color: AppColors.border, width: 0.8),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Text(
                                    c.creator?.username ?? '사용자',
                                    style: AppTextStyles.label.copyWith(
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    c.created?.substring(0, 16).replaceAll('T', ' ') ??
                                        '',
                                    style: AppTextStyles.caption
                                        .copyWith(color: AppColors.textMuted),
                                  ),
                                  const Spacer(),
                                  if (canDeleteComment)
                                    IconButton(
                                      icon: const Icon(Icons.close_rounded,
                                          size: 14, color: AppColors.textMuted),
                                      onPressed: () => _handleDeleteComment(c.pk),
                                      padding: EdgeInsets.zero,
                                      constraints: const BoxConstraints(),
                                    ),
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
                        );
                      },
                    ),
                ],
              ),
            ),
          ),

          // ── 하단 댓글 입력 바 (news.comment 권한 체크) ───────────────────
          if (canComment)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: const BoxDecoration(
                color: AppColors.bgSurface,
                border: Border(top: BorderSide(color: AppColors.border, width: 0.8)),
              ),
              child: SafeArea(
                top: false,
                child: Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _commentController,
                        decoration: InputDecoration(
                          hintText: '댓글을 입력해 주세요...',
                          hintStyle: AppTextStyles.bodyMuted,
                          filled: true,
                          fillColor: AppColors.bgCard,
                          isDense: true,
                          contentPadding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 10),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.zero,
                            borderSide:
                                const BorderSide(color: AppColors.border),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.zero,
                            borderSide:
                                const BorderSide(color: AppColors.border),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.zero,
                            borderSide:
                                const BorderSide(color: AppColors.accentWork),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    FilledButton(
                      onPressed:
                          _isSubmittingComment ? null : _handleAddComment,
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
            ),
        ],
      ),
    );
  }
}
