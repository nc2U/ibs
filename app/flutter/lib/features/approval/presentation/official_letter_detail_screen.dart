import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:open_filex/open_filex.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../data/letter_repository.dart';
import '../data/models/letter_model.dart';
import '../providers/letter_providers.dart';

class OfficialLetterDetailScreen extends ConsumerStatefulWidget {
  final int letterId;

  const OfficialLetterDetailScreen({
    super.key,
    required this.letterId,
  });

  @override
  ConsumerState<OfficialLetterDetailScreen> createState() =>
      _OfficialLetterDetailScreenState();
}

class _OfficialLetterDetailScreenState
    extends ConsumerState<OfficialLetterDetailScreen> {
  bool _isDownloadingPdf = false;
  bool _isSubmittingApproval = false;

  Future<void> _downloadOrSharePdf(OfficialLetterModel letter,
      {bool isShare = false}) async {
    setState(() => _isDownloadingPdf = true);
    try {
      final repo = ref.read(letterRepositoryProvider);
      final filePath = await repo.downloadLetterPdf(
        letter.id,
        letter.documentNumber,
        pdfUrl: letter.pdfFile,
      );

      if (!mounted) return;

      final docNum = letter.documentNumber;
      final title = letter.title;
      final file = XFile(filePath, name: '$docNum.pdf');

      if (isShare) {
        final box = context.findRenderObject() as RenderBox?;
        await Share.shareXFiles(
          [file],
          subject: '[공문] $title ($docNum)',
          text: '$docNum - $title',
          sharePositionOrigin:
              box != null ? box.localToGlobal(Offset.zero) & box.size : null,
        );
      } else {
        final openResult = await OpenFilex.open(filePath);
        if (openResult.type != ResultType.done && mounted) {
          await Share.shareXFiles(
            [file],
            subject: '[공문] $title ($docNum)',
            text: '$docNum - $title',
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('PDF 처리 실패: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isDownloadingPdf = false);
      }
    }
  }

  Future<void> _submitApproval() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        title: const Text('전자결재 상신'),
        content: const Text('이 공문을 전자결재 품의로 상신하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: context.colors.accentApproval,
              foregroundColor: Colors.white,
            ),
            child: const Text('상신'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() => _isSubmittingApproval = true);
    try {
      final repo = ref.read(letterRepositoryProvider);
      await repo.submitApproval(widget.letterId);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('전자결재가 성공적으로 상신되었습니다.'),
            backgroundColor: context.colors.success,
          ),
        );
        ref.invalidate(officialLetterDetailProvider(widget.letterId));
        ref.invalidate(officialLettersProvider);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('결재 상신 실패: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmittingApproval = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final letterAsync =
        ref.watch(officialLetterDetailProvider(widget.letterId));

    return Scaffold(
      backgroundColor: colors.bgPrimary,
      appBar: AppBar(
        backgroundColor: colors.bgSurface,
        elevation: 0,
        title: Text(
          '공문 상세',
          style: AppTextStyles.titleSm.copyWith(
            fontWeight: FontWeight.w700,
            color: colors.textPrimary,
          ),
        ),
        actions: [
          letterAsync.maybeWhen(
            data: (letter) => Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  icon: const Icon(Icons.share_outlined, size: 20),
                  tooltip: 'PDF 공유',
                  onPressed: _isDownloadingPdf
                      ? null
                      : () => _downloadOrSharePdf(letter, isShare: true),
                ),
                IconButton(
                  icon: const Icon(Icons.picture_as_pdf_outlined, size: 20),
                  tooltip: 'PDF 열기',
                  onPressed: _isDownloadingPdf
                      ? null
                      : () => _downloadOrSharePdf(letter, isShare: false),
                ),
              ],
            ),
            orElse: () => const SizedBox.shrink(),
          ),
        ],
      ),
      body: letterAsync.when(
        loading: () => const Center(
          child: LoadingShimmer(itemHeight: 140, itemCount: 4),
        ),
        error: (err, stack) => ErrorView(
          message: err.toString(),
          onRetry: () =>
              ref.refresh(officialLetterDetailProvider(widget.letterId)),
        ),
        data: (letter) {
          final isDispatched = letter.dispatchedAt != null;
          final canSubmit = !isDispatched &&
              letter.approvalStatus == 'none' &&
              !letter.isSoloApproval;

          return Column(
            children: [
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // 1. 공문 메타 박스 (문서번호 / 수신 / 참조 / 일자)
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: colors.bgCard,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: colors.border, width: 0.8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  letter.documentNumber.isNotEmpty
                                      ? letter.documentNumber
                                      : '문서번호 미채번',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontFamily: 'monospace',
                                    fontWeight: FontWeight.w700,
                                    color: colors.accentApproval,
                                  ),
                                ),
                                _buildStatusBadge(letter),
                              ],
                            ),
                            const Divider(height: 20),
                            _buildInfoRow('수신', letter.recipientName),
                            if (letter.via.isNotEmpty) ...[
                              const SizedBox(height: 6),
                              _buildInfoRow('경유', letter.via),
                            ],
                            if (letter.recipientReference.isNotEmpty) ...[
                              const SizedBox(height: 6),
                              _buildInfoRow('참조', letter.recipientReference),
                            ],
                            const SizedBox(height: 6),
                            _buildInfoRow('시행일',
                                letter.effectiveIssueDate ?? letter.issueDate ?? '-'),
                            const SizedBox(height: 6),
                            _buildInfoRow('기안자',
                                '${letter.drafterName} ${letter.drafterPosition}'),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // 2. 공문 제목 및 본문 내용
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: colors.bgCard,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: colors.border, width: 0.8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '제 목',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: colors.textMuted,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              letter.title,
                              style: AppTextStyles.titleSm.copyWith(
                                fontWeight: FontWeight.w800,
                                color: colors.textPrimary,
                              ),
                            ),
                            const Divider(height: 24),
                            Text(
                              '본 문',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: colors.textMuted,
                              ),
                            ),
                            const SizedBox(height: 8),
                            SelectableText(
                              letter.content,
                              style: TextStyle(
                                fontSize: 13.5,
                                height: 1.6,
                                color: colors.textPrimary,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // 3. 첨부 서류 (붙임)
                      if (letter.hasAttachments) ...[
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: colors.bgCard,
                            borderRadius: BorderRadius.circular(8),
                            border:
                                Border.all(color: colors.border, width: 0.8),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '붙 임 (첨부 서류)',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: colors.textPrimary,
                                ),
                              ),
                              const SizedBox(height: 8),
                              if (letter.attachmentText.isNotEmpty)
                                Text(
                                  letter.attachmentText,
                                  style: TextStyle(
                                      fontSize: 12.5, color: colors.textSecond),
                                ),
                              if (letter.attachments.isNotEmpty) ...[
                                ...letter.attachments.asMap().entries.map((e) {
                                  final idx = e.key + 1;
                                  final att = e.value;
                                  return Padding(
                                    padding:
                                        const EdgeInsets.symmetric(vertical: 4),
                                    child: Row(
                                      children: [
                                        Text('$idx. ',
                                            style: TextStyle(
                                                fontSize: 12,
                                                fontWeight: FontWeight.bold,
                                                color: colors.textMuted)),
                                        Expanded(
                                          child: Text(
                                            '${att.name.isNotEmpty ? att.name : att.fileName ?? '첨부파일'} (${att.quantity})',
                                            style: TextStyle(
                                                fontSize: 12.5,
                                                color: colors.textSecond),
                                          ),
                                        ),
                                      ],
                                    ),
                                  );
                                }),
                              ],
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                      ],

                      // 4. 발송 및 배송 정보
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: colors.bgCard,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: colors.border, width: 0.8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '발송 대장 정보',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                color: colors.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 8),
                            _buildInfoRow(
                                '발송방법', letter.dispatchMethodDesc ?? letter.dispatchMethod),
                            if (letter.trackingNumber.isNotEmpty) ...[
                              const SizedBox(height: 6),
                              Row(
                                children: [
                                  SizedBox(
                                    width: 70,
                                    child: Text('등기번호',
                                        style: TextStyle(
                                            fontSize: 12,
                                            color: colors.textMuted,
                                            fontWeight: FontWeight.w600)),
                                  ),
                                  Expanded(
                                    child: InkWell(
                                      onTap: () async {
                                        final numOnly = letter.trackingNumber
                                            .replaceAll(RegExp(r'[^0-9]'), '');
                                        final uri = Uri.parse(
                                            'https://service.epost.go.kr/trace.RetrieveDomRcvTraceInfo.comm?sid1=$numOnly');
                                        if (await canLaunchUrl(uri)) {
                                          await launchUrl(uri,
                                              mode: LaunchMode.externalApplication);
                                        }
                                      },
                                      child: Text(
                                        '${letter.trackingNumber} (우체국 배송조회 ➔)',
                                        style: TextStyle(
                                          fontSize: 12,
                                          fontWeight: FontWeight.bold,
                                          color: colors.accentApproval,
                                          decoration: TextDecoration.underline,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                            if (letter.dispatchedAt != null) ...[
                              const SizedBox(height: 6),
                              _buildInfoRow('발송일시',
                                  letter.dispatchedAt!.substring(0, 16).replaceAll('T', ' ')),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // ── 하단 고정 결재 상신 / PDF 버튼 바 ──
              Container(
                color: colors.bgSurface,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: SafeArea(
                  top: false,
                  child: Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _isDownloadingPdf
                              ? null
                              : () => _downloadOrSharePdf(letter, isShare: false),
                          icon: _isDownloadingPdf
                              ? const SizedBox(
                                  width: 14,
                                  height: 14,
                                  child: CircularProgressIndicator(strokeWidth: 2))
                              : const Icon(Icons.picture_as_pdf_rounded, size: 16),
                          label: const Text('PDF 보기'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: colors.textPrimary,
                            side: BorderSide(color: colors.border),
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                          ),
                        ),
                      ),
                      if (canSubmit) ...[
                        const SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: _isSubmittingApproval ? null : _submitApproval,
                            icon: _isSubmittingApproval
                                ? const SizedBox(
                                    width: 14,
                                    height: 14,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ))
                                : const Icon(Icons.send_rounded, size: 16),
                            label: const Text('전자결재 상신'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: colors.accentApproval,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    final colors = context.colors;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 70,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: colors.textMuted,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontSize: 12.5,
              color: colors.textPrimary,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildStatusBadge(OfficialLetterModel letter) {
    final colors = context.colors;
    final isDispatched = letter.dispatchedAt != null;
    final isApproved = letter.approvalStatus == 'approved';
    final isPending = letter.approvalStatus == 'pending';

    Color badgeColor = colors.textMuted;
    Color badgeBg = colors.bgSurface;
    String badgeLabel = '미상신';

    if (isDispatched) {
      badgeColor = colors.success;
      badgeBg = colors.success.withAlpha(25);
      badgeLabel = '발송완료';
    } else if (isApproved) {
      badgeColor = colors.info;
      badgeBg = colors.info.withAlpha(25);
      badgeLabel = '결재승인';
    } else if (isPending) {
      badgeColor = colors.warning;
      badgeBg = colors.warning.withAlpha(25);
      badgeLabel = '결재진행';
    } else if (letter.isSoloApproval) {
      badgeColor = colors.accentApproval;
      badgeBg = colors.accentApproval.withAlpha(25);
      badgeLabel = '단독발송';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: badgeBg,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: badgeColor.withAlpha(80), width: 0.8),
      ),
      child: Text(
        badgeLabel,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: badgeColor,
        ),
      ),
    );
  }
}
