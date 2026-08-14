import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/models/common_models.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/project_provider.dart';
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

  int _trackerId = 4; // 기본: 기획일반
  int _statusId = 1; // 기본: 준비
  int _priorityId = 2; // 기본: 보통
  bool _isPrivate = false;
  bool _isSaving = false;

  int? _assignedToId;
  int? _parentIssueId;
  int? _fixedVersionId;
  int? _categoryId;
  String? _expectedDuration;

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
      _selectedProjectSlug = issue.project.slug;
      _assignedToId = issue.assignedTo?.pk;
      _parentIssueId = issue.parent?.pk;
      _fixedVersionId = issue.fixedVersion?.pk;
      _categoryId = issue.category;
      _expectedDuration = issue.expectedDuration;
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

    if (widget.initialIssue == null &&
        (_selectedProjectSlug == null || _selectedProjectSlug!.isEmpty)) {
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

    if (_assignedToId != null) {
      payload['assigned_to'] = _assignedToId;
    } else {
      payload['assigned_to'] = null;
    }

    if (_parentIssueId != null) {
      payload['parent'] = _parentIssueId;
    } else {
      payload['parent'] = null;
    }

    if (_fixedVersionId != null) {
      payload['fixed_version'] = _fixedVersionId;
    } else {
      payload['fixed_version'] = null;
    }

    if (_categoryId != null) {
      payload['category'] = _categoryId;
    } else {
      payload['category'] = null;
    }

    if (_expectedDuration != null && _expectedDuration!.isNotEmpty) {
      payload['expected_duration'] = _expectedDuration;
    } else {
      payload['expected_duration'] = null;
    }

    if (_dueDateController.text.trim().isNotEmpty) {
      payload['due_date'] = _dueDateController.text.trim();
    } else {
      payload['due_date'] = null;
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
    final projectsAsync = ref.watch(issueFormProjectsProvider);

    // 현재 선택된 프로젝트의 상세 정보 (멤버, 버전, 범주)
    final projectSlug = _selectedProjectSlug ??
        (projectsAsync.valueOrNull?.isNotEmpty == true
            ? projectsAsync.valueOrNull!.first.slug
            : '');
    final projectDetailAsync = projectSlug.isNotEmpty
        ? ref.watch(projectDetailProvider(projectSlug))
        : null;

    // 상위업무 후보 목록 (현재 프로젝트의 이슈 목록)
    final projectIssuesAsync = projectSlug.isNotEmpty
        ? ref.watch(issueListProvider)
        : null;

    // 전역 공용 상태 & 우선순위 목록
    final statusListAsync = ref.watch(issueStatusListProvider);
    final priorityListAsync = ref.watch(issuePriorityListProvider);

    // 현재 로그인 사용자 정보 (나에게 배정용)
    final currentUser = ref.watch(currentUserProvider).valueOrNull;

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
              // ══════════════════════════════════════════════════════════════
              // 1. 핵심 내용 섹션 (프로젝트 / 제목 / 설명)
              // ══════════════════════════════════════════════════════════════
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

              // ── 설명 ────────────────────────────────────────────────────────
              Text('설명', style: AppTextStyles.titleSm),
              const SizedBox(height: 6),
              TextFormField(
                controller: _descriptionController,
                maxLines: 5,
                style: AppTextStyles.bodyMd,
                decoration:
                    _inputDecoration('상세 설명 및 안내 사항을 입력하세요 (마크다운 지원)'),
              ),
              const SizedBox(height: 20),

              // ══════════════════════════════════════════════════════════════
              // 2. 기본/필수 메타정보 섹션 (유형, 상태, 우선순위, 예상처리기간, 시작/마감일)
              // ══════════════════════════════════════════════════════════════
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.bgCard,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.border, width: 0.8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('기본 설정', style: AppTextStyles.titleMd),
                    const SizedBox(height: 12),

                    // 1. 유형 & 우선순위
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('유형', style: AppTextStyles.titleSm),
                              const SizedBox(height: 6),
                              projectDetailAsync?.when(
                                    loading: () => const SizedBox(height: 48),
                                    error: (_, __) =>
                                        DropdownButtonFormField<int>(
                                      value: _trackerId,
                                      style: AppTextStyles.bodyMd,
                                      dropdownColor: AppColors.bgCard,
                                      decoration: _inputDecoration(''),
                                      items: const [
                                        DropdownMenuItem(
                                            value: 4, child: Text('기획일반')),
                                        DropdownMenuItem(
                                            value: 1, child: Text('결함')),
                                        DropdownMenuItem(
                                            value: 2, child: Text('기능')),
                                        DropdownMenuItem(
                                            value: 3, child: Text('지원')),
                                      ],
                                      onChanged: (v) =>
                                          setState(() => _trackerId = v ?? 4),
                                    ),
                                    data: (proj) {
                                      final trackers = proj.trackers;
                                      final uniqueTrackers = <int, ProjectTrackerModel>{};
                                      for (final t in trackers) {
                                        uniqueTrackers[t.pk] = t;
                                      }
                                      final trackerList = uniqueTrackers.values.toList();
                                      final hasTrackers = trackerList.isNotEmpty;

                                      final currentTrackerId = (hasTrackers &&
                                              !trackerList
                                                  .any((t) => t.pk == _trackerId))
                                          ? trackerList.first.pk
                                          : _trackerId;

                                      return DropdownButtonFormField<int>(
                                        value: currentTrackerId,
                                        style: AppTextStyles.bodyMd,
                                        dropdownColor: AppColors.bgCard,
                                        decoration: _inputDecoration(''),
                                        items: hasTrackers
                                            ? trackerList
                                                .map((t) => DropdownMenuItem(
                                                      value: t.pk,
                                                      child: Text(t.name),
                                                    ))
                                                .toList()
                                            : const [
                                                DropdownMenuItem(
                                                    value: 4,
                                                    child: Text('기획일반')),
                                                DropdownMenuItem(
                                                    value: 1,
                                                    child: Text('결함')),
                                                DropdownMenuItem(
                                                    value: 2,
                                                    child: Text('기능')),
                                                DropdownMenuItem(
                                                    value: 3,
                                                    child: Text('지원')),
                                              ],
                                        onChanged: (v) =>
                                            setState(() => _trackerId = v ?? 4),
                                      );
                                    },
                                  ) ??
                                  DropdownButtonFormField<int>(
                                    value: _trackerId,
                                    style: AppTextStyles.bodyMd,
                                    dropdownColor: AppColors.bgCard,
                                    decoration: _inputDecoration(''),
                                    items: const [
                                      DropdownMenuItem(
                                          value: 4, child: Text('기획일반')),
                                      DropdownMenuItem(
                                          value: 1, child: Text('결함')),
                                      DropdownMenuItem(
                                          value: 2, child: Text('기능')),
                                      DropdownMenuItem(
                                          value: 3, child: Text('지원')),
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
                              Text('우선순위', style: AppTextStyles.titleSm),
                              const SizedBox(height: 6),
                              priorityListAsync.when(
                                loading: () => const SizedBox(height: 48),
                                error: (_, __) => DropdownButtonFormField<int>(
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
                                data: (priorities) {
                                  final uniquePriorities = <int, IssuePriorityModel>{};
                                  for (final p in priorities) {
                                    uniquePriorities[p.pk] = p;
                                  }
                                  final priorityList = uniquePriorities.values.toList();
                                  final hasPriorities = priorityList.isNotEmpty;

                                  final currentPriorityId = (hasPriorities &&
                                          !priorityList
                                              .any((p) => p.pk == _priorityId))
                                      ? priorityList.first.pk
                                      : _priorityId;

                                  return DropdownButtonFormField<int>(
                                    value: currentPriorityId,
                                    style: AppTextStyles.bodyMd,
                                    dropdownColor: AppColors.bgCard,
                                    decoration: _inputDecoration(''),
                                    items: hasPriorities
                                        ? priorityList
                                            .map((p) => DropdownMenuItem(
                                                  value: p.pk,
                                                  child: Text(p.name),
                                                ))
                                            .toList()
                                        : const [
                                            DropdownMenuItem(
                                                value: 1, child: Text('낮음')),
                                            DropdownMenuItem(
                                                value: 2, child: Text('보통')),
                                            DropdownMenuItem(
                                                value: 3, child: Text('높음')),
                                            DropdownMenuItem(
                                                value: 4, child: Text('긴급')),
                                            DropdownMenuItem(
                                                value: 5, child: Text('즉시')),
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

                    // 2. 담당자 & 상태
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                children: [
                                  Text('담당자', style: AppTextStyles.titleSm),
                                  if (currentUser != null &&
                                      _assignedToId != currentUser.pk)
                                    InkWell(
                                      borderRadius: BorderRadius.circular(4),
                                      onTap: () {
                                        setState(() {
                                          _assignedToId = currentUser.pk;
                                        });
                                      },
                                      child: Padding(
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 4, vertical: 1),
                                        child: Text(
                                          '« 나에게',
                                          style: AppTextStyles.caption.copyWith(
                                            color: AppColors.accentWork,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              projectDetailAsync?.when(
                                    loading: () => const SizedBox(
                                      height: 48,
                                      child: Center(
                                          child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                              color: AppColors.accentWork)),
                                    ),
                                    error: (_, __) =>
                                        DropdownButtonFormField<int?>(
                                      value: null,
                                      style: AppTextStyles.bodyMd,
                                      dropdownColor: AppColors.bgCard,
                                      decoration: _inputDecoration('미배정'),
                                      items: const [
                                        DropdownMenuItem(
                                            value: null, child: Text('미배정')),
                                      ],
                                      onChanged: (v) =>
                                          setState(() => _assignedToId = v),
                                    ),
                                    data: (proj) {
                                      final uniqueMembers = <int, ProjectMemberModel>{};
                                      for (final m in proj.members) {
                                        uniqueMembers[m.user.pk] = m;
                                      }
                                      final memberList = uniqueMembers.values.toList();

                                      // 현재 선택된 담당자가 멤버 목록에 없으면(예: 퇴사자, 임의 유저 등) 보정
                                      final currentAssignedId = (_assignedToId != null &&
                                              !memberList.any((m) => m.user.pk == _assignedToId))
                                          ? null
                                          : _assignedToId;

                                      return DropdownButtonFormField<int?>(
                                        value: currentAssignedId,
                                        style: AppTextStyles.bodyMd,
                                        dropdownColor: AppColors.bgCard,
                                        decoration:
                                            _inputDecoration('담당자 선택'),
                                        items: [
                                          const DropdownMenuItem(
                                              value: null, child: Text('미배정')),
                                          ...memberList.map((m) => DropdownMenuItem(
                                                value: m.user.pk,
                                                child: Text(m.user.username),
                                              )),
                                        ],
                                        onChanged: (v) =>
                                            setState(() => _assignedToId = v),
                                      );
                                    },
                                  ) ??
                                  DropdownButtonFormField<int?>(
                                    value: null,
                                    style: AppTextStyles.bodyMd,
                                    dropdownColor: AppColors.bgCard,
                                    decoration: _inputDecoration('미배정'),
                                    items: const [
                                      DropdownMenuItem(
                                          value: null, child: Text('미배정')),
                                    ],
                                    onChanged: (v) =>
                                        setState(() => _assignedToId = v),
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
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                children: [
                                  Text('상태', style: AppTextStyles.titleSm),
                                  // 준비(1) 상태일 때는 '진행 »', 진행(2) 상태일 때는 '완료 »' 빠른 전환 버튼
                                  if (_statusId == 1)
                                    InkWell(
                                      borderRadius: BorderRadius.circular(4),
                                      onTap: () =>
                                          setState(() => _statusId = 2),
                                      child: Padding(
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 4, vertical: 1),
                                        child: Text(
                                          '진행 »',
                                          style: AppTextStyles.caption.copyWith(
                                            color: AppColors.accentWork,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ),
                                    )
                                  else if (_statusId == 2)
                                    InkWell(
                                      borderRadius: BorderRadius.circular(4),
                                      onTap: () =>
                                          setState(() => _statusId = 5),
                                      child: Padding(
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 4, vertical: 1),
                                        child: Text(
                                          '완료 »',
                                          style: AppTextStyles.caption.copyWith(
                                            color: AppColors.success,
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
                                  onChanged: (v) =>
                                      setState(() => _statusId = v ?? 2),
                                ),
                                data: (statuses) {
                                  final filtered = isEdit
                                      ? statuses
                                      : statuses.where((s) => s.pk <= 2).toList();

                                  final uniqueStatuses = <int, IssueStatusModel>{};
                                  for (final s in filtered) {
                                    uniqueStatuses[s.pk] = s;
                                  }
                                  final availableStatuses = uniqueStatuses.values.toList();

                                  final hasStatuses = availableStatuses.isNotEmpty;
                                  final currentStatusId = (hasStatuses &&
                                          !availableStatuses
                                              .any((s) => s.pk == _statusId))
                                      ? availableStatuses.first.pk
                                      : _statusId;

                                  return DropdownButtonFormField<int>(
                                    value: currentStatusId,
                                    style: AppTextStyles.bodyMd,
                                    dropdownColor: AppColors.bgCard,
                                    decoration: _inputDecoration(''),
                                    items: hasStatuses
                                        ? availableStatuses
                                            .map((s) => DropdownMenuItem(
                                                  value: s.pk,
                                                  child: Text(s.name),
                                                ))
                                            .toList()
                                        : const [
                                            DropdownMenuItem(
                                                value: 1, child: Text('준비')),
                                            DropdownMenuItem(
                                                value: 2, child: Text('진행')),
                                          ],
                                    onChanged: (v) =>
                                        setState(() => _statusId = v ?? 1),
                                  );
                                },
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // 3. 시작일 & 예상 처리기간 (필수)
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('시작일 *', style: AppTextStyles.titleSm),
                              const SizedBox(height: 6),
                              TextField(
                                controller: _startDateController,
                                readOnly: true,
                                style: AppTextStyles.bodyMd,
                                decoration:
                                    _inputDecoration('YYYY-MM-DD').copyWith(
                                  suffixIcon: IconButton(
                                    icon: const Icon(Icons.calendar_today,
                                        size: 18),
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
                                // 준비(초기) 상태가 아닐 때는 필수(*) 표기
                                (_statusId == 1)
                                    ? '예상 처리기간'
                                    : '예상 처리기간 *',
                                style: AppTextStyles.titleSm,
                              ),
                              const SizedBox(height: 6),
                              DropdownButtonFormField<String?>(
                                value: _expectedDuration,
                                style: AppTextStyles.bodyMd,
                                dropdownColor: AppColors.bgCard,
                                decoration: _inputDecoration(
                                  (_statusId == 1)
                                      ? '선택사항 (진행 시 필수)'
                                      : '처리기간 선택',
                                ),
                                items: [
                                  const DropdownMenuItem(
                                      value: null, child: Text('선택 안함')),
                                  ..._kDurationOptions
                                      .map((opt) => DropdownMenuItem(
                                            value: opt['value'],
                                            child: Text(opt['label']!),
                                          )),
                                ],
                                validator: (v) {
                                  // 준비(초기 단계, pk=1)를 벗어났을 때만 필수 유효성 검사 수행
                                  if (_statusId != 1 && (v == null || v.isEmpty)) {
                                    return '업무를 진행하려면 예상 처리기간을 선택해 주세요.';
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
                  color: AppColors.bgCard,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.border, width: 0.8),
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
                    leading: const Icon(Icons.tune_rounded,
                        size: 20, color: AppColors.accentWork),
                    title: Text('추가 상세 항목',
                        style: AppTextStyles.titleSm),
                    subtitle: Text(
                      _dueDateController.text.isNotEmpty ||
                              _parentIssueId != null ||
                              _fixedVersionId != null ||
                              _categoryId != null ||
                              _isPrivate
                          ? '설정된 항목이 있습니다.'
                          : '필요 시 펼쳐서 설정할 수 있습니다.',
                      style: AppTextStyles.caption,
                    ),
                    children: [
                      const Divider(height: 16, color: AppColors.border),

                      // ── 완료기한 ───────────────────────────────────────
                      Text('완료기한', style: AppTextStyles.titleSm),
                      const SizedBox(height: 6),
                      TextField(
                        controller: _dueDateController,
                        readOnly: true,
                        style: AppTextStyles.bodyMd,
                        decoration: _inputDecoration('YYYY-MM-DD').copyWith(
                          suffixIcon: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              if (_dueDateController.text.isNotEmpty)
                                IconButton(
                                  icon: const Icon(Icons.clear_rounded,
                                      size: 18, color: AppColors.textMuted),
                                  onPressed: () =>
                                      setState(() => _dueDateController.clear()),
                                ),
                              IconButton(
                                icon: const Icon(Icons.calendar_today,
                                    size: 18),
                                onPressed: () =>
                                    _selectDate(_dueDateController),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 14),

                      // ── 상위업무 (검색 및 선택 바텀시트) ──────────────────
                      Text('상위업무', style: AppTextStyles.titleSm),
                      const SizedBox(height: 6),
                      projectIssuesAsync?.when(
                            loading: () => const SizedBox(
                              height: 48,
                              child: Center(
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: AppColors.accentWork)),
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

                      // ── 목표단계 & 범주 ─────────────────────────────────
                      Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('목표단계 (버전)',
                                    style: AppTextStyles.titleSm),
                                const SizedBox(height: 6),
                                projectDetailAsync?.when(
                                      loading: () =>
                                          const SizedBox(height: 48),
                                      error: (_, __) =>
                                          DropdownButtonFormField<int?>(
                                        value: null,
                                        style: AppTextStyles.bodyMd,
                                        dropdownColor: AppColors.bgCard,
                                        decoration: _inputDecoration('없음'),
                                        items: const [
                                          DropdownMenuItem(
                                              value: null, child: Text('없음')),
                                        ],
                                        onChanged: (v) =>
                                            setState(() => _fixedVersionId = v),
                                      ),
                                      data: (proj) {
                                        final uniqueVersions = <int, ProjectVersionModel>{};
                                        for (final ver in proj.versions) {
                                          uniqueVersions[ver.pk] = ver;
                                        }
                                        final versionList = uniqueVersions.values.toList();

                                        // 신규 생성 모드에서 아직 버전이 선택되지 않은 경우, 프로젝트의 기본 버전(isDefault == true)으로 자동 지정
                                        var selectedVerId = _fixedVersionId;
                                        if (!isEdit && selectedVerId == null && versionList.isNotEmpty) {
                                          final defaultVer = versionList.where((v) => v.isDefault).firstOrNull;
                                          if (defaultVer != null) {
                                            selectedVerId = defaultVer.pk;
                                            // 다음 프레임에 상태값 동기화
                                            WidgetsBinding.instance.addPostFrameCallback((_) {
                                              if (mounted && _fixedVersionId == null) {
                                                setState(() => _fixedVersionId = defaultVer.pk);
                                              }
                                            });
                                          }
                                        }

                                        // 현재 선택된 버전이 버전 목록에 없으면 null로 안전 보정
                                        if (selectedVerId != null && !versionList.any((v) => v.pk == selectedVerId)) {
                                          selectedVerId = null;
                                        }

                                        return DropdownButtonFormField<int?>(
                                          value: selectedVerId,
                                          style: AppTextStyles.bodyMd,
                                          dropdownColor: AppColors.bgCard,
                                          decoration:
                                              _inputDecoration('목표단계 선택'),
                                          items: [
                                            const DropdownMenuItem(
                                                value: null, child: Text('없음')),
                                            ...versionList
                                                .map((ver) => DropdownMenuItem(
                                                      value: ver.pk,
                                                      child: Text(
                                                          '${ver.name}${ver.isDefault ? ' (기본)' : ''}'),
                                                    )),
                                          ],
                                          onChanged: (v) =>
                                              setState(() => _fixedVersionId = v),
                                        );
                                      },
                                    ) ??
                                    DropdownButtonFormField<int?>(
                                      value: null,
                                      style: AppTextStyles.bodyMd,
                                      dropdownColor: AppColors.bgCard,
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
                                Text('범주', style: AppTextStyles.titleSm),
                                const SizedBox(height: 6),
                                projectDetailAsync?.when(
                                      loading: () =>
                                          const SizedBox(height: 48),
                                      error: (_, __) =>
                                          DropdownButtonFormField<int?>(
                                        value: null,
                                        style: AppTextStyles.bodyMd,
                                        dropdownColor: AppColors.bgCard,
                                        decoration: _inputDecoration('없음'),
                                        items: const [
                                          DropdownMenuItem(
                                              value: null, child: Text('없음')),
                                        ],
                                        onChanged: (v) =>
                                            setState(() => _categoryId = v),
                                      ),
                                      data: (proj) {
                                        final uniqueCategories = <int, ProjectCategoryModel>{};
                                        for (final cate in proj.categories) {
                                          uniqueCategories[cate.pk] = cate;
                                        }
                                        final categoryList = uniqueCategories.values.toList();

                                        // 현재 선택된 범주가 목록에 없으면 null로 안전 보정
                                        final currentCategoryId = (_categoryId != null &&
                                                !categoryList.any((c) => c.pk == _categoryId))
                                            ? null
                                            : _categoryId;

                                        return DropdownButtonFormField<int?>(
                                          value: currentCategoryId,
                                          style: AppTextStyles.bodyMd,
                                          dropdownColor: AppColors.bgCard,
                                          decoration: _inputDecoration('범주 선택'),
                                          items: [
                                            const DropdownMenuItem(
                                                value: null, child: Text('없음')),
                                            ...categoryList.map((cate) => DropdownMenuItem(
                                                  value: cate.pk,
                                                  child: Text(cate.name),
                                                )),
                                          ],
                                          onChanged: (v) {
                                            setState(() {
                                              _categoryId = v;
                                              if (v != null) {
                                                final selectedCate = categoryList
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
                                      style: AppTextStyles.bodyMd,
                                      dropdownColor: AppColors.bgCard,
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

                      // ── 비공개 토글 ─────────────────────────────────────
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title:
                            Text('비공개 업무', style: AppTextStyles.titleSm),
                        subtitle: Text(
                            '본인 및 담당자, 권한 있는 관리자에게만 공개됩니다.',
                            style: AppTextStyles.caption),
                        value: _isPrivate,
                        activeColor: AppColors.accentWork,
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
          color: AppColors.bgCard,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: AppColors.border, width: 0.8),
        ),
        child: Row(
          children: [
            Icon(
              Icons.account_tree_outlined,
              size: 18,
              color: isSelected ? AppColors.accentWork : AppColors.textMuted,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                displayTitle,
                style: isSelected
                    ? AppTextStyles.bodyMd.copyWith(color: AppColors.textPrimary)
                    : AppTextStyles.bodyMuted,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (isSelected)
              GestureDetector(
                onTap: () => setState(() => _parentIssueId = null),
                child: const Padding(
                  padding: EdgeInsets.only(left: 8),
                  child: Icon(Icons.close_rounded,
                      size: 18, color: AppColors.textMuted),
                ),
              )
            else
              const Icon(Icons.search_rounded,
                  size: 18, color: AppColors.textMuted),
          ],
        ),
      ),
    );
  }

  void _showParentIssueSearchModal(List<IssueModel> candidateIssues) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.bgCard,
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
                    color: AppColors.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              // ── 헤더 제목 ───────────────────────────────────────────────
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('상위업무 선택', style: AppTextStyles.titleLg),
                  IconButton(
                    icon: const Icon(Icons.close_rounded, size: 20),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              // ── 검색창 ──────────────────────────────────────────────────
              TextField(
                controller: _searchController,
                style: AppTextStyles.bodyMd,
                decoration: InputDecoration(
                  hintText: '업무 번호(#ID) 또는 제목 검색',
                  hintStyle: AppTextStyles.bodyMuted,
                  prefixIcon: const Icon(Icons.search_rounded, size: 20),
                  suffixIcon: _query.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear_rounded, size: 18),
                          onPressed: () {
                            _searchController.clear();
                            setState(() => _query = '');
                          },
                        )
                      : null,
                  filled: true,
                  fillColor: AppColors.bgSurface,
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
                    ? AppColors.accentWork.withAlpha(25)
                    : null,
                leading: Icon(
                  Icons.block_rounded,
                  color: widget.currentParentId == null
                      ? AppColors.accentWork
                      : AppColors.textMuted,
                  size: 20,
                ),
                title: Text(
                  '없음 (최상위 업무로 설정)',
                  style: AppTextStyles.bodyMd.copyWith(
                    fontWeight: widget.currentParentId == null
                        ? FontWeight.bold
                        : FontWeight.normal,
                    color: widget.currentParentId == null
                        ? AppColors.accentWork
                        : AppColors.textPrimary,
                  ),
                ),
                trailing: widget.currentParentId == null
                    ? const Icon(Icons.check_rounded,
                        color: AppColors.accentWork, size: 20)
                    : null,
                onTap: () => widget.onSelect(null),
              ),
              const Divider(height: 12, color: AppColors.border),

              // ── 검색된 업무 목록 ─────────────────────────────────────────
              Expanded(
                child: filtered.isEmpty
                    ? Center(
                        child: Text(
                          _query.isEmpty
                              ? '선택 가능한 업무가 없습니다.'
                              : '검색 결과가 없습니다.',
                          style: AppTextStyles.bodyMuted,
                        ),
                      )
                    : ListView.separated(
                        controller: scrollController,
                        itemCount: filtered.length,
                        separatorBuilder: (_, __) =>
                            const Divider(height: 1, color: AppColors.border),
                        itemBuilder: (context, index) {
                          final item = filtered[index];
                          final isCurrent = widget.currentParentId == item.pk;

                          return ListTile(
                            contentPadding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 4),
                            tileColor: isCurrent
                                ? AppColors.accentWork.withAlpha(25)
                                : null,
                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(6)),
                            leading: Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppColors.bgSurface,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                '#${item.pk}',
                                style: AppTextStyles.caption.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.accentWork,
                                ),
                              ),
                            ),
                            title: Text(
                              item.subject,
                              style: AppTextStyles.bodyMd.copyWith(
                                fontWeight: isCurrent
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            subtitle: Text(
                              '${item.tracker.name} • ${item.status.name} • 담당: ${item.assignedTo?.username ?? "미배정"}',
                              style: AppTextStyles.caption,
                            ),
                            trailing: isCurrent
                                ? const Icon(Icons.check_rounded,
                                    color: AppColors.accentWork, size: 20)
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
