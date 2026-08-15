import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/docs_context_provider.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../project/providers/project_provider.dart';

import '../../data/docs_repository.dart';
import '../../data/models/docs_model.dart';
import '../../providers/docs_provider.dart';

/// 문서 생성 및 수정 폼 바텀시트
class DocumentFormSheet extends ConsumerStatefulWidget {
  final DocumentModel? doc; // null이면 생성, 값이 있으면 수정
  final List<PlatformFile>? initialFiles;
  final List<String>? initialLinks;
  final String? initialTitle;

  const DocumentFormSheet({
    super.key,
    this.doc,
    this.initialFiles,
    this.initialLinks,
    this.initialTitle,
  });

  @override
  ConsumerState<DocumentFormSheet> createState() => _DocumentFormSheetState();
}

class _DocumentFormSheetState extends ConsumerState<DocumentFormSheet> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _titleController;
  late TextEditingController _descController;
  late TextEditingController _dateController;
  final TextEditingController _linkInputController = TextEditingController();

  int? _selectedProjectPk;
  int? _selectedCategory;
  bool _isSecret = false;
  bool _isSubmitting = false;

  // 신규 첨부 목록
  final List<PlatformFile> _newFiles = [];
  final List<String> _newLinks = [];

  // 수정 시 삭제할 기존 항목 PK
  final List<int> _deleteFilePks = [];
  final List<int> _deleteLinkPks = [];

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(
        text: widget.doc?.title ?? widget.initialTitle ?? '');
    _descController =
        TextEditingController(text: widget.doc?.description ?? '');
    _dateController =
        TextEditingController(text: widget.doc?.executionDate ?? '');
    _selectedProjectPk =
        widget.doc?.project?.pk ?? ref.read(docsContextProvider).project?.pk;
    _selectedCategory = widget.doc?.category;
    _isSecret = widget.doc?.isSecret ?? false;

    if (widget.initialFiles != null) {
      _newFiles.addAll(widget.initialFiles!);
    }
    if (widget.initialLinks != null) {
      _newLinks.addAll(widget.initialLinks!);
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    _dateController.dispose();
    _linkInputController.dispose();
    super.dispose();
  }

  String _formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  Future<void> _pickDate() async {
    DateTime initialDate = DateTime.now();
    if (_dateController.text.isNotEmpty) {
      try {
        initialDate = DateTime.parse(_dateController.text);
      } catch (_) {}
    }
    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2050),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.dark(
              primary: AppColors.accentWork,
              onPrimary: Colors.white,
              surface: AppColors.bgSurface,
              onSurface: AppColors.textPrimary,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() {
        _dateController.text =
            "${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}";
      });
    }
  }

  Future<void> _pickFiles() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        allowMultiple: true,
        type: FileType.any,
      );
      if (result != null && result.files.isNotEmpty) {
        setState(() {
          _newFiles.addAll(result.files);
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('파일을 선택하지 못했습니다: $e')),
        );
      }
    }
  }

  void _showAddLinkDialog() {
    _linkInputController.clear();
    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => Dialog(
          insetPadding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
          backgroundColor: AppColors.bgCard,
          shape:
              const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.link_rounded,
                            size: 22, color: Color(0xFF1565C0)),
                        const SizedBox(width: 8),
                        Text('관련 웹 링크 추가', style: AppTextStyles.titleLg),
                      ],
                    ),
                    IconButton(
                      icon: const Icon(Icons.close_rounded, size: 20),
                      color: AppColors.textMuted,
                      onPressed: () => Navigator.pop(ctx),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Google Drive, Notion, 클라우드, 웹 페이지 등의 URL을 입력하세요.',
                  style: AppTextStyles.caption
                      .copyWith(color: AppColors.textMuted),
                ),
                const SizedBox(height: 14),
                // 입력창
                TextField(
                  controller: _linkInputController,
                  autofocus: true,
                  maxLines: 4,
                  minLines: 2,
                  keyboardType: TextInputType.url,
                  style:
                      AppTextStyles.bodyMd.copyWith(fontFamily: 'monospace'),
                  decoration: const InputDecoration(
                    hintText: 'https://drive.google.com/... 또는 https://...',
                    alignLabelWithHint: true,
                    contentPadding: EdgeInsets.all(12),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.zero,
                      borderSide: BorderSide(color: AppColors.border),
                    ),
                  ),
                  onChanged: (_) => setDialogState(() {}),
                ),
                const SizedBox(height: 10),
                // 퀵 액션 (붙여넣기 / 지우기)
                Row(
                  children: [
                    OutlinedButton.icon(
                      onPressed: () async {
                        final data =
                            await Clipboard.getData(Clipboard.kTextPlain);
                        if (data?.text != null &&
                            data!.text!.trim().isNotEmpty) {
                          _linkInputController.text = data.text!.trim();
                          setDialogState(() {});
                        }
                      },
                      icon: const Icon(Icons.content_paste_rounded, size: 15),
                      label: const Text('클립보드 붙여넣기'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.textPrimary,
                        side: const BorderSide(color: AppColors.border),
                        shape: const RoundedRectangleBorder(
                            borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 6),
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                    ),
                    if (_linkInputController.text.isNotEmpty) ...[
                      const SizedBox(width: 8),
                      TextButton.icon(
                        onPressed: () {
                          _linkInputController.clear();
                          setDialogState(() {});
                        },
                        icon: const Icon(Icons.clear_rounded, size: 15),
                        label: const Text('지우기'),
                        style: TextButton.styleFrom(
                          foregroundColor: AppColors.textMuted,
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 6),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 20),
                // 액션 버튼
                Row(
                  children: [
                    Expanded(
                      flex: 1,
                      child: OutlinedButton(
                        onPressed: () => Navigator.pop(ctx),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppColors.textSecond,
                          side: const BorderSide(color: AppColors.border),
                          shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero),
                          padding: const EdgeInsets.symmetric(vertical: 13),
                        ),
                        child: const Text('취소'),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      flex: 2,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1565C0),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 13),
                          shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero),
                        ),
                        onPressed: _linkInputController.text.trim().isEmpty
                            ? null
                            : () {
                                var text = _linkInputController.text.trim();
                                if (text.isNotEmpty) {
                                  if (!text.startsWith('http://') &&
                                      !text.startsWith('https://')) {
                                    text = 'https://$text';
                                  }
                                  setState(() {
                                    _newLinks.add(text);
                                  });
                                }
                                Navigator.pop(ctx);
                              },
                        child: Text(
                          '링크 등록',
                          style: AppTextStyles.titleSm.copyWith(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final isEdit = widget.doc != null;
    final canPerform =
        isEdit ? ref.can(Perm.docsUpdate) : ref.can(Perm.docsCreate);
    if (!canPerform) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(isEdit
              ? '문서 수정 권한(docs.update)이 없습니다.'
              : '문서 등록 권한(docs.create)이 없습니다.'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    final repo = ref.read(docsRepositoryProvider);
    final ctx = ref.read(docsContextProvider);

    final issueProjectId =
        _selectedProjectPk ?? ctx.project?.pk ?? widget.doc?.project?.pk;
    if (widget.doc == null && issueProjectId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('문서를 등록할 워크스페이스를 먼저 선택해 주세요.')),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      if (widget.doc == null) {
        await repo.createDocument(
          issueProjectId: issueProjectId!,
          title: _titleController.text.trim(),
          categoryId: _selectedCategory,
          executionDate: _dateController.text.trim(),
          description: _descController.text.trim(),
          isSecret: _isSecret,
          newFiles: _newFiles.isNotEmpty ? _newFiles : null,
          newLinks: _newLinks.isNotEmpty ? _newLinks : null,
        );
      } else {
        await repo.updateDocument(
          id: widget.doc!.pk,
          title: _titleController.text.trim(),
          categoryId: _selectedCategory,
          executionDate: _dateController.text.trim(),
          description: _descController.text.trim(),
          isSecret: _isSecret,
          newFiles: _newFiles.isNotEmpty ? _newFiles : null,
          newLinks: _newLinks.isNotEmpty ? _newLinks : null,
          deleteFilePks: _deleteFilePks.isNotEmpty ? _deleteFilePks : null,
          deleteLinkPks: _deleteLinkPks.isNotEmpty ? _deleteLinkPks : null,
        );
      }

      ref.read(docsListProvider.notifier).refresh();
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
                widget.doc == null ? '문서가 등록되었습니다.' : '문서가 수정되었습니다.'),
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('처리 실패: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final categoriesAsync = ref.watch(docCategoriesProvider);
    final isEdit = widget.doc != null;

    // 기존 파일 및 링크 중 아직 삭제 표시되지 않은 항목들
    final existingFiles = widget.doc?.files
            .where((f) => !_deleteFilePks.contains(f.pk))
            .toList() ??
        [];
    final existingLinks = widget.doc?.links
            .where((l) => !_deleteLinkPks.contains(l.pk))
            .toList() ??
        [];

    return Container(
      decoration: const BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.zero,
      ),
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 12,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 드래그 핸들 ──────────────────────────────────────────────
              Center(
                child: Container(
                  width: 36,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: AppColors.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              // ── 헤더 (타이틀 & 닫기) ───────────────────────────────────────
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Icon(
                        isEdit ? Icons.edit_note_rounded : Icons.note_add_rounded,
                        color: AppColors.accentWork,
                        size: 24,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        isEdit ? '문서 수정' : '신규 문서 등록',
                        style: AppTextStyles.titleLg,
                      ),
                    ],
                  ),
                  IconButton(
                    icon: const Icon(Icons.close_rounded, size: 22),
                    color: AppColors.textMuted,
                    onPressed: () => Navigator.pop(context),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const Divider(color: AppColors.border, height: 1),
              const SizedBox(height: 16),

              // ── 1. 워크스페이스 선택 ───────────────────────────────────────
              if (!isEdit) ...[
                Text('워크스페이스 *', style: AppTextStyles.caption.copyWith(color: AppColors.textMuted)),
                const SizedBox(height: 6),
                ref.watch(docFormProjectsProvider).when(
                      loading: () => const LinearProgressIndicator(),
                      error: (_, __) => Text('프로젝트 목록 로드 실패',
                          style: AppTextStyles.caption.copyWith(color: AppColors.error)),
                      data: (projects) {
                        final validPk = (_selectedProjectPk != null &&
                                projects.any((p) => p.pk == _selectedProjectPk))
                            ? _selectedProjectPk
                            : (projects.isNotEmpty ? projects.first.pk : null);

                        return DropdownButtonFormField<int>(
                          value: validPk,
                          isExpanded: true,
                          style: AppTextStyles.bodyMd,
                          dropdownColor: AppColors.bgCard,
                          decoration: InputDecoration(
                            hintText: '워크스페이스 선택',
                            prefixIcon: const Icon(Icons.folder_outlined, size: 18, color: AppColors.accentWork),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                            border: const OutlineInputBorder(
                              borderRadius: BorderRadius.zero,
                              borderSide: BorderSide(color: AppColors.border),
                            ),
                          ),
                          items: projects
                              .map((p) => DropdownMenuItem<int>(
                                    value: p.pk,
                                    child: Text(p.indentedLabel, overflow: TextOverflow.ellipsis),
                                  ))
                              .toList(),
                          onChanged: (v) => setState(() => _selectedProjectPk = v),
                          validator: (v) => v == null ? '워크스페이스를 선택해 주세요.' : null,
                        );
                      },
                    ),
                const SizedBox(height: 14),
              ] else if (widget.doc?.project != null) ...[
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: AppColors.bgSurface,
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.folder_open_rounded, size: 18, color: AppColors.accentWork),
                      const SizedBox(width: 8),
                      Text('소속 워크스페이스: ', style: AppTextStyles.caption.copyWith(color: AppColors.textMuted)),
                      Expanded(
                        child: Text(
                          widget.doc!.project!.name,
                          style: AppTextStyles.titleSm.copyWith(color: AppColors.accentWork),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),
              ],

              // ── 2. 문서 제목 ─────────────────────────────────────────────
              Text('문서 제목 *', style: AppTextStyles.caption.copyWith(color: AppColors.textMuted)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _titleController,
                style: AppTextStyles.bodyLg,
                decoration: const InputDecoration(
                  hintText: '문서 제목을 입력하세요',
                  prefixIcon: Icon(Icons.title_rounded, size: 18, color: AppColors.textMuted),
                  contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                ),
                validator: (v) => (v == null || v.trim().isEmpty) ? '제목을 입력해 주세요.' : null,
              ),
              const SizedBox(height: 14),

              // ── 3. 카테고리 & 시행일자 (2열 레이아웃) ──────────────────────
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 카테고리
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('카테고리', style: AppTextStyles.caption.copyWith(color: AppColors.textMuted)),
                        const SizedBox(height: 6),
                        categoriesAsync.when(
                          data: (categories) {
                            final validCate = (_selectedCategory != null &&
                                    categories.any((c) => c.pk == _selectedCategory))
                                ? _selectedCategory
                                : null;

                            return DropdownButtonFormField<int?>(
                              value: validCate,
                              isExpanded: true,
                              style: AppTextStyles.bodyMd,
                              dropdownColor: AppColors.bgCard,
                              decoration: const InputDecoration(
                                prefixIcon: Icon(Icons.label_outline_rounded, size: 18, color: AppColors.textMuted),
                                contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                              ),
                              items: [
                                const DropdownMenuItem<int?>(
                                  value: null,
                                  child: Text('선택 안 함'),
                                ),
                                ...categories.map((c) => DropdownMenuItem<int?>(
                                      value: c.pk,
                                      child: Text(c.name, overflow: TextOverflow.ellipsis),
                                    )),
                              ],
                              onChanged: (v) => setState(() => _selectedCategory = v),
                            );
                          },
                          loading: () => const LinearProgressIndicator(),
                          error: (e, s) => Text('카테고리 로드 실패',
                              style: AppTextStyles.caption.copyWith(color: AppColors.error)),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  // 시행일자 (탭 시 달력)
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('시행일자', style: AppTextStyles.caption.copyWith(color: AppColors.textMuted)),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _dateController,
                          readOnly: true,
                          onTap: _pickDate,
                          style: AppTextStyles.bodyMd,
                          decoration: InputDecoration(
                            hintText: '날짜 선택',
                            prefixIcon: const Icon(Icons.calendar_today_rounded, size: 18, color: AppColors.textMuted),
                            suffixIcon: _dateController.text.isNotEmpty
                                ? IconButton(
                                    icon: const Icon(Icons.clear_rounded, size: 16),
                                    onPressed: () => setState(() => _dateController.clear()),
                                  )
                                : null,
                            contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),

              // ── 4. 설명 / 내용 ───────────────────────────────────────────
              Text('설명 / 비고', style: AppTextStyles.caption.copyWith(color: AppColors.textMuted)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _descController,
                maxLines: 3,
                style: AppTextStyles.bodyMd,
                decoration: const InputDecoration(
                  hintText: '문서 관련 주요 설명이나 비고를 입력하세요',
                  contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                ),
              ),
              const SizedBox(height: 16),

              // ── 5. 첨부 파일 섹션 ─────────────────────────────────────────
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.attach_file_rounded, size: 18, color: AppColors.accentWork),
                      const SizedBox(width: 6),
                      Text('첨부 파일 (${existingFiles.length + _newFiles.length})',
                          style: AppTextStyles.titleSm),
                    ],
                  ),
                  OutlinedButton.icon(
                    onPressed: _pickFiles,
                    icon: const Icon(Icons.add_rounded, size: 15),
                    label: const Text('파일 추가'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.accentWork,
                      side: const BorderSide(color: AppColors.accentWork),
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              if (existingFiles.isEmpty && _newFiles.isEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  decoration: BoxDecoration(
                    color: AppColors.bgSurface,
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Center(
                    child: Text('첨부된 파일이 없습니다. (+ 파일 추가)',
                        style: AppTextStyles.caption.copyWith(color: AppColors.textMuted)),
                  ),
                )
              else
                Column(
                  children: [
                    // 기존 파일 목록
                    ...existingFiles.map((file) => Container(
                          margin: const EdgeInsets.only(bottom: 6),
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                          decoration: BoxDecoration(
                            color: AppColors.bgSurface,
                            border: Border.all(color: AppColors.border),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.insert_drive_file_outlined,
                                  size: 18, color: AppColors.accentWork),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  file.fileName ?? (file.file?.split('/').last ?? '첨부파일'),
                                  style: AppTextStyles.bodySm,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close_rounded, size: 16, color: AppColors.error),
                                onPressed: () {
                                  setState(() {
                                    _deleteFilePks.add(file.pk);
                                  });
                                },
                                padding: EdgeInsets.zero,
                                constraints: const BoxConstraints(),
                                tooltip: '파일 삭제',
                              ),
                            ],
                          ),
                        )),
                    // 신규 추가 파일 목록
                    ..._newFiles.asMap().entries.map((entry) {
                      final idx = entry.key;
                      final file = entry.value;
                      return Container(
                        margin: const EdgeInsets.only(bottom: 6),
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                        decoration: BoxDecoration(
                          color: AppColors.accentWork.withAlpha(15),
                          border: Border.all(color: AppColors.accentWork.withAlpha(80)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.upload_file_rounded, size: 18, color: AppColors.accentWork),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    file.name,
                                    style: AppTextStyles.bodySm.copyWith(fontWeight: FontWeight.w600),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  Text(
                                    _formatFileSize(file.size),
                                    style: AppTextStyles.caption.copyWith(color: AppColors.textMuted),
                                  ),
                                ],
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.close_rounded, size: 16, color: AppColors.textMuted),
                              onPressed: () {
                                setState(() {
                                  _newFiles.removeAt(idx);
                                });
                              },
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(),
                              tooltip: '취소',
                            ),
                          ],
                        ),
                      );
                    }),
                  ],
                ),
              const SizedBox(height: 16),

              // ── 6. 관련 웹 링크 섹션 ───────────────────────────────────────
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.link_rounded, size: 18, color: Color(0xFF1565C0)),
                      const SizedBox(width: 6),
                      Text('관련 링크 (${existingLinks.length + _newLinks.length})',
                          style: AppTextStyles.titleSm),
                    ],
                  ),
                  OutlinedButton.icon(
                    onPressed: _showAddLinkDialog,
                    icon: const Icon(Icons.add_rounded, size: 15),
                    label: const Text('링크 추가'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF1565C0),
                      side: const BorderSide(color: Color(0xFF1565C0)),
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              if (existingLinks.isEmpty && _newLinks.isEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  decoration: BoxDecoration(
                    color: AppColors.bgSurface,
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Center(
                    child: Text('등록된 웹 링크가 없습니다. (+ 링크 추가)',
                        style: AppTextStyles.caption.copyWith(color: AppColors.textMuted)),
                  ),
                )
              else
                Column(
                  children: [
                    // 기존 링크 목록
                    ...existingLinks.map((link) => Container(
                          margin: const EdgeInsets.only(bottom: 6),
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                          decoration: BoxDecoration(
                            color: AppColors.bgSurface,
                            border: Border.all(color: AppColors.border),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.language_rounded, size: 18, color: Color(0xFF1565C0)),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  link.link,
                                  style: AppTextStyles.bodySm.copyWith(color: const Color(0xFF1565C0)),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close_rounded, size: 16, color: AppColors.error),
                                onPressed: () {
                                  setState(() {
                                    _deleteLinkPks.add(link.pk);
                                  });
                                },
                                padding: EdgeInsets.zero,
                                constraints: const BoxConstraints(),
                                tooltip: '링크 삭제',
                              ),
                            ],
                          ),
                        )),
                    // 신규 추가 링크 목록
                    ..._newLinks.asMap().entries.map((entry) {
                      final idx = entry.key;
                      final link = entry.value;
                      return Container(
                        margin: const EdgeInsets.only(bottom: 6),
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1565C0).withAlpha(15),
                          border: Border.all(color: const Color(0xFF1565C0).withAlpha(80)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.add_link_rounded, size: 18, color: Color(0xFF1565C0)),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                link,
                                style: AppTextStyles.bodySm.copyWith(color: const Color(0xFF1565C0)),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.close_rounded, size: 16, color: AppColors.textMuted),
                              onPressed: () {
                                setState(() {
                                  _newLinks.removeAt(idx);
                                });
                              },
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(),
                              tooltip: '취소',
                            ),
                          ],
                        ),
                      );
                    }),
                  ],
                ),
              const SizedBox(height: 16),

              // ── 7. 비밀글 설정 카드 ───────────────────────────────────────
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.bgSurface,
                  border: Border.all(
                    color: _isSecret ? AppColors.warning.withAlpha(120) : AppColors.border,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      _isSecret ? Icons.lock_rounded : Icons.lock_open_rounded,
                      size: 20,
                      color: _isSecret ? AppColors.warning : AppColors.textMuted,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('비밀글 설정', style: AppTextStyles.titleSm),
                          Text('작성자 및 관리자만 조회 가능',
                              style: AppTextStyles.caption.copyWith(color: AppColors.textMuted)),
                        ],
                      ),
                    ),
                    Switch(
                      value: _isSecret,
                      onChanged: (v) => setState(() => _isSecret = v),
                      activeColor: AppColors.warning,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // ── 8. 저장 / 등록 액션 버튼 ──────────────────────────────────
              Row(
                children: [
                  Expanded(
                    flex: 1,
                    child: OutlinedButton(
                      onPressed: () => Navigator.pop(context),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.textSecond,
                        side: const BorderSide(color: AppColors.border),
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(vertical: 13),
                      ),
                      child: const Text('취소'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      onPressed: _isSubmitting ? null : _submit,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.accentWork,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 13),
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
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
                              isEdit ? '수정 사항 저장' : '문서 등록',
                              style: AppTextStyles.titleSm.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
