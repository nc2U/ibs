import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/payment_models.dart';
import '../../providers/payment_provider.dart';

/// 🗓️ 순수 납부 회차 변경 / 지정 전용 바텀시트 (2번 탭 계약건별 납부 전용)
class InstallmentChangeBottomSheet extends ConsumerStatefulWidget {
  final PaymentTransactionItemModel paymentItem;

  const InstallmentChangeBottomSheet({super.key, required this.paymentItem});

  @override
  ConsumerState<InstallmentChangeBottomSheet> createState() =>
      _InstallmentChangeBottomSheetState();
}

class _InstallmentChangeBottomSheetState
    extends ConsumerState<InstallmentChangeBottomSheet> {
  bool _isSaving = false;
  int? _selectedInstallmentOrderId;

  @override
  void initState() {
    super.initState();
    _selectedInstallmentOrderId = widget.paymentItem.installmentOrderId;
  }

  Future<void> _submitChange() async {
    setState(() => _isSaving = true);

    final success = await ref
        .read(paymentTransactionsProvider.notifier)
        .matchPayment(
          paymentPk: widget.paymentItem.pk,
          contractId: widget.paymentItem.contractId,
          installmentOrderId: _selectedInstallmentOrderId,
          bankTransactionId: widget.paymentItem.bankTransactionId,
          accountingEntryId: widget.paymentItem.accountingEntryId,
        );

    if (mounted) {
      setState(() => _isSaving = false);
      if (success) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('납부 회차가 성공적으로 변경되었습니다.'),
            backgroundColor: context.colors.success,
            behavior: SnackBarBehavior.floating,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('회차 변경 저장에 실패했습니다. 다시 시도해 주세요.'),
            backgroundColor: context.colors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final numFormat = NumberFormat('#,###');
    final installmentOrdersAsync = ref.watch(installmentStatusListProvider);

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.75,
      ),
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 1. 모달 헤더 ─────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D9488).withAlpha(25),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: const Icon(
                    Icons.edit_calendar_outlined,
                    size: 18,
                    color: Color(0xFF0D9488),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '납부 회차 변경 / 지정',
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 1),
                      Text(
                        '해당 수납 건의 약정 납부 회차를 선택합니다.',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 20),
                  onPressed: () => Navigator.pop(context),
                  color: context.colors.textSecond,
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 2. 수납 건 요약 ──────────────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: context.colors.bgCard,
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: context.colors.bgSurface,
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Column(
                children: [
                  Row(
                    children: [
                      Text(
                        '${widget.paymentItem.contractorName ?? '계약자'} (${widget.paymentItem.unitStr})',
                        style: AppTextStyles.bodyMd.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '수납일: ${widget.paymentItem.dealDate}',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Text(
                        '수납 금액',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                          fontSize: 11,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '${numFormat.format(widget.paymentItem.amount)}원',
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.success,
                          fontWeight: FontWeight.bold,
                          fontSize: 14.5,
                        ),
                      ),
                      const Spacer(),
                      if (widget.paymentItem.payName != null)
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: context.colors.info.withAlpha(20),
                            border: Border.all(
                              color: context.colors.info.withAlpha(80),
                              width: 0.6,
                            ),
                          ),
                          child: Text(
                            '현재: ${widget.paymentItem.payName}',
                            style: TextStyle(
                              fontSize: 10.5,
                              color: context.colors.info,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 3. 회차 선택 영역 ─────────────────────────────────────────
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '지정할 납부 회차를 선택하세요',
                    style: AppTextStyles.bodySecond.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(height: 10),

                  installmentOrdersAsync.when(
                    loading: () => const Center(
                      child: Padding(
                        padding: EdgeInsets.all(12),
                        child: SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      ),
                    ),
                    error: (_, __) => Text(
                      '회차 정보를 불러오지 못했습니다.',
                      style: TextStyle(
                        color: context.colors.error,
                        fontSize: 12,
                      ),
                    ),
                    data: (orders) {
                      if (orders.isEmpty) {
                        return Padding(
                          padding: const EdgeInsets.all(8.0),
                          child: Text(
                            '등록된 납부 회차가 없습니다.',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textMuted,
                            ),
                          ),
                        );
                      }

                      return Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          // 1. 회차 미지정 칩
                          ChoiceChip(
                            label: const Text('회차 미지정'),
                            selected: _selectedInstallmentOrderId == null,
                            selectedColor: const Color(
                              0xFFEF4444,
                            ).withAlpha(25),
                            backgroundColor: context.colors.bgSurface,
                            labelStyle: TextStyle(
                              fontSize: 12,
                              fontWeight: _selectedInstallmentOrderId == null
                                  ? FontWeight.bold
                                  : FontWeight.normal,
                              color: _selectedInstallmentOrderId == null
                                  ? context.colors.error
                                  : context.colors.textSecond,
                            ),
                            shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero,
                            ),
                            side: BorderSide(
                              color: _selectedInstallmentOrderId == null
                                  ? context.colors.error
                                  : context.colors.border,
                              width: _selectedInstallmentOrderId == null
                                  ? 1.2
                                  : 0.8,
                            ),
                            onSelected: (selected) {
                              if (selected) {
                                setState(
                                  () => _selectedInstallmentOrderId = null,
                                );
                              }
                            },
                          ),
                          // 2. 프로젝트 회차 목록 칩
                          ...orders.map((ord) {
                            final isSel =
                                _selectedInstallmentOrderId == ord.orderId;
                            return ChoiceChip(
                              label: Text(
                                ord.aliasName != null &&
                                        ord.aliasName!.isNotEmpty
                                    ? '${ord.payName} (${ord.aliasName})'
                                    : ord.payName,
                              ),
                              selected: isSel,
                              selectedColor: const Color(0xFF0D9488),
                              backgroundColor: context.colors.bgSurface,
                              labelStyle: TextStyle(
                                fontSize: 12,
                                fontWeight: isSel
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                                color: isSel
                                    ? Colors.white
                                    : context.colors.textPrimary,
                              ),
                              shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.zero,
                              ),
                              side: BorderSide(
                                color: isSel
                                    ? const Color(0xFF0D9488)
                                    : context.colors.border,
                                width: isSel ? 1.2 : 0.8,
                              ),
                              onSelected: (selected) {
                                setState(() {
                                  _selectedInstallmentOrderId = selected
                                      ? ord.orderId
                                      : null;
                                });
                              },
                            );
                          }),
                        ],
                      );
                    },
                  ),
                ],
              ),
            ),
          ),

          // ── 4. 하단 저장 버튼 바 ─────────────────────────────────────
          Divider(color: context.colors.border, height: 1),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            color: context.colors.bgSurface,
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: context.colors.textMuted,
                      side: BorderSide(color: context.colors.border),
                      shape: const RoundedRectangleBorder(
                        borderRadius: BorderRadius.zero,
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 11),
                    ),
                    onPressed: () => Navigator.pop(context),
                    child: const Text('취소'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  flex: 2,
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0D9488),
                      foregroundColor: Colors.white,
                      shape: const RoundedRectangleBorder(
                        borderRadius: BorderRadius.zero,
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 11),
                    ),
                    onPressed: _isSaving ? null : _submitChange,
                    icon: _isSaving
                        ? const SizedBox(
                            width: 14,
                            height: 14,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.check_rounded, size: 18),
                    label: Text(
                      _isSaving ? '저장 중...' : '회차 변경 완료',
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
    );
  }
}
