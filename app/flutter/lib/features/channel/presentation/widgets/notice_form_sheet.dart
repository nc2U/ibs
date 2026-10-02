import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../project/providers/project_provider.dart';
import '../../data/models/notice_model.dart';
import '../../data/notice_repository.dart';
import '../../providers/notice_provider.dart';

/// 공지사항 등록 및 수정 바텀시트 (radius = 0)
class NoticeFormSheet extends ConsumerStatefulWidget {
  final NoticeModel? notice;

  const NoticeFormSheet({super.key, this.notice});

  @override
  ConsumerState<NoticeFormSheet> createState() => _NoticeFormSheetState();
}

class _NoticeFormSheetState extends ConsumerState<NoticeFormSheet> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _titleController;
  late final TextEditingController _summaryController;
  late final TextEditingController _contentController;

  int? _selectedProjectPk;
  bool _isImportant = false;
  bool _isSubmitting = false;

  final List<PlatformFile> _newFiles = [];
  final List<int> _deleteFilePks = [];

  @override
  void initState() {
    super.initState();
    final n = widget.notice;
    _titleController = TextEditingController(text: n?.title ?? '');
    _summaryController = TextEditingController(text: n?.summary ?? '');
    _contentController = TextEditingController(text: n?.content ?? '');
    _isImportant = n?.isImportant ?? false;
    _selectedProjectPk = n?.project?.pk;
  }

  @override
  void dispose() {
    _titleController.dispose();
    _summaryController.dispose();
    _contentController.dispose();
    super.dispose();
  }

  Future<void> _pickFiles() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        allowMultiple: true,
        type: FileType.any,
        withData: true,
      );
      if (result != null && result.files.isNotEmpty) {
        setState(() {
          _newFiles.addAll(result.files);
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('파일 선택 오류: $e')),
        );
      }
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    if (!ref.can(Perm.newsManage)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('공지사항 관리 권한(news.manage)이 없습니다.'),
          backgroundColor: context.colors.error,
        ),
      );
      return;
    }

    final currentWs = ref.read(selectedProjectProvider);
    final targetProjectPk = _selectedProjectPk ?? currentWs?.pk;

    if (widget.notice == null && targetProjectPk == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('공지사항을 등록할 워크스페이스를 선택해 주세요.'),
          backgroundColor: context.colors.error,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    final repo = ref.read(noticeRepositoryProvider);

    try {
      if (widget.notice == null) {
        await repo.createNotice(
          projectId: targetProjectPk!,
          title: _titleController.text.trim(),
          summary: _summaryController.text.trim(),
          content: _contentController.text.trim(),
          isImportant: _isImportant,
          newFiles: _newFiles.isNotEmpty ? _newFiles : null,
        );
      } else {
        await repo.updateNotice(
          id: widget.notice!.pk,
          projectId: targetProjectPk,
          title: _titleController.text.trim(),
          summary: _summaryController.text.trim(),
          content: _contentController.text.trim(),
          isImportant: _isImportant,
          newFiles: _newFiles.isNotEmpty ? _newFiles : null,
          deleteFilePks: _deleteFilePks.isNotEmpty ? _deleteFilePks : null,
        );
        ref.invalidate(noticeDetailProvider(widget.notice!.pk));
      }

      ref.read(noticeListProvider.notifier).refresh();

      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.notice == null
                ? '공지사항이 등록되었습니다.'
                : '공지사항이 수정되었습니다.'),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('처리 실패: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.notice != null;
    final projectsAsync = ref.watch(newsFormProjectsProvider);
    final currentWs = ref.watch(selectedProjectProvider);

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.9,
      ),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
      ),
      child: Form(
        key: _formKey,
        child: Column(
          children: [
            // ── 상단 타이틀 바 ─────────────────────────────────────────
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                border: Border(
                    bottom: BorderSide(color: context.colors.border, width: 0.8)),
              ),
              child: Row(
                children: [
                  Icon(Icons.campaign_rounded,
                      size: 20, color: context.colors.accentWork),
                  const SizedBox(width: 8),
                  Text(
                    isEdit ? '공지사항 수정' : '새 공지사항 등록',
                    style: AppTextStyles.titleLg.copyWith(color: context.colors.textPrimary),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: Icon(Icons.close_rounded, size: 20, color: context.colors.textPrimary),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),

            // ── 입력 폼 스크롤 영역 ──────────────────────────────────────
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 1. 워크스페이스 선택
                    Text('워크스페이스',
                        style: AppTextStyles.caption
                            .copyWith(color: context.colors.textSecond)),
                    const SizedBox(height: 6),
                    projectsAsync.when(
                      data: (projects) {
                        final effectivePk = _selectedProjectPk ??
                            currentWs?.pk ??
                            (projects.isNotEmpty ? projects.first.pk : null);
                        return Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          decoration: BoxDecoration(
                            color: context.colors.bgSurface,
                            border: Border.all(color: context.colors.border),
                          ),
                          child: DropdownButtonHideUnderline(
                            child: DropdownButton<int?>(
                              value: effectivePk,
                              isExpanded: true,
                              dropdownColor: context.colors.bgCard,
                              style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
                              items: projects
                                  .map(
                                    (p) => DropdownMenuItem<int?>(
                                      value: p.pk,
                                      child: Text(p.name,
                                          style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary)),
                                    ),
                                  )
                                  .toList(),
                              onChanged: (val) {
                                setState(() => _selectedProjectPk = val);
                              },
                            ),
                          ),
                        );
                      },
                      loading: () => const LinearProgressIndicator(),
                      error: (e, s) => Text('워크스페이스 로딩 실패: $e',
                          style: AppTextStyles.bodyMuted.copyWith(color: context.colors.error)),
                    ),
                    const SizedBox(height: 14),

                    // 2. 제목 입력
                    Text('공지 제목 *',
                        style: AppTextStyles.caption
                            .copyWith(color: context.colors.textSecond)),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _titleController,
                      style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
                      validator: (val) => (val == null || val.trim().isEmpty)
                          ? '제목을 입력해 주세요.'
                          : null,
                      decoration: InputDecoration(
                        hintText: '공지사항 제목을 입력하세요',
                        hintStyle: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                        filled: true,
                        fillColor: context.colors.bgSurface,
                        contentPadding: const EdgeInsets.all(12),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: context.colors.border),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: context.colors.border),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: context.colors.accentWork),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),

                    // 3. 중요 공지 여부 토글
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: context.colors.bgSurface,
                        border: Border.all(
                          color: _isImportant
                              ? context.colors.error.withAlpha(120)
                              : context.colors.border,
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.campaign_rounded,
                              size: 18,
                              color: _isImportant
                                  ? context.colors.error
                                  : context.colors.textMuted),
                          const SizedBox(width: 8),
                          Text(
                            '중요 공지 (목록 최상단 고정)',
                            style: AppTextStyles.bodySm.copyWith(
                              color: _isImportant
                                  ? context.colors.error
                                  : context.colors.textPrimary,
                              fontWeight: _isImportant
                                  ? FontWeight.bold
                                  : FontWeight.normal,
                            ),
                          ),
                          const Spacer(),
                          Switch(
                            value: _isImportant,
                            activeThumbColor: context.colors.error,
                            onChanged: (val) =>
                                setState(() => _isImportant = val),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // 4. 요약문 입력
                    Text('요약문 (선택)',
                        style: AppTextStyles.caption
                            .copyWith(color: context.colors.textSecond)),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _summaryController,
                      style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
                      maxLines: 2,
                      decoration: InputDecoration(
                        hintText: '공지사항의 핵심 요약을 간단히 입력하세요',
                        hintStyle: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                        filled: true,
                        fillColor: context.colors.bgSurface,
                        contentPadding: const EdgeInsets.all(12),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: context.colors.border),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: context.colors.border),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: context.colors.accentWork),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),

                    // 5. 공지 내용 입력
                    Text('공지 본문 *',
                        style: AppTextStyles.caption
                            .copyWith(color: context.colors.textSecond)),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _contentController,
                      style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
                      maxLines: 6,
                      validator: (val) => (val == null || val.trim().isEmpty)
                          ? '본문 내용을 입력해 주세요.'
                          : null,
                      decoration: InputDecoration(
                        hintText: '공지사항 상세 내용을 입력하세요',
                        hintStyle: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                        filled: true,
                        fillColor: context.colors.bgSurface,
                        contentPadding: const EdgeInsets.all(12),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: context.colors.border),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: context.colors.border),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: context.colors.accentWork),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // 6. 첨부파일 관리
                    Row(
                      children: [
                        Text('첨부파일',
                            style: AppTextStyles.caption
                                .copyWith(color: context.colors.textSecond)),
                        const Spacer(),
                        OutlinedButton.icon(
                          onPressed: _pickFiles,
                          icon: const Icon(Icons.attach_file_rounded, size: 14),
                          label: const Text('파일 추가'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: context.colors.accentWork,
                            side: BorderSide(color: context.colors.accentWork),
                            shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.zero),
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 6),
                            minimumSize: Size.zero,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),

                    // 기존 첨부파일 목록 (수정 모드)
                    if (isEdit && widget.notice!.files.isNotEmpty) ...[
                      ...widget.notice!.files.map((file) {
                        final isDeleted = _deleteFilePks.contains(file.pk);
                        return Container(
                          margin: const EdgeInsets.only(bottom: 6),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: isDeleted
                                ? context.colors.error.withAlpha(20)
                                : context.colors.bgSurface,
                            border: Border.all(color: context.colors.border),
                          ),
                          child: Row(
                            children: [
                              Icon(Icons.insert_drive_file_outlined,
                                  size: 14,
                                  color: isDeleted
                                      ? context.colors.error
                                      : context.colors.textMuted),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  file.fileName,
                                  style: AppTextStyles.bodySm.copyWith(
                                    decoration: isDeleted
                                        ? TextDecoration.lineThrough
                                        : null,
                                    color: isDeleted
                                        ? context.colors.error
                                        : context.colors.textPrimary,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              IconButton(
                                icon: Icon(
                                  isDeleted
                                      ? Icons.undo_rounded
                                      : Icons.close_rounded,
                                  size: 16,
                                  color: isDeleted
                                      ? context.colors.accentWork
                                      : context.colors.error,
                                ),
                                onPressed: () {
                                  setState(() {
                                    if (isDeleted) {
                                      _deleteFilePks.remove(file.pk);
                                    } else {
                                      _deleteFilePks.add(file.pk);
                                    }
                                  });
                                },
                              ),
                            ],
                          ),
                        );
                      }),
                    ],

                    // 새로 추가된 파일 목록
                    if (_newFiles.isNotEmpty) ...[
                      ..._newFiles.asMap().entries.map((entry) {
                        final idx = entry.key;
                        final file = entry.value;
                        return Container(
                          margin: const EdgeInsets.only(bottom: 6),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: context.colors.bgSurface,
                            border:
                                Border.all(color: context.colors.accentWork.withAlpha(80)),
                          ),
                          child: Row(
                            children: [
                              Icon(Icons.upload_file_rounded,
                                  size: 14, color: context.colors.accentWork),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  file.name,
                                  style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              IconButton(
                                icon: Icon(Icons.close_rounded,
                                    size: 16, color: context.colors.error),
                                onPressed: () {
                                  setState(() {
                                    _newFiles.removeAt(idx);
                                  });
                                },
                              ),
                            ],
                          ),
                        );
                      }),
                    ],
                  ],
                ),
              ),
            ),

            // ── 하단 제출 버튼 ─────────────────────────────────────────
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                border: Border(
                    top: BorderSide(color: context.colors.border, width: 0.8)),
              ),
              child: SizedBox(
                width: double.infinity,
                height: 48,
                child: FilledButton(
                  onPressed: _isSubmitting ? null : _submit,
                  style: FilledButton.styleFrom(
                    backgroundColor: context.colors.accentWork,
                    shape: const RoundedRectangleBorder(
                        borderRadius: BorderRadius.zero),
                  ),
                  child: _isSubmitting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Text(
                          isEdit ? '수정 완료' : '공지사항 등록',
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                          ),
                        ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
