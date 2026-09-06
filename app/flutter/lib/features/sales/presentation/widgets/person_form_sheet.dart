import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/sales_models.dart';
import '../../data/sales_repository.dart';
import '../../providers/sales_provider.dart';
import 'person_document_sheet.dart';

/// 영업 인력 등록 / 수정 바텀시트 열기 함수
void showPersonFormSheet(
  BuildContext context, {
  required int projectId,
  SalesPersonModel? existingPerson,
  int? defaultTeamId,
}) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: context.colors.bgCard,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (ctx) => Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(ctx).viewInsets.bottom,
      ),
      child: PersonFormSheet(
        projectId: projectId,
        existingPerson: existingPerson,
        defaultTeamId: defaultTeamId,
      ),
    ),
  );
}

class PersonFormSheet extends ConsumerStatefulWidget {
  final int projectId;
  final SalesPersonModel? existingPerson;
  final int? defaultTeamId;

  const PersonFormSheet({
    super.key,
    required this.projectId,
    this.existingPerson,
    this.defaultTeamId,
  });

  @override
  ConsumerState<PersonFormSheet> createState() => _PersonFormSheetState();
}

class _PersonFormSheetState extends ConsumerState<PersonFormSheet> {
  final _formKey = GlobalKey<FormState>();

  int? _selectedTeamId;
  String _duty = '1'; // 1: 상담사, 2: 팀장, 3: 본부장, 4: 총괄본부장, 5: 지원/기타
  String _status = '1'; // 1: 위촉(재직), 2: 휴직, 3: 해촉(퇴사)
  String _taxType = '1'; // 1: 3.3% 프리랜서, 2: 4대보험, 3: 기타

  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _idNumberController = TextEditingController();
  final TextEditingController _bankNameController = TextEditingController();
  final TextEditingController _accountNumberController = TextEditingController();
  final TextEditingController _accountHolderController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();

  DateTime? _joinDate;
  DateTime? _quitDate;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    final p = widget.existingPerson;
    if (p != null) {
      _selectedTeamId = p.team;
      _duty = p.duty;
      _status = p.status;
      _taxType = p.taxType;
      _nameController.text = p.name;
      _phoneController.text = p.phone ?? '';
      _idNumberController.text = p.idNumber ?? '';
      _bankNameController.text = p.bankName ?? '';
      _accountNumberController.text = p.accountNumber ?? '';
      _accountHolderController.text = p.accountHolder ?? '';
      _notesController.text = p.notes ?? '';
      if (p.joinDate != null && p.joinDate!.isNotEmpty) {
        _joinDate = DateTime.tryParse(p.joinDate!);
      }
      if (p.quitDate != null && p.quitDate!.isNotEmpty) {
        _quitDate = DateTime.tryParse(p.quitDate!);
      }
    } else {
      _selectedTeamId = widget.defaultTeamId;
      _joinDate = DateTime.now();
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _idNumberController.dispose();
    _bankNameController.dispose();
    _accountNumberController.dispose();
    _accountHolderController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _selectJoinDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _joinDate ?? DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
    );
    if (picked != null) {
      setState(() => _joinDate = picked);
    }
  }

  Future<void> _selectQuitDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _quitDate ?? DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
    );
    if (picked != null) {
      setState(() => _quitDate = picked);
    }
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedTeamId == null) {
      _showToast('소속 팀을 선택해 주세요.');
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final repository = ref.read(salesRepositoryProvider);
      final joinStr = _joinDate != null ? DateFormat('yyyy-MM-dd').format(_joinDate!) : null;
      final quitStr = _quitDate != null ? DateFormat('yyyy-MM-dd').format(_quitDate!) : null;

      final payload = <String, dynamic>{
        'team': _selectedTeamId,
        'name': _nameController.text.trim(),
        'duty': _duty,
        'status': _status,
        'phone': _phoneController.text.trim(),
        'id_number': _idNumberController.text.trim(),
        'tax_type': _taxType,
        'bank_name': _bankNameController.text.trim(),
        'account_number': _accountNumberController.text.trim(),
        'account_holder': _accountHolderController.text.trim(),
        'join_date': joinStr,
        'quit_date': quitStr,
        'notes': _notesController.text.trim(),
      };

      if (widget.existingPerson != null) {
        await repository.updateSalesPerson(widget.existingPerson!.id, payload);
        _showToast('영업 인력 정보가 수정되었습니다.');
      } else {
        await repository.createSalesPerson(payload);
        _showToast('영업 인력이 새로 등록되었습니다.');
      }

      ref.invalidate(salesPersonsProvider);
      ref.invalidate(salesTeamsProvider);

      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      _showToast('저장 중 오류가 발생했습니다: $e');
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  Future<void> _handleDelete() async {
    if (widget.existingPerson == null) return;

    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: const Text('인력 삭제 확인', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: Text("'${widget.existingPerson!.name}' 인력 정보를 삭제하시겠습니까?\n(기 체결된 계약 실적이 있는 경우 삭제가 제한될 수 있습니다)"),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('취소'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: context.colors.error,
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('삭제'),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    setState(() => _isSubmitting = true);
    try {
      final repository = ref.read(salesRepositoryProvider);
      await repository.deleteSalesPerson(widget.existingPerson!.id);
      _showToast('영업 인력이 삭제되었습니다.');
      ref.invalidate(salesPersonsProvider);
      ref.invalidate(salesTeamsProvider);
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      _showToast('삭제 중 오류가 발생했습니다: $e');
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  void _showToast(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message, style: const TextStyle(fontSize: 13)),
        duration: const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isEditing = widget.existingPerson != null;
    final teams = ref.watch(salesTeamsProvider).valueOrNull ?? [];

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.88,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 드래그 핸들
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 10, bottom: 8),
              width: 38,
              height: 4,
              decoration: BoxDecoration(
                color: context.colors.textDisabled,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          // 헤더
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: Row(
              children: [
                Icon(
                  isEditing ? Icons.badge_outlined : Icons.person_add_outlined,
                  size: 20,
                  color: const Color(0xFF6366F1),
                ),
                const SizedBox(width: 8),
                Text(
                  isEditing ? '영업 인력 정보 수정' : '신규 영업 인력 등록',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.close_rounded, size: 20),
                  onPressed: () => Navigator.of(context).pop(),
                  color: context.colors.textMuted,
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // 폼 스크롤 영역
          Flexible(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 1. 성명 & 연락처
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('성명 *', style: AppTextStyles.label.copyWith(color: context.colors.textPrimary, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 6),
                              TextFormField(
                                controller: _nameController,
                                decoration: InputDecoration(
                                  hintText: '상담사 성명',
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                                ),
                                style: const TextStyle(fontSize: 13),
                                validator: (val) => val == null || val.trim().isEmpty ? '성명을 입력해 주세요.' : null,
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('휴대전화 *', style: AppTextStyles.label.copyWith(color: context.colors.textPrimary, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 6),
                              TextFormField(
                                controller: _phoneController,
                                keyboardType: TextInputType.phone,
                                decoration: InputDecoration(
                                  hintText: '010-0000-0000',
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                                ),
                                style: const TextStyle(fontSize: 13),
                                validator: (val) => val == null || val.trim().isEmpty ? '연락처를 입력해 주세요.' : null,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // 2. 소속 팀 & 직책
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('소속 팀 *', style: AppTextStyles.label.copyWith(color: context.colors.textPrimary, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 6),
                              DropdownButtonFormField<int>(
                                initialValue: _selectedTeamId,
                                decoration: InputDecoration(
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                                ),
                                isExpanded: true,
                                hint: const Text('팀 선택', style: TextStyle(fontSize: 12)),
                                items: teams.map((t) {
                                  final agencyStr = t.agencyName != null ? ' [${t.agencyName}]' : '';
                                  return DropdownMenuItem<int>(
                                    value: t.id,
                                    child: Text('${t.name}$agencyStr', style: const TextStyle(fontSize: 12.5)),
                                  );
                                }).toList(),
                                onChanged: (val) => setState(() => _selectedTeamId = val),
                                validator: (val) => val == null ? '팀을 선택해 주세요.' : null,
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('직책 *', style: AppTextStyles.label.copyWith(color: context.colors.textPrimary, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 6),
                              DropdownButtonFormField<String>(
                                initialValue: _duty,
                                decoration: InputDecoration(
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                                ),
                                isExpanded: true,
                                items: const [
                                  DropdownMenuItem(value: '1', child: Text('분양상담사', style: TextStyle(fontSize: 12.5))),
                                  DropdownMenuItem(value: '2', child: Text('팀장', style: TextStyle(fontSize: 12.5))),
                                  DropdownMenuItem(value: '3', child: Text('본부장', style: TextStyle(fontSize: 12.5))),
                                  DropdownMenuItem(value: '4', child: Text('총괄본부장', style: TextStyle(fontSize: 12.5))),
                                  DropdownMenuItem(value: '5', child: Text('지원/기타', style: TextStyle(fontSize: 12.5))),
                                ],
                                onChanged: (val) => setState(() => _duty = val ?? '1'),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // 3. 재직 상태 & 세무 구분
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('활동 상태', style: AppTextStyles.label.copyWith(color: context.colors.textPrimary, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 6),
                              DropdownButtonFormField<String>(
                                initialValue: _status,
                                decoration: InputDecoration(
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                                ),
                                isExpanded: true,
                                items: const [
                                  DropdownMenuItem(value: '1', child: Text('위촉 (재직)', style: TextStyle(fontSize: 12.5, color: Color(0xFF10B981)))),
                                  DropdownMenuItem(value: '2', child: Text('휴직', style: TextStyle(fontSize: 12.5, color: Color(0xFFF59E0B)))),
                                  DropdownMenuItem(value: '3', child: Text('해촉 (퇴사)', style: TextStyle(fontSize: 12.5, color: Colors.grey))),
                                ],
                                onChanged: (val) => setState(() => _status = val ?? '1'),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('세무 구분', style: AppTextStyles.label.copyWith(color: context.colors.textPrimary, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 6),
                              DropdownButtonFormField<String>(
                                initialValue: _taxType,
                                decoration: InputDecoration(
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                                ),
                                isExpanded: true,
                                items: const [
                                  DropdownMenuItem(value: '1', child: Text('3.3% 사업소득', style: TextStyle(fontSize: 12.5))),
                                  DropdownMenuItem(value: '2', child: Text('4대보험 근로소득', style: TextStyle(fontSize: 12.5))),
                                  DropdownMenuItem(value: '3', child: Text('기타 소득', style: TextStyle(fontSize: 12.5))),
                                ],
                                onChanged: (val) => setState(() => _taxType = val ?? '1'),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // 4. 위촉일 & 해촉일
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('위촉일자', style: AppTextStyles.label.copyWith(color: context.colors.textPrimary, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 6),
                              InkWell(
                                onTap: _selectJoinDate,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  decoration: BoxDecoration(border: Border.all(color: context.colors.border)),
                                  child: Row(
                                    children: [
                                      Icon(Icons.calendar_today_rounded, size: 14, color: context.colors.textMuted),
                                      const SizedBox(width: 6),
                                      Text(
                                        _joinDate != null ? DateFormat('yyyy-MM-dd').format(_joinDate!) : '선택',
                                        style: const TextStyle(fontSize: 12.5),
                                      ),
                                    ],
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
                              Text('해촉일자 (퇴사 시)', style: AppTextStyles.label.copyWith(color: context.colors.textPrimary, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 6),
                              InkWell(
                                onTap: _selectQuitDate,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                  decoration: BoxDecoration(border: Border.all(color: context.colors.border)),
                                  child: Row(
                                    children: [
                                      Icon(Icons.calendar_today_rounded, size: 14, color: context.colors.textMuted),
                                      const SizedBox(width: 6),
                                      Text(
                                        _quitDate != null ? DateFormat('yyyy-MM-dd').format(_quitDate!) : '-',
                                        style: TextStyle(fontSize: 12.5, color: _quitDate != null ? context.colors.textPrimary : context.colors.textMuted),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // 5. 금융 계좌 정보
                    Row(
                      children: [
                        Container(width: 3, height: 12, color: const Color(0xFF6366F1), margin: const EdgeInsets.only(right: 6)),
                        Text('수수료 입금 계좌 정보', style: AppTextStyles.label.copyWith(color: context.colors.textPrimary, fontWeight: FontWeight.bold)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: TextFormField(
                            controller: _bankNameController,
                            decoration: InputDecoration(
                              labelText: '은행명',
                              hintText: '예: 국민, 신한',
                              contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                            ),
                            style: const TextStyle(fontSize: 12.5),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          flex: 3,
                          child: TextFormField(
                            controller: _accountNumberController,
                            keyboardType: TextInputType.number,
                            decoration: InputDecoration(
                              labelText: '계좌번호',
                              contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                            ),
                            style: const TextStyle(fontSize: 12.5),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          flex: 2,
                          child: TextFormField(
                            controller: _accountHolderController,
                            decoration: InputDecoration(
                              labelText: '예금주',
                              contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                            ),
                            style: const TextStyle(fontSize: 12.5),
                          ),
                        ),
                      ],
                    ),
                    if (isEditing && widget.existingPerson != null) ...[
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          Container(width: 3, height: 12, color: const Color(0xFF6366F1), margin: const EdgeInsets.only(right: 6)),
                          Text('증빙 서류 관리', style: AppTextStyles.label.copyWith(color: context.colors.textPrimary, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      InkWell(
                        onTap: () => showPersonDocumentSheet(
                          context,
                          person: widget.existingPerson!,
                        ),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                          decoration: BoxDecoration(
                            color: context.colors.bgSurface,
                            border: Border.all(color: const Color(0xFF6366F1).withAlpha(80)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.folder_shared_outlined, size: 18, color: Color(0xFF6366F1)),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  '제출 서류 열람 및 공유 (${widget.existingPerson!.documentsCount}건)',
                                  style: const TextStyle(
                                    fontSize: 12.5,
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFF6366F1),
                                  ),
                                ),
                              ),
                              const Icon(Icons.chevron_right, size: 16, color: Color(0xFF6366F1)),
                            ],
                          ),
                        ),
                      ),
                    ],
                    const SizedBox(height: 14),

                    // 6. 비고
                    TextFormField(
                      controller: _notesController,
                      maxLines: 2,
                      decoration: InputDecoration(
                        labelText: '비고 / 특이사항',
                        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                      ),
                      style: const TextStyle(fontSize: 12.5),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // 하단 버튼 바
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                if (isEditing)
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: context.colors.error,
                      side: BorderSide(color: context.colors.error),
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    ),
                    onPressed: _isSubmitting ? null : _handleDelete,
                    child: const Text('인력 삭제'),
                  ),
                if (isEditing) const SizedBox(width: 10),
                Expanded(
                  child: FilledButton(
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF6366F1),
                      foregroundColor: Colors.white,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    onPressed: _isSubmitting ? null : _handleSubmit,
                    child: _isSubmitting
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                        : Text(isEditing ? '수정 저장' : '등록 완료', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
