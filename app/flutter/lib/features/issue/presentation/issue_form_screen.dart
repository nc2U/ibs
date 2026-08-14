import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../data/issue_repository.dart';
import '../data/models/issue_model.dart';
import '../providers/issue_provider.dart';
import '../../project/providers/project_provider.dart';

/// 업무 생성 및 수정 폼 화면
class IssueFormScreen extends ConsumerStatefulWidget {
  final IssueModel? initialIssue;
  final int? initialMeetingId;
  final String? initialProjectSlug;

  const IssueFormScreen({
    super.key,
    this.initialIssue,
    this.initialMeetingId,
    this.initialProjectSlug,
  });

  @override
  ConsumerState<IssueFormScreen> createState() => _IssueFormScreenState();
}

class _IssueFormScreenState extends ConsumerState<IssueFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _subjectController;
  late TextEditingController _descriptionController;
  late TextEditingController _startDateController;
  late TextEditingController _dueDateController;

  int _trackerId = 4; // 기본: 기획일반
  int _statusId = 2; // 기본: 진행
  int _priorityId = 2; // 기본: 보통
  bool _isPrivate = false;
  bool _isSaving = false;

  String? _selectedProjectSlug;
  int? _meetingId;

  @override
  void initState() {
    super.initState();
    final issue = widget.initialIssue;
    _subjectController = TextEditingController(text: issue?.subject ?? '');
    _descriptionController =
        TextEditingController(text: issue?.description ?? '');
    _startDateController = TextEditingController(
        text: issue?.startDate ??
            DateTime.now().toIso8601String().substring(0, 10));
    _dueDateController = TextEditingController(text: issue?.dueDate ?? '');

    if (issue != null) {
      _trackerId = issue.tracker.pk;
      _statusId = issue.status.pk;
      _priorityId = issue.priority.pk;
      _isPrivate = issue.isPrivate;
      _meetingId = issue.meeting;
    } else {
      _meetingId = widget.initialMeetingId;
      _selectedProjectSlug = widget.initialProjectSlug;

      if (_selectedProjectSlug == null) {
        final selectedProj = ref.read(selectedProjectProvider);
        if (selectedProj != null) {
          _selectedProjectSlug = selectedProj.slug;
        }
      }
    }
  }

  @override
  void dispose() {
    _subjectController.dispose();
    _descriptionController.dispose();
    _startDateController.dispose();
    _dueDateController.dispose();
    super.dispose();
  }

  Future<void> _selectDate(TextEditingController controller) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (picked != null) {
      controller.text = picked.toIso8601String().substring(0, 10);
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    if (widget.initialIssue == null && (_selectedProjectSlug == null || _selectedProjectSlug!.isEmpty)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('프로젝트를 먼저 선택해 주세요.')),
      );
      return;
    }

    setState(() => _isSaving = true);

    final payload = <String, dynamic>{
      'subject': _subjectController.text.trim(),
      'description': _descriptionController.text.trim(),
      'tracker': _trackerId,
      'status': _statusId,
      'priority': _priorityId,
      'start_date': _startDateController.text.trim(),
      'is_private': _isPrivate,
    };
    if (_dueDateController.text.trim().isNotEmpty) {
      payload['due_date'] = _dueDateController.text.trim();
    }
    if (_meetingId != null) {
      payload['meeting'] = _meetingId;
    }
    if (widget.initialIssue == null && _selectedProjectSlug != null) {
      payload['project'] = _selectedProjectSlug;
    }

    try {
      if (widget.initialIssue != null) {
        await ref
            .read(issueRepositoryProvider)
            .updateIssue(widget.initialIssue!.pk, payload);
        ref.invalidate(issueDetailProvider(widget.initialIssue!.pk));
      } else {
        await ref.read(issueRepositoryProvider).createIssue(payload);
      }
      ref.invalidate(issueListProvider);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.initialIssue != null
                ? '업무가 수정되었습니다.'
                : '새 업무가 등록되었습니다.'),
            backgroundColor: AppColors.success,
          ),
        );
        context.pop();
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
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.initialIssue != null;
    final projectsAsync = ref.watch(projectListProvider);

    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      appBar: AppBar(
        backgroundColor: AppColors.bgPrimary,
        foregroundColor: AppColors.textPrimary,
        title: Text(isEdit ? '업무 수정' : '새 업무 등록', style: AppTextStyles.titleMd),
        actions: [
          TextButton(
            onPressed: _isSaving ? null : _submit,
            child: _isSaving
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: AppColors.accentWork),
                  )
                : Text('저장',
                    style: AppTextStyles.titleSm
                        .copyWith(color: AppColors.accentWork)),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 프로젝트 선택 ──────────────────────────────────────────────
              if (!isEdit) ...[
                Text('워크스페이스 (프로젝트) *', style: AppTextStyles.titleSm),
                const SizedBox(height: 6),
                projectsAsync.when(
                  loading: () => const SizedBox(
                    height: 48,
                    child: Center(
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: AppColors.accentWork)),
                  ),
                  error: (e, _) => Text('프로젝트 목록을 불러올 수 없습니다.',
                      style: AppTextStyles.bodyMuted),
                  data: (projects) => DropdownButtonFormField<String>(
                    value: _selectedProjectSlug ??
                        (projects.isNotEmpty ? projects.first.slug : null),
                    style: AppTextStyles.bodyMd,
                    dropdownColor: AppColors.bgCard,
                    decoration: _inputDecoration('프로젝트 선택'),
                    items: projects
                        .map((p) => DropdownMenuItem(
                              value: p.slug,
                              child:
                                  Text(p.name, overflow: TextOverflow.ellipsis),
                            ))
                        .toList(),
                    onChanged: (v) => setState(() => _selectedProjectSlug = v),
                    validator: (v) =>
                        (v == null || v.isEmpty) ? '프로젝트를 선택해 주세요.' : null,
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // ── 제목 ────────────────────────────────────────────────────────
              Text('제목 *', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _subjectController,
                style: AppTextStyles.bodyMd,
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? '제목을 입력해 주세요.' : null,
                decoration: _inputDecoration('업무 제목을 입력하세요'),
              ),
              const SizedBox(height: 16),

              // ── 유형 / 상태 / 우선순위 선택 ────────────────────────────────────
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('유형', style: AppTextStyles.titleSm),
                        const SizedBox(height: 6),
                        DropdownButtonFormField<int>(
                          value: _trackerId,
                          style: AppTextStyles.bodyMd,
                          dropdownColor: AppColors.bgCard,
                          decoration: _inputDecoration(''),
                          items: const [
                            DropdownMenuItem(value: 4, child: Text('기획일반')),
                            DropdownMenuItem(value: 1, child: Text('결함')),
                            DropdownMenuItem(value: 2, child: Text('기능')),
                            DropdownMenuItem(value: 3, child: Text('지원')),
                          ],
                          onChanged: (v) =>
                              setState(() => _trackerId = v ?? 4),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('상태', style: AppTextStyles.titleSm),
                        const SizedBox(height: 6),
                        DropdownButtonFormField<int>(
                          value: _statusId,
                          style: AppTextStyles.bodyMd,
                          dropdownColor: AppColors.bgCard,
                          decoration: _inputDecoration(''),
                          items: const [
                            DropdownMenuItem(value: 1, child: Text('신규')),
                            DropdownMenuItem(value: 2, child: Text('진행')),
                            DropdownMenuItem(value: 3, child: Text('해결')),
                            DropdownMenuItem(value: 4, child: Text('의견')),
                            DropdownMenuItem(value: 5, child: Text('완료')),
                          ],
                          onChanged: (v) => setState(() => _statusId = v ?? 2),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // ── 우선순위 & 비공개 ──────────────────────────────────────────────
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('우선순위', style: AppTextStyles.titleSm),
                        const SizedBox(height: 6),
                        DropdownButtonFormField<int>(
                          value: _priorityId,
                          style: AppTextStyles.bodyMd,
                          dropdownColor: AppColors.bgCard,
                          decoration: _inputDecoration(''),
                          items: const [
                            DropdownMenuItem(value: 1, child: Text('낮음')),
                            DropdownMenuItem(value: 2, child: Text('보통')),
                            DropdownMenuItem(value: 3, child: Text('높음')),
                            DropdownMenuItem(value: 4, child: Text('긴급')),
                            DropdownMenuItem(value: 5, child: Text('즉시')),
                          ],
                          onChanged: (v) =>
                              setState(() => _priorityId = v ?? 2),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('비공개 여부', style: AppTextStyles.titleSm),
                        const SizedBox(height: 6),
                        SwitchListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text('비공개', style: AppTextStyles.bodyMd),
                          value: _isPrivate,
                          activeColor: AppColors.accentWork,
                          onChanged: (v) => setState(() => _isPrivate = v),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // ── 시작일 & 완료기한 ─────────────────────────────────────────────
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('시작일', style: AppTextStyles.titleSm),
                        const SizedBox(height: 6),
                        TextField(
                          controller: _startDateController,
                          readOnly: true,
                          style: AppTextStyles.bodyMd,
                          decoration: _inputDecoration('YYYY-MM-DD').copyWith(
                            suffixIcon: IconButton(
                              icon: const Icon(Icons.calendar_today, size: 18),
                              onPressed: () => _selectDate(_startDateController),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('완료기한', style: AppTextStyles.titleSm),
                        const SizedBox(height: 6),
                        TextField(
                          controller: _dueDateController,
                          readOnly: true,
                          style: AppTextStyles.bodyMd,
                          decoration: _inputDecoration('YYYY-MM-DD').copyWith(
                            suffixIcon: IconButton(
                              icon: const Icon(Icons.calendar_today, size: 18),
                              onPressed: () => _selectDate(_dueDateController),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // ── 설명 ────────────────────────────────────────────────────────
              Text('설명', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _descriptionController,
                maxLines: 6,
                style: AppTextStyles.bodyMd,
                decoration: _inputDecoration('상세 설명 및 안내 사항을 입력하세요'),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String hint) {
    return InputDecoration(
      hintText: hint,
      hintStyle: AppTextStyles.bodyMuted,
      filled: true,
      fillColor: AppColors.bgCard,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: const BorderSide(color: AppColors.border, width: 0.8),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: const BorderSide(color: AppColors.border, width: 0.8),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: const BorderSide(color: AppColors.accentWork, width: 1.5),
      ),
    );
  }
}
