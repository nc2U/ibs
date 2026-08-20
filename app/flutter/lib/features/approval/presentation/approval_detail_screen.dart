import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../../../../core/models/common_models.dart';
import '../data/models/approval_model.dart';
import '../providers/approval_providers.dart';
import 'widgets/approval_action_bottom_sheet.dart';
import 'widgets/approval_pdf_helper.dart';
import 'widgets/approval_route_timeline.dart';
import 'widgets/approval_status_chip.dart';

class ApprovalDetailScreen extends ConsumerWidget {
  final int docId;

  const ApprovalDetailScreen({
    super.key,
    required this.docId,
  });

  String _formatDateTime(String? raw) {
    if (raw == null || raw.isEmpty) return '-';
    try {
      final dt = DateTime.parse(raw).toLocal();
      return '${dt.year}.${dt.month.toString().padLeft(2, '0')}.${dt.day.toString().padLeft(2, '0')} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return raw;
    }
  }

  String _formatCurrency(dynamic val) {
    if (val == null) return '-';
    final numVal = num.tryParse(val.toString().replaceAll(',', ''));
    if (numVal == null) return val.toString();
    final parts = numVal.toStringAsFixed(0).split('');
    final buffer = StringBuffer();
    for (int i = 0; i < parts.length; i++) {
      if (i > 0 && (parts.length - i) % 3 == 0) buffer.write(',');
      buffer.write(parts[i]);
    }
    return '${buffer.toString()} 원';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final docAsync = ref.watch(approvalDetailProvider(docId));
    final currentUser = ref.watch(currentUserProvider).valueOrNull;

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        title: Text(
          '결재 문서 상세',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.w800,
            color: context.colors.textPrimary,
          ),
        ),
        backgroundColor: context.colors.bgCard,
        elevation: 0,
        actions: [
          docAsync.maybeWhen(
            data: (doc) => IconButton(
              icon: Icon(Icons.picture_as_pdf_rounded, color: context.colors.accentApprovalDeep),
              tooltip: 'PDF 다운로드 / 인쇄',
              onPressed: () => exportApprovalPdf(context, ref, doc),
            ),
            orElse: () => const SizedBox.shrink(),
          ),
          IconButton(
            icon: Icon(Icons.refresh_rounded, color: context.colors.textSecond),
            tooltip: '새로고침',
            onPressed: () => ref.refresh(approvalDetailProvider(docId)),
          ),
        ],
      ),
      body: docAsync.when(
        data: (doc) => _buildDetailBody(context, ref, doc, currentUser?.pk),
        loading: () => const LoadingShimmer(itemCount: 4, itemHeight: 120),
        error: (err, _) => ErrorView(
          message: '문서 상세 정보를 불러오지 못했습니다.',
          subMessage: err.toString(),
          onRetry: () => ref.refresh(approvalDetailProvider(docId)),
        ),
      ),
      bottomNavigationBar: docAsync.maybeWhen(
        data: (doc) => _buildBottomActionBar(context, ref, doc, currentUser?.pk),
        orElse: () => null,
      ),
    );
  }

  Widget _buildDetailBody(
    BuildContext context,
    WidgetRef ref,
    ApprovalDocumentModel doc,
    int? currentUserId,
  ) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // ── 1. 문서 기본 정보 카드 ─────────────────────────────────
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              borderRadius: BorderRadius.zero,
              border: Border.all(color: context.colors.border, width: 0.8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 유형 & 상태 뱃지
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                      decoration: BoxDecoration(
                        color: context.colors.accentApproval.withAlpha(20),
                        border: Border.all(color: context.colors.accentApproval.withAlpha(70), width: 0.6),
                      ),
                      child: Text(
                        doc.docTypeName ?? '기안서',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: context.colors.accentApprovalDeep,
                        ),
                      ),
                    ),
                    if (doc.docNumber.isNotEmpty) ...[
                      const SizedBox(width: 8),
                      Text(
                        doc.docNumber,
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: context.colors.textMuted,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                    const Spacer(),
                    ApprovalStatusChip(status: doc.status, statusDesc: doc.statusDesc),
                  ],
                ),
                const SizedBox(height: 12),

                // 제목
                Text(
                  doc.title,
                  style: AppTextStyles.titleLg.copyWith(
                    fontWeight: FontWeight.w800,
                    color: context.colors.textPrimary,
                  ),
                ),
                const SizedBox(height: 14),
                Divider(color: context.colors.border, height: 1, thickness: 0.8),
                const SizedBox(height: 14),

                // 기안자 정보 그리드
                _buildInfoRow(context, '기안자', doc.drafterName ?? doc.drafter.username),
                const SizedBox(height: 6),
                _buildInfoRow(context, '기안 부서/직책', doc.drafterAssignmentDesc ?? doc.departmentName ?? '-'),
                const SizedBox(height: 6),
                _buildInfoRow(context, '기안일시', _formatDateTime(doc.submittedAt ?? doc.createdAt)),
                if (doc.completedAt != null) ...[
                  const SizedBox(height: 6),
                  _buildInfoRow(context, '완료일시', _formatDateTime(doc.completedAt)),
                ],
              ],
            ),
          ),
          const SizedBox(height: 14),

          // ── 2. 결재선 타임라인 ──────────────────────────────────────
          if (doc.steps != null && doc.steps!.isNotEmpty) ...[
            ApprovalRouteTimeline(
              steps: doc.steps!,
              drafterName: doc.drafterName ?? doc.drafter.username,
              submittedAt: doc.submittedAt ?? doc.createdAt,
            ),
            const SizedBox(height: 14),
          ],

          // ── 3. 문서 본문 내용 카드 ─────────────────────────────────
          _buildContentCard(context, doc),
          const SizedBox(height: 14),

          // ── 4. 첨부파일 목록 ─────────────────────────────────────────
          if (doc.attachments != null && doc.attachments!.isNotEmpty) ...[
            _buildAttachmentsCard(context, doc.attachments!),
            const SizedBox(height: 14),
          ],

          // ── 5. 참조자 목록 ───────────────────────────────────────────
          if (doc.observers != null && doc.observers!.isNotEmpty) ...[
            _buildObserversCard(context, doc.observers!),
            const SizedBox(height: 24),
          ],
        ],
      ),
    );
  }

  Widget _buildInfoRow(BuildContext context, String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 90,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: context.colors.textMuted,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w500,
              color: context.colors.textPrimary,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildContentCard(BuildContext context, ApprovalDocumentModel doc) {
    final content = doc.content;
    final templateKey = doc.docTypeDetail?.formTemplateKey;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.description_outlined, size: 16, color: context.colors.accentApproval),
              const SizedBox(width: 6),
              Text(
                '문서 내용',
                style: AppTextStyles.titleSm.copyWith(
                  fontWeight: FontWeight.w700,
                  color: context.colors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // 템플릿별 맞춤 뷰
          if (templateKey == 'leave_application')
            _buildLeaveContent(context, content)
          else if (templateKey == 'expense_report')
            _buildExpenseContent(context, content)
          else if (templateKey == 'purchase_order')
            _buildPurchaseContent(context, content)
          else
            _buildGenericContent(context, content),
        ],
      ),
    );
  }

  Widget _buildLeaveContent(BuildContext context, Map<String, dynamic> c) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildContentItem(context, '휴가 구분', c['leave_type']?.toString() ?? '-'),
        _buildContentItem(context, '시작일', c['start_date']?.toString() ?? '-'),
        _buildContentItem(context, '종료일', c['end_date']?.toString() ?? '-'),
        _buildContentItem(context, '휴가 일수', '${c['days'] ?? '-'} 일'),
        if (c['reason'] != null)
          _buildContentItem(context, '사유', c['reason'].toString(), isMultiline: true),
      ],
    );
  }

  Widget _buildExpenseContent(BuildContext context, Map<String, dynamic> c) {
    final items = c['items'] as List?;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildContentItem(context, '총 지출 금액', _formatCurrency(c['total_amount'] ?? c['amount'])),
        if (c['purpose'] != null)
          _buildContentItem(context, '지출 목적', c['purpose'].toString()),
        if (items != null && items.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(
            '세부 지출 내역',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: context.colors.textPrimary),
          ),
          const SizedBox(height: 6),
          for (final item in items)
            if (item is Map)
              Container(
                margin: const EdgeInsets.only(bottom: 6),
                padding: const EdgeInsets.all(8),
                color: context.colors.bgSurface,
                child: Row(
                  children: [
                    Expanded(child: Text(item['name']?.toString() ?? '', style: const TextStyle(fontSize: 12))),
                    Text(_formatCurrency(item['amount']), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                  ],
                ),
              ),
        ],
      ],
    );
  }

  Widget _buildPurchaseContent(BuildContext context, Map<String, dynamic> c) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildContentItem(context, '품의 금액', _formatCurrency(c['total_amount'] ?? c['amount'])),
        if (c['vendor'] != null)
          _buildContentItem(context, '거래처', c['vendor'].toString()),
        if (c['purpose'] != null)
          _buildContentItem(context, '구매 목적/사유', c['purpose'].toString(), isMultiline: true),
      ],
    );
  }

  Widget _buildGenericContent(BuildContext context, Map<String, dynamic> c) {
    if (c.isEmpty) {
      return Text('본문 내용이 없습니다.', style: TextStyle(fontSize: 12.5, color: context.colors.textMuted));
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final entry in c.entries)
          _buildContentItem(
            context,
            entry.key,
            entry.value is num ? _formatCurrency(entry.value) : entry.value.toString(),
            isMultiline: entry.value.toString().length > 30,
          ),
      ],
    );
  }

  Widget _buildContentItem(BuildContext context, String label, String value, {bool isMultiline = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600, color: context.colors.textMuted)),
          const SizedBox(height: 2),
          Text(value, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: context.colors.textPrimary)),
        ],
      ),
    );
  }

  Widget _buildAttachmentsCard(BuildContext context, List<ApprovalAttachmentModel> files) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.attach_file_rounded, size: 16, color: context.colors.accentApproval),
              const SizedBox(width: 6),
              Text(
                '첨부파일 (${files.length})',
                style: AppTextStyles.titleSm.copyWith(fontWeight: FontWeight.w700, color: context.colors.textPrimary),
              ),
            ],
          ),
          const SizedBox(height: 12),
          for (final f in files)
            InkWell(
              onTap: () async {
                final url = f.fileUrl ?? f.file;
                if (url != null && await canLaunchUrl(Uri.parse(url))) {
                  await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
                }
              },
              child: Container(
                margin: const EdgeInsets.only(bottom: 6),
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                decoration: BoxDecoration(
                  color: context.colors.bgSurface,
                  border: Border.all(color: context.colors.borderSubtle, width: 0.6),
                ),
                child: Row(
                  children: [
                    Icon(Icons.insert_drive_file_outlined, size: 16, color: context.colors.textSecond),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        f.fileName,
                        style: TextStyle(fontSize: 12.5, color: context.colors.textPrimary, decoration: TextDecoration.underline),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Icon(Icons.download_rounded, size: 16, color: context.colors.textMuted),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildObserversCard(BuildContext context, List<SimpleUserModel> observers) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Row(
        children: [
          Icon(Icons.visibility_outlined, size: 15, color: context.colors.textMuted),
          const SizedBox(width: 6),
          Text('참조 / 공람: ', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: context.colors.textMuted)),
          const SizedBox(width: 6),
          Expanded(
            child: Wrap(
              spacing: 6,
              children: observers.map((u) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: context.colors.bgSurface,
                    border: Border.all(color: context.colors.border, width: 0.5),
                  ),
                  child: Text(u.username, style: TextStyle(fontSize: 11, color: context.colors.textSecond)),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget? _buildBottomActionBar(
    BuildContext context,
    WidgetRef ref,
    ApprovalDocumentModel doc,
    int? currentUserId,
  ) {
    if (currentUserId == null) return null;

    // 현재 단계에서 내가 결재자이고 단계 상태가 pending인지 확인
    final currentStepObj = doc.steps?.where((s) => s.stepOrder == doc.currentStep).firstOrNull;
    final isMyTurn = doc.status == 'pending' &&
        currentStepObj != null &&
        currentStepObj.status == 'pending' &&
        currentStepObj.approvers.any((u) => u.pk == currentUserId);

    final isMyDraft = doc.drafter.pk == currentUserId;

    if (isMyTurn) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withAlpha(10),
              blurRadius: 8,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: SafeArea(
          child: Row(
            children: [
              // 반려 버튼
              Expanded(
                child: SizedBox(
                  height: 44,
                  child: ElevatedButton.icon(
                    onPressed: () {
                      ApprovalActionBottomSheet.show(
                        context,
                        type: ApprovalActionModalType.reject,
                        title: doc.title,
                        onConfirm: (comment) => ref
                            .read(approvalActionControllerProvider.notifier)
                            .reject(doc.id, comment: comment ?? ''),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: context.colors.error,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      elevation: 0,
                    ),
                    icon: const Icon(Icons.close_rounded, color: Colors.white, size: 18),
                    label: const Text('반려', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                  ),
                ),
              ),
              const SizedBox(width: 8),

              // 의견 버튼
              SizedBox(
                height: 44,
                child: OutlinedButton(
                  onPressed: () {
                    ApprovalActionBottomSheet.show(
                      context,
                      type: ApprovalActionModalType.comment,
                      title: doc.title,
                      onConfirm: (comment) => ref
                          .read(approvalActionControllerProvider.notifier)
                          .addComment(doc.id, comment: comment ?? ''),
                    );
                  },
                  style: OutlinedButton.styleFrom(
                    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                    side: BorderSide(color: context.colors.border),
                  ),
                  child: Text('의견', style: TextStyle(color: context.colors.textSecond, fontWeight: FontWeight.w600)),
                ),
              ),
              const SizedBox(width: 8),

              // 승인 버튼
              Expanded(
                flex: 2,
                child: SizedBox(
                  height: 44,
                  child: ElevatedButton.icon(
                    onPressed: () {
                      ApprovalActionBottomSheet.show(
                        context,
                        type: ApprovalActionModalType.approve,
                        title: doc.title,
                        onConfirm: (comment) => ref
                            .read(approvalActionControllerProvider.notifier)
                            .approve(doc.id, comment: comment),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: context.colors.success,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      elevation: 0,
                    ),
                    icon: const Icon(Icons.check_rounded, color: Colors.white, size: 18),
                    label: const Text('결재 승인', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    // 내가 기안자이고 임시저장 상태인 경우 -> 상신 버튼
    if (isMyDraft && doc.status == 'draft') {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
        ),
        child: SafeArea(
          child: SizedBox(
            height: 44,
            child: ElevatedButton.icon(
              onPressed: () {
                ApprovalActionBottomSheet.show(
                  context,
                  type: ApprovalActionModalType.submit,
                  title: doc.title,
                  onConfirm: (_) => ref
                      .read(approvalActionControllerProvider.notifier)
                      .submit(doc.id),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: context.colors.accentApproval,
                shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                elevation: 0,
              ),
              icon: const Icon(Icons.send_rounded, color: Colors.white, size: 18),
              label: const Text('결재 상신하기', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
            ),
          ),
        ),
      );
    }

    // 내가 기안자이고 결재 진행 중인 경우 -> 회수 버튼
    if (isMyDraft && doc.status == 'pending') {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
        ),
        child: SafeArea(
          child: SizedBox(
            height: 44,
            child: OutlinedButton.icon(
              onPressed: () {
                ApprovalActionBottomSheet.show(
                  context,
                  type: ApprovalActionModalType.cancel,
                  title: doc.title,
                  onConfirm: (_) => ref
                      .read(approvalActionControllerProvider.notifier)
                      .cancel(doc.id),
                );
              },
              style: OutlinedButton.styleFrom(
                shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                side: BorderSide(color: context.colors.error.withAlpha(120)),
              ),
              icon: Icon(Icons.undo_rounded, color: context.colors.error, size: 18),
              label: Text('기안 회수', style: TextStyle(color: context.colors.error, fontWeight: FontWeight.w700)),
            ),
          ),
        ),
      );
    }

    return null;
  }
}
