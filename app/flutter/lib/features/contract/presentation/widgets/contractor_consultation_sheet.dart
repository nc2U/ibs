import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/contract_repository.dart';
import '../../data/models/contract_models.dart';
import '../../providers/contract_provider.dart';

/// 📝 계약자 민원 및 상담 이력 관리 바텀시트
class ContractorConsultationBottomSheet extends ConsumerWidget {
  final ContractItemModel contract;

  const ContractorConsultationBottomSheet({
    super.key,
    required this.contract,
  });

  /// 바텀시트 표출 편의 헬퍼 메서드
  static void show(BuildContext context, {required ContractItemModel contract}) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => ContractorConsultationBottomSheet(contract: contract),
    );
  }

  void _showAddConsultationDialog(BuildContext context, WidgetRef ref) {
    final contractor = contract.contractor;
    if (contractor == null) return;

    showDialog(
      context: context,
      builder: (ctx) => _NewConsultationDialog(
        contractorId: contractor.pk,
        contractorName: contractor.name,
        unitStr: contract.displayUnit,
        onSuccess: () {
          ref.invalidate(contractorConsultationLogsProvider(contractor.pk));
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final contractor = contract.contractor;
    if (contractor == null) {
      return Container(
        height: 200,
        color: context.colors.bgCard,
        child: const Center(child: Text('계약자 정보가 없습니다.')),
      );
    }

    final logsAsync = ref.watch(contractorConsultationLogsProvider(contractor.pk));

    return SafeArea(
      child: Container(
        height: MediaQuery.of(context).size.height * 0.75,
        color: context.colors.bgCard,
        child: Column(
          children: [
            // ── 1. 헤더 바 ──────────────────────────────────────────
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: context.colors.bgSurface,
              child: Row(
                children: [
                  const Icon(Icons.edit_calendar_outlined, size: 20, color: Color(0xFFF59E0B)),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${contractor.name} (${contract.displayUnit})',
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          '민원 및 상담 이력 관리',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                      ],
                    ),
                  ),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF59E0B),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    ),
                    onPressed: () => _showAddConsultationDialog(context, ref),
                    icon: const Icon(Icons.add, size: 16),
                    label: const Text('상담 등록', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            ),
            Divider(color: context.colors.border, height: 1),

            // ── 2. 상담 이력 타임라인 리스트 ───────────────────────
            Expanded(
              child: logsAsync.when(
                loading: () => const Center(
                  child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFF59E0B)),
                ),
                error: (err, _) => Center(
                  child: Text('상담 이력 로드 실패: $err', style: TextStyle(color: context.colors.error)),
                ),
                data: (logs) {
                  if (logs.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.speaker_notes_off_outlined, size: 44, color: context.colors.textDisabled),
                          const SizedBox(height: 12),
                          Text(
                            '등록된 상담/민원 이력이 없습니다.',
                            style: AppTextStyles.bodySecond.copyWith(color: context.colors.textMuted),
                          ),
                          const SizedBox(height: 8),
                          TextButton.icon(
                            onPressed: () => _showAddConsultationDialog(context, ref),
                            icon: const Icon(Icons.add, size: 16, color: Color(0xFFF59E0B)),
                            label: const Text('첫 상담 기록 작성하기', style: TextStyle(color: Color(0xFFF59E0B))),
                          ),
                        ],
                      ),
                    );
                  }

                  return ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: logs.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (ctx, index) {
                      final item = logs[index];
                      return _ConsultationLogCard(log: item);
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 🗂️ 개별 상담 이력 카드 위젯
class _ConsultationLogCard extends StatelessWidget {
  final ContractorConsultationLogModel log;

  const _ConsultationLogCard({required this.log});

  Color _getChannelColor(String channel) {
    switch (channel) {
      case 'phone':
        return const Color(0xFF0D9488);
      case 'visit':
        return const Color(0xFF38BDF8);
      case 'kakao':
        return const Color(0xFFFACC15);
      case 'sms':
        return const Color(0xFF8B5CF6);
      default:
        return const Color(0xFF94A3B8);
    }
  }

  @override
  Widget build(BuildContext context) {
    final channelColor = _getChannelColor(log.channel);

    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgSurface,
        borderRadius: BorderRadius.zero,
        border: Border.all(
          color: log.isImportant ? const Color(0xFFF59E0B) : context.colors.border,
          width: log.isImportant ? 1.2 : 0.8,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 카드 상단 헤더
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            color: context.colors.bgCard,
            child: Row(
              children: [
                // 채널 뱃지
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: channelColor.withAlpha(25),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: channelColor.withAlpha(120), width: 0.6),
                  ),
                  child: Text(
                    log.channelKorean,
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: channelColor,
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                // 카테고리 뱃지
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: context.colors.accentProject.withAlpha(20),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Text(
                    log.categoryKorean,
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: context.colors.accentProject,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  log.consultationDate,
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                ),
                const Spacer(),
                if (log.consultantName != null)
                  Text(
                    '상담: ${log.consultantName}',
                    style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
                  ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // 카드 본문
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (log.title.isNotEmpty) ...[
                  Text(
                    log.title,
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
                    ),
                  ),
                  const SizedBox(height: 6),
                ],
                Text(
                  log.content.isNotEmpty ? log.content : '(상세 내용 없음)',
                  style: AppTextStyles.bodySm.copyWith(
                    color: context.colors.textSecond,
                    height: 1.4,
                  ),
                ),
                if (log.followUpRequired && log.followUpNote != null && log.followUpNote!.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(8),
                    color: const Color(0xFFF59E0B).withAlpha(15),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.assignment_late_outlined, size: 14, color: Color(0xFFF59E0B)),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            '후속조치: ${log.followUpNote}',
                            style: AppTextStyles.caption.copyWith(
                              color: const Color(0xFFB45309),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// ➕ 신규 민원/상담 기록 등록 다이얼로그
class _NewConsultationDialog extends ConsumerStatefulWidget {
  final int contractorId;
  final String contractorName;
  final String unitStr;
  final VoidCallback onSuccess;

  const _NewConsultationDialog({
    required this.contractorId,
    required this.contractorName,
    required this.unitStr,
    required this.onSuccess,
  });

  @override
  ConsumerState<_NewConsultationDialog> createState() => _NewConsultationDialogState();
}

class _NewConsultationDialogState extends ConsumerState<_NewConsultationDialog> {
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  final _followUpController = TextEditingController();

  DateTime _selectedDate = DateTime.now();
  String _channel = 'phone';
  String _category = 'payment';
  String _priority = 'normal';
  bool _followUpRequired = false;
  bool _isImportant = false;
  bool _isLoading = false;

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    _followUpController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_contentController.text.trim().isEmpty && _titleController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('상담 제목 또는 내용을 입력하세요.'), behavior: SnackBarBehavior.floating),
      );
      return;
    }

    setState(() => _isLoading = true);

    final repository = ref.read(contractRepositoryProvider);
    final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);

    final success = await repository.createConsultationLog(
      contractorId: widget.contractorId,
      consultationDate: dateStr,
      channel: _channel,
      category: _category,
      title: _titleController.text.trim(),
      content: _contentController.text.trim(),
      priority: _priority,
      followUpRequired: _followUpRequired,
      followUpNote: _followUpController.text.trim(),
      isImportant: _isImportant,
    );

    // unmounted 상태에서 setState 호출 방지
    if (!mounted) return;
    setState(() => _isLoading = false);

    if (success) {
      widget.onSuccess();
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('상담 기록이 성공적으로 등록되었습니다.'), behavior: SnackBarBehavior.floating),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('상담 기록 등록에 실패했습니다.'), behavior: SnackBarBehavior.floating),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      scrollable: true,
      backgroundColor: context.colors.bgCard,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.zero,
        side: BorderSide(color: context.colors.border, width: 0.8),
      ),
      titlePadding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16),
      actionsPadding: const EdgeInsets.all(12),
      title: Row(
        children: [
          const Icon(Icons.edit_note_rounded, size: 22, color: Color(0xFFF59E0B)),
          const SizedBox(width: 8),
          Text(
            '상담일지 작성',
            style: AppTextStyles.titleSm.copyWith(
              color: context.colors.textPrimary,
              fontWeight: FontWeight.bold,
            ),
          ),
          const Spacer(),
          Text(
            '${widget.contractorName} (${widget.unitStr})',
            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
          ),
        ],
      ),
      content: SizedBox(
        width: MediaQuery.of(context).size.width * 0.9,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Divider(color: context.colors.border, height: 1),
            const SizedBox(height: 12),

            // 1. 상담일자 & 중요도(우선순위)
            Row(
              children: [
                Expanded(
                  child: InkWell(
                    onTap: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: _selectedDate,
                        firstDate: DateTime(2015),
                        lastDate: DateTime(2035),
                        builder: (context, child) {
                          return Theme(
                            data: Theme.of(context).copyWith(
                              colorScheme: ColorScheme.dark(
                                primary: context.colors.accentProject,
                                surface: context.colors.bgCard,
                              ),
                            ),
                            child: child!,
                          );
                        },
                      );
                      if (picked != null) {
                        setState(() => _selectedDate = picked);
                      }
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
                      decoration: BoxDecoration(
                        color: context.colors.bgSurface,
                        border: Border.all(color: context.colors.border, width: 0.8),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.calendar_today_outlined, size: 14, color: context.colors.textMuted),
                          const SizedBox(width: 6),
                          Text(
                            DateFormat('yyyy-MM-dd').format(_selectedDate),
                            style: const TextStyle(fontSize: 12.5),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _priority,
                    decoration: const InputDecoration(
                      labelText: '중요도',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'low', child: Text('낮음')),
                      DropdownMenuItem(value: 'normal', child: Text('보통')),
                      DropdownMenuItem(value: 'high', child: Text('높음')),
                      DropdownMenuItem(value: 'urgent', child: Text('긴급')),
                    ],
                    onChanged: (val) => setState(() => _priority = val ?? 'normal'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // 2. 상담채널 & 상담유형
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _channel,
                    decoration: const InputDecoration(
                      labelText: '상담채널',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'phone', child: Text('전화')),
                      DropdownMenuItem(value: 'visit', child: Text('방문')),
                      DropdownMenuItem(value: 'kakao', child: Text('카카오톡')),
                      DropdownMenuItem(value: 'sms', child: Text('문자')),
                      DropdownMenuItem(value: 'email', child: Text('이메일')),
                      DropdownMenuItem(value: 'other', child: Text('기타')),
                    ],
                    onChanged: (val) => setState(() => _channel = val ?? 'phone'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _category,
                    decoration: const InputDecoration(
                      labelText: '상담유형',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'payment', child: Text('납부상담')),
                      DropdownMenuItem(value: 'contract', child: Text('계약상담')),
                      DropdownMenuItem(value: 'complaint', child: Text('민원/불만')),
                      DropdownMenuItem(value: 'succession', child: Text('승계상담')),
                      DropdownMenuItem(value: 'release', child: Text('해지상담')),
                      DropdownMenuItem(value: 'change', child: Text('변경상담')),
                      DropdownMenuItem(value: 'document', child: Text('서류관련')),
                      DropdownMenuItem(value: 'question', child: Text('단순문의')),
                      DropdownMenuItem(value: 'etc', child: Text('기타')),
                    ],
                    onChanged: (val) => setState(() => _category = val ?? 'payment'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // 3. 제목
            TextField(
              controller: _titleController,
              style: const TextStyle(fontSize: 13),
              decoration: const InputDecoration(
                labelText: '상담 제목 (요약)',
                hintText: '예: 2차 중도금 납부 일정 및 연체 문의',
                isDense: true,
                border: OutlineInputBorder(borderRadius: BorderRadius.zero),
              ),
            ),
            const SizedBox(height: 12),

            // 4. 내용
            TextField(
              controller: _contentController,
              maxLines: 4,
              style: const TextStyle(fontSize: 13),
              decoration: const InputDecoration(
                labelText: '상세 상담 및 통화 내용',
                hintText: '계약자와의 통화/면담 세부 내용을 입력하세요.',
                isDense: true,
                border: OutlineInputBorder(borderRadius: BorderRadius.zero),
              ),
            ),
            const SizedBox(height: 10),

            // 5. 후속조치 및 중요도 체크
            Row(
              children: [
                Expanded(
                  child: CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    controlAffinity: ListTileControlAffinity.leading,
                    dense: true,
                    title: const Text('후속 조치 필요', style: TextStyle(fontSize: 12)),
                    value: _followUpRequired,
                    onChanged: (val) => setState(() => _followUpRequired = val ?? false),
                  ),
                ),
                Expanded(
                  child: CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    controlAffinity: ListTileControlAffinity.leading,
                    dense: true,
                    title: const Text('중요 민원 표시', style: TextStyle(fontSize: 12, color: Color(0xFFF59E0B))),
                    value: _isImportant,
                    onChanged: (val) => setState(() => _isImportant = val ?? false),
                  ),
                ),
              ],
            ),
            if (_followUpRequired)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: TextField(
                  controller: _followUpController,
                  style: const TextStyle(fontSize: 12.5),
                  decoration: const InputDecoration(
                    labelText: '후속조치 메모',
                    hintText: '예: 08/28 수납 확인 후 유선 회신 예정',
                    isDense: true,
                    border: OutlineInputBorder(borderRadius: BorderRadius.zero),
                  ),
                ),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.pop(context),
          child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFF59E0B),
            foregroundColor: Colors.white,
            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          ),
          onPressed: _isLoading ? null : _submit,
          child: _isLoading
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Text('등록 완료', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }
}
