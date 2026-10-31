import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/inbound_letter_model.dart';

class InboundReportSubmitBottomSheet extends StatefulWidget {
  final InboundLetterModel letter;

  const InboundReportSubmitBottomSheet({
    super.key,
    required this.letter,
  });

  @override
  State<InboundReportSubmitBottomSheet> createState() =>
      _InboundReportSubmitBottomSheetState();
}

class _InboundReportSubmitBottomSheetState
    extends State<InboundReportSubmitBottomSheet> {
  String _actionType = 'REPLY_LETTER';
  final _opinionController = TextEditingController();
  final _budgetController = TextEditingController();
  DateTime? _replyPlannedDate;

  final List<Map<String, String>> _actionTypes = const [
    {'value': 'REPLY_LETTER', 'label': '대외 회신(답신) 공문 발송 필요'},
    {'value': 'INTERNAL_ACTION', 'label': '내부 조치 및 처리 (회신 불필요)'},
    {'value': 'RECEIPT_ONLY', 'label': '단순 접수 및 부서 공람 / 보고'},
    {'value': 'BUDGET_ACTION', 'label': '예산 집행 및 시정·보수 조치 수반'},
    {'value': 'OTHER', 'label': '기타'},
  ];

  @override
  void initState() {
    super.initState();
    // 공문에 회신기한이 있는 경우 회신 예정일 기본값으로 제안
    if (widget.letter.replyDueDate != null &&
        widget.letter.replyDueDate!.isNotEmpty) {
      _replyPlannedDate = DateTime.tryParse(widget.letter.replyDueDate!);
    }
  }

  @override
  void dispose() {
    _opinionController.dispose();
    _budgetController.dispose();
    super.dispose();
  }

  Future<void> _pickReplyPlannedDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _replyPlannedDate ?? now,
      firstDate: now.subtract(const Duration(days: 30)),
      lastDate: now.add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() => _replyPlannedDate = picked);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.85,
      ),
      decoration: BoxDecoration(
        color: colors.bgCard,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
      ),
      padding: EdgeInsets.only(bottom: bottomInset),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 드래그 핸들
            Center(
              child: Container(
                margin: const EdgeInsets.only(top: 10, bottom: 8),
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: colors.borderSubtle,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),

            // 상단 헤더
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: colors.accentApproval.withAlpha(25),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(
                      Icons.assignment_turned_in_outlined,
                      color: colors.accentApproval,
                      size: 22,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '수신 공문 처리 보고 / 품의 상신',
                          style: AppTextStyles.titleSm.copyWith(
                            fontWeight: FontWeight.bold,
                            color: colors.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          widget.letter.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: AppTextStyles.caption.copyWith(
                            color: colors.textMuted,
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: Icon(Icons.close, size: 20, color: colors.textMuted),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),

            // 스크롤 영역
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 공문 요약 정보 카드
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: colors.bgSurface,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: colors.borderSubtle, width: 0.8),
                      ),
                      child: Column(
                        children: [
                          _buildSummaryRow(context, '발신처', widget.letter.senderName),
                          const SizedBox(height: 4),
                          _buildSummaryRow(
                              context, '발신문서번호', widget.letter.documentNumber),
                          const SizedBox(height: 4),
                          _buildSummaryRow(
                              context, '접수번호', widget.letter.receiptNumber),
                          const SizedBox(height: 4),
                          _buildSummaryRow(
                              context, '회신기한', widget.letter.replyDueDate ?? '기한 없음'),
                        ],
                      ),
                    ),
                    const SizedBox(height: 18),

                    // 1. 처리 방향 선택
                    Text(
                      '처리 방향 (결재 유형)',
                      style: AppTextStyles.bodySm.copyWith(
                        fontWeight: FontWeight.bold,
                        color: colors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      decoration: BoxDecoration(
                        color: colors.bgSurface,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: colors.borderSubtle, width: 0.8),
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: _actionType,
                          isExpanded: true,
                          icon: Icon(Icons.arrow_drop_down, color: colors.textMuted),
                          style: TextStyle(
                            fontSize: 13,
                            color: colors.textPrimary,
                            fontWeight: FontWeight.w600,
                          ),
                          dropdownColor: colors.bgCard,
                          items: _actionTypes.map((item) {
                            return DropdownMenuItem<String>(
                              value: item['value'],
                              child: Text(item['label']!),
                            );
                          }).toList(),
                          onChanged: (val) {
                            if (val != null) {
                              setState(() => _actionType = val);
                            }
                          },
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // 2. 회신 예정일 (회신 필요한 경우 표시)
                    if (_actionType == 'REPLY_LETTER') ...[
                      Text(
                        '회신 예정일',
                        style: AppTextStyles.bodySm.copyWith(
                          fontWeight: FontWeight.bold,
                          color: colors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 8),
                      InkWell(
                        onTap: _pickReplyPlannedDate,
                        borderRadius: BorderRadius.circular(8),
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 12),
                          decoration: BoxDecoration(
                            color: colors.bgSurface,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                                color: colors.borderSubtle, width: 0.8),
                          ),
                          child: Row(
                            children: [
                              Icon(Icons.calendar_today_outlined,
                                  size: 16, color: colors.accentApproval),
                              const SizedBox(width: 8),
                              Text(
                                _replyPlannedDate != null
                                    ? '${_replyPlannedDate!.year}-${_replyPlannedDate!.month.toString().padLeft(2, '0')}-${_replyPlannedDate!.day.toString().padLeft(2, '0')}'
                                    : '회신 공문 발송 예정일 선택',
                                style: TextStyle(
                                  fontSize: 13,
                                  color: _replyPlannedDate != null
                                      ? colors.textPrimary
                                      : colors.textMuted,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // 3. 검토 의견 및 조치 계획
                    Text(
                      '검토의견 및 조치계획 (기안 내용)',
                      style: AppTextStyles.bodySm.copyWith(
                        fontWeight: FontWeight.bold,
                        color: colors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _opinionController,
                      maxLines: 4,
                      style: TextStyle(fontSize: 13, color: colors.textPrimary),
                      decoration: InputDecoration(
                        hintText: '공문 검토의견, 회신 방향 및 조치 계획을 입력하세요. (미입력 시 기본 요약문으로 상신됩니다)',
                        hintStyle: TextStyle(fontSize: 12, color: colors.textMuted),
                        filled: true,
                        fillColor: colors.bgSurface,
                        contentPadding: const EdgeInsets.all(12),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide(color: colors.borderSubtle, width: 0.8),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide(color: colors.borderSubtle, width: 0.8),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide(color: colors.accentApproval, width: 1.2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // 4. 소요 예산 (선택)
                    Text(
                      '조치 소요예산 (비용 수반 시)',
                      style: AppTextStyles.bodySm.copyWith(
                        fontWeight: FontWeight.bold,
                        color: colors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _budgetController,
                      keyboardType: TextInputType.number,
                      style: TextStyle(fontSize: 13, color: colors.textPrimary),
                      decoration: InputDecoration(
                        hintText: '소요 예산 (원 단위, 비소요 시 0원 또는 공란)',
                        hintStyle: TextStyle(fontSize: 12, color: colors.textMuted),
                        filled: true,
                        fillColor: colors.bgSurface,
                        suffixText: '원',
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide(color: colors.borderSubtle, width: 0.8),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide(color: colors.borderSubtle, width: 0.8),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide(color: colors.accentApproval, width: 1.2),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // 하단 버튼 영역
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              decoration: BoxDecoration(
                color: colors.bgCard,
                border: Border(top: BorderSide(color: colors.borderSubtle, width: 0.8)),
              ),
              child: Row(
                children: [
                  Expanded(
                    flex: 1,
                    child: OutlinedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        side: BorderSide(color: colors.border),
                      ),
                      child: Text('취소', style: TextStyle(color: colors.textSecond)),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      onPressed: () {
                        final replyDateStr = _replyPlannedDate != null
                            ? '${_replyPlannedDate!.year}-${_replyPlannedDate!.month.toString().padLeft(2, '0')}-${_replyPlannedDate!.day.toString().padLeft(2, '0')}'
                            : null;
                        final budget = int.tryParse(_budgetController.text.replaceAll(',', '').trim()) ?? 0;

                        Navigator.of(context).pop({
                          'action_type': _actionType,
                          'review_opinion': _opinionController.text.trim(),
                          'reply_planned_date': replyDateStr,
                          'action_budget': budget,
                        });
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: colors.accentApproval,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      child: const Text('상신 진행', style: TextStyle(fontWeight: FontWeight.bold)),
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

  Widget _buildSummaryRow(BuildContext context, String label, String value) {
    final colors = context.colors;
    return Row(
      children: [
        SizedBox(
          width: 76,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w600,
              color: colors.textMuted,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value.isNotEmpty ? value : '-',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: colors.textPrimary,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}
