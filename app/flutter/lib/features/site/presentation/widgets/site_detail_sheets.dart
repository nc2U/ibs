import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/site_models.dart';
import 'site_common_widgets.dart';
import 'site_consultation_sheet.dart';
import 'site_file_helper.dart';

/// 🗺️ 사업부지 관리 상세 바텀시트 3종 (필지 상세, 소유자 상세, 매입계약 상세)

/// 1. 필지 상세 바텀시트
void showSiteDetailBottomSheet({
  required BuildContext context,
  required WidgetRef ref,
  required SiteItemModel item,
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
                      color: const Color(0xFF0D9488).withAlpha(25),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.pin_drop_outlined,
                      size: 20,
                      color: Color(0xFF0D9488),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${item.district} ${item.lotNumber}',
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          '순번 #${item.order} | 지목: ${item.sitePurpose}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 18),
                    onPressed: () => Navigator.pop(ctx),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Divider(color: context.colors.border, height: 1),
              const SizedBox(height: 14),

              SiteDetailRow(
                label: '공부면적',
                value: '${item.officialArea.toStringAsFixed(2)}㎡ (${item.pyungArea.toStringAsFixed(1)}평)',
                isHighlight: true,
                color: const Color(0xFF0D9488),
              ),
              if (item.returnedArea != null && item.returnedArea! > 0)
                SiteDetailRow(
                  label: '환지면적',
                  value: '${item.returnedArea!.toStringAsFixed(2)}㎡ (${(item.returnedArea! / 3.305785).toStringAsFixed(1)}평)',
                  isHighlight: true,
                ),
              if (item.noticePrice != null)
                SiteDetailRow(
                  label: '공시지가',
                  value: '㎡당 ${numFormat.format(item.noticePrice)}원',
                ),
              if (item.dupIssueDate != null && item.dupIssueDate!.isNotEmpty)
                SiteDetailRow(
                  label: '등본 발급일',
                  value: item.dupIssueDate!,
                ),
              if (item.rightsA.isNotEmpty)
                SiteDetailRow(
                  label: '갑구 권리제한',
                  value: item.rightsA,
                  isDanger: true,
                ),
              if (item.rightsB.isNotEmpty)
                SiteDetailRow(
                  label: '을구 권리제한',
                  value: item.rightsB,
                  isDanger: true,
                ),
              if (item.note.isNotEmpty)
                SiteDetailRow(label: '비고 메모', value: item.note),

              if (item.owners.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(
                  '👤 소유자 정보 (${item.owners.length}명)',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.all(8),
                  color: context.colors.bgSurface,
                  child: Column(
                    children: item.owners.map((o) {
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 3),
                        child: Row(
                          children: [
                            Text(
                              o.owner,
                              style: AppTextStyles.bodySecond.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            if (o.ownSortDesc != null) ...[
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                decoration: BoxDecoration(
                                  color: context.colors.border,
                                  borderRadius: BorderRadius.zero,
                                ),
                                child: Text(
                                  o.ownSortDesc!,
                                  style: TextStyle(fontSize: 9.5, color: context.colors.textSecond),
                                ),
                              ),
                            ],
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

              // 하단 액션 버튼 영역 (등기부등본 열람/공유 버튼 상시 노출)
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: item.hasRegisterFile
                            ? const Color(0xFF0D9488)
                            : context.colors.bgSurface,
                        foregroundColor: item.hasRegisterFile
                            ? Colors.white
                            : context.colors.textMuted,
                        elevation: item.hasRegisterFile ? 1 : 0,
                        side: BorderSide(
                          color: item.hasRegisterFile
                              ? const Color(0xFF0D9488)
                              : context.colors.border,
                          width: 0.8,
                        ),
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                      ),
                      onPressed: () {
                        if (item.hasRegisterFile) {
                          Navigator.pop(ctx);
                          SiteFileHelper.downloadAndShareRegisterPdf(context: context, ref: ref, item: item);
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('해당 필지의 등기부등본 파일이 아직 등록되지 않았습니다.'),
                              behavior: SnackBarBehavior.floating,
                            ),
                          );
                        }
                      },
                      icon: Icon(
                        item.hasRegisterFile
                            ? Icons.picture_as_pdf
                            : Icons.picture_as_pdf_outlined,
                        size: 16,
                        color: item.hasRegisterFile
                            ? Colors.white
                            : context.colors.textMuted,
                      ),
                      label: Text(
                        item.hasRegisterFile ? '등기부등본 열기/공유' : '등본 파일 미등록',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: item.hasRegisterFile ? FontWeight.bold : FontWeight.normal,
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
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                      ),
                      onPressed: () {
                        Navigator.pop(ctx);
                        Clipboard.setData(ClipboardData(
                            text: '${item.district} ${item.lotNumber} (${item.officialArea}㎡ / ${item.sitePurpose})'));
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('필지 정보가 복사되었습니다.'),
                            behavior: SnackBarBehavior.floating,
                          ),
                        );
                      },
                      icon: const Icon(Icons.copy_rounded, size: 16),
                      label: const Text('정보 복사', style: TextStyle(fontSize: 12)),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      );
    },
  );
}

/// 2. 소유자 상세 바텀시트
void showSiteOwnerDetailBottomSheet({
  required BuildContext context,
  required WidgetRef ref,
  required SiteOwnerItemModel item,
}) {
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
                      color: const Color(0xFF38BDF8).withAlpha(25),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.person_outline_rounded,
                      size: 20,
                      color: Color(0xFF38BDF8),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.owner,
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          '소유구분: ${item.ownSortDesc ?? "개인"} | 동의여부: ${item.useConsent ? "동의완료" : "미동의"}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 18),
                    onPressed: () => Navigator.pop(ctx),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Divider(color: context.colors.border, height: 1),
              const SizedBox(height: 14),

              if (item.phone1.isNotEmpty)
                SiteDetailRow(
                  label: '연락처 1',
                  value: item.phone1,
                  isPhone: true,
                  onPhoneTap: () => makeSitePhoneCall(context, item.phone1, targetName: item.owner),
                  onSmsTap: () => sendSiteSms(item.phone1),
                ),
              if (item.phone2.isNotEmpty)
                SiteDetailRow(
                  label: '비상연락처',
                  value: item.phone2,
                  isPhone: true,
                  onPhoneTap: () => makeSitePhoneCall(context, item.phone2, targetName: item.owner),
                  onSmsTap: () => sendSiteSms(item.phone2),
                ),
              if (item.dateOfBirth != null && item.dateOfBirth!.isNotEmpty)
                SiteDetailRow(label: '생년월일', value: item.dateOfBirth!),
              if (item.address1.isNotEmpty)
                SiteDetailRow(label: '주소', value: '${item.address1} ${item.address2} ${item.address3}'.trim()),
              SiteDetailRow(
                label: '소유 총 면적',
                value: '${item.totalOwnedArea.toStringAsFixed(2)}㎡ (${(item.totalOwnedArea / 3.305785).toStringAsFixed(1)}평)',
                isHighlight: true,
                color: const Color(0xFF38BDF8),
              ),
              if (item.note.isNotEmpty)
                SiteDetailRow(label: '특이사항', value: item.note),

              if (item.sites.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(
                  '📌 소유 필지 목록 (${item.sites.length}필지)',
                  style: AppTextStyles.caption.copyWith(
                    color: context.colors.textMuted,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.all(8),
                  color: context.colors.bgSurface,
                  child: Column(
                    children: item.sites.map((s) {
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 3),
                        child: Row(
                          children: [
                            Text(
                              s.siteName,
                              style: AppTextStyles.bodySecond.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const Spacer(),
                            if (s.ownedArea != null)
                              Text(
                                '${s.ownedArea!.toStringAsFixed(1)}㎡',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textSecond,
                                ),
                              ),
                            if (s.ownershipRatio != null) ...[
                              const SizedBox(width: 6),
                              Text(
                                '(${(s.ownershipRatio! * 100).toStringAsFixed(1)}%)',
                                style: AppTextStyles.caption.copyWith(
                                  color: const Color(0xFF0D9488),
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
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

              // 하단 통화/상담기록/복사 버튼 행
              Row(
                children: [
                  if (item.phone1.isNotEmpty) ...[
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF10B981),
                          foregroundColor: Colors.white,
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        onPressed: () {
                          Navigator.pop(ctx);
                          makeSitePhoneCall(context, item.phone1, targetName: item.owner);
                        },
                        icon: const Icon(Icons.phone_outlined, size: 16),
                        label: const Text('전화 걸기', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                      ),
                    ),
                    const SizedBox(width: 8),
                  ],
                  Expanded(
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFF59E0B),
                        foregroundColor: Colors.white,
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                      ),
                      onPressed: () {
                        Navigator.pop(ctx);
                        showModalBottomSheet(
                          context: context,
                          isScrollControlled: true,
                          backgroundColor: Colors.transparent,
                          builder: (consultationCtx) => SiteOwnerConsultationBottomSheet(owner: item),
                        );
                      },
                      icon: const Icon(Icons.edit_calendar_outlined, size: 16),
                      label: const Text('상담/협의 기록', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    style: IconButton.styleFrom(
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      side: BorderSide(color: context.colors.border),
                      padding: const EdgeInsets.all(10),
                    ),
                    onPressed: () {
                      Navigator.pop(ctx);
                      Clipboard.setData(ClipboardData(
                          text: '${item.owner} (${item.phone1}) 소유: ${item.displaySiteSummary}'));
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('소유자 정보가 복사되었습니다.'),
                          behavior: SnackBarBehavior.floating,
                        ),
                      );
                    },
                    icon: const Icon(Icons.copy_rounded, size: 16),
                    tooltip: '정보 복사',
                  ),
                ],
              ),
            ],
          ),
        ),
      );
    },
  );
}

/// 3. 매입 계약 상세 바텀시트
void showSiteContractDetailBottomSheet({
  required BuildContext context,
  required WidgetRef ref,
  required SiteContractItemModel item,
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
                      color: const Color(0xFFF59E0B).withAlpha(25),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.receipt_long_rounded,
                      size: 20,
                      color: Color(0xFFF59E0B),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '매도인: ${item.ownerName}',
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          '계약체결일: ${item.contractDate} | 소유권확보: ${item.ownershipCompletion ? '완료' : '진행중'}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 18),
                    onPressed: () => Navigator.pop(ctx),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Divider(color: context.colors.border, height: 1),
              const SizedBox(height: 14),

              SiteDetailRow(
                label: '총 매매대금',
                value: '${numFormat.format(item.totalPrice)}원',
                isHighlight: true,
                color: const Color(0xFFF59E0B),
              ),
              SiteDetailRow(
                label: '계약면적 / 평단가',
                value: '${item.contractArea.toStringAsFixed(2)}㎡ (${item.contractPyung.toStringAsFixed(1)}평) / 평당 ${numFormat.format(item.pricePerPyung)}원',
              ),
              SiteDetailRow(
                label: '대금 지급률',
                value: '${item.paymentRate.toStringAsFixed(1)}% (기지급: ${numFormat.format(item.totalPaidAmount)}원 / 미지급: ${numFormat.format(item.unpaidAmount)}원)',
                isHighlight: true,
                color: item.paymentRate >= 100 ? const Color(0xFF10B981) : const Color(0xFF38BDF8),
              ),

              const SizedBox(height: 10),
              Text(
                '💳 대금 분할 지급 현황',
                style: AppTextStyles.caption.copyWith(
                  color: context.colors.textMuted,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.all(8),
                color: context.colors.bgSurface,
                child: Column(
                  children: [
                    SitePaymentStepRow(
                      title: '계약금 1',
                      amount: item.downPay1,
                      date: item.downPay1Date,
                      isPaid: item.downPay1IsPaid,
                    ),
                    if (item.downPay2 != null && item.downPay2! > 0)
                      SitePaymentStepRow(
                        title: '계약금 2',
                        amount: item.downPay2,
                        date: item.downPay2Date,
                        isPaid: item.downPay2IsPaid,
                      ),
                    if (item.interPay1 != null && item.interPay1! > 0)
                      SitePaymentStepRow(
                        title: '중도금 1',
                        amount: item.interPay1,
                        date: item.interPay1Date,
                        isPaid: item.interPay1IsPaid,
                      ),
                    if (item.interPay2 != null && item.interPay2! > 0)
                      SitePaymentStepRow(
                        title: '중도금 2',
                        amount: item.interPay2,
                        date: item.interPay2Date,
                        isPaid: item.interPay2IsPaid,
                      ),
                    if (item.remainPay != null && item.remainPay! > 0)
                      SitePaymentStepRow(
                        title: '잔금',
                        amount: item.remainPay,
                        date: item.remainPayDate,
                        isPaid: item.remainPayIsPaid,
                      ),
                  ],
                ),
              ),

              if (item.accNumber.isNotEmpty)
                SiteDetailRow(
                  label: '지급 수령계좌',
                  value: '${item.accBank} ${item.accNumber} (예금주: ${item.accOwner})',
                ),
              if (item.note.isNotEmpty)
                SiteDetailRow(label: '특이사항', value: item.note),

              const SizedBox(height: 14),
              Divider(color: context.colors.border, height: 1),
              const SizedBox(height: 10),

              // 하단 액션 버튼 영역 (매매계약서 열기/공유 버튼 상시 노출)
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: item.hasContractFile
                            ? const Color(0xFFF59E0B)
                            : context.colors.bgSurface,
                        foregroundColor: item.hasContractFile
                            ? Colors.white
                            : context.colors.textMuted,
                        elevation: item.hasContractFile ? 1 : 0,
                        side: BorderSide(
                          color: item.hasContractFile
                              ? const Color(0xFFF59E0B)
                              : context.colors.border,
                          width: 0.8,
                        ),
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                      ),
                      onPressed: () {
                        if (item.hasContractFile) {
                          Navigator.pop(ctx);
                          SiteFileHelper.downloadAndShareContractPdf(context: context, ref: ref, item: item);
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('해당 계약건의 매매계약서 파일이 아직 등록되지 않았습니다.'),
                              behavior: SnackBarBehavior.floating,
                            ),
                          );
                        }
                      },
                      icon: Icon(
                        item.hasContractFile
                            ? Icons.description
                            : Icons.description_outlined,
                        size: 16,
                        color: item.hasContractFile
                            ? Colors.white
                            : context.colors.textMuted,
                      ),
                      label: Text(
                        item.hasContractFile ? '계약서 열기/공유' : '계약서 미등록',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: item.hasContractFile ? FontWeight.bold : FontWeight.normal,
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
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                      ),
                      onPressed: () {
                        Navigator.pop(ctx);
                        Clipboard.setData(ClipboardData(
                            text: '매도인: ${item.ownerName}, 총 매매대금: ${numFormat.format(item.totalPrice)}원 (${item.contractArea}㎡)'));
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('계약 정보가 복사되었습니다.'),
                            behavior: SnackBarBehavior.floating,
                          ),
                        );
                      },
                      icon: const Icon(Icons.copy_rounded, size: 16),
                      label: const Text('계약 정보 복사', style: TextStyle(fontSize: 12)),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      );
    },
  );
}
