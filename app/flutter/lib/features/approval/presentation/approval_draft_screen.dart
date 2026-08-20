import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../data/approval_repository.dart';
import '../data/models/approval_model.dart';
import '../providers/approval_providers.dart';

class ApprovalDraftScreen extends ConsumerStatefulWidget {
  const ApprovalDraftScreen({super.key});

  @override
  ConsumerState<ApprovalDraftScreen> createState() => _ApprovalDraftScreenState();
}

class _ApprovalDraftScreenState extends ConsumerState<ApprovalDraftScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();

  // 폼 선택 상태
  StaffAssignmentItemModel? _selectedAssignment;
  DocumentTypeModel? _selectedDocType;
  final List<String> _attachedFilePaths = [];
  bool _isSubmitting = false;

  // ── 양식별 컨트롤러 ─────────────────────────────────────────────
  // 휴가신청서
  String _leaveType = '연차';
  DateTime? _startDate;
  DateTime? _endDate;
  final _leaveDaysController = TextEditingController(text: '1.0');
  final _leaveReasonController = TextEditingController();

  // 지출결의서 / 구매품의서
  final _amountController = TextEditingController();
  final _purposeController = TextEditingController();
  final _vendorController = TextEditingController();
  final _generalContentController = TextEditingController();

  // 실시간 결재선 미리보기 상태
  List<RoutePreviewStepModel> _previewSteps = [];
  bool _isPreviewLoading = false;

  @override
  void dispose() {
    _titleController.dispose();
    _leaveDaysController.dispose();
    _leaveReasonController.dispose();
    _amountController.dispose();
    _purposeController.dispose();
    _vendorController.dispose();
    _generalContentController.dispose();
    super.dispose();
  }

  Future<void> _updateRoutePreview() async {
    if (_selectedDocType == null) {
      setState(() => _previewSteps = []);
      return;
    }

    setState(() => _isPreviewLoading = true);
    try {
      final amount = num.tryParse(_amountController.text.replaceAll(',', '').trim());
      final repo = ref.read(approvalRepositoryProvider);
      final steps = await repo.fetchRoutePreview(
        docTypeId: _selectedDocType!.id,
        assignmentId: _selectedAssignment?.id,
        amount: amount,
      );
      if (mounted) {
        setState(() {
          _previewSteps = steps;
          _isPreviewLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _isPreviewLoading = false);
      }
    }
  }

  Future<void> _pickFiles() async {
    final result = await FilePicker.platform.pickFiles(allowMultiple: true);
    if (result != null && result.paths.isNotEmpty) {
      setState(() {
        _attachedFilePaths.addAll(result.paths.whereType<String>());
      });
    }
  }

  void _removeFile(int index) {
    setState(() {
      _attachedFilePaths.removeAt(index);
    });
  }

  Map<String, dynamic> _buildContentMap() {
    final key = _selectedDocType?.formTemplateKey;
    final map = <String, dynamic>{};

    if (key == 'leave_application') {
      map['leave_type'] = _leaveType;
      map['start_date'] = _startDate?.toIso8601String().split('T').first;
      map['end_date'] = _endDate?.toIso8601String().split('T').first;
      map['days'] = double.tryParse(_leaveDaysController.text) ?? 1.0;
      map['reason'] = _leaveReasonController.text.trim();
    } else if (key == 'expense_report') {
      map['total_amount'] = num.tryParse(_amountController.text.replaceAll(',', '').trim()) ?? 0;
      map['amount'] = map['total_amount'];
      map['purpose'] = _purposeController.text.trim();
    } else if (key == 'purchase_order') {
      map['total_amount'] = num.tryParse(_amountController.text.replaceAll(',', '').trim()) ?? 0;
      map['amount'] = map['total_amount'];
      map['vendor'] = _vendorController.text.trim();
      map['purpose'] = _purposeController.text.trim();
    } else {
      map['body'] = _generalContentController.text.trim();
      final amt = num.tryParse(_amountController.text.replaceAll(',', '').trim());
      if (amt != null) map['amount'] = amt;
    }
    return map;
  }

  Future<void> _handleSave({required bool isDirectSubmit}) async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedDocType == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('문서 유형을 선택해 주세요.')),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      final repo = ref.read(approvalRepositoryProvider);
      final content = _buildContentMap();

      final payload = <String, dynamic>{
        'title': _titleController.text.trim(),
        'doc_type': _selectedDocType!.id,
        if (_selectedAssignment != null) 'drafter_assignment': _selectedAssignment!.id,
        'content': content,
      };

      final doc = await repo.createDocument(
        payload,
        filePaths: _attachedFilePaths.isNotEmpty ? _attachedFilePaths : null,
      );

      if (isDirectSubmit) {
        await repo.submitDocument(doc.id);
      }

      ref.invalidate(pendingApprovalsProvider);
      ref.invalidate(draftedApprovalsProvider);
      ref.invalidate(approvedApprovalsProvider);
      ref.invalidate(allApprovalsProvider);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(isDirectSubmit ? '결재가 성공적으로 상신되었습니다.' : '문서가 임시저장되었습니다.'),
            backgroundColor: context.colors.success,
          ),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSubmitting = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('처리 중 오류가 발생했습니다: $e'), backgroundColor: context.colors.error),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final assignmentsAsync = ref.watch(myAssignmentsProvider);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        title: Text(
          '새 결재 기안',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.w800,
            color: context.colors.textPrimary,
          ),
        ),
        backgroundColor: context.colors.bgCard,
        elevation: 0,
      ),
      body: assignmentsAsync.when(
        data: (assignments) => _buildForm(context, assignments),
        loading: () => const LoadingShimmer(itemCount: 5, itemHeight: 80),
        error: (e, _) => Center(child: Text('보직 정보를 불러올 수 없습니다: $e')),
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
        ),
        child: SafeArea(
          child: Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 46,
                  child: OutlinedButton(
                    onPressed: _isSubmitting ? null : () => _handleSave(isDirectSubmit: false),
                    style: OutlinedButton.styleFrom(
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      side: BorderSide(color: context.colors.border),
                    ),
                    child: const Text('임시저장', style: TextStyle(fontWeight: FontWeight.w700)),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                flex: 2,
                child: SizedBox(
                  height: 46,
                  child: ElevatedButton.icon(
                    onPressed: _isSubmitting ? null : () => _handleSave(isDirectSubmit: true),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: context.colors.accentApproval,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      elevation: 0,
                    ),
                    icon: _isSubmitting
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Icon(Icons.send_rounded, color: Colors.white, size: 18),
                    label: const Text(
                      '결재 상신',
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildForm(BuildContext context, List<StaffAssignmentItemModel> assignments) {
    if (_selectedAssignment == null && assignments.isNotEmpty) {
      _selectedAssignment = assignments.where((a) => a.isPrimary).firstOrNull ?? assignments.first;
    }

    final docTypesAsync = ref.watch(forDraftDocTypesProvider(_selectedAssignment?.id));

    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── 1. 기안 보직 선택 ───────────────────────────────────────
            _buildSectionCard(
              context,
              title: '기안자 정보',
              icon: Icons.person_pin_circle_outlined,
              child: DropdownButtonFormField<StaffAssignmentItemModel>(
                value: _selectedAssignment,
                decoration: _inputDecoration(context, '기안 보직'),
                items: assignments.map((a) {
                  final primary = a.isPrimary ? '[주]' : '[겸]';
                  final label = '$primary ${a.departmentName ?? ''} ${a.dutyName ?? a.positionName ?? ''}'.trim();
                  return DropdownMenuItem(value: a, child: Text(label, style: const TextStyle(fontSize: 13)));
                }).toList(),
                onChanged: (val) {
                  setState(() {
                    _selectedAssignment = val;
                    _selectedDocType = null;
                  });
                  _updateRoutePreview();
                },
              ),
            ),
            const SizedBox(height: 14),

            // ── 2. 문서 유형 선택 ───────────────────────────────────────
            _buildSectionCard(
              context,
              title: '결재 문서 양식',
              icon: Icons.category_outlined,
              child: docTypesAsync.when(
                data: (docTypes) {
                  return DropdownButtonFormField<DocumentTypeModel>(
                    value: _selectedDocType,
                    decoration: _inputDecoration(context, '문서 유형 선택'),
                    items: docTypes.map((dt) {
                      final cat = dt.categoryName != null ? '[${dt.categoryName}] ' : '';
                      return DropdownMenuItem(
                        value: dt,
                        child: Text('$cat${dt.name}', style: const TextStyle(fontSize: 13)),
                      );
                    }).toList(),
                    onChanged: (val) {
                      setState(() => _selectedDocType = val);
                      _updateRoutePreview();
                    },
                    validator: (v) => v == null ? '문서 유형을 선택하세요' : null,
                  );
                },
                loading: () => const LinearProgressIndicator(),
                error: (e, _) => Text('문서 유형 로드 실패: $e'),
              ),
            ),
            const SizedBox(height: 14),

            // ── 3. 문서 기본 정보 및 본문 ─────────────────────────────
            _buildSectionCard(
              context,
              title: '문서 내용 작성',
              icon: Icons.edit_note_rounded,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // 제목
                  TextFormField(
                    controller: _titleController,
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                    decoration: _inputDecoration(context, '문서 제목 (필수)'),
                    validator: (v) => (v == null || v.trim().isEmpty) ? '제목을 입력하세요' : null,
                  ),
                  const SizedBox(height: 12),

                  // 템플릿별 필드 렌더링
                  if (_selectedDocType?.formTemplateKey == 'leave_application')
                    _buildLeaveFormFields(context)
                  else if (_selectedDocType?.formTemplateKey == 'expense_report')
                    _buildExpenseFormFields(context)
                  else if (_selectedDocType?.formTemplateKey == 'purchase_order')
                    _buildPurchaseFormFields(context)
                  else
                    _buildGeneralFormFields(context),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // ── 4. 실시간 결재선 미리보기 ─────────────────────────────
            _buildSectionCard(
              context,
              title: '자동 결재선 미리보기',
              icon: Icons.alt_route_rounded,
              child: _buildRoutePreviewWidget(context),
            ),
            const SizedBox(height: 14),

            // ── 5. 첨부파일 ─────────────────────────────────────────────
            _buildSectionCard(
              context,
              title: '첨부파일',
              icon: Icons.attach_file_rounded,
              action: TextButton.icon(
                onPressed: _pickFiles,
                icon: const Icon(Icons.add, size: 16),
                label: const Text('파일 추가', style: TextStyle(fontSize: 12)),
              ),
              child: Column(
                children: [
                  if (_attachedFilePaths.isEmpty)
                    Text('첨부된 파일이 없습니다.', style: TextStyle(fontSize: 12, color: context.colors.textMuted))
                  else
                    for (int i = 0; i < _attachedFilePaths.length; i++)
                      Container(
                        margin: const EdgeInsets.only(bottom: 6),
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        color: context.colors.bgSurface,
                        child: Row(
                          children: [
                            Icon(Icons.insert_drive_file_outlined, size: 16, color: context.colors.textSecond),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _attachedFilePaths[i].split('/').last,
                                style: const TextStyle(fontSize: 12),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.close, size: 16),
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(),
                              onPressed: () => _removeFile(i),
                            ),
                          ],
                        ),
                      ),
                ],
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildLeaveFormFields(BuildContext context) {
    return Column(
      children: [
        DropdownButtonFormField<String>(
          value: _leaveType,
          decoration: _inputDecoration(context, '휴가 구분'),
          items: const [
            DropdownMenuItem(value: '연차', child: Text('연차')),
            DropdownMenuItem(value: '반차', child: Text('반차')),
            DropdownMenuItem(value: '경조사', child: Text('경조사')),
            DropdownMenuItem(value: '병가', child: Text('병가')),
            DropdownMenuItem(value: '공가', child: Text('공가')),
            DropdownMenuItem(value: '기타', child: Text('기타')),
          ],
          onChanged: (v) => setState(() => _leaveType = v ?? '연차'),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _startDate ?? DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _startDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _startDate != null ? '시작: ${_startDate!.toIso8601String().split('T').first}' : '시작일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _endDate ?? (_startDate ?? DateTime.now()),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _endDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _endDate != null ? '종료: ${_endDate!.toIso8601String().split('T').first}' : '종료일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _leaveDaysController,
          keyboardType: TextInputType.number,
          decoration: _inputDecoration(context, '휴가 일수 (예: 1.0, 0.5)'),
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _leaveReasonController,
          maxLines: 3,
          decoration: _inputDecoration(context, '휴가 사유'),
        ),
      ],
    );
  }

  Widget _buildExpenseFormFields(BuildContext context) {
    return Column(
      children: [
        TextFormField(
          controller: _amountController,
          keyboardType: TextInputType.number,
          decoration: _inputDecoration(context, '총 지출 금액 (원)'),
          onChanged: (_) => _updateRoutePreview(),
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _purposeController,
          maxLines: 3,
          decoration: _inputDecoration(context, '지출 목적 및 상세 내역'),
        ),
      ],
    );
  }

  Widget _buildPurchaseFormFields(BuildContext context) {
    return Column(
      children: [
        TextFormField(
          controller: _amountController,
          keyboardType: TextInputType.number,
          decoration: _inputDecoration(context, '품의 금액 (원)'),
          onChanged: (_) => _updateRoutePreview(),
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _vendorController,
          decoration: _inputDecoration(context, '거래처 / 공급업체'),
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _purposeController,
          maxLines: 3,
          decoration: _inputDecoration(context, '구매 목적 및 품목 내역'),
        ),
      ],
    );
  }

  Widget _buildGeneralFormFields(BuildContext context) {
    return Column(
      children: [
        TextFormField(
          controller: _amountController,
          keyboardType: TextInputType.number,
          decoration: _inputDecoration(context, '관련 금액 (선택 사항)'),
          onChanged: (_) => _updateRoutePreview(),
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _generalContentController,
          maxLines: 5,
          decoration: _inputDecoration(context, '품의/기안 상세 내용'),
        ),
      ],
    );
  }

  Widget _buildRoutePreviewWidget(BuildContext context) {
    if (_isPreviewLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 12),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      );
    }
    if (_selectedDocType == null) {
      return Text('문서 유형을 선택하면 결재선이 자동 계산됩니다.',
          style: TextStyle(fontSize: 12, color: context.colors.textMuted));
    }
    if (_previewSteps.isEmpty) {
      return Text('자동 생성된 결재선이 없습니다. (단독 전결 또는 즉시 승인)',
          style: TextStyle(fontSize: 12, color: context.colors.textMuted));
    }

    return Column(
      children: [
        for (int i = 0; i < _previewSteps.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Row(
              children: [
                Container(
                  width: 20,
                  height: 20,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: context.colors.accentApproval.withAlpha(30),
                    border: Border.all(color: context.colors.accentApproval, width: 0.8),
                  ),
                  child: Text('${i + 1}',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: context.colors.accentApprovalDeep)),
                ),
                const SizedBox(width: 8),
                Text(_previewSteps[i].roleLabel,
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: context.colors.textPrimary)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    _previewSteps[i].approvers.map((u) => u.username).join(', '),
                    style: TextStyle(fontSize: 11.5, color: context.colors.textSecond),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildSectionCard(
    BuildContext context, {
    required String title,
    required IconData icon,
    required Widget child,
    Widget? action,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 15, color: context.colors.accentApproval),
              const SizedBox(width: 6),
              Text(title, style: AppTextStyles.titleSm.copyWith(fontWeight: FontWeight.w700)),
              const Spacer(),
              if (action != null) action,
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }

  InputDecoration _inputDecoration(BuildContext context, String label) {
    return InputDecoration(
      labelText: label,
      labelStyle: TextStyle(fontSize: 12.5, color: context.colors.textMuted),
      filled: true,
      fillColor: context.colors.bgSurface,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: context.colors.border, width: 0.8),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: context.colors.border, width: 0.8),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: context.colors.accentApproval, width: 1.2),
      ),
    );
  }
}
