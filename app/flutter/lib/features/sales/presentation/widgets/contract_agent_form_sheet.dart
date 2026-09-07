import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/sales_models.dart';
import '../../data/sales_repository.dart';
import '../../providers/sales_provider.dart';

/// 계약 영업 담당자 배정 / 수정 바텀시트 열기 함수
void showContractAgentFormSheet(
  BuildContext context, {
  required int projectId,
  int? initialContractId,
  String? initialContractLabel,
  ContractSalesAgentModel? existingMapping,
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
      child: ContractAgentFormSheet(
        projectId: projectId,
        initialContractId: initialContractId,
        initialContractLabel: initialContractLabel,
        existingMapping: existingMapping,
      ),
    ),
  );
}

class ContractAgentFormSheet extends ConsumerStatefulWidget {
  final int projectId;
  final int? initialContractId;
  final String? initialContractLabel;
  final ContractSalesAgentModel? existingMapping;

  const ContractAgentFormSheet({
    super.key,
    required this.projectId,
    this.initialContractId,
    this.initialContractLabel,
    this.existingMapping,
  });

  @override
  ConsumerState<ContractAgentFormSheet> createState() =>
      _ContractAgentFormSheetState();
}

class _ContractAgentFormSheetState
    extends ConsumerState<ContractAgentFormSheet> {
  final _formKey = GlobalKey<FormState>();

  int? _selectedContractId;
  int? _selectedSalesPersonId;
  int? _selectedPolicyId;
  DateTime? _selectedContractDate;

  final TextEditingController _mgmNameController = TextEditingController();
  final TextEditingController _mgmPhoneController = TextEditingController();
  final TextEditingController _mgmFeeController = TextEditingController();
  final TextEditingController _noteController = TextEditingController();
  final TextEditingController _approvalNoteController = TextEditingController();

  bool _isSettlementApproved = true;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    final mapping = widget.existingMapping;

    if (mapping != null) {
      _selectedContractId = mapping.contract;
      _selectedSalesPersonId = mapping.salesPerson;
      _selectedPolicyId = mapping.policy;
      if (mapping.contractDate != null && mapping.contractDate!.isNotEmpty) {
        _selectedContractDate = DateTime.tryParse(mapping.contractDate!);
      }
      _mgmNameController.text = mapping.mgmName ?? '';
      _mgmPhoneController.text = mapping.mgmPhone ?? '';
      if (mapping.mgmFee > 0) {
        _mgmFeeController.text = mapping.mgmFee.toString();
      }
      _noteController.text = mapping.note ?? '';
      _isSettlementApproved = mapping.isSettlementApproved;
      _approvalNoteController.text = mapping.approvalNote ?? '';
    } else {
      _selectedContractId = widget.initialContractId;
      _selectedContractDate = DateTime.now();
      _isSettlementApproved = true;
    }
  }

  @override
  void dispose() {
    _mgmNameController.dispose();
    _mgmPhoneController.dispose();
    _mgmFeeController.dispose();
    _noteController.dispose();
    _approvalNoteController.dispose();
    super.dispose();
  }

  Future<void> _selectDate() async {
    final now = DateTime.now();
    final initialDate = _selectedContractDate ?? now;
    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
      builder: (ctx, child) {
        return Theme(
          data: Theme.of(ctx).copyWith(
            colorScheme: ColorScheme.light(
              primary: const Color(0xFF8B5CF6),
              onPrimary: Colors.white,
              onSurface: context.colors.textPrimary,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() => _selectedContractDate = picked);
    }
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedContractId == null) {
      _showToast('분양 계약을 선택해 주세요.');
      return;
    }
    if (_selectedSalesPersonId == null) {
      _showToast('담당 영업직원(상담사)을 선택해 주세요.');
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final repository = ref.read(salesRepositoryProvider);
      final fee = int.tryParse(_mgmFeeController.text.replaceAll(',', '')) ?? 0;
      final dateStr = _selectedContractDate != null
          ? DateFormat('yyyy-MM-dd').format(_selectedContractDate!)
          : null;

      final payload = <String, dynamic>{
        'contract': _selectedContractId,
        'sales_person': _selectedSalesPersonId,
        'policy': _selectedPolicyId,
        'contract_date': dateStr,
        'mgm_name': _mgmNameController.text.trim(),
        'mgm_phone': _mgmPhoneController.text.trim(),
        'mgm_fee': fee,
        'note': _noteController.text.trim(),
        'is_settlement_approved': _isSettlementApproved,
        'approval_note': _approvalNoteController.text.trim(),
      };

      if (widget.existingMapping != null) {
        await repository.updateContractSalesAgent(
          widget.existingMapping!.id,
          payload,
        );
        _showToast('영업 담당자 매핑이 수정되었습니다.');
      } else {
        await repository.createContractSalesAgent(payload);
        _showToast('영업 담당자가 성공적으로 배정되었습니다.');
      }

      // 프로바이더 갱신
      ref.invalidate(rawContractSalesAgentsProvider);

      if (mounted) {
        Navigator.of(context).pop();
      }
    } catch (e) {
      _showToast('저장 중 오류가 발생했습니다: $e');
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _handleDelete() async {
    if (widget.existingMapping == null) return;

    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: const Text('배정 해제 확인', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: const Text('해당 계약의 영업 담당자 배정을 해제(삭제)하시겠습니까?'),
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
            child: const Text('해제'),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    setState(() => _isSubmitting = true);
    try {
      final repository = ref.read(salesRepositoryProvider);
      await repository.deleteContractSalesAgent(widget.existingMapping!.id);
      _showToast('영업 담당자 배정이 해제되었습니다.');
      ref.invalidate(rawContractSalesAgentsProvider);
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
    final isEditing = widget.existingMapping != null;
    final contractsAsync = ref.watch(simpleContractsProvider);
    final personsAsync = ref.watch(salesPersonsProvider);
    final policiesAsync = ref.watch(salesPoliciesProvider);

    final contracts = contractsAsync.valueOrNull ?? [];
    final persons = personsAsync.valueOrNull ?? [];
    final policies = policiesAsync.valueOrNull ?? [];

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.85,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // ── 드래그 핸들 ──────────────────────────────────────────
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

          // ── 헤더 ────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: Row(
              children: [
                Icon(
                  isEditing ? Icons.edit_note_rounded : Icons.person_add_alt_1_rounded,
                  size: 20,
                  color: const Color(0xFF8B5CF6),
                ),
                const SizedBox(width: 8),
                Text(
                  isEditing ? '영업 담당자 배정 수정' : '영업 담당자 신규 배정',
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

          // ── 입력 폼 스크롤 영역 ──────────────────────────────────
          Flexible(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 1. 대상 분양 계약
                    Text(
                      '대상 분양 계약 *',
                      style: AppTextStyles.label.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    if (widget.initialContractLabel != null)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          border: Border.all(color: context.colors.border),
                        ),
                        child: Text(
                          widget.initialContractLabel!,
                          style: AppTextStyles.bodySecond.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      )
                    else
                      DropdownButtonFormField<int>(
                        initialValue: _selectedContractId,
                        decoration: InputDecoration(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                          border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                          hintText: '계약 건 선택',
                        ),
                        isExpanded: true,
                        items: contracts.map((c) {
                          return DropdownMenuItem<int>(
                            value: c.value,
                            child: Text(c.label, style: const TextStyle(fontSize: 13)),
                          );
                        }).toList(),
                        onChanged: (val) => setState(() => _selectedContractId = val),
                        validator: (val) => val == null ? '계약을 선택해 주세요.' : null,
                      ),
                    const SizedBox(height: 16),

                    // 2. 담당 영업직원 (상담사)
                    Text(
                      '담당 영업직원 (상담사) *',
                      style: AppTextStyles.label.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<int>(
                      initialValue: _selectedSalesPersonId,
                      decoration: InputDecoration(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                        hintText: '상담사 선택',
                      ),
                      isExpanded: true,
                      items: persons.map((p) {
                        final teamStr = p.teamName != null ? ' (${p.teamName})' : '';
                        return DropdownMenuItem<int>(
                          value: p.id,
                          child: Text('${p.name}$teamStr', style: const TextStyle(fontSize: 13)),
                        );
                      }).toList(),
                      onChanged: (val) => setState(() => _selectedSalesPersonId = val),
                      validator: (val) => val == null ? '담당 영업직원을 선택해 주세요.' : null,
                    ),
                    const SizedBox(height: 16),

                    // 3. 적용 수수료 정책
                    Text(
                      '적용 수수료 정책 (선택)',
                      style: AppTextStyles.label.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<int?>(
                      initialValue: _selectedPolicyId,
                      decoration: InputDecoration(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                        hintText: '기본 정책 적용 (미지정)',
                      ),
                      isExpanded: true,
                      items: [
                        const DropdownMenuItem<int?>(
                          value: null,
                          child: Text('기본 정책 자동 산출', style: TextStyle(fontSize: 13, color: Colors.grey)),
                        ),
                        ...policies.map((pol) {
                          return DropdownMenuItem<int?>(
                            value: pol.id,
                            child: Text(pol.name, style: const TextStyle(fontSize: 13)),
                          );
                        }),
                      ],
                      onChanged: (val) => setState(() => _selectedPolicyId = val),
                    ),
                    const SizedBox(height: 16),

                    // 4. 성과 인정일
                    Text(
                      '영업 성과 인정일',
                      style: AppTextStyles.label.copyWith(
                        color: context.colors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    InkWell(
                      onTap: _selectDate,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          border: Border.all(color: context.colors.border),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.calendar_today_rounded, size: 16, color: context.colors.textMuted),
                            const SizedBox(width: 8),
                            Text(
                              _selectedContractDate != null
                                  ? DateFormat('yyyy-MM-dd').format(_selectedContractDate!)
                                  : '일자 선택',
                              style: AppTextStyles.bodySecond.copyWith(
                                color: _selectedContractDate != null
                                    ? context.colors.textPrimary
                                    : context.colors.textMuted,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // ── MGM 소개 정보 구분선 ──────────────────────────
                    Row(
                      children: [
                        Container(width: 3, height: 12, color: const Color(0xFF06B6D4), margin: const EdgeInsets.only(right: 6)),
                        Text(
                          'MGM (중개사 소개) 정보',
                          style: AppTextStyles.label.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),

                    // MGM 성명 & 연락처
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: _mgmNameController,
                            decoration: InputDecoration(
                              labelText: '중개사/MGM 성명',
                              contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                            ),
                            style: const TextStyle(fontSize: 13),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: TextFormField(
                            controller: _mgmPhoneController,
                            keyboardType: TextInputType.phone,
                            decoration: InputDecoration(
                              labelText: 'MGM 연락처',
                              contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                            ),
                            style: const TextStyle(fontSize: 13),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),

                    // MGM 수수료
                    TextFormField(
                      controller: _mgmFeeController,
                      keyboardType: TextInputType.number,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                      decoration: InputDecoration(
                        labelText: 'MGM 지급 수수료 (원)',
                        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                        suffixText: '원',
                      ),
                      style: const TextStyle(fontSize: 13),
                    ),
                    const SizedBox(height: 16),

                    // 5. 비고
                    TextFormField(
                      controller: _noteController,
                      maxLines: 2,
                      decoration: InputDecoration(
                        labelText: '비고 / 특이사항',
                        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.zero, borderSide: BorderSide(color: context.colors.border)),
                      ),
                      style: const TextStyle(fontSize: 13),
                    ),
                    const SizedBox(height: 20),

                    // ── 6. 수수료 정산 승인 / 보류 ──────────────────────────
                    Row(
                      children: [
                        Container(width: 3, height: 12, color: const Color(0xFF10B981), margin: const EdgeInsets.only(right: 6)),
                        Text(
                          '수수료 정산 승인 관리',
                          style: AppTextStyles.label.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),

                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: _isSettlementApproved
                            ? const Color(0xFF10B981).withAlpha(15)
                            : const Color(0xFFEF4444).withAlpha(15),
                        border: Border.all(
                          color: _isSettlementApproved
                              ? const Color(0xFF10B981).withAlpha(80)
                              : const Color(0xFFEF4444).withAlpha(80),
                          width: 0.8,
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                _isSettlementApproved ? Icons.check_circle : Icons.error_outline,
                                size: 18,
                                color: _isSettlementApproved
                                    ? const Color(0xFF10B981)
                                    : const Color(0xFFEF4444),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  _isSettlementApproved ? '정산 승인 대상' : '정산 보류 (미승인)',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 13,
                                    color: _isSettlementApproved
                                        ? const Color(0xFF10B981)
                                        : const Color(0xFFEF4444),
                                  ),
                                ),
                              ),
                              Switch.adaptive(
                                value: _isSettlementApproved,
                                activeTrackColor: const Color(0xFF10B981),
                                onChanged: (val) {
                                  setState(() => _isSettlementApproved = val);
                                },
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _isSettlementApproved
                                ? '계약금 및 서류 완비 확인 건으로, 정산 실행 시 정상 집계됩니다.'
                                : '서류 미비/분납 등 사유로 정산 계산 대상에서 자동으로 제외됩니다.',
                            style: TextStyle(
                              fontSize: 11,
                              color: context.colors.textSecond,
                            ),
                          ),
                          if (!_isSettlementApproved) ...[
                            const SizedBox(height: 10),
                            TextFormField(
                              controller: _approvalNoteController,
                              maxLines: 2,
                              decoration: InputDecoration(
                                labelText: '정산 보류 사유 (선택 또는 권장)',
                                hintText: '예: 계약금 2차 분납 500만원 미납, 인감 미징구 등',
                                hintStyle: TextStyle(fontSize: 11, color: context.colors.textMuted),
                                contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.zero,
                                  borderSide: BorderSide(color: const Color(0xFFEF4444).withAlpha(80)),
                                ),
                              ),
                              style: const TextStyle(fontSize: 12),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // ── 하단 액션 버튼 바 ────────────────────────────────────
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
                    child: const Text('배정 해제'),
                  ),
                if (isEditing) const SizedBox(width: 10),
                Expanded(
                  child: FilledButton(
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF8B5CF6),
                      foregroundColor: Colors.white,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    onPressed: _isSubmitting ? null : _handleSubmit,
                    child: _isSubmitting
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                          )
                        : Text(
                            isEditing ? '수정 저장' : '배정 완료',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                          ),
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
