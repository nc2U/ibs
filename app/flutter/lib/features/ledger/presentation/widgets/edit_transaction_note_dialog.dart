import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/ledger_repository.dart';
import '../../data/models/ledger_models.dart';
import '../../providers/ledger_provider.dart';

/// ✏️ 적요 및 프로젝트 메모 빠른 수정 다이얼로그
class EditTransactionNoteDialog extends ConsumerStatefulWidget {
  final ProjectTransactionItemModel item;
  final VoidCallback? onSaved;

  const EditTransactionNoteDialog({
    super.key,
    required this.item,
    this.onSaved,
  });

  static Future<void> show(
    BuildContext context, {
    required ProjectTransactionItemModel item,
    VoidCallback? onSaved,
  }) {
    return showDialog(
      context: context,
      builder: (dialogCtx) => EditTransactionNoteDialog(
        item: item,
        onSaved: onSaved,
      ),
    );
  }

  @override
  ConsumerState<EditTransactionNoteDialog> createState() =>
      _EditTransactionNoteDialogState();
}

class _EditTransactionNoteDialogState
    extends ConsumerState<EditTransactionNoteDialog> {
  late final TextEditingController _contentCtrl;
  late final TextEditingController _noteCtrl;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _contentCtrl = TextEditingController(text: widget.item.content ?? '');
    _noteCtrl = TextEditingController(text: widget.item.note ?? '');
  }

  @override
  void dispose() {
    _contentCtrl.dispose();
    _noteCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _isLoading = true);
    final repo = ref.read(ledgerRepositoryProvider);
    final success = await repo.updateTransactionNoteAndContent(
      pk: widget.item.pk,
      content: _contentCtrl.text.trim(),
      note: _noteCtrl.text.trim(),
    );

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (success) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('전표 적요 및 메모가 저장되었습니다.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      ref.read(projectTransactionsProvider.notifier).fetchInitial();
      widget.onSaved?.call();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('저장에 실패했습니다. 권한을 확인해주세요.'),
          backgroundColor: context.colors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: context.colors.bgCard,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      title: Row(
        children: [
          const Icon(Icons.edit_note_rounded,
              color: Color(0xFFF59E0B), size: 22),
          const SizedBox(width: 8),
          Text(
            '적요 및 메모 수정',
            style: AppTextStyles.titleSm.copyWith(
              color: context.colors.textPrimary,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '거래일자: ${widget.item.dealDate} | 계좌: ${widget.item.bankAccountName ?? ''}',
              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
            ),
            const SizedBox(height: 14),

            // 적요 입력
            Text(
              '적요 (거래 내용)',
              style: AppTextStyles.caption.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            TextField(
              controller: _contentCtrl,
              style: AppTextStyles.bodySecond.copyWith(color: context.colors.textPrimary),
              decoration: InputDecoration(
                isDense: true,
                hintText: '적요를 입력하세요',
                hintStyle: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.zero,
                  borderSide: BorderSide(color: context.colors.border),
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              ),
            ),
            const SizedBox(height: 14),

            // 비고/프로젝트 메모 입력
            Text(
              '비고 / 프로젝트 메모 (담당자 메모)',
              style: AppTextStyles.caption.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            TextField(
              controller: _noteCtrl,
              maxLines: 3,
              style: AppTextStyles.bodySecond.copyWith(color: context.colors.textPrimary),
              decoration: InputDecoration(
                isDense: true,
                hintText: '지출 사유나 비고 메모를 입력하세요',
                hintStyle: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.zero,
                  borderSide: BorderSide(color: context.colors.border),
                ),
                contentPadding: const EdgeInsets.all(10),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.pop(context),
          child: Text('취소', style: TextStyle(color: context.colors.textSecond)),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: context.colors.accentProject,
            foregroundColor: Colors.white,
            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
          ),
          onPressed: _isLoading ? null : _save,
          child: _isLoading
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Text('저장하기'),
        ),
      ],
    );
  }
}
