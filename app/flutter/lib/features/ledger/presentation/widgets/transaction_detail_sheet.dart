import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../contract/data/contract_repository.dart';
import '../../../contract/data/models/contract_models.dart';
import '../../../contract/providers/contract_provider.dart';
import '../../../payment/providers/payment_provider.dart';
import '../../../project/presentation/project_screen.dart';
import '../../data/models/ledger_models.dart';
import 'edit_transaction_note_dialog.dart';

/// 📄 거래 전표 상세 및 분개 내역 바텀시트
class TransactionDetailSheet extends ConsumerWidget {
  final ProjectTransactionItemModel item;
  final VoidCallback? onNoteEdited;

  static final NumberFormat _currencyFormat = NumberFormat('#,###');

  const TransactionDetailSheet({
    super.key,
    required this.item,
    this.onNoteEdited,
  });

  static Future<void> show(
    BuildContext context, {
    required ProjectTransactionItemModel item,
    VoidCallback? onNoteEdited,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) => TransactionDetailSheet(
        item: item,
        onNoteEdited: onNoteEdited,
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedProject = ref.watch(selectedRealEstateProjectProvider);
    final canEditNote = ref.can(Perm.ledgerUpdate, projectSlug: selectedProject?.slug);

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: item.sortColor.withAlpha(25),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    item.isIncome
                        ? Icons.arrow_downward_rounded
                        : (item.isExpense
                            ? Icons.arrow_upward_rounded
                            : Icons.swap_horiz_rounded),
                    size: 20,
                    color: item.sortColor,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.content ?? '거래 전표 상세',
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      Text(
                        '거래일시: ${item.dealDate}',
                        style: AppTextStyles.caption
                            .copyWith(color: context.colors.textMuted),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 18),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Divider(color: context.colors.border, height: 1),
            const SizedBox(height: 14),

            // 상세 내용
            _DetailRow(
              label: '거래 구분',
              value: item.sortName ?? '출납',
              isHighlight: true,
              color: item.sortColor,
            ),
            _DetailRow(
              label: '거래 금액',
              value: '${item.sortSign}${_currencyFormat.format(item.amount)}원',
              isHighlight: true,
              color: item.sortColor,
            ),
            _DetailRow(
              label: '거래 계좌',
              value: item.bankAccountName ?? '프로젝트 전용계좌',
            ),
            if (item.trader != null && item.trader!.isNotEmpty)
              _DetailRow(label: '거래처 / 입금자', value: item.trader!),
            if (item.accountName != null && item.accountName!.isNotEmpty)
              _DetailRow(label: '대표 계정과목', value: item.accountName!),
            if (item.note != null && item.note!.isNotEmpty)
              _DetailRow(label: '비고 / 메모', value: item.note!),

            // 복식분개 항목이 있는 경우
            if (item.accountingEntries.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                '📑 회계 분개 상세 (${item.accountingEntries.length}건)',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: context.colors.bgSurface,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Column(
                  children: item.accountingEntries.map((e) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Row(
                        children: [
                          Text(
                            e.accountName ?? '계정',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textPrimary,
                            ),
                          ),
                          if (e.trader != null && e.trader!.isNotEmpty) ...[
                            const SizedBox(width: 6),
                            Text(
                              '(${e.trader})',
                              style: AppTextStyles.caption.copyWith(
                                color: context.colors.textMuted,
                                fontSize: 11,
                              ),
                            ),
                          ],
                          const Spacer(),
                          Text(
                            '${_currencyFormat.format(e.amount)}원',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],

            const SizedBox(height: 14),
            Divider(color: context.colors.border, height: 1),
            const SizedBox(height: 10),

            // 하단 스마트 액션 버튼들
            Column(
              children: [
                Row(
                  children: [
                    // 1. 적요 및 프로젝트 메모 빠른 수정 버튼 (권한 통제)
                    if (canEditNote) ...[
                      Expanded(
                        child: ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFFF59E0B),
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(6),
                            ),
                            padding: const EdgeInsets.symmetric(vertical: 10),
                          ),
                          onPressed: () {
                            Navigator.pop(context);
                            EditTransactionNoteDialog.show(
                              context,
                              item: item,
                              onSaved: onNoteEdited,
                            );
                          },
                          icon: const Icon(Icons.edit_note_rounded, size: 17),
                          label: const Text('적요/메모 수정',
                              style: TextStyle(
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.bold)),
                        ),
                      ),
                      const SizedBox(width: 8),
                    ],

                    // 2. 전표 복사 버튼
                    Expanded(
                      child: OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: context.colors.textPrimary,
                          side: BorderSide(color: context.colors.border),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(6),
                          ),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onPressed: () {
                          Navigator.pop(context);
                          Clipboard.setData(ClipboardData(
                              text:
                                  '${item.dealDate} [${item.sortName}] ${item.content} ${_currencyFormat.format(item.amount)}원'));
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('전표 정보가 복사되었습니다.'),
                              behavior: SnackBarBehavior.floating,
                            ),
                          );
                        },
                        icon: const Icon(Icons.copy_rounded, size: 16),
                        label: const Text('전표 복사',
                            style: TextStyle(fontSize: 12.5)),
                      ),
                    ),
                  ],
                ),

                // 3. 순수 분양대금(분담금, is_payment=true) 수납건인 경우: 계약건 납부목록 전체보기 연동
                if (item.paymentContractEntry != null) ...[
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFF0D9488),
                        side: const BorderSide(
                            color: Color(0xFF0D9488), width: 0.9),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(6),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                      ),
                      onPressed: () async {
                        Navigator.pop(context);
                        final contractEntry = item.paymentContractEntry!;

                        // 해당 계약건 Provider에 세팅
                        final contractsState = ref.read(validContractListProvider);
                        ContractItemModel? targetContract;
                        for (final c in contractsState.items) {
                          if (c.pk == contractEntry.contractId) {
                            targetContract = c;
                            break;
                          }
                        }

                        if (targetContract == null && contractEntry.contractId != null) {
                          final contractRepo = ref.read(contractRepositoryProvider);
                          targetContract = await contractRepo.fetchContractDetail(contractEntry.contractId!);
                        }

                        if (targetContract != null) {
                          ref.read(selectedContractForPaymentProvider.notifier).state = targetContract;
                        }

                        // 수납 관리 서브모듈로 즉시 전환
                        ref.read(paymentCurrentSubTabProvider.notifier).state =
                            PaymentSubTab.byContract;
                        ref.read(projectActiveModuleProvider.notifier).state =
                            ProjectActiveModule.payment;
                      },
                      icon: const Icon(Icons.receipt_long_outlined, size: 16),
                      label: Text(
                        '이 계약건(${item.paymentContractEntry!.contractDisplay ?? '계약자'}) 전체 납부내역 보기',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isHighlight;
  final Color? color;

  const _DetailRow({
    required this.label,
    required this.value,
    this.isHighlight = false,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 90,
            child: Text(
              label,
              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: AppTextStyles.bodySecond.copyWith(
                color: isHighlight
                    ? (color ?? context.colors.textPrimary)
                    : context.colors.textPrimary,
                fontWeight: isHighlight ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
