import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/models/common_models.dart';
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
  late TextEditingController _otherAttendeesController;
  late TextEditingController _agendaController;
  late TextEditingController _contentController;
  late TextEditingController _decisionsController;
  late TextEditingController _actionItemsController;

  String _status = '1'; // 1: 예정, 2: 종료
  bool _isConfirmed = false;
  bool _isSaving = false;
  int? _selectedProjectPk;
  int? _selectedCategoryPk;
  List<int> _selectedAttendeePks = [];

  @override
  void initState() {
    super.initState();
    final m = widget.initialMeeting;
    _titleController = TextEditingController(text: m?.title ?? '');

    String initialDateStr = '';
    if (m?.meetingDate != null && m!.meetingDate.isNotEmpty) {
      final clean = m.meetingDate.replaceAll('T', ' ');
      initialDateStr = clean.length >= 16 ? clean.substring(0, 16) : clean;
    } else {
      final now = DateTime.now();
      final y = now.year.toString().padLeft(4, '0');
      final mo = now.month.toString().padLeft(2, '0');
      final d = now.day.toString().padLeft(2, '0');
      final h = now.hour.toString().padLeft(2, '0');
      final mi = now.minute.toString().padLeft(2, '0');
      initialDateStr = '$y-$mo-$d $h:$mi';
    }
    _meetingDateController = TextEditingController(text: initialDateStr);

    _otherAttendeesController =
        TextEditingController(text: m?.otherAttendees ?? '');
    _agendaController = TextEditingController(text: m?.agenda ?? '');
    _contentController = TextEditingController(text: m?.content ?? '');
    _decisionsController = TextEditingController(text: m?.decisions ?? '');
    _actionItemsController = TextEditingController(text: m?.actionItems ?? '');

    if (m != null) {
      _status = m.status;
      _isConfirmed = m.isConfirmed;
      _selectedCategoryPk = m.category;
      _selectedAttendeePks = List.from(m.attendees);
      _selectedProjectPk = m.project;
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
    _otherAttendeesController.dispose();
    _agendaController.dispose();
    _contentController.dispose();
    _decisionsController.dispose();
    _actionItemsController.dispose();
    super.dispose();
  }

  Future<void> _selectDateTime() async {
    DateTime initialDateTime = DateTime.now();
    try {
      final text = _meetingDateController.text.trim();
      if (text.isNotEmpty) {
        final parsed = DateTime.tryParse(text.replaceAll(' ', 'T'));
        if (parsed != null) initialDateTime = parsed;
      }
    } catch (_) {}

    final pickedDate = await showDatePicker(
      context: context,
      initialDate: initialDateTime,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (pickedDate == null || !mounted) return;

    final pickedTime = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(initialDateTime),
    );
    if (pickedTime == null || !mounted) return;

    final y = pickedDate.year.toString().padLeft(4, '0');
    final mo = pickedDate.month.toString().padLeft(2, '0');
    final d = pickedDate.day.toString().padLeft(2, '0');
    final h = pickedTime.hour.toString().padLeft(2, '0');
    final mi = pickedTime.minute.toString().padLeft(2, '0');

    _meetingDateController.text = '$y-$mo-$d $h:$mi';
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
      'category': _selectedCategoryPk,
      'attendees': _selectedAttendeePks,
      'other_attendees': _otherAttendeesController.text.trim(),
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
    final projectsAsync = ref.watch(meetingFormProjectsProvider);

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
              // ── 섹션 1: 회의 개요 ─────────────────────────────────────────
              _buildSectionHeader('회의 개요', Icons.info_outline_rounded),

              // 프로젝트 선택 (신규 등록 시)
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
                  data: (projects) {
                    final validProjectPk = (_selectedProjectPk != null &&
                            projects.any((p) => p.pk == _selectedProjectPk))
                        ? _selectedProjectPk
                        : (projects.isNotEmpty ? projects.first.pk : null);

                    return DropdownButtonFormField<int>(
                      value: validProjectPk,
                      isExpanded: true,
                      style: AppTextStyles.bodyMd,
                      dropdownColor: AppColors.bgCard,
                      decoration: _inputDecoration('프로젝트 선택'),
                      items: projects
                          .map((p) => DropdownMenuItem(
                                value: p.pk,
                                child: Text(p.indentedLabel,
                                    overflow: TextOverflow.ellipsis),
                              ))
                          .toList(),
                      onChanged: (v) {
                        setState(() {
                          _selectedProjectPk = v;
                          _selectedCategoryPk = null;
                          _selectedAttendeePks = [];
                        });
                      },
                      validator: (v) => v == null ? '프로젝트를 선택해 주세요.' : null,
                    );
                  },
                ),
                const SizedBox(height: 14),
              ],

              // 회의 제목
              Text('회의 제목 *', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _titleController,
                style: AppTextStyles.bodyMd,
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? '제목을 입력해 주세요.' : null,
                decoration: _inputDecoration('회의 제목을 입력하세요'),
              ),
              const SizedBox(height: 14),

              // Row: 회의 일시 (50%) & 진행 상태 (50%)
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('회의 일시', style: AppTextStyles.titleSm),
                        const SizedBox(height: 6),
                        TextField(
                          controller: _meetingDateController,
                          readOnly: true,
                          style: AppTextStyles.bodyMd,
                          decoration:
                              _inputDecoration('YYYY-MM-DD HH:mm').copyWith(
                            suffixIcon: IconButton(
                              icon: const Icon(Icons.access_time_rounded,
                                  size: 18),
                              onPressed: _selectDateTime,
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
                        Text('진행 상태', style: AppTextStyles.titleSm),
                        const SizedBox(height: 6),
                        DropdownButtonFormField<String>(
                          value: _status,
                          isExpanded: true,
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
              const SizedBox(height: 14),

              // 카테고리 (100% 전체 폭)
              Text('카테고리', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              ref.watch(meetingCategoriesProvider(_selectedProjectPk)).when(
                    data: (categories) {
                      final validCategoryPk = (_selectedCategoryPk != null &&
                              categories.any((c) => c.pk == _selectedCategoryPk))
                          ? _selectedCategoryPk
                          : null;

                      return DropdownButtonFormField<int?>(
                        value: validCategoryPk,
                        isExpanded: true,
                        style: AppTextStyles.bodyMd,
                        dropdownColor: AppColors.bgCard,
                        decoration: _inputDecoration('카테고리 선택'),
                        items: [
                          const DropdownMenuItem<int?>(
                            value: null,
                            child: Text('선택 안 함'),
                          ),
                          ...categories.map((c) => DropdownMenuItem<int?>(
                                value: c.pk,
                                child: Text(c.name,
                                    overflow: TextOverflow.ellipsis),
                              )),
                        ],
                        onChanged: (v) =>
                            setState(() => _selectedCategoryPk = v),
                      );
                    },
                    loading: () => DropdownButtonFormField<int?>(
                      items: const [],
                      onChanged: null,
                      decoration: _inputDecoration('로딩 중...'),
                    ),
                    error: (_, __) => DropdownButtonFormField<int?>(
                      items: const [],
                      onChanged: null,
                      decoration: _inputDecoration('선택 안 함'),
                    ),
                  ),
              const SizedBox(height: 24),

              // ── 섹션 2: 참석자 ───────────────────────────────────────────
              _buildSectionHeader('참석자', Icons.people_outline_rounded),

              // 사내 멤버 참석자
              ref.watch(meetingMembersProvider(_selectedProjectPk)).when(
                    data: (members) {
                      final selectedUsers = members
                          .where((u) => _selectedAttendeePks.contains(u.pk))
                          .toList();

                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text('참석자 (사내 멤버)', style: AppTextStyles.titleSm),
                              if (_selectedAttendeePks.isNotEmpty) ...[
                                const SizedBox(width: 6),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 6, vertical: 1),
                                  decoration: BoxDecoration(
                                    color: AppColors.accentWork.withAlpha(40),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Text('${_selectedAttendeePks.length}',
                                      style: AppTextStyles.label.copyWith(
                                          color: AppColors.accentWork)),
                                ),
                              ],
                            ],
                          ),
                          const SizedBox(height: 6),
                          InkWell(
                            onTap: () => _openAttendeePicker(members),
                            borderRadius: BorderRadius.circular(6),
                            child: Container(
                              width: double.infinity,
                              constraints: const BoxConstraints(minHeight: 48),
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 10),
                              decoration: BoxDecoration(
                                color: AppColors.bgCard,
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(
                                    color: AppColors.border, width: 0.8),
                              ),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: selectedUsers.isEmpty
                                        ? Text('참석자를 선택하세요 (검색 가능)',
                                            style: AppTextStyles.bodyMuted)
                                        : Wrap(
                                            spacing: 6,
                                            runSpacing: 4,
                                            children: selectedUsers
                                                .map(
                                                  (u) => Container(
                                                    padding:
                                                        const EdgeInsets.symmetric(
                                                            horizontal: 8,
                                                            vertical: 3),
                                                    decoration: BoxDecoration(
                                                      color: AppColors
                                                          .accentWork
                                                          .withAlpha(30),
                                                      border: Border.all(
                                                        color: AppColors
                                                            .accentWork
                                                            .withAlpha(100),
                                                        width: 0.8,
                                                      ),
                                                      borderRadius:
                                                          BorderRadius.circular(
                                                              4),
                                                    ),
                                                    child: Text(
                                                      u.username,
                                                      style: AppTextStyles.label
                                                          .copyWith(
                                                        color:
                                                            AppColors.accentWork,
                                                      ),
                                                    ),
                                                  ),
                                                )
                                                .toList(),
                                          ),
                                  ),
                                  const SizedBox(width: 8),
                                  const Icon(Icons.people_alt_outlined,
                                      size: 20, color: AppColors.textMuted),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 14),
                        ],
                      );
                    },
                    loading: () => const SizedBox.shrink(),
                    error: (_, __) => const SizedBox.shrink(),
                  ),

              // 기타 참석자 (외부인)
              Text('기타 참석자 (외부인/기관)', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _otherAttendeesController,
                style: AppTextStyles.bodyMd,
                decoration: _inputDecoration(
                    '예: 시공사 김소장, 감리단 박팀장 (쉼표 구분)'),
              ),
              const SizedBox(height: 24),

              // ── 섹션 3: 회의 기록 ─────────────────────────────────────────
              _buildSectionHeader('회의 기록', Icons.edit_note_rounded),

              // 회의 의제
              Text('회의 의제 (Agenda)', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _agendaController,
                maxLines: 3,
                style: AppTextStyles.bodyMd,
                decoration: _inputDecoration('회의 안건 및 의제를 입력하세요'),
              ),
              const SizedBox(height: 14),

              // 회의 내용
              Text('회의 내용 (Content)', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _contentController,
                maxLines: 5,
                style: AppTextStyles.bodyMd,
                decoration: _inputDecoration('논의된 회의 상세 내용을 입력하세요'),
              ),
              const SizedBox(height: 14),

              // 주요 결정 사항
              Text('주요 결정 사항 (Decisions)', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _decisionsController,
                maxLines: 3,
                style: AppTextStyles.bodyMd,
                decoration: _inputDecoration('회의에서 결정된 최종 사항을 입력하세요'),
              ),
              const SizedBox(height: 14),

              // 후속 조치 사항
              Text('후속 조치 사항 (Action Items)', style: AppTextStyles.titleSm),
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

  Widget _buildSectionHeader(String title, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(top: 6, bottom: 14),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.accentWork),
          const SizedBox(width: 8),
          Text(
            title,
            style: AppTextStyles.titleSm.copyWith(
              fontWeight: FontWeight.bold,
              color: AppColors.accentWork,
            ),
          ),
          const SizedBox(width: 10),
          const Expanded(
            child: Divider(height: 1, color: AppColors.border),
          ),
        ],
      ),
    );
  }

  Future<void> _openAttendeePicker(List<SimpleUserModel> allMembers) async {
    final tempSelected = List<int>.from(_selectedAttendeePks);
    String searchQuery = '';

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final filteredMembers = allMembers.where((u) {
              if (searchQuery.trim().isEmpty) return true;
              final query = searchQuery.toLowerCase();
              final username = u.username.toLowerCase();
              final email = (u.email ?? '').toLowerCase();
              return username.contains(query) || email.contains(query);
            }).toList();

            return DraggableScrollableSheet(
              expand: false,
              initialChildSize: 0.7,
              minChildSize: 0.4,
              maxChildSize: 0.9,
              builder: (context, scrollController) {
                return Column(
                  children: [
                    // 드래그 핸들바
                    Center(
                      child: Container(
                        margin: const EdgeInsets.symmetric(vertical: 8),
                        width: 36,
                        height: 4,
                        decoration: BoxDecoration(
                          color: AppColors.textDisabled.withAlpha(80),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    // 상단 헤더
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                      child: Row(
                        children: [
                          Text('참석자 선택', style: AppTextStyles.titleMd),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                            decoration: BoxDecoration(
                              color: AppColors.accentWork.withAlpha(40),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text('${tempSelected.length}명',
                                style: AppTextStyles.label.copyWith(color: AppColors.accentWork)),
                          ),
                          const Spacer(),
                          if (tempSelected.isNotEmpty)
                            TextButton(
                              onPressed: () {
                                setModalState(() => tempSelected.clear());
                              },
                              child: Text('전체 해제', style: AppTextStyles.caption.copyWith(color: AppColors.accentApproval)),
                            ),
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.accentWork,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                            ),
                            onPressed: () => Navigator.pop(context),
                            child: const Text('완료', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                          ),
                        ],
                      ),
                    ),
                    // 검색창
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: TextField(
                        style: AppTextStyles.bodyMd,
                        decoration: InputDecoration(
                          hintText: '이름 또는 이메일 검색',
                          hintStyle: AppTextStyles.bodyMuted,
                          prefixIcon: const Icon(Icons.search, size: 20, color: AppColors.textMuted),
                          filled: true,
                          fillColor: AppColors.bgPrimary,
                          contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 12),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                            borderSide: const BorderSide(color: AppColors.border, width: 0.8),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                            borderSide: const BorderSide(color: AppColors.border, width: 0.8),
                          ),
                        ),
                        onChanged: (v) {
                          setModalState(() => searchQuery = v);
                        },
                      ),
                    ),
                    const Divider(height: 1, color: AppColors.border),
                    // 멤버 목록
                    Expanded(
                      child: filteredMembers.isEmpty
                          ? Center(
                              child: Text(
                                '검색 결과가 없습니다.',
                                style: AppTextStyles.bodyMuted,
                              ),
                            )
                          : ListView.separated(
                              controller: scrollController,
                              padding: const EdgeInsets.symmetric(vertical: 6),
                              itemCount: filteredMembers.length,
                              separatorBuilder: (_, __) => const Divider(
                                height: 1,
                                color: Color(0xFF2E334D),
                                indent: 56,
                              ),
                              itemBuilder: (context, idx) {
                                final user = filteredMembers[idx];
                                final isSelected = tempSelected.contains(user.pk);

                                return CheckboxListTile(
                                  value: isSelected,
                                  activeColor: AppColors.accentWork,
                                  checkColor: Colors.white,
                                  title: Text(user.username, style: AppTextStyles.bodyMd),
                                  subtitle: user.email != null && user.email!.isNotEmpty
                                      ? Text(user.email!, style: AppTextStyles.caption.copyWith(color: AppColors.textMuted))
                                      : null,
                                  secondary: CircleAvatar(
                                    radius: 16,
                                    backgroundColor: isSelected
                                        ? AppColors.accentWork.withAlpha(40)
                                        : AppColors.bgPrimary,
                                    child: Text(
                                      user.username.isNotEmpty ? user.username.substring(0, 1) : '?',
                                      style: TextStyle(
                                        color: isSelected ? AppColors.accentWork : AppColors.textMuted,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ),
                                  onChanged: (val) {
                                    setModalState(() {
                                      if (val == true) {
                                        tempSelected.add(user.pk);
                                      } else {
                                        tempSelected.remove(user.pk);
                                      }
                                    });
                                  },
                                );
                              },
                            ),
                    ),
                  ],
                );
              },
            );
          },
        );
      },
    );

    setState(() {
      _selectedAttendeePks = tempSelected;
    });
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
