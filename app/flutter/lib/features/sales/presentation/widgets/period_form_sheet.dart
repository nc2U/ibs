import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/sales_models.dart';
import '../../data/sales_repository.dart';
import '../../providers/sales_provider.dart';

/// 수수료 정산 회차 등록 / 수정 바텀시트 열기 함수
void showPeriodFormSheet(
  BuildContext context, {
  required int projectId,
  SettlementPeriodModel? existingPeriod,
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
      child: PeriodFormSheet(
        projectId: projectId,
        existingPeriod: existingPeriod,
      ),
    ),
  );
}

class PeriodFormSheet extends ConsumerStatefulWidget {
  final int projectId;
  final SettlementPeriodModel? existingPeriod;

  const PeriodFormSheet({
    super.key,
    required this.projectId,
    this.existingPeriod,
  });

  @override
  ConsumerState<PeriodFormSheet> createState() => _PeriodFormSheetState();
}

class _PeriodFormSheetState extends ConsumerState<PeriodFormSheet> {
  final _formKey = GlobalKey<FormState>();

  late final TextEditingController _titleController;
  DateTime? _startDate;
  DateTime? _endDate;
  DateTime? _payoutDate;
  String _status = '1';
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    final p = widget.existingPeriod;
    final now = DateTime.now();
    _titleController = TextEditingController(
      text: p?.title ??
          '${now.year}년 ${now.month}월 ${now.day <= 15 ? "1회차" : "2회차"} 수수료 정산',
    );

    if (p != null && p.startDate.isNotEmpty) {
      _startDate = DateTime.tryParse(p.startDate);
    } else {
      _startDate = DateTime(now.year, now.month, now.day <= 15 ? 1 : 16);
    }

    if (p != null && p.endDate.isNotEmpty) {
      _endDate = DateTime.tryParse(p.endDate);
    } else {
      if (now.day <= 15) {
        _endDate = DateTime(now.year, now.month, 15);
      } else {
        final lastDay = DateTime(now.year, now.month + 1, 0).day;
        _endDate = DateTime(now.year, now.month, lastDay);
      }
    }

    if (p?.payoutDate != null && p!.payoutDate!.isNotEmpty) {
      _payoutDate = DateTime.tryParse(p.payoutDate!);
    }

    _status = p?.status ?? '1';
  }

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _selectDate(BuildContext context, int type) async {
    // 0: start, 1: end, 2: payout
    final initial = type == 0
        ? (_startDate ?? DateTime.now())
        : (type == 1
            ? (_endDate ?? _startDate ?? DateTime.now())
            : (_payoutDate ?? _endDate ?? DateTime.now()));

    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
      builder: (ctx, child) {
        return Theme(
          data: Theme.of(ctx).copyWith(
            colorScheme: ColorScheme.light(
              primary: const Color(0xFF6366F1),
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
        if (type == 0) {
          _startDate = picked;
          if (_endDate != null && _endDate!.isBefore(_startDate!)) {
            _endDate = _startDate;
          }
        } else if (type == 1) {
          _endDate = picked;
        } else {
          _payoutDate = picked;
        }
      });
    }
  }

  Future<void> _handleSave() async {
    if (!_formKey.currentState!.validate()) return;
    if (_startDate == null || _endDate == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('정산 대상 기간(시작일/종료일)을 설정해 주세요.')),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final repository = ref.read(salesRepositoryProvider);
      final startStr = DateFormat('yyyy-MM-dd').format(_startDate!);
      final endStr = DateFormat('yyyy-MM-dd').format(_endDate!);
      final payoutStr =
          _payoutDate != null ? DateFormat('yyyy-MM-dd').format(_payoutDate!) : null;

      final payload = <String, dynamic>{
        'project': widget.projectId,
        'title': _titleController.text.trim(),
        'start_date': startStr,
        'end_date': endStr,
        'payout_date': payoutStr,
        'status': _status,
      };

      if (widget.existingPeriod != null) {
        await repository.updateSettlementPeriod(widget.existingPeriod!.id, payload);
      } else {
        final newPeriod = await repository.createSettlementPeriod(payload);
        ref.read(selectedPeriodIdProvider.notifier).state = newPeriod.id;
      }

      ref.invalidate(settlementPeriodsProvider);
      ref.invalidate(commissionPayoutsProvider);

      if (mounted) {
        Navigator.of(context).pop(true);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              widget.existingPeriod != null
                  ? '정산 회차 정보가 수정되었습니다.'
                  : '신규 정산 회차가 생성되었습니다.',
            ),
            backgroundColor: const Color(0xFF6366F1),
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
    final period = widget.existingPeriod;
    if (period == null) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        title: Text(
          '정산 회차 삭제',
          style: AppTextStyles.titleSm.copyWith(
            color: context.colors.textPrimary,
            fontWeight: FontWeight.bold,
          ),
        ),
        content: Text(
          '\'${period.title}\' 정산 회차를 삭제하시겠습니까?\n생성된 개인별 지급 명세 및 계약 매핑 내역이 함께 삭제됩니다.',
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
        await repository.deleteSettlementPeriod(period.id);
        ref.read(selectedPeriodIdProvider.notifier).state = null;
        ref.invalidate(settlementPeriodsProvider);
        ref.invalidate(commissionPayoutsProvider);

        if (mounted) {
          Navigator.of(context).pop(true);
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('정산 회차가 삭제되었습니다.'),
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
    final isEdit = widget.existingPeriod != null;

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.85,
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
                    Icons.calendar_month_outlined,
                    size: 20,
                    color: Color(0xFF6366F1),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    isEdit ? '수수료 정산 회차 수정' : '신규 수수료 정산 회차 생성',
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
                    // 1. 회차 명칭
                    TextFormField(
                      controller: _titleController,
                      style: const TextStyle(fontSize: 13),
                      decoration: const InputDecoration(
                        labelText: '정산 회차명 *',
                        hintText: '예: 2026년 9월 1회차 수수료 정산',
                        border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                        isDense: true,
                      ),
                      validator: (val) {
                        if (val == null || val.trim().isEmpty) {
                          return '정산 회차명을 입력해 주세요.';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 14),

                    // 안내 배너
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF6366F1).withAlpha(12),
                        border: Border.all(
                          color: const Color(0xFF6366F1).withAlpha(50),
                          width: 0.8,
                        ),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.info_outline_rounded,
                            size: 16,
                            color: Color(0xFF6366F1),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              '정산 대상 시작일 ~ 종료일 사이에 체결된 분양 계약 실적이 자동으로 집계되어 개인별 인센티브로 산출됩니다.',
                              style: AppTextStyles.caption.copyWith(
                                color: context.colors.textSecond,
                                fontSize: 11.5,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // 2. 정산 대상 기간 (시작일 / 종료일)
                    Text(
                      '정산 대상 실적 기간 *',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Expanded(
                          child: InkWell(
                            onTap: () => _selectDate(context, 0),
                            child: InputDecorator(
                              decoration: const InputDecoration(
                                labelText: '대상 시작일 *',
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
                            onTap: () => _selectDate(context, 1),
                            child: InputDecorator(
                              decoration: const InputDecoration(
                                labelText: '대상 종료일 *',
                                border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                                isDense: true,
                                suffixIcon: Icon(Icons.calendar_today, size: 16),
                              ),
                              child: Text(
                                _endDate != null
                                    ? DateFormat('yyyy-MM-dd').format(_endDate!)
                                    : '선택',
                                style: const TextStyle(fontSize: 12.5),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // 3. 지급 예정일
                    InkWell(
                      onTap: () => _selectDate(context, 2),
                      child: InputDecorator(
                        decoration: InputDecoration(
                          labelText: '지급 예정일',
                          border: const OutlineInputBorder(borderRadius: BorderRadius.zero),
                          isDense: true,
                          suffixIcon: _payoutDate != null
                              ? IconButton(
                                  icon: const Icon(Icons.clear, size: 16),
                                  onPressed: () => setState(() => _payoutDate = null),
                                  padding: EdgeInsets.zero,
                                )
                              : const Icon(Icons.calendar_today, size: 16),
                        ),
                        child: Text(
                          _payoutDate != null
                              ? DateFormat('yyyy-MM-dd').format(_payoutDate!)
                              : '미정 (선택 사항)',
                          style: TextStyle(
                            fontSize: 12.5,
                            color: _payoutDate != null
                                ? context.colors.textPrimary
                                : context.colors.textMuted,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),

                    // 4. 정산 상태 (수정 시)
                    if (isEdit) ...[
                      DropdownButtonFormField<String>(
                        initialValue: _status,
                        style: TextStyle(fontSize: 12.5, color: context.colors.textPrimary),
                        decoration: const InputDecoration(
                          labelText: '정산 상태',
                          border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                          isDense: true,
                        ),
                        items: const [
                          DropdownMenuItem(value: '1', child: Text('1. 정산 작성 중')),
                          DropdownMenuItem(value: '2', child: Text('2. 정산 확정 (승인 대기)')),
                          DropdownMenuItem(value: '3', child: Text('3. 지급 완료')),
                        ],
                        onChanged: (val) {
                          if (val != null) setState(() => _status = val);
                        },
                      ),
                      const SizedBox(height: 10),
                    ],
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
                        backgroundColor: const Color(0xFF6366F1),
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
                              isEdit ? '회차 정보 저장' : '정산 회차 생성',
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
}
