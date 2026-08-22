import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../data/issue_repository.dart';
import '../data/models/issue_model.dart';
import '../providers/issue_provider.dart';
import '../../project/data/models/project_model.dart';
import '../../project/providers/project_provider.dart';

/// 예상 처리기간 선택 옵션 리스트 (웹과 100% 동일)
const _kDurationOptions = [
  {'value': '1', 'label': '당일 처리'},
  {'value': '2', 'label': '2일 이내'},
  {'value': '3', 'label': '3일 이내'},
  {'value': '5', 'label': '5일 이내'},
  {'value': '10', 'label': '10일 이내'},
  {'value': '30', 'label': '30일 이내'},
  {'value': '90', 'label': '3개월 이내'},
  {'value': '180', 'label': '6개월 이내'},
  {'value': '365', 'label': '1년 이내'},
  {'value': '366', 'label': '1년 이상'},
];

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

  int _trackerId = 4; // 기본값: 기획일반(4)
  int _statusId = 1; // 기본값: 준비/신규(1)
  int _priorityId = 2; // 기본값: 보통(2)
  int? _assignedToId;
  int? _parentIssueId;
  int? _fixedVersionId;
  int? _categoryId;
  String? _expectedDuration;
  bool _isPrivate = false;

  String? _selectedProjectSlug;
  int? _meetingId;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    final issue = widget.initialIssue;

    _subjectController = TextEditingController(text: issue?.subject ?? '');
    _descriptionController =
        TextEditingController(text: issue?.description ?? '');
    _startDateController =
        TextEditingController(text: issue?.startDate ?? _todayStr());
    _dueDateController = TextEditingController(text: issue?.dueDate ?? '');

    if (issue != null) {
      _trackerId = issue.tracker.pk;
      _statusId = issue.status.pk;
      _priorityId = issue.priority.pk;
      _assignedToId = issue.assignedTo?.pk;
      _parentIssueId = issue.parent?.pk;
      _fixedVersionId = issue.fixedVersion?.pk;
      _categoryId = issue.category;
      _expectedDuration = issue.expectedDuration;
      _isPrivate = issue.isPrivate;
      _meetingId = issue.meeting ?? widget.initialMeetingId;
      _selectedProjectSlug = issue.project.slug;
    } else {
      _meetingId = widget.initialMeetingId;
      if (widget.initialProjectSlug != null) {
        _selectedProjectSlug = widget.initialProjectSlug;
      } else {
        final currentProj = ref.read(selectedProjectProvider);
        if (currentProj != null) {
          _selectedProjectSlug = currentProj.slug;
        }
      }
    }
  }

  String _todayStr() {
    final now = DateTime.now();
    return "${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}";
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
    final now = DateTime.now();
    DateTime initial = now;
    if (controller.text.trim().isNotEmpty) {
      final parsed = DateTime.tryParse(controller.text.trim());
      if (parsed != null) initial = parsed;
    }

    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
    );

    if (picked != null) {
      final str =
          "${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}";
      setState(() => controller.text = str);
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    if (_selectedProjectSlug == null || _selectedProjectSlug!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('워크스페이스(프로젝트)를 선택해 주세요.'),
          backgroundColor: context.colors.error,
        ),
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
      'is_private': _isPrivate,
      'start_date': _startDateController.text.trim().isNotEmpty
          ? _startDateController.text.trim()
          : null,
    };

    if (_assignedToId != null) payload['assigned_to'] = _assignedToId;
    if (_parentIssueId != null) payload['parent'] = _parentIssueId;
    if (_fixedVersionId != null) payload['fixed_version'] = _fixedVersionId;
    if (_categoryId != null) payload['category'] = _categoryId;
    if (_expectedDuration != null && _expectedDuration!.isNotEmpty) {
      payload['expected_duration'] = _expectedDuration;
    }
    if (_dueDateController.text.trim().isNotEmpty) {
      payload['due_date'] = _dueDateController.text.trim();
    }
    if (_meetingId != null) payload['meeting'] = _meetingId;
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
            backgroundColor: context.colors.success,
          ),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('저장 실패: $e'),
            backgroundColor: context.colors.error,
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
    final projectsAsync = ref.watch(issueFormProjectsProvider);

    final projectSlug = _selectedProjectSlug ??
        (projectsAsync.valueOrNull?.isNotEmpty == true
            ? projectsAsync.valueOrNull!.first.slug
            : '');
    final projectDetailAsync = projectSlug.isNotEmpty
        ? ref.watch(projectDetailProvider(projectSlug))
        : null;

    final projectIssuesAsync = projectSlug.isNotEmpty
        ? ref.watch(issueListProvider)
        : null;

    final statusListAsync = ref.watch(issueStatusListProvider);
    final priorityListAsync = ref.watch(issuePriorityListProvider);
    final currentUser = ref.watch(currentUserProvider).valueOrNull;

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        backgroundColor: context.colors.bgPrimary,
        foregroundColor: context.colors.textPrimary,
        title: Text(isEdit ? '업무 수정' : '새 업무 등록', style: AppTextStyles.titleMd.copyWith(color: context.colors.textPrimary)),
        actions: [
          TextButton(
            onPressed: _isSaving ? null : _submit,
            child: _isSaving
                ? SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: context.colors.accentWork),
                  )
                : Text('저장',
                    style: AppTextStyles.titleSm
                        .copyWith(color: context.colors.accentWork)),
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
              if (!isEdit) ...[
                Text('워크스페이스 (프로젝트) *', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                const SizedBox(height: 6),
                projectsAsync.when(
                  loading: () => SizedBox(
                    height: 48,
                    child: Center(
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: context.colors.accentWork)),
                  ),
                  error: (e, _) => Text('프로젝트 목록을 불러올 수 없습니다.',
                      style: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted)),
                  data: (projects) => DropdownButtonFormField<String>(
                    value: _selectedProjectSlug ??
                        (projects.isNotEmpty ? projects.first.slug : null),
                    isExpanded: true,
                    style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                    dropdownColor: context.colors.bgCard,
                    decoration: _inputDecoration('프로젝트 선택'),
                    items: projects
                        .map((p) => DropdownMenuItem(
                              value: p.slug,
                              child: Text(p.indentedLabel,
                                  overflow: TextOverflow.ellipsis),
                            ))
                        .toList(),
                    onChanged: (v) {
                      setState(() {
                        _selectedProjectSlug = v;
                        _assignedToId = null;
                        _parentIssueId = null;
                        _fixedVersionId = null;
                        _categoryId = null;
                      });
                    },
                    validator: (v) =>
                        (v == null || v.isEmpty) ? '프로젝트를 선택해 주세요.' : null,
                  ),
                ),
                const SizedBox(height: 16),
              ],

              Text('제목 *', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _subjectController,
                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? '제목을 입력해 주세요.' : null,
                decoration: _inputDecoration('업무 제목을 입력하세요'),
              ),
              const SizedBox(height: 16),

              Text('설명', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _descriptionController,
                maxLines: 5,
                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                decoration:
                    _inputDecoration('상세 설명 및 안내 사항을 입력하세요 (마크다운 지원)'),
              ),
              const SizedBox(height: 20),

              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: context.colors.bgCard,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: context.colors.border, width: 0.8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('기본 설정', style: AppTextStyles.titleMd.copyWith(color: context.colors.textPrimary)),
                    const SizedBox(height: 12),

                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('유형', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                              const SizedBox(height: 6),
                              projectDetailAsync?.when(
                                    loading: () => const SizedBox(height: 48),
                                    error: (_, __) =>
                                        DropdownButtonFormField<int>(
                                      value: _trackerId,
                                      style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                      dropdownColor: context.colors.bgCard,
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
                                    data: (proj) {
                                      final trackers = proj.trackers;
                                      final uniqueTrackers = <int, ProjectTrackerModel>{};
                                      for (final t in trackers) uniqueTrackers[t.pk] = t;
                                      final trackerList = uniqueTrackers.values.toList();
                                      final hasTrackers = trackerList.isNotEmpty;

                                      final currentTrackerId = (hasTrackers &&
                                              !trackerList.any((t) => t.pk == _trackerId))
                                          ? trackerList.first.pk
                                          : _trackerId;

                                      return DropdownButtonFormField<int>(
                                        value: currentTrackerId,
                                        isExpanded: true,
                                        style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                        dropdownColor: context.colors.bgCard,
                                        decoration: _inputDecoration(''),
                                        items: hasTrackers
                                            ? trackerList
                                                .map((t) => DropdownMenuItem(
                                                      value: t.pk,
                                                      child: Text(t.name),
                                                    ))
                                                .toList()
                                            : const [
                                                DropdownMenuItem(value: 4, child: Text('기획일반')),
                                                DropdownMenuItem(value: 1, child: Text('결함')),
                                                DropdownMenuItem(value: 2, child: Text('기능')),
                                                DropdownMenuItem(value: 3, child: Text('지원')),
                                              ],
                                        onChanged: (v) =>
                                            setState(() => _trackerId = v ?? 4),
                                      );
                                    },
                                  ) ??
                                  DropdownButtonFormField<int>(
                                    value: _trackerId,
                                    isExpanded: true,
                                    style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                    dropdownColor: context.colors.bgCard,
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
                              Text('우선순위', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                              const SizedBox(height: 6),
                              priorityListAsync.when(
                                loading: () => const SizedBox(height: 48),
                                error: (_, __) => DropdownButtonFormField<int>(
                                  value: _priorityId,
                                  isExpanded: true,
                                  style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                  dropdownColor: context.colors.bgCard,
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
                                data: (priorities) {
                                  final uniquePriorities = <int, IssuePriorityModel>{};
                                  for (final p in priorities) uniquePriorities[p.pk] = p;
                                  final priorityList = uniquePriorities.values.toList();
                                  final hasPriorities = priorityList.isNotEmpty;

                                  final currentPriorityId = (hasPriorities &&
                                          !priorityList.any((p) => p.pk == _priorityId))
                                      ? priorityList.first.pk
                                      : _priorityId;

                                  return DropdownButtonFormField<int>(
                                    value: currentPriorityId,
                                    isExpanded: true,
                                    style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                    dropdownColor: context.colors.bgCard,
                                    decoration: _inputDecoration(''),
                                    items: hasPriorities
                                        ? priorityList
                                            .map((p) => DropdownMenuItem(
                                                  value: p.pk,
                                                  child: Text(p.name),
                                                ))
                                            .toList()
                                        : const [
                                            DropdownMenuItem(value: 1, child: Text('낮음')),
                                            DropdownMenuItem(value: 2, child: Text('보통')),
                                            DropdownMenuItem(value: 3, child: Text('높음')),
                                            DropdownMenuItem(value: 4, child: Text('긴급')),
                                            DropdownMenuItem(value: 5, child: Text('즉시')),
                                          ],
                                    onChanged: (v) =>
                                        setState(() => _priorityId = v ?? 2),
                                  );
                                },
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text('담당자', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                                  if (currentUser != null && _assignedToId != currentUser.pk)
                                    InkWell(
                                      borderRadius: BorderRadius.circular(4),
                                      onTap: () => setState(() => _assignedToId = currentUser.pk),
                                      child: Padding(
                                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                        child: Text(
                                          '« 나에게',
                                          style: AppTextStyles.caption.copyWith(
                                            color: context.colors.accentWork,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              projectDetailAsync?.when(
                                    loading: () => SizedBox(
                                      height: 48,
                                      child: Center(
                                          child: CircularProgressIndicator(
                                              strokeWidth: 2, color: context.colors.accentWork)),
                                    ),
                                    error: (_, __) =>
                                        DropdownButtonFormField<int?>(
                                      value: null,
                                      isExpanded: true,
                                      style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                      dropdownColor: context.colors.bgCard,
                                      decoration: _inputDecoration('미배정'),
                                      items: const [
                                        DropdownMenuItem(value: null, child: Text('미배정')),
                                      ],
                                      onChanged: (v) => setState(() => _assignedToId = v),
                                    ),
                                    data: (proj) {
                                      final uniqueMembers = <int, ProjectMemberModel>{};
                                      for (final m in proj.members) uniqueMembers[m.user.pk] = m;
                                      final memberList = uniqueMembers.values.toList();
                                      final currentAssignedId = (_assignedToId != null &&
                                              !memberList.any((m) => m.user.pk == _assignedToId))
                                          ? null
                                          : _assignedToId;

                                      return DropdownButtonFormField<int?>(
                                        value: currentAssignedId,
                                        isExpanded: true,
                                        style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                        dropdownColor: context.colors.bgCard,
                                        decoration: _inputDecoration('담당자 선택'),
                                        items: [
                                          const DropdownMenuItem(value: null, child: Text('미배정')),
                                          ...memberList.map((m) => DropdownMenuItem(
                                                value: m.user.pk,
                                                child: Text(m.user.username),
                                              )),
                                        ],
                                        onChanged: (v) => setState(() => _assignedToId = v),
                                      );
                                    },
                                  ) ??
                                  DropdownButtonFormField<int?>(
                                    value: null,
                                    isExpanded: true,
                                    style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                    dropdownColor: context.colors.bgCard,
                                    decoration: _inputDecoration('미배정'),
                                    items: const [
                                      DropdownMenuItem(value: null, child: Text('미배정')),
                                    ],
                                    onChanged: (v) => setState(() => _assignedToId = v),
                                  ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text('상태', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                                  if (_statusId == 1)
                                    InkWell(
                                      borderRadius: BorderRadius.circular(4),
                                      onTap: () => setState(() => _statusId = 2),
                                      child: Padding(
                                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                        child: Text(
                                          '진행 »',
                                          style: AppTextStyles.caption.copyWith(
                                            color: context.colors.accentWork,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ),
                                    )
                                  else if (_statusId == 2)
                                    InkWell(
                                      borderRadius: BorderRadius.circular(4),
                                      onTap: () => setState(() => _statusId = 5),
                                      child: Padding(
                                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                        child: Text(
                                          '완료 »',
                                          style: AppTextStyles.caption.copyWith(
                                            color: context.colors.success,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              statusListAsync.when(
                                loading: () => const SizedBox(height: 48),
                                error: (_, __) => DropdownButtonFormField<int>(
                                  value: _statusId,
                                  isExpanded: true,
                                  style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                  dropdownColor: context.colors.bgCard,
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
                                data: (statuses) {
                                  final filtered = isEdit ? statuses : statuses.where((s) => s.pk <= 2).toList();
                                  final uniqueStatuses = <int, IssueStatusModel>{};
                                  for (final s in filtered) uniqueStatuses[s.pk] = s;
                                  final availableStatuses = uniqueStatuses.values.toList();
                                  final hasStatuses = availableStatuses.isNotEmpty;
                                  final currentStatusId = (hasStatuses &&
                                          !availableStatuses.any((s) => s.pk == _statusId))
                                      ? availableStatuses.first.pk
                                      : _statusId;

                                  return DropdownButtonFormField<int>(
                                    value: currentStatusId,
                                    isExpanded: true,
                                    style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                    dropdownColor: context.colors.bgCard,
                                    decoration: _inputDecoration(''),
                                    items: hasStatuses
                                        ? availableStatuses
                                            .map((s) => DropdownMenuItem(
                                                  value: s.pk,
                                                  child: Text(s.name),
                                                ))
                                            .toList()
                                        : const [
                                            DropdownMenuItem(value: 1, child: Text('준비')),
                                            DropdownMenuItem(value: 2, child: Text('진행')),
                                          ],
                                    onChanged: (v) => setState(() => _statusId = v ?? 1),
                                  );
                                },
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('시작일 *', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                              const SizedBox(height: 6),
                              TextField(
                                controller: _startDateController,
                                readOnly: true,
                                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                decoration:
                                    _inputDecoration('YYYY-MM-DD').copyWith(
                                  suffixIcon: IconButton(
                                    icon: Icon(Icons.calendar_today,
                                        size: 18, color: context.colors.textMuted),
                                    onPressed: () =>
                                        _selectDate(_startDateController),
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
                              Text(
                                (_statusId == 1) ? '예상 처리기간' : '예상 처리기간 *',
                                style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary),
                              ),
                              const SizedBox(height: 6),
                              DropdownButtonFormField<String?>(
                                value: _expectedDuration,
                                isExpanded: true,
                                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                dropdownColor: context.colors.bgCard,
                                decoration: _inputDecoration(
                                  (_statusId == 1) ? '선택 안함' : '처리기간 선택',
                                ),
                                items: [
                                  const DropdownMenuItem(
                                      value: null,
                                      child: Text('선택 안함',
                                          overflow: TextOverflow.ellipsis)),
                                  ..._kDurationOptions
                                      .map((opt) => DropdownMenuItem(
                                            value: opt['value'],
                                            child: Text(opt['label']!,
                                                overflow: TextOverflow.ellipsis),
                                          )),
                                ],
                                validator: (v) {
                                  // 준비(초기 단계, pk=1)를 벗어났을 때만 필수 유효성 검사 수행
                                  if (_statusId != 1 && (v == null || v.isEmpty)) {
                                    return '예상 처리기간을 선택해 주세요.';
                                  }
                                  return null;
                                },
                                onChanged: (v) =>
                                    setState(() => _expectedDuration = v),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // ══════════════════════════════════════════════════════════════
              // 3. 추가 메타정보 (접이식 ExpansionTile: 완료기한, 상위업무, 목표단계, 범주, 비공개)
              // ══════════════════════════════════════════════════════════════
              Container(
                decoration: BoxDecoration(
                  color: context.colors.bgCard,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: context.colors.border, width: 0.8),
                ),
                child: Theme(
                  data: Theme.of(context)
                      .copyWith(dividerColor: Colors.transparent),
                  child: ExpansionTile(
                    initiallyExpanded: isEdit ||
                        _dueDateController.text.isNotEmpty ||
                        _parentIssueId != null ||
                        _fixedVersionId != null ||
                        _categoryId != null ||
                        _isPrivate,
                    tilePadding: const EdgeInsets.symmetric(horizontal: 14),
                    childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 16),
                    leading: Icon(Icons.tune_rounded,
                        size: 20, color: context.colors.accentWork),
                    title: Text('추가 상세 항목',
                        style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                    subtitle: Text(
                      _dueDateController.text.isNotEmpty ||
                              _parentIssueId != null ||
                              _fixedVersionId != null ||
                              _categoryId != null ||
                              _isPrivate
                          ? '설정된 항목이 있습니다.'
                          : '필요 시 펼쳐서 설정할 수 있습니다.',
                      style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                    ),
                    children: [
                      Divider(height: 16, color: context.colors.border),

                      // ── Row 1: 목표단계 (50%) & 범주 (50%) ───────────────
                      Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('목표단계 (버전)',
                                    style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                                const SizedBox(height: 6),
                                projectDetailAsync?.when(
                                      loading: () =>
                                          const SizedBox(height: 48),
                                      error: (_, __) =>
                                          DropdownButtonFormField<int?>(
                                        value: null,
                                        isExpanded: true,
                                        style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                        dropdownColor: context.colors.bgCard,
                                        decoration: _inputDecoration('없음'),
                                        items: const [
                                          DropdownMenuItem(
                                              value: null, child: Text('없음')),
                                        ],
                                        onChanged: (v) =>
                                            setState(() => _fixedVersionId = v),
                                      ),
                                      data: (proj) {
                                        final uniqueVersions =
                                            <int, ProjectVersionModel>{};
                                        for (final ver in proj.versions) {
                                          uniqueVersions[ver.pk] = ver;
                                        }
                                        final versionList =
                                            uniqueVersions.values.toList();

                                        var selectedVerId = _fixedVersionId;
                                        if (!isEdit &&
                                            selectedVerId == null &&
                                            versionList.isNotEmpty) {
                                          final defaultVer = versionList
                                              .where((v) => v.isDefault)
                                              .firstOrNull;
                                          if (defaultVer != null) {
                                            selectedVerId = defaultVer.pk;
                                            WidgetsBinding.instance
                                                .addPostFrameCallback((_) {
                                              if (mounted &&
                                                  _fixedVersionId == null) {
                                                setState(() =>
                                                    _fixedVersionId =
                                                        defaultVer.pk);
                                              }
                                            });
                                          }
                                        }

                                        if (selectedVerId != null &&
                                            !versionList.any(
                                                (v) => v.pk == selectedVerId)) {
                                          selectedVerId = null;
                                        }

                                        return DropdownButtonFormField<int?>(
                                          value: selectedVerId,
                                          isExpanded: true,
                                          style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                          dropdownColor: context.colors.bgCard,
                                          decoration:
                                              _inputDecoration('목표단계 선택'),
                                          items: [
                                            const DropdownMenuItem(
                                                value: null, child: Text('없음')),
                                            ...versionList
                                                .map((ver) => DropdownMenuItem(
                                                      value: ver.pk,
                                                      child: Text(
                                                          '${ver.name}${ver.isDefault ? ' (기본)' : ''}',
                                                          overflow:
                                                              TextOverflow
                                                                  .ellipsis),
                                                    )),
                                          ],
                                          onChanged: (v) => setState(
                                              () => _fixedVersionId = v),
                                        );
                                      },
                                    ) ??
                                    DropdownButtonFormField<int?>(
                                      value: null,
                                      isExpanded: true,
                                      style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                      dropdownColor: context.colors.bgCard,
                                      decoration: _inputDecoration('없음'),
                                      items: const [
                                        DropdownMenuItem(
                                            value: null, child: Text('없음')),
                                      ],
                                      onChanged: (v) =>
                                          setState(() => _fixedVersionId = v),
                                    ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('범주', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                                const SizedBox(height: 6),
                                projectDetailAsync?.when(
                                      loading: () =>
                                          const SizedBox(height: 48),
                                      error: (_, __) =>
                                          DropdownButtonFormField<int?>(
                                        value: null,
                                        isExpanded: true,
                                        style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                        dropdownColor: context.colors.bgCard,
                                        decoration: _inputDecoration('없음'),
                                        items: const [
                                          DropdownMenuItem(
                                              value: null, child: Text('없음')),
                                        ],
                                        onChanged: (v) =>
                                            setState(() => _categoryId = v),
                                      ),
                                      data: (proj) {
                                        final uniqueCategories =
                                            <int, ProjectCategoryModel>{};
                                        for (final cate in proj.categories) {
                                          uniqueCategories[cate.pk] = cate;
                                        }
                                        final categoryList =
                                            uniqueCategories.values.toList();

                                        final currentCategoryId =
                                            (_categoryId != null &&
                                                    !categoryList.any((c) =>
                                                        c.pk == _categoryId))
                                                ? null
                                                : _categoryId;

                                        return DropdownButtonFormField<int?>(
                                          value: currentCategoryId,
                                          isExpanded: true,
                                          style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                          dropdownColor: context.colors.bgCard,
                                          decoration: _inputDecoration('범주 선택'),
                                          items: [
                                            const DropdownMenuItem(
                                                value: null, child: Text('없음')),
                                            ...categoryList.map((cate) =>
                                                DropdownMenuItem(
                                                  value: cate.pk,
                                                  child: Text(cate.name,
                                                      overflow:
                                                          TextOverflow
                                                              .ellipsis),
                                                )),
                                          ],
                                          onChanged: (v) {
                                            setState(() {
                                              _categoryId = v;
                                              if (v != null) {
                                                final selectedCate =
                                                    categoryList
                                                        .where((c) => c.pk == v)
                                                        .firstOrNull;
                                                if (selectedCate?.assignedTo !=
                                                        null &&
                                                    _assignedToId == null) {
                                                  _assignedToId = selectedCate!
                                                      .assignedTo!.pk;
                                                }
                                              }
                                            });
                                          },
                                        );
                                      },
                                    ) ??
                                    DropdownButtonFormField<int?>(
                                      value: null,
                                      isExpanded: true,
                                      style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                                      dropdownColor: context.colors.bgCard,
                                      decoration: _inputDecoration('없음'),
                                      items: const [
                                        DropdownMenuItem(
                                            value: null, child: Text('없음')),
                                      ],
                                      onChanged: (v) =>
                                          setState(() => _categoryId = v),
                                    ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),

                      // ── Row 2: 완료기한 (100% 전체 폭) ─────────────────────
                      Text('완료기한', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                      const SizedBox(height: 6),
                      TextField(
                        controller: _dueDateController,
                        readOnly: true,
                        onTap: () => _selectDate(_dueDateController),
                        style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                        decoration: _inputDecoration('YYYY-MM-DD').copyWith(
                          suffixIcon: _dueDateController.text.isNotEmpty
                              ? IconButton(
                                  icon: Icon(Icons.clear_rounded,
                                      size: 18, color: context.colors.textMuted),
                                  tooltip: '기한 삭제',
                                  onPressed: () => setState(
                                      () => _dueDateController.clear()),
                                )
                              : IconButton(
                                  icon: Icon(Icons.calendar_today,
                                      size: 18, color: context.colors.textMuted),
                                  onPressed: () =>
                                      _selectDate(_dueDateController),
                                ),
                        ),
                      ),
                      const SizedBox(height: 14),

                      // ── Row 3: 상위업무 (100% 전체 폭) ───────────────────
                      Text('상위업무', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                      const SizedBox(height: 6),
                      projectIssuesAsync?.when(
                            loading: () => SizedBox(
                              height: 48,
                              child: Center(
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: context.colors.accentWork)),
                            ),
                            error: (_, __) =>
                                _buildParentIssueSelector(const []),
                            data: (state) {
                              final candidateIssues = state.items
                                  .where((i) =>
                                      widget.initialIssue == null ||
                                      i.pk != widget.initialIssue!.pk)
                                  .toList();

                              return _buildParentIssueSelector(candidateIssues);
                            },
                          ) ??
                          _buildParentIssueSelector(const []),
                      const SizedBox(height: 14),

                      // ── Row 4: 비공개 업무 토글 (100% 전체 폭 및 상세 설명) ──
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: Text('비공개 업무', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                        subtitle: Text(
                          '본인 및 담당자, 권한 있는 관리자에게만 공개됩니다.',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                        value: _isPrivate,
                        activeThumbColor: context.colors.accentWork,
                        onChanged: (v) => setState(() => _isPrivate = v),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildParentIssueSelector(List<IssueModel> candidateIssues) {
    // 현재 선택된 상위 업무 찾기
    String displayTitle = '상위업무 없음 (최상위 업무)';
    if (_parentIssueId != null) {
      final found = candidateIssues.where((i) => i.pk == _parentIssueId).firstOrNull;
      if (found != null) {
        displayTitle = '#${found.pk} ${found.subject}';
      } else if (widget.initialIssue?.parent != null &&
          widget.initialIssue!.parent!.pk == _parentIssueId) {
        displayTitle =
            '#${widget.initialIssue!.parent!.pk} ${widget.initialIssue!.parent!.subject}';
      } else {
        displayTitle = '#$_parentIssueId 번 업무';
      }
    }

    final isSelected = _parentIssueId != null;

    return InkWell(
      onTap: () => _showParentIssueSearchModal(candidateIssues),
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 13),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: context.colors.border, width: 0.8),
        ),
        child: Row(
          children: [
            Icon(
              Icons.account_tree_outlined,
              size: 18,
              color: isSelected ? context.colors.accentWork : context.colors.textMuted,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                displayTitle,
                style: isSelected
                    ? AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary)
                    : AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (isSelected)
              GestureDetector(
                onTap: () => setState(() => _parentIssueId = null),
                child: Padding(
                  padding: const EdgeInsets.only(left: 8),
                  child: Icon(Icons.close_rounded,
                      size: 18, color: context.colors.textMuted),
                ),
              )
            else
              Icon(Icons.search_rounded,
                  size: 18, color: context.colors.textMuted),
          ],
        ),
      ),
    );
  }

  void _showParentIssueSearchModal(List<IssueModel> candidateIssues) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: context.colors.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return _ParentIssueSearchModal(
          currentParentId: _parentIssueId,
          candidates: candidateIssues,
          onSelect: (selectedId) {
            setState(() => _parentIssueId = selectedId);
            Navigator.pop(ctx);
          },
        );
      },
    );
  }

  InputDecoration _inputDecoration(String hint) {
    return InputDecoration(
      hintText: hint,
      hintStyle: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
      filled: true,
      fillColor: context.colors.bgCard,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: BorderSide(color: context.colors.border, width: 0.8),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: BorderSide(color: context.colors.border, width: 0.8),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: BorderSide(color: context.colors.accentWork, width: 1.5),
      ),
    );
  }
}

/// 상위 업무 검색 및 선택 바텀시트
class _ParentIssueSearchModal extends StatefulWidget {
  final int? currentParentId;
  final List<IssueModel> candidates;
  final ValueChanged<int?> onSelect;

  const _ParentIssueSearchModal({
    required this.currentParentId,
    required this.candidates,
    required this.onSelect,
  });

  @override
  State<_ParentIssueSearchModal> createState() =>
      _ParentIssueSearchModalState();
}

class _ParentIssueSearchModalState extends State<_ParentIssueSearchModal> {
  final _searchController = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final filtered = widget.candidates.where((i) {
      if (_query.isEmpty) return true;
      final q = _query.toLowerCase();
      return i.subject.toLowerCase().contains(q) ||
          i.pk.toString().contains(q) ||
          i.tracker.name.toLowerCase().contains(q);
    }).toList();

    return DraggableScrollableSheet(
      initialChildSize: 0.75,
      minChildSize: 0.4,
      maxChildSize: 0.92,
      expand: false,
      builder: (context, scrollController) {
        return Container(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 드래그 핸들 ─────────────────────────────────────────────
              Center(
                child: Container(
                  width: 36,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: context.colors.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              // ── 헤더 제목 ───────────────────────────────────────────────
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('상위업무 선택', style: AppTextStyles.titleLg.copyWith(color: context.colors.textPrimary)),
                  IconButton(
                    icon: Icon(Icons.close_rounded, size: 20, color: context.colors.textPrimary),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              // ── 검색창 ──────────────────────────────────────────────────
              TextField(
                controller: _searchController,
                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                decoration: InputDecoration(
                  hintText: '업무 번호(#ID) 또는 제목 검색',
                  hintStyle: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                  prefixIcon: Icon(Icons.search_rounded, size: 20, color: context.colors.textMuted),
                  suffixIcon: _query.isNotEmpty
                      ? IconButton(
                          icon: Icon(Icons.clear_rounded, size: 18, color: context.colors.textMuted),
                          onPressed: () {
                            _searchController.clear();
                            setState(() => _query = '');
                          },
                        )
                      : null,
                  filled: true,
                  fillColor: context.colors.bgSurface,
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                    borderSide: BorderSide.none,
                  ),
                ),
                onChanged: (v) => setState(() => _query = v.trim()),
              ),
              const SizedBox(height: 12),

              // ── 없음(최상위 업무) 선택 옵션 ─────────────────────────────
              ListTile(
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(6)),
                tileColor: widget.currentParentId == null
                    ? context.colors.accentWork.withAlpha(25)
                    : null,
                leading: Icon(
                  Icons.block_rounded,
                  color: widget.currentParentId == null
                      ? context.colors.accentWork
                      : context.colors.textMuted,
                  size: 20,
                ),
                title: Text(
                  '없음 (최상위 업무로 설정)',
                  style: AppTextStyles.bodyMd.copyWith(
                    fontWeight: widget.currentParentId == null
                        ? FontWeight.bold
                        : FontWeight.normal,
                    color: widget.currentParentId == null
                        ? context.colors.accentWork
                        : context.colors.textPrimary,
                  ),
                ),
                trailing: widget.currentParentId == null
                    ? Icon(Icons.check_rounded,
                        color: context.colors.accentWork, size: 20)
                    : null,
                onTap: () => widget.onSelect(null),
              ),
              Divider(height: 12, color: context.colors.border),

              // ── 검색된 업무 목록 ─────────────────────────────────────────
              Expanded(
                child: filtered.isEmpty
                    ? Center(
                        child: Text(
                          _query.isEmpty
                              ? '선택 가능한 업무가 없습니다.'
                              : '검색 결과가 없습니다.',
                          style: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                        ),
                      )
                    : ListView.separated(
                        controller: scrollController,
                        itemCount: filtered.length,
                        separatorBuilder: (_, __) =>
                            Divider(height: 1, color: context.colors.border),
                        itemBuilder: (context, index) {
                          final item = filtered[index];
                          final isCurrent = widget.currentParentId == item.pk;

                          return ListTile(
                            contentPadding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 4),
                            tileColor: isCurrent
                                ? context.colors.accentWork.withAlpha(25)
                                : null,
                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(6)),
                            leading: Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: context.colors.bgSurface,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                '#${item.pk}',
                                style: AppTextStyles.caption.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: context.colors.accentWork,
                                ),
                              ),
                            ),
                            title: Text(
                              item.subject,
                              style: AppTextStyles.bodyMd.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: isCurrent
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            subtitle: Text(
                              '${item.tracker.name} • ${item.status.name} • 담당: ${item.assignedTo?.username ?? "미배정"}',
                              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                            ),
                            trailing: isCurrent
                                ? Icon(Icons.check_rounded,
                                    color: context.colors.accentWork, size: 20)
                                : null,
                            onTap: () => widget.onSelect(item.pk),
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}
