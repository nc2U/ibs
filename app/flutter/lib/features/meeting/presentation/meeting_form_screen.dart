import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../data/meeting_repository.dart';
import '../data/models/meeting_model.dart';
import '../providers/meeting_provider.dart';

import '../../project/providers/project_provider.dart';

/// 회의 생성 및 수정 폼 화면
class MeetingFormScreen extends ConsumerStatefulWidget {
  final MeetingModel? initialMeeting;

  const MeetingFormScreen({super.key, this.initialMeeting});

  @override
  ConsumerState<MeetingFormScreen> createState() => _MeetingFormScreenState();
}

class _MeetingFormScreenState extends ConsumerState<MeetingFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _titleController;
  late TextEditingController _meetingDateController;
  late TextEditingController _agendaController;
  late TextEditingController _contentController;
  late TextEditingController _decisionsController;
  late TextEditingController _actionItemsController;

  String _status = '1'; // 1: 예정, 2: 종료
  bool _isConfirmed = false;
  bool _isSaving = false;
  int? _selectedProjectPk;

  @override
  void initState() {
    super.initState();
    final m = widget.initialMeeting;
    _titleController = TextEditingController(text: m?.title ?? '');
    _meetingDateController = TextEditingController(
        text: m?.meetingDate ??
            DateTime.now().toIso8601String().substring(0, 10));
    _agendaController = TextEditingController(text: m?.agenda ?? '');
    _contentController = TextEditingController(text: m?.content ?? '');
    _decisionsController = TextEditingController(text: m?.decisions ?? '');
    _actionItemsController = TextEditingController(text: m?.actionItems ?? '');

    if (m != null) {
      _status = m.status;
      _isConfirmed = m.isConfirmed;
    } else {
      final selectedProj = ref.read(selectedProjectProvider);
      if (selectedProj != null) {
        _selectedProjectPk = selectedProj.pk;
      }
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _meetingDateController.dispose();
    _agendaController.dispose();
    _contentController.dispose();
    _decisionsController.dispose();
    _actionItemsController.dispose();
    super.dispose();
  }

  Future<void> _selectDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (picked != null) {
      _meetingDateController.text = picked.toIso8601String().substring(0, 10);
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    if (widget.initialMeeting == null && _selectedProjectPk == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('프로젝트를 먼저 선택해 주세요.')),
      );
      return;
    }

    setState(() => _isSaving = true);

    final payload = <String, dynamic>{
      'title': _titleController.text.trim(),
      'meeting_date': _meetingDateController.text.trim(),
      'status': _status,
      'is_confirmed': _isConfirmed,
      'agenda': _agendaController.text.trim(),
      'content': _contentController.text.trim(),
      'decisions': _decisionsController.text.trim(),
      'action_items': _actionItemsController.text.trim(),
    };
    if (widget.initialMeeting == null && _selectedProjectPk != null) {
      payload['project'] = _selectedProjectPk;
    }

    try {
      if (widget.initialMeeting != null) {
        await ref
            .read(meetingRepositoryProvider)
            .updateMeeting(widget.initialMeeting!.pk, payload);
        ref.invalidate(meetingDetailProvider(widget.initialMeeting!.pk));
      } else {
        await ref.read(meetingRepositoryProvider).createMeeting(payload);
      }
      ref.invalidate(meetingListProvider);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.initialMeeting != null
                ? '회의록이 수정되었습니다.'
                : '새 회의록이 등록되었습니다.'),
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
    final isEdit = widget.initialMeeting != null;
    final projectsAsync = ref.watch(projectListProvider);

    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      appBar: AppBar(
        backgroundColor: AppColors.bgPrimary,
        foregroundColor: AppColors.textPrimary,
        title:
            Text(isEdit ? '회의록 수정' : '새 회의록 작성', style: AppTextStyles.titleMd),
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
              // ── 프로젝트 선택 (신규 등록 시) ──────────────────────────────────
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
                  data: (projects) => DropdownButtonFormField<int>(
                    value: _selectedProjectPk ??
                        (projects.isNotEmpty ? projects.first.pk : null),
                    style: AppTextStyles.bodyMd,
                    dropdownColor: AppColors.bgCard,
                    decoration: _inputDecoration('프로젝트 선택'),
                    items: projects
                        .map((p) => DropdownMenuItem(
                              value: p.pk,
                              child:
                                  Text(p.name, overflow: TextOverflow.ellipsis),
                            ))
                        .toList(),
                    onChanged: (v) => setState(() => _selectedProjectPk = v),
                    validator: (v) => v == null ? '프로젝트를 선택해 주세요.' : null,
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // ── 회의 제목 ──────────────────────────────────────────────────
              Text('회의 제목 *', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _titleController,
                style: AppTextStyles.bodyMd,
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? '제목을 입력해 주세요.' : null,
                decoration: _inputDecoration('회의 제목을 입력하세요'),
              ),
              const SizedBox(height: 16),

              // ── 회의 일자 & 상태 ──────────────────────────────────────────────
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('회의 일자', style: AppTextStyles.titleSm),
                        const SizedBox(height: 6),
                        TextField(
                          controller: _meetingDateController,
                          readOnly: true,
                          style: AppTextStyles.bodyMd,
                          decoration: _inputDecoration('YYYY-MM-DD').copyWith(
                            suffixIcon: IconButton(
                              icon: const Icon(Icons.calendar_today, size: 18),
                              onPressed: _selectDate,
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
                        Text('상태', style: AppTextStyles.titleSm),
                        const SizedBox(height: 6),
                        DropdownButtonFormField<String>(
                          value: _status,
                          style: AppTextStyles.bodyMd,
                          dropdownColor: AppColors.bgCard,
                          decoration: _inputDecoration(''),
                          items: const [
                            DropdownMenuItem(value: '1', child: Text('예정/진행')),
                            DropdownMenuItem(value: '2', child: Text('종료')),
                          ],
                          onChanged: (v) => setState(() => _status = v ?? '1'),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // ── 의제 (Agenda) ──────────────────────────────────────────────
              Text('의제 (Agenda)', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _agendaController,
                maxLines: 3,
                style: AppTextStyles.bodyMd,
                decoration: _inputDecoration('회의 안건 및 의제를 입력하세요'),
              ),
              const SizedBox(height: 16),

              // ── 회의 내용 ──────────────────────────────────────────────────
              Text('회의 내용', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _contentController,
                maxLines: 5,
                style: AppTextStyles.bodyMd,
                decoration: _inputDecoration('논의된 회의 상세 내용을 입력하세요'),
              ),
              const SizedBox(height: 16),

              // ── 결정 사항 ──────────────────────────────────────────────────
              Text('결정 사항 (Decisions)', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _decisionsController,
                maxLines: 3,
                style: AppTextStyles.bodyMd,
                decoration: _inputDecoration('회의에서 결정된 최종 사항을 입력하세요'),
              ),
              const SizedBox(height: 16),

              // ── 후속 조치 (Action Items) ──────────────────────────────────
              Text('후속 조치 (Action Items)', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _actionItemsController,
                maxLines: 3,
                style: AppTextStyles.bodyMd,
                decoration: _inputDecoration('회의 후 진행할 액션 아이템을 입력하세요'),
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
