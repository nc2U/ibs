import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/sales_models.dart';
import '../../data/sales_repository.dart';
import '../../providers/sales_provider.dart';

/// 수수료 정책 등록 / 수정 바텀시트 열기 함수
void showPolicyFormSheet(
  BuildContext context, {
  required int projectId,
  CommissionPolicyModel? existingPolicy,
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
      child: PolicyFormSheet(
        projectId: projectId,
        existingPolicy: existingPolicy,
      ),
    ),
  );
}

class PolicyFormSheet extends ConsumerStatefulWidget {
  final int projectId;
  final CommissionPolicyModel? existingPolicy;

  const PolicyFormSheet({
    super.key,
    required this.projectId,
    this.existingPolicy,
  });

  @override
  ConsumerState<PolicyFormSheet> createState() => _PolicyFormSheetState();
}

class _PolicyFormSheetState extends ConsumerState<PolicyFormSheet> {
  final _formKey = GlobalKey<FormState>();

  late final TextEditingController _nameController;
  late final TextEditingController _agentFeeController;
  late final TextEditingController _leaderFeeController;
  late final TextEditingController _directorFeeController;
  late final TextEditingController _agencyFeeController;

  int? _selectedOrderGroupId;
  int? _selectedUnitTypeId;
  String _payCondition = '1';
  bool _isActive = true;
  DateTime? _startDate;
  DateTime? _endDate;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    final p = widget.existingPolicy;
    _nameController = TextEditingController(text: p?.name ?? '');
    _agentFeeController = TextEditingController(
        text: p != null ? NumberFormat('#,###').format(p.agentFee) : '0');
    _leaderFeeController = TextEditingController(
        text: p != null ? NumberFormat('#,###').format(p.leaderFee) : '0');
    _directorFeeController = TextEditingController(
        text: p != null ? NumberFormat('#,###').format(p.directorFee) : '0');
    _agencyFeeController = TextEditingController(
        text: p != null ? NumberFormat('#,###').format(p.agencyFee) : '0');

    _selectedOrderGroupId = p?.orderGroup;
    _selectedUnitTypeId = p?.unitType;
    _payCondition = p?.payCondition ?? '1';
    _isActive = p?.isActive ?? true;

    if (p != null && p.startDate.isNotEmpty) {
      _startDate = DateTime.tryParse(p.startDate);
    } else {
      _startDate = DateTime.now();
    }

    if (p?.endDate != null && p!.endDate!.isNotEmpty) {
      _endDate = DateTime.tryParse(p.endDate!);
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _agentFeeController.dispose();
    _leaderFeeController.dispose();
    _directorFeeController.dispose();
    _agencyFeeController.dispose();
    super.dispose();
  }

  int _parseFee(String text) {
    final clean = text.replaceAll(RegExp(r'[^0-9]'), '');
    return int.tryParse(clean) ?? 0;
  }

  int get _totalFee {
    return _parseFee(_agentFeeController.text) +
        _parseFee(_leaderFeeController.text) +
        _parseFee(_directorFeeController.text) +
        _parseFee(_agencyFeeController.text);
  }

  Future<void> _selectDate(BuildContext context, bool isStart) async {
    final initial = isStart
        ? (_startDate ?? DateTime.now())
        : (_endDate ?? _startDate ?? DateTime.now());

    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
      builder: (ctx, child) {
        return Theme(
          data: Theme.of(ctx).copyWith(
            colorScheme: ColorScheme.light(
              primary: const Color(0xFFEC4899),
              onPrimary: Colors.white,
              surface: context.colors.bgCard,
              onSurface: context.colors.textPrimary,
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      setState(() {
        if (isStart) {
          _startDate = picked;
        } else {
          _endDate = picked;
        }
      });
    }
  }

  Future<void> _handleSave() async {
    if (!_formKey.currentState!.validate()) return;
    if (_startDate == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('적용 시작일을 선택해 주세요.')),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final repository = ref.read(salesRepositoryProvider);
      final startStr = DateFormat('yyyy-MM-dd').format(_startDate!);
      final endStr = _endDate != null ? DateFormat('yyyy-MM-dd').format(_endDate!) : null;

      final payload = <String, dynamic>{
        'project': widget.projectId,
        'name': _nameController.text.trim(),
        'order_group': _selectedOrderGroupId,
        'unit_type': _selectedUnitTypeId,
        'agent_fee': _parseFee(_agentFeeController.text),
        'leader_fee': _parseFee(_leaderFeeController.text),
        'director_fee': _parseFee(_directorFeeController.text),
        'agency_fee': _parseFee(_agencyFeeController.text),
        'pay_condition': _payCondition,
        'start_date': startStr,
        'end_date': endStr,
        'is_active': _isActive,
      };

      if (widget.existingPolicy != null) {
        await repository.updateCommissionPolicy(widget.existingPolicy!.id, payload);
      } else {
        await repository.createCommissionPolicy(payload);
      }

      ref.invalidate(salesPoliciesProvider);

      if (mounted) {
        Navigator.of(context).pop(true);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              widget.existingPolicy != null
                  ? '수수료 정책이 수정되었습니다.'
                  : '신규 수수료 정책이 등록되었습니다.',
            ),
            backgroundColor: const Color(0xFFEC4899),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('저장 중 오류가 발생했습니다: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _handleDelete() async {
    final policy = widget.existingPolicy;
    if (policy == null) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Text(
          '정책 삭제 확인',
          style: AppTextStyles.titleSm.copyWith(
            color: context.colors.textPrimary,
            fontWeight: FontWeight.bold,
          ),
        ),
        content: Text(
          '\'${policy.name}\' 수수료 정책을 삭제하시겠습니까?\n이미 계약에 매핑된 경우 주의가 필요합니다.',
          style: AppTextStyles.bodySecond.copyWith(color: context.colors.textSecond),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: const Color(0xFFEF4444),
              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('삭제'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      setState(() => _isSubmitting = true);
      try {
        final repository = ref.read(salesRepositoryProvider);
        await repository.deleteCommissionPolicy(policy.id);
        ref.invalidate(salesPoliciesProvider);

        if (mounted) {
          Navigator.of(context).pop(true);
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('수수료 정책이 삭제되었습니다.'),
              backgroundColor: Color(0xFFEF4444),
            ),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('삭제 중 오류가 발생했습니다: $e'),
              backgroundColor: context.colors.error,
            ),
          );
        }
      } finally {
        if (mounted) {
          setState(() => _isSubmitting = false);
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.existingPolicy != null;
    final orderGroups = ref.watch(orderGroupsProvider).valueOrNull ?? [];
    final unitTypes = ref.watch(unitTypesProvider).valueOrNull ?? [];
    final total = _totalFee;

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.88,
      ),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 상단 헤더
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(
                border: Border(bottom: BorderSide(color: context.colors.border, width: 0.8)),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.rule_folder_outlined,
                    size: 20,
                    color: Color(0xFFEC4899),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    isEdit ? '수수료 정책 (R값) 수정' : '신규 수수료 정책 등록',
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close, size: 20),
                    color: context.colors.textMuted,
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),

            // 폼 스크롤 바디
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 1. 정책명 & 활성 상태 스위치
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: _nameController,
                            style: const TextStyle(fontSize: 13),
                            decoration: const InputDecoration(
                              labelText: '정책 명칭 *',
                              hintText: '예: 84A 정규 분양 수수료 기준',
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                              isDense: true,
                            ),
                            validator: (val) {
                              if (val == null || val.trim().isEmpty) {
                                return '정책 명칭을 입력해 주세요.';
                              }
                              return null;
                            },
                          ),
                        ),
                        const SizedBox(width: 12),
                        InkWell(
                          onTap: () => setState(() => _isActive = !_isActive),
                          child: Container(
                            height: 48,
                            padding: const EdgeInsets.symmetric(horizontal: 10),
                            decoration: BoxDecoration(
                              color: _isActive
                                  ? const Color(0xFF10B981).withAlpha(20)
                                  : context.colors.bgSurface,
                              border: Border.all(
                                color: _isActive
                                    ? const Color(0xFF10B981)
                                    : context.colors.border,
                                width: 0.8,
                              ),
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  _isActive ? Icons.check_circle : Icons.pause_circle_outline,
                                  size: 16,
                                  color: _isActive
                                      ? const Color(0xFF10B981)
                                      : context.colors.textMuted,
                                ),
                                const SizedBox(width: 5),
                                Text(
                                  _isActive ? '활성' : '비활성',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: _isActive
                                        ? const Color(0xFF10B981)
                                        : context.colors.textMuted,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // 2. 적용 대상 (차수 & 타입)
                    Text(
                      '적용 대상 (미지정 시 전체 공통 적용)',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        // 공급 차수
                        Expanded(
                          child: DropdownButtonFormField<int?>(
                            initialValue: _selectedOrderGroupId,
                            style: TextStyle(fontSize: 12.5, color: context.colors.textPrimary),
                            decoration: const InputDecoration(
                              labelText: '공급 차수',
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                              isDense: true,
                            ),
                            items: [
                              const DropdownMenuItem<int?>(
                                value: null,
                                child: Text('전체 차수 공통'),
                              ),
                              ...orderGroups.map(
                                (og) => DropdownMenuItem<int?>(
                                  value: og.id,
                                  child: Text(og.name),
                                ),
                              ),
                            ],
                            onChanged: (val) => setState(() => _selectedOrderGroupId = val),
                          ),
                        ),
                        const SizedBox(width: 8),
                        // 유니트 타입
                        Expanded(
                          child: DropdownButtonFormField<int?>(
                            initialValue: _selectedUnitTypeId,
                            style: TextStyle(fontSize: 12.5, color: context.colors.textPrimary),
                            decoration: const InputDecoration(
                              labelText: '유니트 타입',
                              border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                              isDense: true,
                            ),
                            items: [
                              const DropdownMenuItem<int?>(
                                value: null,
                                child: Text('전체 타입 공통'),
                              ),
                              ...unitTypes.map(
                                (t) => DropdownMenuItem<int?>(
                                  value: t.id,
                                  child: Text(t.name),
                                ),
                              ),
                            ],
                            onChanged: (val) => setState(() => _selectedUnitTypeId = val),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // 3. 실시간 건당 총 수수료 합산 프리뷰 배너
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFEC4899).withAlpha(15),
                        border: Border.all(
                          color: const Color(0xFFEC4899).withAlpha(60),
                          width: 1,
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                '건당 총 수수료 (합계)',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textSecond,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              Text(
                                '${NumberFormat('#,###').format(total)}원',
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: Color(0xFFDB2777),
                                ),
                              ),
                            ],
                          ),
                          if (total > 0) ...[
                            const SizedBox(height: 6),
                            Row(
                              children: [
                                _buildFeeRatioChip(
                                  '상담사',
                                  _parseFee(_agentFeeController.text),
                                  total,
                                  const Color(0xFF38BDF8),
                                ),
                                const SizedBox(width: 4),
                                _buildFeeRatioChip(
                                  '팀장',
                                  _parseFee(_leaderFeeController.text),
                                  total,
                                  const Color(0xFF8B5CF6),
                                ),
                                const SizedBox(width: 4),
                                _buildFeeRatioChip(
                                  '본부장',
                                  _parseFee(_directorFeeController.text),
                                  total,
                                  const Color(0xFFF59E0B),
                                ),
                                const SizedBox(width: 4),
                                _buildFeeRatioChip(
                                  '대행사',
                                  _parseFee(_agencyFeeController.text),
                                  total,
                                  const Color(0xFF10B981),
                                ),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // 4. 직책별 수수료 입력 필드 4종
                    Text(
                      '직책별 건당 지급 기준 (원)',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),

                    // 상담사 & 팀장
                    Row(
                      children: [
                        Expanded(
                          child: _buildFeeInputField(
                            controller: _agentFeeController,
                            label: '상담사 fee',
                            accentColor: const Color(0xFF38BDF8),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: _buildFeeInputField(
                            controller: _leaderFeeController,
                            label: '팀장 fee',
                            accentColor: const Color(0xFF8B5CF6),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),

                    // 본부장 & 대행사
                    Row(
                      children: [
                        Expanded(
                          child: _buildFeeInputField(
                            controller: _directorFeeController,
                            label: '본부장 fee',
                            accentColor: const Color(0xFFF59E0B),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: _buildFeeInputField(
                            controller: _agencyFeeController,
                            label: '대행사 fee',
                            accentColor: const Color(0xFF10B981),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // 5. 지급 조건
                    DropdownButtonFormField<String>(
                      initialValue: _payCondition,
                      style: TextStyle(fontSize: 12.5, color: context.colors.textPrimary),
                      decoration: const InputDecoration(
                        labelText: '지급 조건 *',
                        border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                        isDense: true,
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: '1',
                          child: Text('계약금 100% 완납 시 전액 지급'),
                        ),
                        DropdownMenuItem(
                          value: '2',
                          child: Text('계약금 1차 50%, 2차 완납 50% 분할 지급'),
                        ),
                        DropdownMenuItem(
                          value: '3',
                          child: Text('공급계약 체결 시 전액 지급'),
                        ),
                        DropdownMenuItem(
                          value: '4',
                          child: Text('청약/가계약금 납부 시 선지급'),
                        ),
                      ],
                      onChanged: (val) {
                        if (val != null) setState(() => _payCondition = val);
                      },
                    ),
                    const SizedBox(height: 14),

                    // 6. 적용 기간 (시작일 / 종료일)
                    Row(
                      children: [
                        Expanded(
                          child: InkWell(
                            onTap: () => _selectDate(context, true),
                            child: InputDecorator(
                              decoration: const InputDecoration(
                                labelText: '적용 시작일 *',
                                border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                                isDense: true,
                                suffixIcon: Icon(Icons.calendar_today, size: 16),
                              ),
                              child: Text(
                                _startDate != null
                                    ? DateFormat('yyyy-MM-dd').format(_startDate!)
                                    : '선택',
                                style: const TextStyle(fontSize: 12.5),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: InkWell(
                            onTap: () => _selectDate(context, false),
                            child: InputDecorator(
                              decoration: InputDecoration(
                                labelText: '적용 종료일',
                                border: const OutlineInputBorder(borderRadius: BorderRadius.zero),
                                isDense: true,
                                suffixIcon: _endDate != null
                                    ? IconButton(
                                        icon: const Icon(Icons.clear, size: 16),
                                        onPressed: () => setState(() => _endDate = null),
                                        padding: EdgeInsets.zero,
                                      )
                                    : const Icon(Icons.calendar_today, size: 16),
                              ),
                              child: Text(
                                _endDate != null
                                    ? DateFormat('yyyy-MM-dd').format(_endDate!)
                                    : '종료일 없음 (상시)',
                                style: TextStyle(
                                  fontSize: 12.5,
                                  color: _endDate != null
                                      ? context.colors.textPrimary
                                      : context.colors.textMuted,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                  ],
                ),
              ),
            ),

            // 하단 버튼 영역
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
              ),
              child: Row(
                children: [
                  if (isEdit) ...[
                    OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFFEF4444),
                        side: const BorderSide(color: Color(0xFFEF4444)),
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      ),
                      onPressed: _isSubmitting ? null : _handleDelete,
                      child: const Text('삭제', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                    const SizedBox(width: 8),
                  ],
                  Expanded(
                    child: FilledButton(
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFFEC4899),
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                      onPressed: _isSubmitting ? null : _handleSave,
                      child: _isSubmitting
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : Text(
                              isEdit ? '수정 내용 저장' : '수수료 정책 등록',
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 13.5,
                              ),
                            ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeeRatioChip(String role, int fee, int total, Color color) {
    final ratio = total > 0 ? ((fee / total) * 100).toStringAsFixed(0) : '0';
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 3),
        decoration: BoxDecoration(
          color: color.withAlpha(20),
          border: Border.all(color: color.withAlpha(60), width: 0.7),
        ),
        child: Text(
          '$role $ratio%',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 9.5,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ),
    );
  }

  Widget _buildFeeInputField({
    required TextEditingController controller,
    required String label,
    required Color accentColor,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: TextInputType.number,
      inputFormatters: [
        FilteringTextInputFormatter.digitsOnly,
      ],
      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(borderRadius: BorderRadius.zero),
        isDense: true,
        suffixText: '원',
        suffixStyle: TextStyle(fontSize: 11, color: context.colors.textMuted),
        prefixIcon: Container(
          width: 8,
          margin: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
          decoration: BoxDecoration(
            color: accentColor,
            borderRadius: BorderRadius.zero,
          ),
        ),
      ),
      onChanged: (val) {
        setState(() {});
      },
    );
  }
}
