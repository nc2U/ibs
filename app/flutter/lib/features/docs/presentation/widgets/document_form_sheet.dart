import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/docs_context_provider.dart';

import '../../data/docs_repository.dart';
import '../../data/models/docs_model.dart';
import '../../providers/docs_provider.dart';

/// 문서 생성 및 수정 폼 바텀시트 (radius = 0)
class DocumentFormSheet extends ConsumerStatefulWidget {
  final DocumentModel? doc; // null이면 생성, 값이 있으면 수정

  const DocumentFormSheet({super.key, this.doc});

  @override
  ConsumerState<DocumentFormSheet> createState() => _DocumentFormSheetState();
}

class _DocumentFormSheetState extends ConsumerState<DocumentFormSheet> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _titleController;
  late TextEditingController _descController;
  late TextEditingController _dateController;
  int? _selectedCategory;
  bool _isSecret = false;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(text: widget.doc?.title ?? '');
    _descController =
        TextEditingController(text: widget.doc?.description ?? '');
    _dateController =
        TextEditingController(text: widget.doc?.executionDate ?? '');
    _selectedCategory = widget.doc?.category;
    _isSecret = widget.doc?.isSecret ?? false;
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    _dateController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final repo = ref.read(docsRepositoryProvider);
    final ctx = ref.read(docsContextProvider);

    // 신규 작성 시 issueProject 필요
    final issueProjectId = ctx.project?.pk ?? widget.doc?.project?.pk;
    if (widget.doc == null && issueProjectId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('문서를 등록할 워크스페이스 또는 프로젝트를 먼저 선택해 주세요.')),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      if (widget.doc == null) {
        // 생성
        await repo.createDocument(
          issueProjectId: issueProjectId!,
          title: _titleController.text.trim(),
          categoryId: _selectedCategory,
          executionDate: _dateController.text.trim(),
          description: _descController.text.trim(),
          isSecret: _isSecret,
        );
      } else {
        // 수정
        await repo.updateDocument(
          id: widget.doc!.pk,
          title: _titleController.text.trim(),
          categoryId: _selectedCategory,
          executionDate: _dateController.text.trim(),
          description: _descController.text.trim(),
          isSecret: _isSecret,
        );
      }

      ref.read(docsListProvider.notifier).refresh();
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content:
                  Text(widget.doc == null ? '문서가 등록되었습니다.' : '문서가 수정되었습니다.')),
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
    final ctx = ref.watch(docsContextProvider);

    final targetName = widget.doc?.project?.name ??
        ctx.project?.name ??
        '전체 공용 범위';

    return Container(
      color: AppColors.bgCard,
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 헤더 ────────────────────────────────────────────────────────
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    widget.doc == null ? '신규 문서 등록' : '문서 수정',
                    style: AppTextStyles.titleLg,
                  ),
                  IconButton(
                    icon: const Icon(Icons.close_rounded),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 10),

              // ── 대상 정보 표시 ────────────────────────────────────────────────
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.bgSurface,
                  borderRadius: BorderRadius.zero,
                  border: Border.all(color: AppColors.border),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.folder_open_rounded,
                        size: 16, color: AppColors.accentWork),
                    const SizedBox(width: 8),
                    Text('등록 대상: ', style: AppTextStyles.caption),
                    Expanded(
                      child: Text(
                        targetName,
                        style: AppTextStyles.titleSm
                            .copyWith(color: AppColors.accentWork),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // ── 제목 입력 ──────────────────────────────────────────────────
              TextFormField(
                controller: _titleController,
                style: AppTextStyles.bodyLg,
                decoration: const InputDecoration(
                  labelText: '문서 제목 *',
                  hintText: '문서 제목을 입력하세요',
                ),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? '제목을 입력해 주세요.' : null,
              ),
              const SizedBox(height: 14),

              // ── 카테고리 드롭다운 ─────────────────────────────────────────────
              categoriesAsync.when(
                data: (categories) => DropdownButtonFormField<int>(
                  value: _selectedCategory,
                  decoration: const InputDecoration(labelText: '카테고리'),
                  items: categories
                      .map((c) => DropdownMenuItem<int>(
                            value: c.pk,
                            child: Text(c.name),
                          ))
                      .toList(),
                  onChanged: (v) => setState(() => _selectedCategory = v),
                ),
                loading: () => const LinearProgressIndicator(),
                error: (e, s) => Text('카테고리 로드 실패',
                    style: AppTextStyles.caption
                        .copyWith(color: AppColors.error)),
              ),
              const SizedBox(height: 14),

              // ── 시행일자 ────────────────────────────────────────────────────
              TextFormField(
                controller: _dateController,
                style: AppTextStyles.bodyMd,
                decoration: const InputDecoration(
                  labelText: '시행일자 (YYYY-MM-DD)',
                  hintText: '예: 2026-08-13',
                  prefixIcon: Icon(Icons.calendar_today_rounded, size: 18),
                ),
              ),
              const SizedBox(height: 14),

              // ── 설명 ──────────────────────────────────────────────────────
              TextFormField(
                controller: _descController,
                maxLines: 3,
                style: AppTextStyles.bodyMd,
                decoration: const InputDecoration(
                  labelText: '설명 / 메모',
                  hintText: '문서 관련 주요 설명이나 비고를 입력하세요',
                ),
              ),
              const SizedBox(height: 14),

              // ── 비밀글 설정 스위치 ───────────────────────────────────────────
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: Text('비밀글 설정', style: AppTextStyles.bodyMd),
                subtitle: Text('작성자 및 관리자만 조회 가능한 비밀 문선으로 등록',
                    style: AppTextStyles.caption),
                value: _isSecret,
                onChanged: (v) => setState(() => _isSecret = v),
                activeColor: AppColors.warning,
              ),
              const SizedBox(height: 20),

              // ── 저장 버튼 ──────────────────────────────────────────────────
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isSubmitting ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.accentWork,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: const RoundedRectangleBorder(
                        borderRadius: BorderRadius.zero),
                  ),
                  child: _isSubmitting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white),
                        )
                      : Text(widget.doc == null ? '문서 등록' : '수정 사항 저장',
                          style: AppTextStyles.titleLg
                              .copyWith(color: Colors.white)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
