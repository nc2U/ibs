import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../project/providers/project_provider.dart';
import '../data/models/todo_model.dart';
import 'providers/todo_provider.dart';

/// 할일을 워크스페이스 공식 업무(Issue)로 전환하는 바텀시트.
///
/// 전환에 성공하면 [TodoConvertResult]를 pop 결과로 반환하고,
/// 취소/닫기 시에는 null을 반환한다.
Future<TodoConvertResult?> showConvertTodoSheet(
  BuildContext context,
  TodoItem item,
) {
  return showModalBottomSheet<TodoConvertResult>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    backgroundColor: context.colors.bgPrimary,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) => ConvertTodoSheet(item: item),
  );
}

class ConvertTodoSheet extends ConsumerStatefulWidget {
  final TodoItem item;

  const ConvertTodoSheet({super.key, required this.item});

  @override
  ConsumerState<ConvertTodoSheet> createState() => _ConvertTodoSheetState();
}

class _ConvertTodoSheetState extends ConsumerState<ConvertTodoSheet> {
  late final TextEditingController _subjectController;
  final TextEditingController _descController = TextEditingController();

  int? _selectedProjectId;
  bool _didInitDefaultProject = false;
  bool _submitting = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _subjectController = TextEditingController(text: widget.item.title);
  }

  @override
  void dispose() {
    _subjectController.dispose();
    _descController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final subject = _subjectController.text.trim();
    if (_selectedProjectId == null) {
      setState(() => _errorMessage = '업무를 등록할 워크스페이스를 선택해 주세요.');
      return;
    }
    if (subject.isEmpty) {
      setState(() => _errorMessage = '업무 제목을 입력해 주세요.');
      return;
    }

    setState(() {
      _submitting = true;
      _errorMessage = null;
    });

    try {
      final result = await ref.read(todoListProvider.notifier).convertToIssue(
            item: widget.item,
            projectId: _selectedProjectId!,
            subject: subject,
            description: _descController.text.trim(),
          );
      if (mounted) Navigator.of(context).pop(result);
    } catch (e) {
      if (mounted) {
        String msg = '업무 전환 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.';
        if (e is DioException) {
          final data = e.response?.data;
          if (data is Map) {
            if (data['error'] != null) {
              msg = data['error'].toString();
            } else if (data['detail'] != null) {
              msg = data['detail'].toString();
            }
          }
        }
        setState(() {
          _submitting = false;
          _errorMessage = msg;
        });
      }
    }
  }

  InputDecoration _fieldDecoration(String hint) {
    return InputDecoration(
      hintText: hint,
      hintStyle: AppTextStyles.bodyMd.copyWith(color: context.colors.textMuted),
      counterStyle: TextStyle(color: context.colors.textMuted, fontSize: 11),
      filled: true,
      fillColor: context.colors.bgInput,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: context.colors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: context.colors.accentWork, width: 2),
      ),
      disabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: context.colors.borderSubtle),
      ),
    );
  }

  Widget _label(String text, {bool required = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text.rich(
        TextSpan(
          text: text,
          style: AppTextStyles.bodySm.copyWith(
            fontWeight: FontWeight.w600,
            color: context.colors.textSecond,
          ),
          children: [
            if (required)
              const TextSpan(
                text: ' *',
                style: TextStyle(color: Colors.redAccent),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildProjectSelector() {
    final projectsAsync = ref.watch(issueFormProjectsProvider);

    return projectsAsync.when(
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: 14),
        child: Center(
          child: SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      ),
      error: (_, __) => Row(
        children: [
          Expanded(
            child: Text(
              '워크스페이스 목록을 불러오지 못했습니다.',
              style: AppTextStyles.bodySm.copyWith(color: Colors.redAccent),
            ),
          ),
          TextButton(
            onPressed: () => ref.invalidate(issueFormProjectsProvider),
            child: const Text('다시 시도'),
          ),
        ],
      ),
      data: (projects) {
        if (projects.isEmpty) {
          return Text(
            '업무를 등록할 수 있는 워크스페이스가 없습니다.',
            style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
          );
        }

        // 최초 진입 시 활성 워크스페이스 또는 첫 번째 워크스페이스를 기본 선택
        int? selected = projects.any((p) => p.pk == _selectedProjectId)
            ? _selectedProjectId
            : null;
        if (selected == null && !_didInitDefaultProject) {
          _didInitDefaultProject = true;
          final currentProj = ref.read(selectedProjectProvider);
          final defaultId = projects.any((p) => p.slug == currentProj?.slug)
              ? projects.firstWhere((p) => p.slug == currentProj?.slug).pk
              : projects.first.pk;
          selected = defaultId;
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (mounted && _selectedProjectId == null) {
              setState(() => _selectedProjectId = defaultId);
            }
          });
        }

        return InputDecorator(
          decoration: _fieldDecoration('').copyWith(
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<int>(
              isExpanded: true,
              value: selected,
              dropdownColor: context.colors.bgCard,
              hint: Text(
                '워크스페이스를 선택하세요',
                style: AppTextStyles.bodyMd.copyWith(
                  color: context.colors.textMuted,
                ),
              ),
              style: AppTextStyles.bodyMd.copyWith(
                color: context.colors.textPrimary,
              ),
              items: [
                for (final p in projects)
                  DropdownMenuItem<int>(
                    value: p.pk,
                    child: Text(
                      p.indentedLabel,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
              onChanged: _submitting
                  ? null
                  : (v) => setState(() => _selectedProjectId = v),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return Padding(
      padding: EdgeInsets.only(bottom: bottomInset),
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 드래그 핸들
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: context.colors.borderSubtle,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Icon(Icons.assignment_turned_in_outlined,
                    size: 22, color: context.colors.accentWork),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '할일을 업무로 전환',
                    style: AppTextStyles.titleMd.copyWith(
                      fontWeight: FontWeight.bold,
                      color: context.colors.textPrimary,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              '개인 할일을 워크스페이스 공식 업무로 등록합니다. 전환이 완료되면 이 할일은 자동으로 완료 처리됩니다.',
              style: AppTextStyles.bodySm.copyWith(
                color: context.colors.textMuted,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 16),

            if (_errorMessage != null) ...[
              Container(
                width: double.infinity,
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.redAccent.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: Colors.redAccent.withValues(alpha: 0.4),
                  ),
                ),
                child: Text(
                  _errorMessage!,
                  style: AppTextStyles.bodySm.copyWith(color: Colors.redAccent),
                ),
              ),
              const SizedBox(height: 12),
            ],

            _label('대상 워크스페이스', required: true),
            _buildProjectSelector(),
            const SizedBox(height: 14),

            _label('업무 제목', required: true),
            TextField(
              controller: _subjectController,
              enabled: !_submitting,
              maxLength: 100,
              style: AppTextStyles.bodyMd.copyWith(
                color: context.colors.textPrimary,
              ),
              textInputAction: TextInputAction.next,
              decoration: _fieldDecoration('업무 제목을 입력하세요'),
            ),
            const SizedBox(height: 6),

            _label('설명 (선택)'),
            TextField(
              controller: _descController,
              enabled: !_submitting,
              minLines: 3,
              maxLines: 5,
              style: AppTextStyles.bodyMd.copyWith(
                color: context.colors.textPrimary,
              ),
              decoration: _fieldDecoration('추가 세부 사항이나 메모를 입력하세요'),
            ),
            const SizedBox(height: 20),

            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      side: BorderSide(color: context.colors.border),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    onPressed:
                        _submitting ? null : () => Navigator.of(context).pop(),
                    child: Text(
                      '취소',
                      style: TextStyle(color: context.colors.textSecond),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  flex: 2,
                  child: FilledButton(
                    style: FilledButton.styleFrom(
                      backgroundColor: context.colors.accentWork,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    onPressed:
                        (_submitting || _selectedProjectId == null) ? null : _submit,
                    child: _submitting
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('업무로 전환'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
