import 'package:mobile_ibs/core/services/share_helper.dart';
import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../contract/data/contract_repository.dart';
import '../../contract/data/models/contract_models.dart';
import '../../contract/providers/contract_provider.dart';
import '../data/models/payment_models.dart';
import '../data/payment_repository.dart';
import '../providers/payment_provider.dart';
import 'widgets/contract_match_sheet.dart';
import 'widgets/installment_change_sheet.dart';
import 'widgets/payment_by_contract_card.dart';
import 'widgets/payment_ui_parts.dart';

/// 💳 대금 수납 관리 (Payment) 메인 화면
class PaymentListScreen extends ConsumerStatefulWidget {
  final VoidCallback onBackToMain;

  const PaymentListScreen({super.key, required this.onBackToMain});

  @override
  ConsumerState<PaymentListScreen> createState() => _PaymentListScreenState();
}

class _PaymentListScreenState extends ConsumerState<PaymentListScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _transactionsScrollController = ScrollController();
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    _transactionsScrollController.addListener(_onTransactionsScroll);

    // ── 화면 진입 시 현재 선택된 프로젝트 기준으로 최신 데이터 동기화 ──
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        _refreshAll(resetSelection: true);
      }
    });
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _searchController.dispose();
    _transactionsScrollController.dispose();
    super.dispose();
  }

  void _onTransactionsScroll() {
    if (_transactionsScrollController.position.pixels >=
        _transactionsScrollController.position.maxScrollExtent - 200) {
      final currentTab = ref.read(paymentCurrentSubTabProvider);
      if (currentTab == PaymentSubTab.transactions) {
        ref.read(paymentTransactionsProvider.notifier).fetchNextPage();
      } else if (currentTab == PaymentSubTab.byContract) {
        final selectedContract = ref.read(selectedContractForPaymentProvider);
        if (selectedContract == null) {
          ref.read(validContractListProvider.notifier).fetchNextPage();
        }
      }
    }
  }

  void _onSearchChanged(String value) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 350), () {
      if (!mounted) return;
      ref.read(paymentSearchQueryProvider.notifier).state = value;
      ref.read(contractSearchQueryProvider.notifier).state = value;
      // 검색어를 새로 입력하면 계약자 상세 뷰에서 검색 결과 모드로 전환
      if (value.trim().isNotEmpty) {
        ref.read(selectedContractForPaymentProvider.notifier).state = null;
      }
      ref.read(paymentTransactionsProvider.notifier).fetchInitial();
      ref.read(validContractListProvider.notifier).fetchInitial();
    });
  }

  void _onClearSearch() {
    _debounceTimer?.cancel();
    _searchController.clear();
    ref.read(paymentSearchQueryProvider.notifier).state = '';
    ref.read(contractSearchQueryProvider.notifier).state = '';
    ref.read(selectedContractForPaymentProvider.notifier).state = null;
    ref.read(paymentTransactionsProvider.notifier).fetchInitial();
    ref.read(validContractListProvider.notifier).fetchInitial();
  }

  /// 프로젝트 변경 시 이전 프로젝트의 검색어/매칭 필터가 남지 않도록 초기화
  void _resetFiltersAndSearch() {
    _debounceTimer?.cancel();
    _searchController.clear();
    ref.read(paymentSearchQueryProvider.notifier).state = '';
    ref.read(contractSearchQueryProvider.notifier).state = '';
    ref.read(paymentMatchFilterProvider.notifier).state =
        PaymentMatchFilter.all;
  }

  /// 모든 탭의 데이터를 재조회하고 완료까지 대기 (RefreshIndicator 연동)
  Future<void> _refreshAll({bool resetSelection = false}) async {
    ref.invalidate(paymentOverallAggregateProvider);
    ref.invalidate(installmentStatusListProvider);
    if (resetSelection) {
      ref.read(selectedContractForPaymentProvider.notifier).state = null;
    }
    await Future.wait([
      ref.read(paymentTransactionsProvider.notifier).fetchInitial(),
      ref.read(validContractListProvider.notifier).fetchInitial(),
    ]);
  }

  Future<void> _makePhoneCall(
    String? phoneNumber, {
    String? contractorName,
    String? unitStr,
  }) async {
    if (phoneNumber == null || phoneNumber.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('등록된 연락처가 없습니다.'),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }

    final cleanNumber = phoneNumber.replaceAll(RegExp(r'[^0-9]'), '');

    final bool? shouldCall = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.zero,
          side: BorderSide(color: context.colors.border, width: 0.8),
        ),
        title: Row(
          children: [
            const Icon(
              Icons.phone_in_talk_outlined,
              size: 20,
              color: Color(0xFF0D9488),
            ),
            const SizedBox(width: 8),
            Text(
              '계약자 전화 연결',
              style: AppTextStyles.titleSm.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${contractorName ?? '계약자'}${unitStr != null ? ' ($unitStr)' : ''}',
              style: AppTextStyles.bodyMd.copyWith(
                color: context.colors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              phoneNumber,
              style: AppTextStyles.titleMd.copyWith(
                color: const Color(0xFF0D9488),
                fontWeight: FontWeight.bold,
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              color: context.colors.bgSurface,
              child: Row(
                children: [
                  Icon(
                    Icons.info_outline,
                    size: 14,
                    color: context.colors.textMuted,
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      '확인 버튼을 누르면 기기의 기본 전화 앱으로 연결됩니다.',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                        fontSize: 11,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text(
              '취소',
              style: TextStyle(color: context.colors.textMuted),
            ),
          ),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0D9488),
              foregroundColor: Colors.white,
              shape: const RoundedRectangleBorder(
                borderRadius: BorderRadius.zero,
              ),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            icon: const Icon(Icons.call, size: 16),
            label: const Text(
              '통화 시작',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );

    if (shouldCall == true) {
      final Uri launchUri = Uri(scheme: 'tel', path: cleanNumber);
      if (await canLaunchUrl(launchUri)) {
        await launchUrl(launchUri);
      }
    }
  }

  /// 📄 분양대금 납부 고지서 PDF 생성 및 즉시 열람/공유 메소드
  Future<void> _downloadAndSharePaymentBillPdf({
    required int projectId,
    required ContractItemModel contract,
  }) {
    return _generateAndSharePdf(
      contract: contract,
      fetchBytes: () => ref
          .read(paymentRepositoryProvider)
          .downloadPaymentBillPdf(
            projectId: projectId,
            contractId: contract.pk,
          ),
      docName: '납부 고지서',
      filePrefix: '납부고지서',
      accentColor: context.colors.error,
      emptyMessage: '납부 고지서 PDF를 생성할 수 없습니다. (고지서 발행 정보 확인 필요)',
      errorLabel: '고지서',
      openTitle: '고지서 열람 (PDF 뷰어)',
      openSubtitle: '기기의 기본 PDF 뷰어로 고지서 내용을 확인합니다.',
      shareTitle: '고지서 전달 및 공유 (Share)',
      shareSubtitle: '카카오톡, 문자, 이메일 등으로 계약자에게 PDF를 발송합니다.',
      shareSubject: '분양대금 납부 고지서',
    );
  }

  /// 📄 분양대금 납부 확인서 PDF 생성 및 즉시 열람/공유 메소드
  Future<void> _downloadAndSharePaymentCertPdf({
    required ContractItemModel contract,
  }) {
    return _generateAndSharePdf(
      contract: contract,
      fetchBytes: () => ref
          .read(contractRepositoryProvider)
          .downloadPaymentCertPdf(contractId: contract.pk),
      docName: '납부확인서',
      filePrefix: '납부확인서',
      accentColor: context.colors.info,
      emptyMessage: '납부확인서 PDF를 생성할 수 없습니다. (데이터 확인 필요)',
      errorLabel: '납부확인서',
      openTitle: '납부확인서 열람 (PDF 뷰어)',
      openSubtitle: '기기의 기본 PDF 뷰어로 기납부 내역을 확인합니다.',
      shareTitle: '납부확인서 전달 및 공유 (Share)',
      shareSubtitle: '카카오톡, 문자, 이메일 등으로 계약자/금융기관에 발송합니다.',
      shareSubject: '분양대금 납부확인서',
    );
  }

  /// 📄 PDF 공통 흐름: 로딩 다이얼로그 → 바이트 조회 → 임시 파일 저장 → 열람/공유 바텀시트
  Future<void> _generateAndSharePdf({
    required ContractItemModel contract,
    required Future<dynamic> Function() fetchBytes,
    required String docName,
    required String filePrefix,
    required Color accentColor,
    required String emptyMessage,
    required String errorLabel,
    required String openTitle,
    required String openSubtitle,
    required String shareTitle,
    required String shareSubtitle,
    required String shareSubject,
  }) async {
    final contractorName = contract.contractor?.name ?? '계약자';
    final unitStr = contract.displayUnit;

    BuildContext? progressDialogContext;

    void closeProgress() {
      final ctx = progressDialogContext;
      if (ctx != null && ctx.mounted) {
        Navigator.of(ctx).pop();
      }
      progressDialogContext = null;
    }

    // 로딩 인디케이터 표시
    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black45,
      useRootNavigator: true,
      builder: (ctx) {
        progressDialogContext = ctx;
        return Center(
          child: Material(
            color: Colors.transparent,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: context.colors.border, width: 0.8),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withAlpha(50),
                    blurRadius: 16,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      color: accentColor,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Text(
                    '$docName PDF 생성 중...',
                    style: AppTextStyles.bodyMd.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );

    try {
      final rawBytes = await fetchBytes();
      closeProgress();

      Uint8List? pdfBytes;
      if (rawBytes is Uint8List) {
        pdfBytes = rawBytes;
      } else if (rawBytes is List<int>) {
        pdfBytes = Uint8List.fromList(rawBytes);
      } else if (rawBytes is List) {
        pdfBytes = Uint8List.fromList(rawBytes.cast<int>());
      }

      if (pdfBytes == null || pdfBytes.isEmpty) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(emptyMessage),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
        return;
      }

      // 임시 디렉토리에 파일 저장
      final tempDir = await getTemporaryDirectory();
      final nowStr = DateFormat('yyyyMMdd_HHmmss').format(DateTime.now());
      final cleanUnitStr = unitStr.replaceAll(RegExp(r'[^a-zA-Z0-9가-힣]'), '_');
      final fileName =
          '${filePrefix}_${contractorName}_${cleanUnitStr}_$nowStr.pdf';
      final file = File('${tempDir.path}/$fileName');
      await file.writeAsBytes(pdfBytes);

      if (!mounted) return;

      // 액션 선택 다이얼로그 (바로 열람 vs 공유)
      showModalBottomSheet(
        context: context,
        backgroundColor: context.colors.bgCard,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        builder: (dialogCtx) => SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.picture_as_pdf, size: 22, color: accentColor),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '$docName PDF 준비 완료',
                        style: AppTextStyles.titleSm.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  fileName,
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                  ),
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                ListTile(
                  leading: const Icon(
                    Icons.open_in_new_rounded,
                    color: Color(0xFF0D9488),
                  ),
                  title: Text(
                    openTitle,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
                    ),
                  ),
                  subtitle: Text(
                    openSubtitle,
                    style: const TextStyle(fontSize: 11),
                  ),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    final result = await OpenFilex.open(file.path);
                    if (result.type != ResultType.done && mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('파일 열기 실패: ${result.message}')),
                      );
                    }
                  },
                ),
                ListTile(
                  leading: Icon(
                    Icons.share_outlined,
                    color: context.colors.info,
                  ),
                  title: Text(
                    shareTitle,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
                    ),
                  ),
                  subtitle: Text(
                    shareSubtitle,
                    style: const TextStyle(fontSize: 11),
                  ),
                  onTap: () async {
                    final box = dialogCtx.findRenderObject() as RenderBox?;
                    final origin = box != null && box.hasSize
                        ? box.localToGlobal(Offset.zero) & box.size
                        : null;
                    Navigator.pop(dialogCtx);
                    await AppShareHelper.shareXFiles(
                      [XFile(file.path)],
                      subject: '[$contractorName 고객님] $shareSubject',
                      sharePositionOrigin: origin,
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      );
    } catch (e) {
      closeProgress();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('$errorLabel 생성 중 오류 발생: $e'),
            backgroundColor: context.colors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  /// ⚙️ 현재 고지서 발행 기준 회차(SalesBillIssue.now_payment_order) 간편 설정 다이얼로그
  void _showEditNowPaymentOrderDialog({
    required SalesBillIssueModel billIssue,
    required List<InstallmentStatusItemModel> installmentOrders,
  }) {
    int? selectedOrder = billIssue.nowPaymentOrder;
    bool isSaving = false;

    showDialog(
      context: context,
      builder: (dialogCtx) => StatefulBuilder(
        builder: (ctx, setModalState) {
          return AlertDialog(
            backgroundColor: context.colors.bgCard,
            shape: const RoundedRectangleBorder(
              borderRadius: BorderRadius.zero,
            ),
            title: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(5),
                  decoration: BoxDecoration(
                    color: context.colors.error.withAlpha(20),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Icon(
                    Icons.tune_rounded,
                    size: 18,
                    color: context.colors.error,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  '고지서 발행 기준 회차 설정',
                  style: AppTextStyles.titleSm.copyWith(
                    color: context.colors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            content: SizedBox(
              width: MediaQuery.of(context).size.width * 0.9,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(8),
                    color: context.colors.info.withAlpha(15),
                    child: Text(
                      '💡 선택한 회차를 기준으로 모든 계약자의 고지서 납부 도래 회차 및 연체/미납금이 계산됩니다.',
                      style: TextStyle(
                        fontSize: 11,
                        color: context.colors.textPrimary,
                        height: 1.35,
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Text(
                    '현재 발행 대상 회차',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: context.colors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10),
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: context.colors.border,
                        width: 0.8,
                      ),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<int?>(
                        value: selectedOrder,
                        isExpanded: true,
                        hint: const Text(
                          '발행 회차를 선택하세요',
                          style: TextStyle(fontSize: 13),
                        ),
                        items: [
                          const DropdownMenuItem<int?>(
                            value: null,
                            child: Text(
                              '회차 미지정 (기본값)',
                              style: TextStyle(fontSize: 12.5),
                            ),
                          ),
                          ...installmentOrders.map(
                            (ord) => DropdownMenuItem<int?>(
                              value: ord.orderId,
                              child: Text(
                                '[${ord.payName}] ${ord.displayDueDate}',
                                style: const TextStyle(fontSize: 12.5),
                              ),
                            ),
                          ),
                        ],
                        onChanged: (val) {
                          setModalState(() => selectedOrder = val);
                        },
                      ),
                    ),
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: isSaving ? null : () => Navigator.pop(dialogCtx),
                child: Text(
                  '취소',
                  style: TextStyle(color: context.colors.textMuted),
                ),
              ),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0D9488),
                  foregroundColor: Colors.white,
                  shape: const RoundedRectangleBorder(
                    borderRadius: BorderRadius.zero,
                  ),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 8,
                  ),
                ),
                onPressed: isSaving
                    ? null
                    : () async {
                        setModalState(() => isSaving = true);
                        bool success = false;
                        try {
                          final repo = ref.read(paymentRepositoryProvider);
                          success = await repo.updateNowPaymentOrder(
                            billIssueId: billIssue.pk,
                            nowPaymentOrderId: selectedOrder,
                          );
                        } catch (_) {
                          success = false;
                        }
                        if (dialogCtx.mounted) {
                          Navigator.pop(dialogCtx);
                        }
                        if (mounted) {
                          if (success) {
                            ref.invalidate(salesBillIssueProvider);
                            ref.invalidate(installmentStatusListProvider);
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: const Text(
                                  '고지서 발행 기준 회차가 성공적으로 변경되었습니다.',
                                ),
                                behavior: SnackBarBehavior.floating,
                                backgroundColor: context.colors.success,
                              ),
                            );
                          } else {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: const Text('회차 변경 저장에 실패했습니다.'),
                                behavior: SnackBarBehavior.floating,
                                backgroundColor: context.colors.error,
                              ),
                            );
                          }
                        }
                      },
                child: isSaving
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text(
                        '설정 저장',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showTransactionDetailBottomSheet(
    PaymentTransactionItemModel item, {
    bool showContractorPaymentLink = true,
  }) {
    final numFormat = NumberFormat('#,###');

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) {
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
                        color:
                            (item.isContractUnmatched
                                    ? context.colors.warning
                                    : (item.isInstallmentUnmatched
                                          ? context.colors.error
                                          : context.colors.success))
                                .withAlpha(25),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        item.isContractUnmatched
                            ? Icons.link_off_rounded
                            : (item.isInstallmentUnmatched
                                  ? Icons.assignment_late_outlined
                                  : Icons.receipt_long_outlined),
                        size: 20,
                        color: item.isContractUnmatched
                            ? context.colors.warning
                            : (item.isInstallmentUnmatched
                                  ? context.colors.error
                                  : context.colors.success),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${item.contractorName ?? '입금자'} (${item.unitStr})',
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          '입금일시: ${item.dealDate}',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textMuted,
                          ),
                        ),
                      ],
                    ),
                    const Spacer(),
                    IconButton(
                      icon: const Icon(Icons.close, size: 18),
                      onPressed: () => Navigator.pop(ctx),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 14),

                // 상세 데이터 테이블
                PaymentDetailRow(
                  label: '납부 회차',
                  value:
                      item.payName ??
                      (item.isInstallmentUnmatched ? '회차 미지정' : '-'),
                  isHighlight: item.isInstallmentUnmatched,
                ),
                PaymentDetailRow(
                  label: '수납 금액',
                  value: '${numFormat.format(item.amount)}원',
                  isHighlight: true,
                ),
                PaymentDetailRow(
                  label: '입금 계좌',
                  value: item.bankAccountName ?? '수납 전용 계좌',
                ),
                if (item.trader != null && item.trader!.isNotEmpty)
                  PaymentDetailRow(label: '실제 통장표시 입금자', value: item.trader!),
                if (item.note != null && item.note!.isNotEmpty)
                  PaymentDetailRow(label: '비고 / 메모', value: item.note!),

                const SizedBox(height: 14),
                Divider(color: context.colors.border, height: 1),
                const SizedBox(height: 12),

                // 하단 퀵 액션
                Column(
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: item.isContractUnmatched
                                  ? context.colors.warning
                                  : (item.isInstallmentUnmatched
                                        ? context.colors.error
                                        : const Color(0xFF0D9488)),
                              foregroundColor: Colors.white,
                              shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.zero,
                              ),
                              padding: const EdgeInsets.symmetric(vertical: 11),
                            ),
                            onPressed: () {
                              Navigator.pop(ctx);
                              if (showContractorPaymentLink) {
                                _showMatchContractBottomSheet(item);
                              } else {
                                _showChangeInstallmentBottomSheet(item);
                              }
                            },
                            icon: Icon(
                              item.isContractUnmatched
                                  ? Icons.link_rounded
                                  : Icons.edit_calendar_outlined,
                              size: 16,
                            ),
                            label: Text(
                              item.isContractUnmatched
                                  ? '계약 매칭하기'
                                  : (item.isInstallmentUnmatched
                                        ? '회차 지정하기'
                                        : '납부 회차 변경'),
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton.icon(
                            style: OutlinedButton.styleFrom(
                              foregroundColor: context.colors.textPrimary,
                              side: BorderSide(color: context.colors.border),
                              shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.zero,
                              ),
                              padding: const EdgeInsets.symmetric(vertical: 11),
                            ),
                            onPressed: () {
                              Navigator.pop(ctx);
                              Clipboard.setData(
                                ClipboardData(
                                  text:
                                      '${item.contractorName ?? item.trader ?? '입금자 미상'} ${item.unitStr ?? '-'} ${numFormat.format(item.amount)}원',
                                ),
                              );
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('수납 정보가 복사되었습니다.'),
                                  behavior: SnackBarBehavior.floating,
                                ),
                              );
                            },
                            icon: const Icon(Icons.copy_rounded, size: 16),
                            label: const Text(
                              '정보 복사',
                              style: TextStyle(fontSize: 12.5),
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (showContractorPaymentLink &&
                        item.contractId != null) ...[
                      const SizedBox(height: 8),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: const Color(0xFF0D9488),
                            side: const BorderSide(
                              color: Color(0xFF0D9488),
                              width: 0.9,
                            ),
                            shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero,
                            ),
                            padding: const EdgeInsets.symmetric(vertical: 9),
                          ),
                          onPressed: () async {
                            Navigator.pop(ctx);
                            // 1. 해당 계약 정보 찾기 (목록 → 없으면 단건 조회)
                            final contractId = item.contractId!;
                            final contractsState = ref.read(
                              validContractListProvider,
                            );
                            ContractItemModel? targetContract;
                            for (final c in contractsState.items) {
                              if (c.pk == contractId) {
                                targetContract = c;
                                break;
                              }
                            }
                            if (targetContract == null) {
                              try {
                                targetContract = await ref
                                    .read(contractRepositoryProvider)
                                    .fetchContractDetail(contractId);
                              } catch (_) {
                                targetContract = null;
                              }
                            }
                            if (!mounted) return;
                            if (targetContract == null) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text(
                                    '계약 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.',
                                  ),
                                  behavior: SnackBarBehavior.floating,
                                ),
                              );
                              return;
                            }
                            ref
                                    .read(
                                      selectedContractForPaymentProvider
                                          .notifier,
                                    )
                                    .state =
                                targetContract;
                            // 2. 계약건별 납부 탭으로 전환
                            ref
                                    .read(paymentCurrentSubTabProvider.notifier)
                                    .state =
                                PaymentSubTab.byContract;
                          },
                          icon: const Icon(
                            Icons.person_search_outlined,
                            size: 15,
                          ),
                          label: const Text(
                            '이 계약자의 전체 납부내역 조회',
                            style: TextStyle(
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
      },
    );
  }

  /// 🔗 실시간 계약 & 회차 매칭 바텀시트 모달 (1번 탭 전용)
  void _showMatchContractBottomSheet(PaymentTransactionItemModel item) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) => ContractMatchBottomSheet(paymentItem: item),
    );
  }

  /// 🗓️ 순수 납부 회차 변경/지정 전용 바텀시트 모달 (2번 탭 전용)
  void _showChangeInstallmentBottomSheet(PaymentTransactionItemModel item) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) => InstallmentChangeBottomSheet(paymentItem: item),
    );
  }

  @override
  Widget build(BuildContext context) {
    // ── 🔄 프로젝트 변경 감지 리스너: 프로젝트가 변경되면 3대 탭 목록 및 종합 집계를 즉시 자동 갱신 ──
    ref.listen(selectedRealEstateProjectProvider, (previous, next) {
      if (previous?.realProjectId != next?.realProjectId) {
        _resetFiltersAndSearch();
        _refreshAll(resetSelection: true);
      }
    });

    final selectedProject = ref.watch(selectedRealEstateProjectProvider);
    final aggregateAsync = ref.watch(paymentOverallAggregateProvider);
    final currentTab = ref.watch(paymentCurrentSubTabProvider);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      body: Column(
        children: [
          // ── 1. 수납 모듈 헤더 배너 ─────────────────────────────────────────
          Container(
            color: context.colors.bgSurface,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: context.colors.success.withAlpha(30),
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Icon(
                    Icons.payments_outlined,
                    size: 20,
                    color: context.colors.success,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Text(
                            '대금 수납 관리',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 5,
                              vertical: 1.5,
                            ),
                            decoration: BoxDecoration(
                              color: context.colors.success.withAlpha(20),
                              border: Border.all(
                                color: context.colors.success.withAlpha(120),
                                width: 0.8,
                              ),
                              borderRadius: BorderRadius.circular(2),
                            ),
                            child: Text(
                              'PAYMENT',
                              style: TextStyle(
                                fontSize: 9.5,
                                fontWeight: FontWeight.bold,
                                color: context.colors.success,
                                letterSpacing: 0.6,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        selectedProject?.name ?? '부동산 개발 프로젝트',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textMuted,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: _refreshAll,
                  icon: const Icon(Icons.refresh_rounded, size: 18),
                  tooltip: '새로고침',
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  color: context.colors.textSecond,
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 헤더 아래 전체를 CustomScrollView로 스크롤 가능하게 구성 ──────────────
          Expanded(
            child: RefreshIndicator(
              color: context.colors.success,
              onRefresh: _refreshAll,
              child: CustomScrollView(
                controller: _transactionsScrollController,
                slivers: [
                  // ── 2. KPI 대시보드 – 스크롤과 함께 올라감 ─────────────────────
                  SliverToBoxAdapter(
                    child: aggregateAsync.when(
                      loading: () => const SizedBox(
                        height: 112,
                        child: Center(
                          child: SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                        ),
                      ),
                      error: (_, __) => Container(
                        color: context.colors.bgCard,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 10,
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.error_outline,
                              size: 16,
                              color: context.colors.error,
                            ),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                '수납 집계를 불러오지 못했습니다.',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.error,
                                ),
                              ),
                            ),
                            TextButton(
                              onPressed: () => ref.invalidate(
                                paymentOverallAggregateProvider,
                              ),
                              style: TextButton.styleFrom(
                                minimumSize: Size.zero,
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 4,
                                ),
                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                              ),
                              child: const Text(
                                '재시도',
                                style: TextStyle(fontSize: 12),
                              ),
                            ),
                          ],
                        ),
                      ),
                      data: (aggregate) {
                        if (aggregate == null) return const SizedBox.shrink();

                        final salesRate = aggregate.totalBudget > 0
                            ? (aggregate.totalContractAmount /
                                      aggregate.totalBudget *
                                      100)
                                  .toStringAsFixed(1)
                            : '-';
                        final payRate = aggregate.totalContractAmount > 0
                            ? (aggregate.totalPaidAmount /
                                      aggregate.totalContractAmount *
                                      100)
                                  .toStringAsFixed(1)
                            : '-';

                        return Container(
                          color: context.colors.bgCard,
                          padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              // ── 헤더행: 총 매출예산 (A) ────────────────────────
                              Row(
                                children: [
                                  Icon(
                                    Icons.account_balance_outlined,
                                    size: 13,
                                    color: context.colors.textMuted,
                                  ),
                                  const SizedBox(width: 5),
                                  Text(
                                    '총 매출예산 (A)',
                                    style: AppTextStyles.caption.copyWith(
                                      color: context.colors.textMuted,
                                      fontSize: 10.5,
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    _formatToBillion(aggregate.totalBudget),
                                    style: AppTextStyles.titleSm.copyWith(
                                      color: context.colors.textPrimary,
                                      fontSize: 13.5,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Divider(color: context.colors.border, height: 1),
                              const SizedBox(height: 7),
                              // ── 분양 행: 총분양금액(B) | 미분양금액(A-B) | 분양율 ──
                              Row(
                                children: [
                                  PaymentKpiItem(
                                    label: '총 분양금액 (B)',
                                    value: _formatToBillion(
                                      aggregate.totalContractAmount,
                                    ),
                                    color: context.colors.info,
                                  ),
                                  _divider(),
                                  PaymentKpiItem(
                                    label: '미분양금액 (A-B)',
                                    value: _formatToBillion(
                                      aggregate.unsoldAmount,
                                    ),
                                    color: context.colors.textSecond,
                                  ),
                                  _divider(),
                                  PaymentKpiItem(
                                    label: '분양율',
                                    value: '$salesRate%',
                                    color: context.colors.info,
                                  ),
                                ],
                              ),
                              const SizedBox(height: 7),
                              Divider(color: context.colors.border, height: 1),
                              const SizedBox(height: 7),
                              // ── 수납 행: 총수납금액(C) | 미수납금액(B-C) | 수납율 ──
                              Row(
                                children: [
                                  PaymentKpiItem(
                                    label: '총 수납금액 (C)',
                                    value: _formatToBillion(
                                      aggregate.totalPaidAmount,
                                    ),
                                    color: context.colors.success,
                                  ),
                                  _divider(),
                                  PaymentKpiItem(
                                    label: '미수납금액 (B-C)',
                                    value: _formatToBillion(
                                      aggregate.totalUnpaidAmount,
                                    ),
                                    color: context.colors.warning,
                                  ),
                                  _divider(),
                                  PaymentKpiItem(
                                    label: '수납율',
                                    value: '$payRate%',
                                    color: const Color(0xFF818CF8),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: Divider(color: context.colors.border, height: 1),
                  ),

                  // ── 3. 탭 바 – 스크롤 시 상단에 고정(sticky) ─────────────────
                  SliverPersistentHeader(
                    pinned: true,
                    delegate: PaymentPinnedHeaderDelegate(
                      height: 52.0,
                      child: Container(
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          border: Border(
                            bottom: BorderSide(
                              color: context.colors.border,
                              width: 0.8,
                            ),
                          ),
                        ),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 7,
                        ),
                        child: Row(
                          children: [
                            PaymentSubTabButton(
                              title: '납부 내역',
                              icon: Icons.receipt_long_outlined,
                              isSelected:
                                  currentTab == PaymentSubTab.transactions,
                              onTap: () {
                                ref
                                    .read(paymentCurrentSubTabProvider.notifier)
                                    .state = PaymentSubTab
                                    .transactions;
                              },
                            ),
                            const SizedBox(width: 6),
                            PaymentSubTabButton(
                              title: '계약건별 납부',
                              icon: Icons.person_search_outlined,
                              isSelected:
                                  currentTab == PaymentSubTab.byContract,
                              onTap: () {
                                ref
                                    .read(paymentCurrentSubTabProvider.notifier)
                                    .state = PaymentSubTab
                                    .byContract;
                              },
                            ),
                            const SizedBox(width: 6),
                            PaymentSubTabButton(
                              title: '회차별 현황',
                              icon: Icons.bar_chart_rounded,
                              isSelected:
                                  currentTab == PaymentSubTab.byInstallment,
                              onTap: () {
                                ref
                                    .read(paymentCurrentSubTabProvider.notifier)
                                    .state = PaymentSubTab
                                    .byInstallment;
                              },
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  // ── 4. 검색창 & 매칭 퀵 필터 (납부내역 & 계약건별 탭에서만 활성화) ──
                  if (currentTab != PaymentSubTab.byInstallment) ...[
                    SliverToBoxAdapter(
                      child: Container(
                        color: context.colors.bgCard,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                        child: Column(
                          children: [
                            Container(
                              height: 38,
                              decoration: BoxDecoration(
                                color: context.colors.bgSurface,
                                borderRadius: BorderRadius.zero,
                                border: Border.all(
                                  color: context.colors.border,
                                  width: 0.8,
                                ),
                              ),
                              child: ValueListenableBuilder<TextEditingValue>(
                                valueListenable: _searchController,
                                builder: (context, value, _) => TextField(
                                  controller: _searchController,
                                  onChanged: _onSearchChanged,
                                  style: AppTextStyles.bodySecond.copyWith(
                                    color: context.colors.textPrimary,
                                    fontSize: 13,
                                  ),
                                  decoration: InputDecoration(
                                    isDense: true,
                                    hintText:
                                        currentTab == PaymentSubTab.transactions
                                        ? '입금자명, 계약자명, 동·호수, 계좌 검색...'
                                        : '계약자명, 동·호수, 연락처, 일련번호 검색...',
                                    hintStyle: AppTextStyles.bodySecond
                                        .copyWith(
                                          color: context.colors.textMuted,
                                          fontSize: 12.5,
                                        ),
                                    prefixIcon: Icon(
                                      Icons.search_rounded,
                                      size: 18,
                                      color: context.colors.textMuted,
                                    ),
                                    suffixIcon: value.text.isNotEmpty
                                        ? IconButton(
                                            icon: const Icon(
                                              Icons.clear_rounded,
                                              size: 16,
                                            ),
                                            color: context.colors.textMuted,
                                            onPressed: _onClearSearch,
                                          )
                                        : null,
                                    border: InputBorder.none,
                                    contentPadding: const EdgeInsets.symmetric(
                                      vertical: 9,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                            // 납부 내역 탭 전용: 계약/회차 미매칭 퀵 필터 칩 바
                            if (currentTab == PaymentSubTab.transactions) ...[
                              const SizedBox(height: 8),
                              Consumer(
                                builder: (context, ref, _) {
                                  final currentFilter = ref.watch(
                                    paymentMatchFilterProvider,
                                  );
                                  void selectFilter(PaymentMatchFilter filter) {
                                    if (currentFilter == filter) return;
                                    ref
                                            .read(
                                              paymentMatchFilterProvider
                                                  .notifier,
                                            )
                                            .state =
                                        filter;
                                    ref
                                        .read(
                                          paymentTransactionsProvider.notifier,
                                        )
                                        .fetchInitial();
                                  }

                                  return Row(
                                    children: [
                                      PaymentMatchFilterChip(
                                        label: '전체',
                                        isSelected:
                                            currentFilter ==
                                            PaymentMatchFilter.all,
                                        onTap: () => selectFilter(
                                          PaymentMatchFilter.all,
                                        ),
                                      ),
                                      const SizedBox(width: 6),
                                      PaymentMatchFilterChip(
                                        label: '계약 미매칭',
                                        badgeColor: context.colors.warning,
                                        isSelected:
                                            currentFilter ==
                                            PaymentMatchFilter.noContract,
                                        onTap: () => selectFilter(
                                          PaymentMatchFilter.noContract,
                                        ),
                                      ),
                                      const SizedBox(width: 6),
                                      PaymentMatchFilterChip(
                                        label: '회차 미지정',
                                        badgeColor: context.colors.error,
                                        isSelected:
                                            currentFilter ==
                                            PaymentMatchFilter.noInstall,
                                        onTap: () => selectFilter(
                                          PaymentMatchFilter.noInstall,
                                        ),
                                      ),
                                    ],
                                  );
                                },
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                    SliverToBoxAdapter(
                      child: Divider(color: context.colors.border, height: 1),
                    ),
                  ],

                  // ── 5. 탭별 맞춤 콘텐츠 (Slivers) ──
                  ...switch (currentTab) {
                    PaymentSubTab.transactions => _buildTransactionsSlivers(),
                    PaymentSubTab.byContract => _buildByContractSlivers(),
                    PaymentSubTab.byInstallment => _buildByInstallmentSlivers(),
                  },
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 💰 1. 납부 내역 목록 Slivers
  List<Widget> _buildTransactionsSlivers() {
    final state = ref.watch(paymentTransactionsProvider);
    final numFormat = NumberFormat('#,###');

    if (state.isLoading) {
      return [
        SliverFillRemaining(
          hasScrollBody: false,
          child: Center(
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: context.colors.success,
            ),
          ),
        ),
      ];
    }

    if (state.error != null && state.items.isEmpty) {
      return [
        _errorSliver(
          '데이터 로드 실패: ${state.error}',
          () => ref.read(paymentTransactionsProvider.notifier).fetchInitial(),
        ),
      ];
    }

    if (state.items.isEmpty) {
      return [
        SliverFillRemaining(
          hasScrollBody: false,
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.search_off_rounded,
                  size: 40,
                  color: context.colors.textDisabled,
                ),
                const SizedBox(height: 12),
                Text(
                  '조회된 수납 입금 내역이 없습니다.',
                  style: AppTextStyles.bodySecond.copyWith(
                    color: context.colors.textMuted,
                  ),
                ),
              ],
            ),
          ),
        ),
      ];
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return [
      SliverPadding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        sliver: SliverList(
          delegate: SliverChildBuilderDelegate((ctx, index) {
            if (index == state.items.length) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 14),
                child: Center(
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              );
            }

            final item = state.items[index];
            final bool isUnmatched =
                item.isContractUnmatched || item.isInstallmentUnmatched;
            final Color cardBorderColor = item.isContractUnmatched
                ? context.colors.warning.withAlpha(160)
                : (item.isInstallmentUnmatched
                      ? context.colors.error.withAlpha(160)
                      : context.colors.textDisabled.withAlpha(180));

            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Container(
                decoration: BoxDecoration(
                  color: context.colors.bgCard,
                  borderRadius: BorderRadius.zero,
                  border: Border.all(
                    color: cardBorderColor,
                    width: isUnmatched ? 1.4 : 1.2,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: isUnmatched
                          ? (item.isContractUnmatched
                                ? context.colors.warning.withAlpha(15)
                                : context.colors.error.withAlpha(15))
                          : Colors.black.withAlpha(12),
                      offset: const Offset(0, 2),
                      blurRadius: 4,
                    ),
                  ],
                ),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: () => _showTransactionDetailBottomSheet(item),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // 카드 상단 헤더
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 14,
                            vertical: 8,
                          ),
                          color: item.isContractUnmatched
                              ? context.colors.warning.withAlpha(16)
                              : (item.isInstallmentUnmatched
                                    ? context.colors.error.withAlpha(14)
                                    : context.colors.bgSurface),
                          child: Row(
                            children: [
                              if (item.isContractUnmatched) ...[
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 6,
                                    vertical: 2,
                                  ),
                                  decoration: BoxDecoration(
                                    color: context.colors.warning,
                                    borderRadius: BorderRadius.circular(2),
                                  ),
                                  child: const Text(
                                    '계약 미매칭',
                                    style: TextStyle(
                                      fontSize: 10.5,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.white,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                              ] else if (item.unitTypeName != null) ...[
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 7,
                                    vertical: 2.5,
                                  ),
                                  decoration: BoxDecoration(
                                    color: item.typeBadgeBgColor,
                                    borderRadius: BorderRadius.circular(2),
                                  ),
                                  child: Text(
                                    item.unitTypeName!,
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.bold,
                                      color: item.typeBadgeTextColor,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                              ],
                              Expanded(
                                child: Text(
                                  item.unitStr ?? '-',
                                  style: AppTextStyles.titleSm.copyWith(
                                    color: item.isContractUnmatched
                                        ? context.colors.warning
                                        : context.colors.textPrimary,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 13.5,
                                  ),
                                ),
                              ),
                              if (item.isInstallmentUnmatched) ...[
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 6,
                                    vertical: 2,
                                  ),
                                  decoration: BoxDecoration(
                                    color: context.colors.error.withAlpha(25),
                                    border: Border.all(
                                      color: context.colors.error.withAlpha(
                                        120,
                                      ),
                                      width: 0.7,
                                    ),
                                    borderRadius: BorderRadius.circular(2),
                                  ),
                                  child: Text(
                                    '회차 미지정',
                                    style: TextStyle(
                                      fontSize: 10.5,
                                      fontWeight: FontWeight.bold,
                                      color: context.colors.error,
                                    ),
                                  ),
                                ),
                              ] else ...[
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 6,
                                    vertical: 2,
                                  ),
                                  decoration: BoxDecoration(
                                    color: context.colors.success.withAlpha(20),
                                    border: Border.all(
                                      color: context.colors.success.withAlpha(
                                        80,
                                      ),
                                      width: 0.6,
                                    ),
                                  ),
                                  child: Text(
                                    item.payName ?? '수납',
                                    style: TextStyle(
                                      fontSize: 10.5,
                                      fontWeight: FontWeight.bold,
                                      color: context.colors.success,
                                    ),
                                  ),
                                ),
                              ],
                              const SizedBox(width: 4),
                              Icon(
                                Icons.more_vert_rounded,
                                size: 18,
                                color: context.colors.textMuted,
                              ),
                            ],
                          ),
                        ),
                        Divider(color: context.colors.border, height: 1),

                        // 카드 본문
                        Padding(
                          padding: const EdgeInsets.all(14),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          item.contractorName ??
                                              (item.trader ?? '입금자 미상'),
                                          style: AppTextStyles.titleSm.copyWith(
                                            color: context.colors.textPrimary,
                                            fontWeight: FontWeight.bold,
                                            fontSize: 14.5,
                                          ),
                                        ),
                                        if (item.isContractUnmatched &&
                                            item.trader != null &&
                                            item.trader!.isNotEmpty) ...[
                                          const SizedBox(height: 2),
                                          Text(
                                            '통장 표시: ${item.trader}',
                                            style: AppTextStyles.caption
                                                .copyWith(
                                                  color: context.colors.warning,
                                                  fontSize: 11,
                                                ),
                                          ),
                                        ],
                                      ],
                                    ),
                                  ),
                                  Text(
                                    '입금일: ${item.dealDate}',
                                    style: AppTextStyles.caption.copyWith(
                                      color: context.colors.textMuted,
                                      fontSize: 11.5,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 10),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 8,
                                ),
                                color: context.colors.bgSurface,
                                child: Row(
                                  children: [
                                    Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          '수납 금액',
                                          style: AppTextStyles.caption.copyWith(
                                            color: context.colors.textMuted,
                                            fontSize: 10.5,
                                          ),
                                        ),
                                        const SizedBox(height: 2),
                                        Text(
                                          '${numFormat.format(item.amount)}원',
                                          style: AppTextStyles.titleSm.copyWith(
                                            color: context.colors.success,
                                            fontWeight: FontWeight.bold,
                                            fontSize: 13.5,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const Spacer(),
                                    Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.end,
                                      children: [
                                        Text(
                                          '수납 계좌',
                                          style: AppTextStyles.caption.copyWith(
                                            color: context.colors.textMuted,
                                            fontSize: 10.5,
                                          ),
                                        ),
                                        const SizedBox(height: 2),
                                        Text(
                                          item.bankAccountName ?? '수납계좌',
                                          style: AppTextStyles.bodySecond
                                              .copyWith(
                                                color:
                                                    context.colors.textPrimary,
                                                fontSize: 11.5,
                                              ),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                              if (isUnmatched) ...[
                                const SizedBox(height: 10),
                                SizedBox(
                                  width: double.infinity,
                                  child: OutlinedButton.icon(
                                    style: OutlinedButton.styleFrom(
                                      foregroundColor: item.isContractUnmatched
                                          ? context.colors.warning
                                          : const Color(0xFF0284C7),
                                      side: BorderSide(
                                        color: item.isContractUnmatched
                                            ? context.colors.warning
                                            : context.colors.info,
                                        width: 1,
                                      ),
                                      shape: const RoundedRectangleBorder(
                                        borderRadius: BorderRadius.zero,
                                      ),
                                      padding: const EdgeInsets.symmetric(
                                        vertical: 7,
                                      ),
                                    ),
                                    onPressed: () =>
                                        _showMatchContractBottomSheet(item),
                                    icon: Icon(
                                      item.isContractUnmatched
                                          ? Icons.link_rounded
                                          : Icons.edit_calendar_outlined,
                                      size: 15,
                                    ),
                                    label: Text(
                                      item.isContractUnmatched
                                          ? '계약 건 즉시 매칭'
                                          : '납부 회차 지정',
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
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            );
          }, childCount: itemCount),
        ),
      ),
    ];
  }

  /// 📋 2. 계약건별 납부내역 Slivers
  List<Widget> _buildByContractSlivers() {
    final selectedContract = ref.watch(selectedContractForPaymentProvider);

    if (selectedContract != null) {
      return _buildSelectedContractPaymentSlivers(selectedContract);
    }

    return _buildContractSelectionListSlivers();
  }

  List<Widget> _buildContractSelectionListSlivers() {
    final searchQuery = ref.watch(contractSearchQueryProvider);
    final state = ref.watch(validContractListProvider);

    if (searchQuery.trim().isEmpty) {
      return [
        SliverFillRemaining(
          hasScrollBody: false,
          child: Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: context.colors.accentProject.withAlpha(15),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.person_search_outlined,
                      size: 48,
                      color: context.colors.accentProject,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '조회할 계약자를 검색해 주세요',
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '상단 검색창에 계약자명, 동·호수 또는 일련번호를\n입력하면 해당 계약자의 납부 내역이 표시됩니다.',
                    textAlign: TextAlign.center,
                    style: AppTextStyles.bodySecond.copyWith(
                      color: context.colors.textMuted,
                      fontSize: 13,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ];
    }

    if (state.isLoading) {
      return [
        SliverFillRemaining(
          hasScrollBody: false,
          child: Center(
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: context.colors.success,
            ),
          ),
        ),
      ];
    }

    if (state.error != null && state.items.isEmpty) {
      return [
        _errorSliver(
          '검색 실패: ${state.error}',
          () => ref.read(validContractListProvider.notifier).fetchInitial(),
        ),
      ];
    }

    if (state.items.isEmpty) {
      return [
        SliverFillRemaining(
          hasScrollBody: false,
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.search_off_rounded,
                  size: 40,
                  color: context.colors.textDisabled,
                ),
                const SizedBox(height: 12),
                Text(
                  '\'$searchQuery\' 검색 결과와 일치하는 계약이 없습니다.',
                  style: AppTextStyles.bodySecond.copyWith(
                    color: context.colors.textMuted,
                  ),
                ),
              ],
            ),
          ),
        ),
      ];
    }

    final itemCount = state.items.length + (state.isFetchingNextPage ? 1 : 0);

    return [
      SliverToBoxAdapter(
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: context.colors.bgSurface,
          child: Row(
            children: [
              Icon(
                Icons.check_circle_outline,
                size: 14,
                color: context.colors.success,
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  '검색된 계약 (${state.items.length}건) 중 납부 내역을 확인할 계약자를 선택하세요.',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textSecond,
                    fontSize: 11.5,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
      SliverToBoxAdapter(
        child: Divider(color: context.colors.border, height: 1),
      ),
      SliverPadding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        sliver: SliverList(
          delegate: SliverChildBuilderDelegate((ctx, index) {
            if (index == state.items.length) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 14),
                child: Center(
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              );
            }

            final item = state.items[index];
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: PaymentByContractCard(
                contract: item,
                onSelect: () {
                  ref.read(selectedContractForPaymentProvider.notifier).state =
                      item;
                },
                onCall: () => _makePhoneCall(
                  item.contractor?.contact?.cellPhone,
                  contractorName: item.contractor?.name,
                  unitStr: item.displayUnit,
                ),
              ),
            );
          }, childCount: itemCount),
        ),
      ),
    ];
  }

  List<Widget> _buildSelectedContractPaymentSlivers(
    ContractItemModel contract,
  ) {
    final paymentsAsync = ref.watch(paymentsByContractProvider);
    final numFormat = NumberFormat('#,###');
    final contractor = contract.contractor;

    return [
      SliverToBoxAdapter(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              color: context.colors.bgCard,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      if (contract.orderGroupName != null &&
                          contract.orderGroupName!.isNotEmpty) ...[
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFF4F46E5),
                            borderRadius: BorderRadius.circular(2),
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF4F46E5).withAlpha(40),
                                blurRadius: 2,
                                offset: const Offset(0, 1),
                              ),
                            ],
                          ),
                          child: Text(
                            contract.orderGroupName!,
                            style: const TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                        const SizedBox(width: 5),
                      ],
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 6,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: contract.parsedTypeColor,
                          borderRadius: BorderRadius.circular(2),
                          border: Border.all(
                            color: contract.typeBorderColor,
                            width: 0.8,
                          ),
                        ),
                        child: Text(
                          contract.unitTypeName ?? '타입',
                          style: TextStyle(
                            fontSize: 10.5,
                            fontWeight: FontWeight.bold,
                            color: contract.typeTextColor,
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          '${contractor?.name ?? '계약자'} (${contract.displayUnit})',
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                            fontSize: 13.5,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (contractor?.contact?.cellPhone != null) ...[
                        IconButton(
                          icon: const Icon(
                            Icons.phone_outlined,
                            size: 17,
                            color: Color(0xFF0D9488),
                          ),
                          tooltip: '전화 연결',
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                          onPressed: () => _makePhoneCall(
                            contractor!.contact!.cellPhone,
                            contractorName: contractor.name,
                            unitStr: contract.displayUnit,
                          ),
                        ),
                        const SizedBox(width: 8),
                      ],
                      OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: context.colors.textSecond,
                          side: BorderSide(color: context.colors.border),
                          shape: const RoundedRectangleBorder(
                            borderRadius: BorderRadius.zero,
                          ),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 3,
                          ),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        onPressed: () {
                          ref
                                  .read(
                                    selectedContractForPaymentProvider.notifier,
                                  )
                                  .state =
                              null;
                        },
                        icon: const Icon(Icons.sync_alt_rounded, size: 12),
                        label: const Text(
                          '변경',
                          style: TextStyle(fontSize: 10.5),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 6,
                    ),
                    color: context.colors.bgSurface,
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '공급가',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textMuted,
                                  fontSize: 10,
                                ),
                              ),
                              const SizedBox(height: 1),
                              Text(
                                contract.price > 0
                                    ? '${numFormat.format(contract.price)}원'
                                    : '산정전',
                                style: AppTextStyles.bodySecond.copyWith(
                                  color: context.colors.textPrimary,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Container(
                          width: 1,
                          height: 18,
                          color: context.colors.border,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '기수납 누계',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textMuted,
                                  fontSize: 10,
                                ),
                              ),
                              const SizedBox(height: 1),
                              Text(
                                '${numFormat.format(contract.totalPaid)}원',
                                style: AppTextStyles.bodySecond.copyWith(
                                  color: context.colors.success,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Container(
                          width: 1,
                          height: 18,
                          color: context.colors.border,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '수납률',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textMuted,
                                  fontSize: 10,
                                ),
                              ),
                              const SizedBox(height: 1),
                              Text(
                                '${contract.paymentRate.toStringAsFixed(1)}%',
                                style: AppTextStyles.bodySecond.copyWith(
                                  color: context.colors.info,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 6),
                  Builder(
                    builder: (context) {
                      final selectedProject = ref.watch(
                        selectedRealEstateProjectProvider,
                      );
                      final billIssueAsync = ref.watch(salesBillIssueProvider);
                      final installmentOrdersAsync = ref.watch(
                        installmentStatusListProvider,
                      );

                      final isFullyPaid =
                          contract.price > 0 && contract.paymentRate >= 100.0;
                      final hasPaid = contract.totalPaid > 0;
                      final billIssue = billIssueAsync.valueOrNull;
                      final installList =
                          installmentOrdersAsync.valueOrNull ?? [];

                      String currentOrderName = '미지정 (기본값)';
                      if (billIssue?.nowPaymentOrder != null &&
                          installList.isNotEmpty) {
                        final matched = installList
                            .where(
                              (o) => o.orderId == billIssue!.nowPaymentOrder,
                            )
                            .toList();
                        if (matched.isNotEmpty) {
                          currentOrderName = matched.first.payName;
                        }
                      }

                      return Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 7,
                        ),
                        decoration: BoxDecoration(
                          color: isFullyPaid
                              ? context.colors.bgSurface
                              : context.colors.error.withAlpha(12),
                          border: Border.all(
                            color: isFullyPaid
                                ? context.colors.border
                                : context.colors.error.withAlpha(60),
                            width: 0.8,
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  isFullyPaid
                                      ? Icons.check_circle_outlined
                                      : Icons.receipt_long_outlined,
                                  size: 15,
                                  color: isFullyPaid
                                      ? context.colors.success
                                      : context.colors.error,
                                ),
                                const SizedBox(width: 5),
                                Expanded(
                                  child: Text(
                                    isFullyPaid ? '전액 완납 완료' : '문서 발급',
                                    style: TextStyle(
                                      fontSize: 11.5,
                                      fontWeight: FontWeight.bold,
                                      color: isFullyPaid
                                          ? context.colors.textSecond
                                          : context.colors.textPrimary,
                                    ),
                                  ),
                                ),
                                ElevatedButton.icon(
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: hasPaid
                                        ? const Color(0xFF0D9488)
                                        : context.colors.bgSurface,
                                    foregroundColor: hasPaid
                                        ? Colors.white
                                        : context.colors.textDisabled,
                                    elevation: 0,
                                    side: BorderSide(
                                      color: hasPaid
                                          ? const Color(0xFF0D9488)
                                          : context.colors.border,
                                      width: 0.8,
                                    ),
                                    shape: const RoundedRectangleBorder(
                                      borderRadius: BorderRadius.zero,
                                    ),
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 7,
                                      vertical: 3.5,
                                    ),
                                    minimumSize: Size.zero,
                                    tapTargetSize:
                                        MaterialTapTargetSize.shrinkWrap,
                                  ),
                                  onPressed: hasPaid
                                      ? () => _downloadAndSharePaymentCertPdf(
                                          contract: contract,
                                        )
                                      : null,
                                  icon: Icon(
                                    Icons.verified_outlined,
                                    size: 11.5,
                                    color: hasPaid
                                        ? Colors.white
                                        : context.colors.textDisabled,
                                  ),
                                  label: Text(
                                    '납부확인서',
                                    style: TextStyle(
                                      fontSize: 10.5,
                                      fontWeight: FontWeight.bold,
                                      color: hasPaid
                                          ? Colors.white
                                          : context.colors.textDisabled,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 5),
                                ElevatedButton.icon(
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: isFullyPaid
                                        ? context.colors.bgSurface
                                        : context.colors.error,
                                    foregroundColor: isFullyPaid
                                        ? context.colors.textDisabled
                                        : Colors.white,
                                    elevation: 0,
                                    side: BorderSide(
                                      color: isFullyPaid
                                          ? context.colors.border
                                          : context.colors.error,
                                      width: 0.8,
                                    ),
                                    shape: const RoundedRectangleBorder(
                                      borderRadius: BorderRadius.zero,
                                    ),
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 7,
                                      vertical: 3.5,
                                    ),
                                    minimumSize: Size.zero,
                                    tapTargetSize:
                                        MaterialTapTargetSize.shrinkWrap,
                                  ),
                                  onPressed:
                                      (!isFullyPaid && selectedProject != null)
                                      ? () => _downloadAndSharePaymentBillPdf(
                                          projectId:
                                              selectedProject.realProjectId,
                                          contract: contract,
                                        )
                                      : null,
                                  icon: Icon(
                                    Icons.picture_as_pdf_rounded,
                                    size: 11.5,
                                    color: isFullyPaid
                                        ? context.colors.textDisabled
                                        : Colors.white,
                                  ),
                                  label: Text(
                                    '고지서 발급',
                                    style: TextStyle(
                                      fontSize: 10.5,
                                      fontWeight: FontWeight.bold,
                                      color: isFullyPaid
                                          ? context.colors.textDisabled
                                          : Colors.white,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            if (billIssue != null) ...[
                              const SizedBox(height: 5),
                              Divider(
                                color: context.colors.border.withAlpha(80),
                                height: 1,
                              ),
                              const SizedBox(height: 4),
                              Row(
                                children: [
                                  Text(
                                    '고지 기준 회차: ',
                                    style: TextStyle(
                                      fontSize: 10.5,
                                      color: context.colors.textMuted,
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 5,
                                      vertical: 1,
                                    ),
                                    decoration: BoxDecoration(
                                      color: context.colors.error.withAlpha(18),
                                      border: Border.all(
                                        color: context.colors.error.withAlpha(
                                          90,
                                        ),
                                        width: 0.6,
                                      ),
                                    ),
                                    child: Text(
                                      currentOrderName,
                                      style: TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                        color: context.colors.error,
                                      ),
                                    ),
                                  ),
                                  const Spacer(),
                                  InkWell(
                                    onTap: () => _showEditNowPaymentOrderDialog(
                                      billIssue: billIssue,
                                      installmentOrders: installList,
                                    ),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Icon(
                                          Icons.tune_rounded,
                                          size: 12,
                                          color: context.colors.accentProject,
                                        ),
                                        const SizedBox(width: 2),
                                        Text(
                                          '기준 변경',
                                          style: TextStyle(
                                            fontSize: 10.5,
                                            fontWeight: FontWeight.bold,
                                            color: context.colors.accentProject,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ],
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
            Divider(color: context.colors.border, height: 1),
          ],
        ),
      ),
      paymentsAsync.when(
        loading: () => const SliverFillRemaining(
          hasScrollBody: false,
          child: Center(
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: Color(0xFF0D9488),
            ),
          ),
        ),
        error: (err, _) => _errorSliver(
          '수납 내역 조회 실패: $err',
          () => ref.invalidate(paymentsByContractProvider),
        ),
        data: (payments) {
          if (payments.isEmpty) {
            return SliverFillRemaining(
              hasScrollBody: false,
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.receipt_long_outlined,
                      size: 40,
                      color: context.colors.textDisabled,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      '등록된 수납(입금) 내역이 없습니다.',
                      style: AppTextStyles.bodySecond.copyWith(
                        color: context.colors.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }

          final totalPaidSum = payments.fold<int>(
            0,
            (sum, p) => sum + p.amount,
          );

          return SliverMainAxisGroup(
            slivers: [
              SliverToBoxAdapter(
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 7,
                  ),
                  color: context.colors.bgSurface,
                  child: Row(
                    children: [
                      Text(
                        '납부 내역 (${payments.length}건)',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.textPrimary,
                          fontWeight: FontWeight.bold,
                          fontSize: 11.5,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '합계: ${numFormat.format(totalPaidSum)}원',
                        style: AppTextStyles.caption.copyWith(
                          color: context.colors.success,
                          fontWeight: FontWeight.bold,
                          fontSize: 11.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: Divider(color: context.colors.border, height: 1),
              ),
              SliverPadding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate((ctx, idx) {
                    final p = payments[idx];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Container(
                        decoration: BoxDecoration(
                          color: context.colors.bgCard,
                          border: Border.all(
                            color: p.isInstallmentUnmatched
                                ? context.colors.error.withAlpha(140)
                                : context.colors.border,
                            width: 1,
                          ),
                        ),
                        child: InkWell(
                          onTap: () => _showTransactionDetailBottomSheet(
                            p,
                            showContractorPaymentLink: false,
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(10),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 5,
                                        vertical: 1.5,
                                      ),
                                      decoration: BoxDecoration(
                                        color: p.isInstallmentUnmatched
                                            ? context.colors.error.withAlpha(20)
                                            : context.colors.success.withAlpha(
                                                20,
                                              ),
                                        border: Border.all(
                                          color: p.isInstallmentUnmatched
                                              ? context.colors.error.withAlpha(
                                                  100,
                                                )
                                              : context.colors.success
                                                    .withAlpha(80),
                                          width: 0.6,
                                        ),
                                      ),
                                      child: Text(
                                        p.payName ??
                                            (p.isInstallmentUnmatched
                                                ? '회차 미지정'
                                                : '수납'),
                                        style: TextStyle(
                                          fontSize: 10.5,
                                          fontWeight: FontWeight.bold,
                                          color: p.isInstallmentUnmatched
                                              ? context.colors.error
                                              : context.colors.success,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      '수납일: ${p.dealDate}',
                                      style: AppTextStyles.caption.copyWith(
                                        color: context.colors.textMuted,
                                        fontSize: 11,
                                      ),
                                    ),
                                    const Spacer(),
                                    Text(
                                      '${numFormat.format(p.amount)}원',
                                      style: AppTextStyles.titleSm.copyWith(
                                        color: context.colors.success,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 13.5,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        '입금계좌: ${p.bankAccountName ?? '-'}${p.trader != null && p.trader!.isNotEmpty ? ' (${p.trader})' : ''}',
                                        style: AppTextStyles.caption.copyWith(
                                          color: context.colors.textSecond,
                                          fontSize: 10.5,
                                        ),
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                    InkWell(
                                      onTap: () =>
                                          _showChangeInstallmentBottomSheet(p),
                                      child: Padding(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 4,
                                          vertical: 2,
                                        ),
                                        child: Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Icon(
                                              Icons.edit_calendar_outlined,
                                              size: 12,
                                              color: p.isInstallmentUnmatched
                                                  ? context.colors.error
                                                  : context.colors.info,
                                            ),
                                            const SizedBox(width: 2),
                                            Text(
                                              p.isInstallmentUnmatched
                                                  ? '회차 지정'
                                                  : '회차 변경',
                                              style: TextStyle(
                                                fontSize: 10.5,
                                                color: p.isInstallmentUnmatched
                                                    ? context.colors.error
                                                    : context.colors.info,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    );
                  }, childCount: payments.length),
                ),
              ),
            ],
          );
        },
      ),
    ];
  }

  /// 📊 3. 회차별 납부 현황 Slivers
  List<Widget> _buildByInstallmentSlivers() {
    final listAsync = ref.watch(installmentStatusListProvider);
    final numFormat = NumberFormat('#,###');

    return listAsync.when(
      loading: () => [
        SliverFillRemaining(
          hasScrollBody: false,
          child: Center(
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: context.colors.success,
            ),
          ),
        ),
      ],
      error: (err, _) => [
        _errorSliver(
          '회차별 현황 로드 실패: $err',
          () => ref.invalidate(installmentStatusListProvider),
        ),
      ],
      data: (items) {
        if (items.isEmpty) {
          return [
            SliverFillRemaining(
              hasScrollBody: false,
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.bar_chart_outlined,
                      size: 40,
                      color: context.colors.textDisabled,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      '등록된 납부 회차 정보가 없습니다.',
                      style: AppTextStyles.bodySecond.copyWith(
                        color: context.colors.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ];
        }

        return [
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            sliver: SliverList(
              delegate: SliverChildBuilderDelegate((ctx, index) {
                final order = items[index];

                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Container(
                    decoration: BoxDecoration(
                      color: context.colors.bgCard,
                      borderRadius: BorderRadius.zero,
                      border: Border.all(
                        color: context.colors.textDisabled.withAlpha(180),
                        width: 1.2,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withAlpha(12),
                          offset: const Offset(0, 2),
                          blurRadius: 4,
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // 상단 헤더
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 14,
                            vertical: 9,
                          ),
                          color: context.colors.bgSurface,
                          child: Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 3,
                                ),
                                decoration: BoxDecoration(
                                  color: context.colors.info.withAlpha(25),
                                  borderRadius: BorderRadius.circular(2),
                                  border: Border.all(
                                    color: context.colors.info.withAlpha(100),
                                    width: 0.8,
                                  ),
                                ),
                                child: Text(
                                  order.payName,
                                  style: TextStyle(
                                    fontSize: 11.5,
                                    fontWeight: FontWeight.bold,
                                    color: context.colors.info,
                                  ),
                                ),
                              ),
                              if (order.aliasName != null &&
                                  order.aliasName!.isNotEmpty) ...[
                                const SizedBox(width: 8),
                                Text(
                                  '(${order.aliasName})',
                                  style: AppTextStyles.caption.copyWith(
                                    color: context.colors.textMuted,
                                    fontSize: 11.5,
                                  ),
                                ),
                              ],
                              const Spacer(),
                              Text(
                                '약정일: ${order.displayDueDate}',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textMuted,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 11.5,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Divider(color: context.colors.border, height: 1),

                        // 본문 요약 바
                        Padding(
                          padding: const EdgeInsets.all(14),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Text(
                                    '수납률: ${order.collectionRate.toStringAsFixed(1)}%',
                                    style: AppTextStyles.titleSm.copyWith(
                                      color: order.collectionRate >= 90
                                          ? context.colors.success
                                          : (order.collectionRate >= 50
                                                ? context.colors.info
                                                : context.colors.warning),
                                      fontWeight: FontWeight.bold,
                                      fontSize: 14.5,
                                    ),
                                  ),
                                  const Spacer(),
                                  if (order.payRatio > 0)
                                    Text(
                                      '회당 비율: ${order.payRatio.toStringAsFixed(0)}%',
                                      style: AppTextStyles.caption.copyWith(
                                        color: context.colors.textMuted,
                                        fontSize: 11.5,
                                      ),
                                    ),
                                ],
                              ),
                              const SizedBox(height: 10),

                              // 프로그레스 바
                              ClipRRect(
                                borderRadius: BorderRadius.circular(2),
                                child: LinearProgressIndicator(
                                  value: (order.collectionRate / 100).clamp(
                                    0.0,
                                    1.0,
                                  ),
                                  minHeight: 6,
                                  backgroundColor: context.colors.border,
                                  color: order.collectionRate >= 90
                                      ? context.colors.success
                                      : context.colors.info,
                                ),
                              ),
                              const SizedBox(height: 12),

                              // 금액 요약 박스
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 10,
                                  vertical: 8,
                                ),
                                color: context.colors.bgSurface,
                                child: Row(
                                  children: [
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            '실제 수납액',
                                            style: AppTextStyles.caption
                                                .copyWith(
                                                  color:
                                                      context.colors.textMuted,
                                                  fontSize: 10.5,
                                                ),
                                          ),
                                          const SizedBox(height: 2),
                                          Text(
                                            order.totalPaidAmount > 0
                                                ? '${numFormat.format(order.totalPaidAmount)}원'
                                                : '0원',
                                            style: AppTextStyles.bodySecond
                                                .copyWith(
                                                  color: context.colors.success,
                                                  fontWeight: FontWeight.bold,
                                                  fontSize: 12,
                                                ),
                                          ),
                                        ],
                                      ),
                                    ),
                                    Container(
                                      width: 1,
                                      height: 20,
                                      color: context.colors.border,
                                    ),
                                    const SizedBox(width: 10),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            '총 약정액',
                                            style: AppTextStyles.caption
                                                .copyWith(
                                                  color:
                                                      context.colors.textMuted,
                                                  fontSize: 10.5,
                                                ),
                                          ),
                                          const SizedBox(height: 2),
                                          Text(
                                            order.totalDueAmount > 0
                                                ? '${numFormat.format(order.totalDueAmount)}원'
                                                : '산정 전',
                                            style: AppTextStyles.bodySecond
                                                .copyWith(
                                                  color: context
                                                      .colors
                                                      .textPrimary,
                                                  fontWeight: FontWeight.bold,
                                                  fontSize: 12,
                                                ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }, childCount: items.length),
            ),
          ),
        ];
      },
    );
  }

  /// 목록 로드 실패 시 메시지와 재시도 버튼을 표시하는 공통 Sliver
  Widget _errorSliver(String message, VoidCallback onRetry) {
    return SliverFillRemaining(
      hasScrollBody: false,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                message,
                textAlign: TextAlign.center,
                style: TextStyle(color: context.colors.error),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded, size: 16),
                label: const Text('다시 시도'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: context.colors.textPrimary,
                  side: BorderSide(color: context.colors.border),
                  shape: const RoundedRectangleBorder(
                    borderRadius: BorderRadius.zero,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatToBillion(int amount) {
    if (amount <= 0) return '0원';
    final double billion = amount / 100000000;
    if (billion >= 10000) {
      final double trillion = billion / 10000;
      return '${trillion.toStringAsFixed(1)}조원';
    }
    return '${billion.toStringAsFixed(1)}억원';
  }

  Widget _divider() {
    return Container(
      width: 1,
      height: 24,
      color: context.colors.border,
      margin: const EdgeInsets.symmetric(horizontal: 4),
    );
  }
}
