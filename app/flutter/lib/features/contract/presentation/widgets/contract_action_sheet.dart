import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/services/share_helper.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/contract_repository.dart';
import '../../data/models/contract_models.dart';
import 'contractor_address_sheet.dart';
import 'contractor_consultation_sheet.dart';

/// 📞 계약자/양수인 전화 통화 연결 헬퍼 함수
Future<void> makeContractPhoneCall(
  BuildContext context,
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

  // ── 2단계 확인 다이얼로그 (오발신 및 개인정보 노출 안내) ──
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
          const Icon(Icons.phone_in_talk_outlined, size: 20, color: Color(0xFF0D9488)),
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
                Icon(Icons.info_outline, size: 14, color: context.colors.textMuted),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    '개인 모바일 발신 번호가 상대방에게 표시됩니다.',
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
          child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
        ),
        ElevatedButton.icon(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF0D9488),
            foregroundColor: Colors.white,
            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          ),
          onPressed: () => Navigator.pop(ctx, true),
          icon: const Icon(Icons.phone, size: 16),
          label: const Text('통화 연결', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
        ),
      ],
    ),
  );

  if (shouldCall == true) {
    final Uri launchUri = Uri(scheme: 'tel', path: cleanNumber);
    try {
      if (await canLaunchUrl(launchUri)) {
        await launchUrl(launchUri);
      } else {
        // 전화 기능 미지원 기기 (태블릿, 에뮬레이터 등) 대비 클립보드 복사 Fallback
        Clipboard.setData(ClipboardData(text: phoneNumber));
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('통화를 지원하지 않는 기기입니다. 전화번호($phoneNumber)가 복사되었습니다.'),
              behavior: SnackBarBehavior.floating,
              duration: const Duration(seconds: 3),
            ),
          );
        }
      }
    } catch (_) {
      Clipboard.setData(ClipboardData(text: phoneNumber));
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('전화 연결에 실패했습니다. 전화번호($phoneNumber)가 복사되었습니다.'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }
}

/// 📋 계약 항목 더보기 액션 바텀시트
class ContractActionSheet extends ConsumerWidget {
  final ContractItemModel contract;

  const ContractActionSheet({
    super.key,
    required this.contract,
  });

  /// 액션 바텀시트 표출 편의 헬퍼 메서드
  static void show(BuildContext context, {required ContractItemModel contract}) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
      backgroundColor: context.colors.bgCard,
      builder: (ctx) => ContractActionSheet(contract: contract),
    );
  }

  void _copyToClipboard(BuildContext context, String text, String label) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$label ($text) 복사되었습니다.'),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  Future<void> _downloadAndSharePaymentCertPdf(BuildContext context, WidgetRef ref) async {
    final contractorName = contract.contractor?.name ?? '계약자';
    final unitStr = contract.displayUnit;

    BuildContext? progressDialogContext;

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
                  const SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      color: Color(0xFF38BDF8),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Text(
                    '납부확인서 PDF 생성 중...',
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
      final repository = ref.read(contractRepositoryProvider);
      final pdfBytes = await repository.downloadPaymentCertPdf(
        contractId: contract.pk,
      );

      // 로딩 닫기 (안전한 dialog context 사용)
      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }

      if (pdfBytes == null || pdfBytes.isEmpty) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('납부확인서 PDF를 생성할 수 없습니다. (데이터 확인 필요)'),
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
      final fileName = '납부확인서_${contractorName}_${cleanUnitStr}_$nowStr.pdf';
      final file = File('${tempDir.path}/$fileName');
      await file.writeAsBytes(pdfBytes);

      if (!context.mounted) return;

      // 액션 선택 바텀시트 (바로 열람 vs 공유)
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
                    const Icon(Icons.picture_as_pdf, size: 22, color: Color(0xFF38BDF8)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '납부확인서 PDF 준비 완료',
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
                  style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                ),
                const SizedBox(height: 12),
                Divider(color: context.colors.border, height: 1),
                ListTile(
                  leading: const Icon(Icons.visibility_outlined, color: Color(0xFF38BDF8)),
                  title: const Text('PDF 바로 열기 (뷰어 확인)'),
                  subtitle: const Text('화면에서 기납부 내역 직접 확인', style: TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    await OpenFilex.open(file.path);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.share_outlined, color: Color(0xFF34D399)),
                  title: const Text('모바일 전송 / 공유 (카카오톡, 문자, 메일)'),
                  subtitle: const Text('계약자 또는 대출기관에 파일 직접 전송', style: TextStyle(fontSize: 11.5)),
                  onTap: () async {
                    Navigator.pop(dialogCtx);
                    await AppShareHelper.shareXFiles(
                      [XFile(file.path, mimeType: 'application/pdf')],
                      text: '$contractorName님 ($unitStr) 분양대금 납부확인서입니다.',
                      subject: '분양대금 납부확인서 - $contractorName',
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      );
    } catch (e) {
      if (progressDialogContext != null && progressDialogContext!.mounted) {
        Navigator.of(progressDialogContext!).pop();
        progressDialogContext = null;
      }
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('납부확인서 발급 중 오류가 발생했습니다: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cellPhone = contract.contractor?.contact?.cellPhone;
    final contractorName = contract.contractor?.name ?? '계약자';

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Row(
                children: [
                  Icon(Icons.assignment_outlined, size: 18, color: context.colors.accentProject),
                  const SizedBox(width: 8),
                  Text(
                    '$contractorName (${contract.displayUnit})',
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
            Divider(color: context.colors.border, height: 1),
            ListTile(
              leading: const Icon(Icons.phone_outlined, size: 20, color: Color(0xFF0D9488)),
              title: const Text('계약자 전화 연결', style: TextStyle(fontSize: 13.5)),
              subtitle: Text(
                cellPhone ?? '연락처 미등록',
                style: TextStyle(fontSize: 11.5, color: context.colors.textMuted),
              ),
              trailing: cellPhone != null && cellPhone.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.copy_rounded, size: 16),
                      tooltip: '전화번호 복사',
                      color: context.colors.textMuted,
                      onPressed: () {
                        Navigator.pop(context);
                        _copyToClipboard(context, cellPhone, '$contractorName 연락처');
                      },
                    )
                  : null,
              onTap: () {
                Navigator.pop(context);
                makeContractPhoneCall(
                  context,
                  cellPhone,
                  contractorName: contractorName,
                  unitStr: contract.displayUnit,
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.picture_as_pdf_outlined, size: 20, color: Color(0xFF38BDF8)),
              title: const Text('분양대금 납부확인서 발급', style: TextStyle(fontSize: 13.5)),
              subtitle: const Text('기납부 및 약정 내역 PDF 출력·공유', style: TextStyle(fontSize: 11.5)),
              onTap: () {
                Navigator.pop(context);
                _downloadAndSharePaymentCertPdf(context, ref);
              },
            ),
            ListTile(
              leading: const Icon(Icons.edit_calendar_outlined, size: 20, color: Color(0xFFF59E0B)),
              title: const Text('민원 및 상담 이력 / 기록 등록', style: TextStyle(fontSize: 13.5)),
              subtitle: const Text('과거 상담 이력 조회 및 신규 상담일지 작성', style: TextStyle(fontSize: 11.5)),
              onTap: () {
                Navigator.pop(context);
                ContractorConsultationBottomSheet.show(context, contract: contract);
              },
            ),
            ListTile(
              leading: const Icon(Icons.home_work_outlined, size: 20, color: Color(0xFF10B981)),
              title: const Text('주소 변경 이력 / 신규 등록', style: TextStyle(fontSize: 13.5)),
              subtitle: const Text('주민등록 및 우편물 수령지 변경 내역 관리', style: TextStyle(fontSize: 11.5)),
              onTap: () {
                Navigator.pop(context);
                ContractorAddressBottomSheet.show(context, contract: contract);
              },
            ),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }
}
