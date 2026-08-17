import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../data/models/forum_model.dart';
import '../../data/forum_repository.dart';
import '../../providers/forum_provider.dart';

/// 게시글 등록 및 수정 바텀시트 (radius = 0)
class PostFormSheet extends ConsumerStatefulWidget {
  final PostModel? post;
  final int? initialForumId;

  const PostFormSheet({
    super.key,
    this.post,
    this.initialForumId,
  });

  @override
  ConsumerState<PostFormSheet> createState() => _PostFormSheetState();
}

class _PostFormSheetState extends ConsumerState<PostFormSheet> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _titleController;
  late final TextEditingController _contentController;

  int? _selectedForumPk;
  int? _selectedCategoryPk;
  bool _isNotice = false;
  bool _isFaq = false;
  bool _isSubmitting = false;
  bool _isLoadingCategories = false;

  List<PostCategoryModel> _availableCategories = [];

  final List<PlatformFile> _newFiles = [];
  final List<int> _deleteFilePks = [];

  @override
  void initState() {
    super.initState();
    final p = widget.post;
    _titleController = TextEditingController(text: p?.title ?? '');
    _contentController = TextEditingController(text: p?.content ?? '');
    _isNotice = p?.isNotice ?? false;
    _isFaq = p?.isFaq ?? false;
    _selectedForumPk = p?.forum ?? widget.initialForumId;
    _selectedCategoryPk = p?.category;

    if (_selectedForumPk != null) {
      _loadCategories(_selectedForumPk!);
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    super.dispose();
  }

  Future<void> _loadCategories(int forumId) async {
    setState(() {
      _isLoadingCategories = true;
      _availableCategories = [];
    });
    try {
      final repo = ref.read(forumRepositoryProvider);
      final list = await repo.fetchCategories(forumId);

      final forums = ref.read(forumListProvider).valueOrNull ?? [];
      final currentForum =
          forums.where((f) => f.pk == forumId).firstOrNull;
      final currentUser = ref.read(currentUserProvider).valueOrNull;
      final isManager = (currentUser?.isSuperuser ?? false) ||
          (currentForum?.manager.contains(currentUser?.pk ?? -1) ?? false);

      final filteredList =
          list.where((c) => !c.isManagerOnly || isManager).toList();

      if (mounted) {
        setState(() {
          _availableCategories = filteredList;
          // 기존에 선택된 카테고리가 새 게시판의 카테고리 목록에 없으면 리셋
          if (_selectedCategoryPk != null &&
              !filteredList.any((c) => c.pk == _selectedCategoryPk)) {
            _selectedCategoryPk = null;
          }
        });
      }
    } catch (_) {
    } finally {
      if (mounted) {
        setState(() => _isLoadingCategories = false);
      }
    }
  }

  Color _parseCategoryColor(String? colorStr) {
    if (colorStr == null || colorStr.isEmpty) return AppColors.accentWork;
    try {
      final hex = colorStr.replaceAll('#', '');
      if (hex.length == 6) {
        return Color(int.parse('FF$hex', radix: 16));
      }
    } catch (_) {}
    return AppColors.accentWork;
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

    final isEdit = widget.post != null;
    final canAction = isEdit
        ? ref.can(Perm.forumUpdate) || ref.can(Perm.forumOwnUpdate) || ref.can(Perm.forumManage)
        : ref.can(Perm.forumCreate) || ref.can(Perm.forumManage);

    if (!canAction) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('게시글 작성/수정 권한이 없습니다.'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    if (_selectedForumPk == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('게시판을 선택해 주세요.'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final repo = ref.read(forumRepositoryProvider);

      if (isEdit) {
        await repo.updatePost(
          id: widget.post!.pk,
          forumId: _selectedForumPk,
          categoryId: _selectedCategoryPk,
          title: _titleController.text.trim(),
          content: _contentController.text.trim(),
          isNotice: _isNotice,
          isFaq: _isFaq,
          newFiles: _newFiles,
          deleteFilePks: _deleteFilePks,
        );
        ref.invalidate(postDetailProvider(widget.post!.pk));
      } else {
        await repo.createPost(
          forumId: _selectedForumPk!,
          categoryId: _selectedCategoryPk,
          title: _titleController.text.trim(),
          content: _contentController.text.trim(),
          isNotice: _isNotice,
          isFaq: _isFaq,
          newFiles: _newFiles,
        );
      }

      ref.read(postListProvider.notifier).refresh();

      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              isEdit ? '게시글이 수정되었습니다.' : '게시글이 등록되었습니다.',
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('저장 실패: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.post != null;
    final forumsAsync = ref.watch(forumListProvider);
    final canManageForum = ref.can(Perm.forumManage);

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
          // ── 상단 타이틀 바 ──────────────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.border, width: 0.8)),
            ),
            child: Row(
              children: [
                Icon(
                  isEdit ? Icons.edit_note_rounded : Icons.post_add_rounded,
                  size: 20,
                  color: AppColors.accentWork,
                ),
                const SizedBox(width: 8),
                Text(
                  isEdit ? '게시글 수정' : '새 게시글 작성',
                  style: AppTextStyles.titleMd,
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.close_rounded, size: 20),
                  color: AppColors.textPrimary,
                  onPressed: () => Navigator.pop(context),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
          ),

          // ── 폼 본문 ────────────────────────────────────────────────
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 1. 게시판 선택
                    Text('게시판 *', style: AppTextStyles.label),
                    const SizedBox(height: 6),
                    forumsAsync.when(
                      data: (forums) {
                        final currentUser =
                            ref.watch(currentUserProvider).valueOrNull;
                        final isSuper = currentUser?.isSuperuser ?? false;
                        final userPk = currentUser?.pk ?? -1;

                        final availableForums = forums.where((f) {
                          if (!f.managerOnly) return true;
                          return isSuper || f.manager.contains(userPk);
                        }).toList();

                        if (availableForums.isEmpty) {
                          return const Text(
                            '작성 가능한 게시판이 없습니다.',
                            style: TextStyle(color: AppColors.textMuted),
                          );
                        }
                        return DropdownButtonFormField<int>(
                          value: availableForums
                                  .any((f) => f.pk == _selectedForumPk)
                              ? _selectedForumPk
                              : null,
                          decoration: InputDecoration(
                            filled: true,
                            fillColor: AppColors.bgSurface,
                            isDense: true,
                            contentPadding: const EdgeInsets.symmetric(
                                horizontal: 12, vertical: 10),
                            border: const OutlineInputBorder(
                              borderRadius: BorderRadius.zero,
                              borderSide: BorderSide(color: AppColors.border),
                            ),
                          ),
                          hint: const Text('게시판을 선택해 주세요'),
                          items: availableForums.map((f) {
                            return DropdownMenuItem<int>(
                              value: f.pk,
                              child: Text(f.name, style: AppTextStyles.bodySm),
                            );
                          }).toList(),
                          onChanged: (val) {
                            setState(() {
                              _selectedForumPk = val;
                              _selectedCategoryPk = null;
                            });
                            if (val != null) {
                              _loadCategories(val);
                            }
                          },
                          validator: (val) =>
                              val == null ? '게시판을 선택해 주세요.' : null,
                        );
                      },
                      loading: () => const LinearProgressIndicator(),
                      error: (e, _) => Text('게시판 로드 실패: $e'),
                    ),
                    const SizedBox(height: 16),

                    // 2. 카테고리 선택 (Forum의 PostCategory 목록)
                    if (_isLoadingCategories) ...[
                      Text('카테고리', style: AppTextStyles.label),
                      const SizedBox(height: 6),
                      const SizedBox(
                        height: 36,
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ] else if (_availableCategories.isNotEmpty) ...[
                      Text('카테고리', style: AppTextStyles.label),
                      const SizedBox(height: 6),
                      DropdownButtonFormField<int?>(
                        value: _selectedCategoryPk,
                        decoration: const InputDecoration(
                          filled: true,
                          fillColor: AppColors.bgSurface,
                          isDense: true,
                          contentPadding: EdgeInsets.symmetric(
                              horizontal: 12, vertical: 10),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.zero,
                            borderSide: BorderSide(color: AppColors.border),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.zero,
                            borderSide: BorderSide(color: AppColors.border),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.zero,
                            borderSide: BorderSide(color: AppColors.accentWork),
                          ),
                        ),
                        hint: const Text('카테고리 선택 (선택 사항)'),
                        items: [
                          const DropdownMenuItem<int?>(
                            value: null,
                            child: Text('카테고리 없음 (전체)',
                                style: TextStyle(color: AppColors.textMuted)),
                          ),
                          ..._availableCategories.map((c) {
                            return DropdownMenuItem<int?>(
                              value: c.pk,
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  if (c.color != null && c.color!.isNotEmpty) ...[
                                    Container(
                                      width: 8,
                                      height: 8,
                                      margin: const EdgeInsets.only(right: 6),
                                      decoration: BoxDecoration(
                                        color: _parseCategoryColor(c.color),
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                  ],
                                  Text(c.name, style: AppTextStyles.bodySm),
                                ],
                              ),
                            );
                          }),
                        ],
                        onChanged: (val) =>
                            setState(() => _selectedCategoryPk = val),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // 3. 제목
                    Text('제목 *', style: AppTextStyles.label),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _titleController,
                      style: AppTextStyles.bodySm,
                      decoration: InputDecoration(
                        hintText: '게시글 제목을 입력하세요',
                        filled: true,
                        fillColor: AppColors.bgSurface,
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 10),
                        border: const OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: AppColors.border),
                        ),
                      ),
                      validator: (val) {
                        if (val == null || val.trim().isEmpty) {
                          return '제목을 입력해 주세요.';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // 4. 공지 및 FAQ 여부 스위치 (게시판 관리자 전용)
                    if (canManageForum) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: AppColors.bgSurface,
                          borderRadius: BorderRadius.zero,
                          border: Border.all(color: AppColors.border, width: 0.8),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.campaign_outlined,
                                size: 18, color: AppColors.error),
                            const SizedBox(width: 8),
                            Text('게시판 상단 공지로 등록',
                                style: AppTextStyles.bodySm.copyWith(
                                    fontWeight: FontWeight.w600)),
                            const Spacer(),
                            Switch(
                              value: _isNotice,
                              activeThumbColor: AppColors.error,
                              onChanged: (v) => setState(() => _isNotice = v),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: AppColors.bgSurface,
                          borderRadius: BorderRadius.zero,
                          border: Border.all(color: AppColors.border, width: 0.8),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.help_outline_rounded,
                                size: 18, color: AppColors.accentApproval),
                            const SizedBox(width: 8),
                            Text('FAQ (자주 묻는 질문)으로 등록',
                                style: AppTextStyles.bodySm.copyWith(
                                    fontWeight: FontWeight.w600)),
                            const Spacer(),
                            Switch(
                              value: _isFaq,
                              activeThumbColor: AppColors.accentApproval,
                              onChanged: (v) => setState(() => _isFaq = v),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // 5. 본문
                    Text('본문 내용', style: AppTextStyles.label),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _contentController,
                      maxLines: 8,
                      style: AppTextStyles.bodySm,
                      decoration: InputDecoration(
                        hintText: '게시글 내용을 작성해 주세요...',
                        filled: true,
                        fillColor: AppColors.bgSurface,
                        isDense: true,
                        contentPadding: const EdgeInsets.all(12),
                        border: const OutlineInputBorder(
                          borderRadius: BorderRadius.zero,
                          borderSide: BorderSide(color: AppColors.border),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // 6. 파일 첨부
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('첨부파일', style: AppTextStyles.label),
                        TextButton.icon(
                          onPressed: _pickFiles,
                          icon: const Icon(Icons.attach_file_rounded, size: 16),
                          label: const Text('파일 추가'),
                          style: TextButton.styleFrom(
                            foregroundColor: AppColors.accentWork,
                            padding: EdgeInsets.zero,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),

                    // 기존 파일 목록 (수정 시)
                    if (widget.post != null &&
                        widget.post!.files.isNotEmpty) ...[
                      ...widget.post!.files.map((file) {
                        final isDeleted = _deleteFilePks.contains(file.pk);
                        return Container(
                          margin: const EdgeInsets.only(bottom: 6),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 8),
                          decoration: BoxDecoration(
                            color: isDeleted
                                ? AppColors.error.withAlpha(15)
                                : AppColors.bgSurface,
                            borderRadius: BorderRadius.zero,
                            border: Border.all(
                              color: isDeleted
                                  ? AppColors.error
                                  : AppColors.border,
                              width: 0.8,
                            ),
                          ),
                          child: Row(
                            children: [
                              Icon(Icons.insert_drive_file_outlined,
                                  size: 16,
                                  color: isDeleted
                                      ? AppColors.error
                                      : AppColors.textMuted),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  file.fileName,
                                  style: AppTextStyles.bodySm.copyWith(
                                    decoration: isDeleted
                                        ? TextDecoration.lineThrough
                                        : null,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              IconButton(
                                icon: Icon(
                                  isDeleted
                                      ? Icons.undo_rounded
                                      : Icons.delete_outline_rounded,
                                  size: 16,
                                  color: isDeleted
                                      ? AppColors.accentWork
                                      : AppColors.error,
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

                    // 신규 첨부 파일 목록
                    if (_newFiles.isNotEmpty) ...[
                      ..._newFiles.asMap().entries.map((entry) {
                        final index = entry.key;
                        final file = entry.value;
                        return Container(
                          margin: const EdgeInsets.only(bottom: 6),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 8),
                          decoration: BoxDecoration(
                            color: AppColors.accentWork.withAlpha(15),
                            borderRadius: BorderRadius.zero,
                            border: Border.all(
                              color: AppColors.accentWork.withAlpha(50),
                              width: 0.8,
                            ),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.add_circle_outline_rounded,
                                  size: 16, color: AppColors.accentWork),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  file.name,
                                  style: AppTextStyles.bodySm,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close_rounded,
                                    size: 16, color: AppColors.error),
                                onPressed: () {
                                  setState(() => _newFiles.removeAt(index));
                                },
                              ),
                            ],
                          ),
                        );
                      }),
                    ],
                    const SizedBox(height: 24),

                    // ── 7. 저장 버튼 ───────────────────────────────────────
                    SizedBox(
                      width: double.infinity,
                      height: 46,
                      child: FilledButton(
                        onPressed: _isSubmitting ? null : _submit,
                        style: FilledButton.styleFrom(
                          backgroundColor: AppColors.accentWork,
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
                                isEdit ? '수정 완료' : '게시글 등록',
                                style: AppTextStyles.titleSm.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
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
