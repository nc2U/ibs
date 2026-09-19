import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:open_filex/open_filex.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_router.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../data/inbound_letter_repository.dart';
import '../data/models/inbound_letter_model.dart';
import '../providers/inbound_letter_providers.dart';
import 'widgets/inbound_report_submit_sheet.dart';

class InboundLetterDetailScreen extends ConsumerStatefulWidget {
  final int letterId;

  const InboundLetterDetailScreen({
    super.key,
    required this.letterId,
  });

  @override
  ConsumerState<InboundLetterDetailScreen> createState() =>
      _InboundLetterDetailScreenState();
}

class _InboundLetterDetailScreenState
    extends ConsumerState<InboundLetterDetailScreen> {
  bool _isDownloadingPdf = false;
  bool _isSubmittingApproval = false;

  Future<void> _downloadOrSharePdf(InboundLetterModel letter,
      {bool isShare = false}) async {
    if (letter.scanFile == null || letter.scanFile!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('등록된 원본 스캔본 파일이 없습니다.')),
      );
      return;
    }

    setState(() => _isDownloadingPdf = true);
    try {
      final repo = ref.read(inboundLetterRepositoryProvider);
      final filePath = await repo.downloadScanPdf(
        letter.id,
        letter.receiptNumber,
        scanUrl: letter.scanFile,
      );

      if (!mounted) return;

      final docNum = letter.receiptNumber.isNotEmpty ? letter.receiptNumber : '수신공문_${letter.id}';
      final title = letter.title;
      final file = XFile(filePath, name: '$docNum.pdf');

      if (isShare) {
        final box = context.findRenderObject() as RenderBox?;
        await Share.shareXFiles(
          [file],
          subject: '[수신공문] $title ($docNum)',
          text: '$docNum - $title',
          sharePositionOrigin:
              box != null ? box.localToGlobal(Offset.zero) & box.size : null,
        );
      } else {
        final openResult = await OpenFilex.open(filePath);
        if (openResult.type != ResultType.done && mounted) {
          await Share.shareXFiles(
            [file],
            subject: '[수신공문] $title ($docNum)',
            text: '$docNum - $title',
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('스캔 파일 열람 실패: $e'),
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

  Future<void> _submitApproval(InboundLetterModel letter) async {
    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => InboundReportSubmitBottomSheet(letter: letter),
    );

    if (result == null) return;

    setState(() => _isSubmittingApproval = true);
    try {
      final repo = ref.read(inboundLetterRepositoryProvider);
      final res = await repo.submitApproval(widget.letterId, data: result);
      if (mounted) {
        ref.invalidate(inboundLetterDetailProvider(widget.letterId));
        ref.invalidate(inboundLettersProvider);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('전자결재 품의가 성공적으로 상신되었습니다.')),
        );
        final docId = res['approval_document_id'] ?? res['approval_document'];
        if (docId != null && docId is num) {
          context.push('${AppRoutes.approval}/${docId.toInt()}');
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('전자결재 상신 실패: $e'),
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
    final letterAsync = ref.watch(inboundLetterDetailProvider(widget.letterId));

    return Scaffold(
      backgroundColor: colors.bgPrimary,
      appBar: AppBar(
        title: Text(
          '수신 공문 상세',
          style: AppTextStyles.titleSm.copyWith(
            fontWeight: FontWeight.w700,
            color: colors.textPrimary,
          ),
        ),
        backgroundColor: colors.bgSurface,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, size: 18, color: colors.textPrimary),
          onPressed: () => Navigator.of(context).pop(),
        ),
        actions: [
          letterAsync.when(
            data: (letter) {
              if (!letter.hasScan) return const SizedBox.shrink();
              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: _isDownloadingPdf
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Icon(Icons.share_outlined, size: 20, color: colors.textPrimary),
                    tooltip: '스캔본 공유',
                    onPressed: _isDownloadingPdf
                        ? null
                        : () => _downloadOrSharePdf(letter, isShare: true),
                  ),
                  IconButton(
                    icon: Icon(Icons.picture_as_pdf_outlined,
                        size: 20, color: colors.accentApproval),
                    tooltip: '스캔본 보기',
                    onPressed: _isDownloadingPdf
                        ? null
                        : () => _downloadOrSharePdf(letter, isShare: false),
                  ),
                ],
              );
            },
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
      body: letterAsync.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(16),
          child: LoadingShimmer(itemHeight: 120, itemCount: 4),
        ),
        error: (err, _) => ErrorView(
          message: err.toString(),
          onRetry: () => ref.refresh(inboundLetterDetailProvider(widget.letterId)),
        ),
        data: (letter) => RefreshIndicator(
          onRefresh: () async =>
              ref.refresh(inboundLetterDetailProvider(widget.letterId).future),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // 1. 접수 메타 박스
                _buildMetaBox(context, letter),
                const SizedBox(height: 12),

                // 2. 공문 제목 및 본문 요지
                _buildContentBox(context, letter),
                const SizedBox(height: 12),

                // 3. 원본 스캔본 다운로드 및 바로보기 카드
                _buildScanFileCard(context, letter),
                const SizedBox(height: 12),

                // 4. 첨부서류 목록
                if (letter.attachments.isNotEmpty) ...[
                  _buildAttachmentsBox(context, letter),
                  const SizedBox(height: 12),
                ],

                // 5. 연동된 전자결재 및 회신 공문
                _buildRelationBox(context, letter),
                const SizedBox(height: 24),

                // 6. 하단 액션 버튼 (전자결재 상신)
                if (letter.status != 'closed' && letter.approvalDocument == null)
                  ElevatedButton.icon(
                    onPressed: _isSubmittingApproval ? null : () => _submitApproval(letter),
                    icon: _isSubmittingApproval
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Icon(Icons.send_rounded, size: 18),
                    label: const Text('전자결재 보고/품의 상신'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: colors.accentApproval,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 13),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMetaBox(BuildContext context, InboundLetterModel letter) {
    final colors = context.colors;

    // 상태 뱃지
    Color badgeColor = colors.info;
    Color badgeBg = colors.info.withAlpha(25);
    String badgeLabel = letter.statusDesc ?? '접수';

    switch (letter.status) {
      case 'received':
        badgeColor = colors.info;
        badgeBg = colors.info.withAlpha(25);
        badgeLabel = '접수';
        break;
      case 'in_progress':
        badgeColor = colors.warning;
        badgeBg = colors.warning.withAlpha(25);
        badgeLabel = '처리중';
        break;
      case 'replied':
        badgeColor = colors.success;
        badgeBg = colors.success.withAlpha(25);
        badgeLabel = '회신완료';
        break;
      case 'closed':
        badgeColor = colors.textMuted;
        badgeBg = colors.textMuted.withAlpha(20);
        badgeLabel = '종결';
        break;
    }

    return Container(
      decoration: BoxDecoration(
        color: colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: colors.border, width: 0.8),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                '접수 정보',
                style: AppTextStyles.bodySm.copyWith(
                  fontWeight: FontWeight.bold,
                  color: colors.textSecond,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: badgeBg,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: badgeColor.withAlpha(80), width: 0.8),
                ),
                child: Text(
                  badgeLabel,
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.bold,
                    color: badgeColor,
                  ),
                ),
              ),
              if (letter.dDayFormatted != null &&
                  letter.status != 'closed' &&
                  letter.status != 'replied') ...[
                const SizedBox(width: 6),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: colors.error.withAlpha(20),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: colors.error.withAlpha(80), width: 0.8),
                  ),
                  child: Text(
                    letter.dDayFormatted!,
                    style: TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.bold,
                      color: colors.error,
                    ),
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 12),
          _buildMetaRow(context, '사내 접수번호', letter.receiptNumber.isNotEmpty ? letter.receiptNumber : '-'),
          _buildMetaRow(context, '발신 기관/업체', letter.senderName.isNotEmpty ? letter.senderName : '-'),
          if (letter.documentNumber.isNotEmpty)
            _buildMetaRow(context, '발신처 문서번호', letter.documentNumber),
          if (letter.senderContact.isNotEmpty)
            _buildMetaRow(context, '발신처 연락처', letter.senderContact),
          _buildMetaRow(context, '접수일자', letter.receivedDate.isNotEmpty ? letter.receivedDate : '-'),
          if (letter.replyDueDate != null && letter.replyDueDate!.isNotEmpty)
            _buildMetaRow(context, '회신 기한', letter.replyDueDate!),
          if (letter.recipientDeptName != null && letter.recipientDeptName!.isNotEmpty)
            _buildMetaRow(context, '배부/주관 부서', letter.recipientDeptName!),
          if (letter.recipientManagerName != null && letter.recipientManagerName!.isNotEmpty)
            _buildMetaRow(context, '처리 담당자', letter.recipientManagerName!),
          if (letter.creator != null)
            _buildMetaRow(context, '접수 등록자', letter.creator!.username),
        ],
      ),
    );
  }

  Widget _buildMetaRow(BuildContext context, String label, String value) {
    final colors = context.colors;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 95,
            child: Text(
              label,
              style: TextStyle(
                fontSize: 12.5,
                color: colors.textMuted,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                fontSize: 13,
                color: colors.textPrimary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContentBox(BuildContext context, InboundLetterModel letter) {
    final colors = context.colors;
    return Container(
      decoration: BoxDecoration(
        color: colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: colors.border, width: 0.8),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            letter.title,
            style: AppTextStyles.titleSm.copyWith(
              fontWeight: FontWeight.w700,
              color: colors.textPrimary,
            ),
          ),
          if (letter.content.isNotEmpty) ...[
            const SizedBox(height: 12),
            Divider(color: colors.borderSubtle, height: 1),
            const SizedBox(height: 12),
            Text(
              letter.content,
              style: TextStyle(
                fontSize: 13.5,
                color: colors.textPrimary,
                height: 1.6,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildScanFileCard(BuildContext context, InboundLetterModel letter) {
    final colors = context.colors;
    final hasScan = letter.hasScan;

    return Container(
      decoration: BoxDecoration(
        color: colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: colors.border, width: 0.8),
      ),
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: hasScan
                  ? colors.accentApproval.withAlpha(20)
                  : colors.bgSurface,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              Icons.picture_as_pdf_rounded,
              color: hasScan ? colors.accentApproval : colors.textMuted,
              size: 26,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '공문 원본 스캔본',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: colors.textPrimary,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  hasScan ? '원본 스캔 PDF 파일이 등록되어 있습니다.' : '등록된 원본 스캔본이 없습니다.',
                  style: TextStyle(fontSize: 11.5, color: colors.textMuted),
                ),
              ],
            ),
          ),
          if (hasScan)
            ElevatedButton(
              onPressed: _isDownloadingPdf
                  ? null
                  : () => _downloadOrSharePdf(letter, isShare: false),
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.accentApproval,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
              ),
              child: _isDownloadingPdf
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('열람 / 공유', style: TextStyle(fontSize: 12)),
            ),
        ],
      ),
    );
  }

  Widget _buildAttachmentsBox(BuildContext context, InboundLetterModel letter) {
    final colors = context.colors;
    return Container(
      decoration: BoxDecoration(
        color: colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: colors.border, width: 0.8),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.attach_file_rounded, size: 16, color: colors.textMuted),
              const SizedBox(width: 6),
              Text(
                '붙임 서류 (${letter.attachments.length})',
                style: AppTextStyles.bodySm.copyWith(
                  fontWeight: FontWeight.bold,
                  color: colors.textSecond,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ...letter.attachments.map((att) {
            return Container(
              margin: const EdgeInsets.only(bottom: 6),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: colors.bgSurface,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: colors.borderSubtle, width: 0.6),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          att.name.isNotEmpty ? att.name : (att.fileName ?? '첨부파일'),
                          style: TextStyle(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w600,
                            color: colors.textPrimary,
                          ),
                        ),
                        if (att.quantity.isNotEmpty)
                          Text(
                            att.quantity,
                            style: TextStyle(fontSize: 11, color: colors.textMuted),
                          ),
                      ],
                    ),
                  ),
                  if (att.file != null && att.file!.isNotEmpty)
                    IconButton(
                      icon: Icon(Icons.download_rounded, size: 18, color: colors.accentApproval),
                      onPressed: () async {
                        final uri = Uri.tryParse(att.file!);
                        if (uri != null) {
                          await launchUrl(uri, mode: LaunchMode.externalApplication);
                        }
                      },
                    ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildRelationBox(BuildContext context, InboundLetterModel letter) {
    final colors = context.colors;
    final approval = letter.approvalDocumentDetail;
    final replies = letter.replyLetters;

    if (approval == null && replies.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      decoration: BoxDecoration(
        color: colors.bgCard,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: colors.border, width: 0.8),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '연관 문서 정보',
            style: AppTextStyles.bodySm.copyWith(
              fontWeight: FontWeight.bold,
              color: colors.textSecond,
            ),
          ),
          const SizedBox(height: 10),
          if (approval != null) ...[
            InkWell(
              onTap: () {
                final docId = approval['pk'];
                if (docId != null) {
                  context.push('${AppRoutes.approval}/$docId');
                }
              },
              child: Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: colors.bgSurface,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: colors.borderSubtle, width: 0.6),
                ),
                child: Row(
                  children: [
                    Icon(Icons.assignment_outlined, size: 18, color: colors.accentApproval),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '연동 전자결재: ${approval['title'] ?? '-'}',
                            style: TextStyle(
                              fontSize: 12.5,
                              fontWeight: FontWeight.bold,
                              color: colors.textPrimary,
                            ),
                          ),
                          Text(
                            '상태: ${approval['status_desc'] ?? '-'}',
                            style: TextStyle(fontSize: 11, color: colors.textMuted),
                          ),
                        ],
                      ),
                    ),
                    Icon(Icons.chevron_right_rounded, size: 18, color: colors.textMuted),
                  ],
                ),
              ),
            ),
          ],
          if (replies.isNotEmpty) ...[
            const SizedBox(height: 8),
            ...replies.map((r) {
              final rPk = r['pk'];
              final rNum = r['document_number'] ?? '';
              final rTitle = r['title'] ?? '';
              return InkWell(
                onTap: () {
                  if (rPk != null) {
                    context.push('${AppRoutes.approval}/letters/$rPk');
                  }
                },
                child: Container(
                  margin: const EdgeInsets.only(top: 4),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: colors.bgSurface,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: colors.borderSubtle, width: 0.6),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.reply_rounded, size: 18, color: colors.success),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '회신 발신공문: $rTitle',
                              style: TextStyle(
                                fontSize: 12.5,
                                fontWeight: FontWeight.bold,
                                color: colors.textPrimary,
                              ),
                            ),
                            if (rNum.isNotEmpty)
                              Text(
                                '문서번호: $rNum',
                                style: TextStyle(fontSize: 11, color: colors.textMuted),
                              ),
                          ],
                        ),
                      ),
                      Icon(Icons.chevron_right_rounded, size: 18, color: colors.textMuted),
                    ],
                  ),
                ),
              );
            }),
          ],
        ],
      ),
    );
  }
}
