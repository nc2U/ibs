import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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
    final currentUserId = ref.watch(currentUserIdProvider);

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
            data: (doc) => (doc.status == 'approved' && doc.pdfUrl != null && doc.pdfUrl!.isNotEmpty)
                ? IconButton(
                    icon: Icon(Icons.picture_as_pdf_rounded, color: context.colors.accentApprovalDeep),
                    tooltip: 'PDF 다운로드 / 인쇄',
                    onPressed: () => exportApprovalPdf(context, ref, doc),
                  )
                : const SizedBox.shrink(),
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
        data: (doc) => _buildDetailBody(context, ref, doc, currentUserId),
        loading: () => const LoadingShimmer(itemCount: 4, itemHeight: 120),
        error: (err, _) => ErrorView(
          message: '문서 상세 정보를 불러오지 못했습니다.',
          subMessage: err.toString(),
          onRetry: () => ref.refresh(approvalDetailProvider(docId)),
        ),
      ),
      bottomNavigationBar: docAsync.maybeWhen(
        data: (doc) => _buildBottomActionBar(context, ref, doc, currentUserId),
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
          // ── 회수/임시저장 안내 배너 (결재자가 과거 알림/링크로 유입된 경우) ──
          if (doc.status == 'draft' && doc.drafter.pk != currentUserId) ...[
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(
                color: Colors.amber.withAlpha(25),
                border: Border.all(color: Colors.amber.withAlpha(120), width: 0.8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline_rounded, color: Colors.amber, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      '이 문서는 기안자가 내용을 수정/보완하기 위해 회수한 상태(임시저장)입니다. 기안자가 재상신하면 결재를 진행하실 수 있습니다.',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: context.colors.textPrimary),
                    ),
                  ),
                ],
              ),
            ),
          ],

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
    final normKey = templateKey?.toUpperCase();

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
          if (normKey == 'LEAVE_APPLICATION' || normKey == 'LEAVE')
            _buildLeaveContent(context, content)
          else if (normKey == 'EXPENSE_REPORT' || normKey == 'EXPENSE')
            _buildExpenseContent(context, content)
          else if (normKey == 'PURCHASE_ORDER' || normKey == 'PURCHASE')
            _buildPurchaseContent(context, content)
          else if (normKey == 'OFFICIAL_LETTER')
            _buildOfficialLetterContent(context, content)
          else if (normKey == 'BUSINESS_TRIP' || normKey == 'TRIP')
            _buildBusinessTripContent(context, content)
          else if (normKey == 'OVERTIME' || normKey == 'OVERTIME_WORK')
            _buildOvertimeContent(context, content)
          else if (normKey == 'HR_APPOINTMENT' || normKey == 'APPOINTMENT')
            _buildHrAppointmentContent(context, content)
          else if (normKey == 'HR_REQUEST' || normKey == 'CERT_REQUEST')
            _buildHrRequestContent(context, content)
          else if (normKey == 'EXPENSE_SETTLEMENT' || normKey == 'SETTLEMENT')
            _buildExpenseSettlementContent(context, content)
          else if (normKey == 'ADVANCE' || normKey == 'ADVANCE_PAY' || normKey == 'ADVANCE_REQUEST')
            _buildAdvancePaymentContent(context, content)
          else if (normKey == 'CONTRACT' || normKey == 'CONTRACT_APPROVAL' || normKey == 'CONTRACT_PROPOSAL')
            _buildContractContent(context, content)
          else if (normKey == 'CONTRACT_CHANGE' || normKey == 'CONTRACT_TERMINATION' || normKey == 'CONTRACT_AMENDMENT')
            _buildContractChangeContent(context, content)
          else if (normKey == 'LEGAL_REVIEW' || normKey == 'LEGAL_CONSULTATION' || normKey == 'LEGAL_ADVICE')
            _buildLegalReviewContent(context, content)
          else if (normKey == 'BUSINESS_REVIEW' || normKey == 'PROJECT_FEASIBILITY' || normKey == 'BIZ_FEASIBILITY' || normKey == 'PROJECT_REVIEW' || normKey == 'INVESTMENT_REVIEW')
            _buildBusinessReviewContent(context, content)
          else if (normKey == 'BUSINESS_APPROVAL' || normKey == 'PROJECT_APPROVAL' || normKey == 'DEV_APPROVAL' || normKey == 'INVESTMENT_APPROVAL')
            _buildBusinessApprovalContent(context, content)
          else if (normKey == 'PROJECT_DECISION' || normKey == 'PROJECT_KEY_DECISION' || normKey == 'DECISION_PROPOSAL' || normKey == 'KEY_DECISION')
            _buildProjectDecisionContent(context, content)
          else if (normKey == 'GENERAL' || normKey == 'BIZ_APPROVAL')
            _buildGeneralProposalContent(context, content)
          else
            _buildGenericContent(context, content),
        ],
      ),
    );
  }

  Widget _buildProjectDecisionContent(BuildContext context, Map<String, dynamic> c) {
    String dtTypeName;
    final dt = c['decision_type'];
    if (dt == 'DESIGN_SPEC') {
      dtTypeName = '설계변경/스펙결정';
    } else if (dt == 'SALES_PRICING') {
      dtTypeName = '분양가/분양조건';
    } else if (dt == 'CONSTRUCTION_METHOD') {
      dtTypeName = '시공공법/자재선정';
    } else if (dt == 'FINANCIAL_STRUCTURING') {
      dtTypeName = '금융구조/PF변경';
    } else if (dt == 'CLAIM_DISPUTE') {
      dtTypeName = '민원/분쟁대응';
    } else if (dt == 'CONTRACTOR_TERMINATION') {
      dtTypeName = '업체선정/타절';
    } else {
      dtTypeName = '프로젝트 의사결정';
    }

    String ugTypeName;
    final ug = c['urgency'];
    if (ug == 'CRITICAL') {
      ugTypeName = '즉시 결정';
    } else if (ug == 'URGENT') {
      ugTypeName = '긴급(금주내)';
    } else {
      ugTypeName = '보통';
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '현안 분야', dtTypeName)),
            Expanded(child: _buildContentItem(context, '긴급도', ugTypeName)),
          ],
        ),
        Row(
          children: [
            Expanded(
              child: _buildContentItem(
                context,
                '심의 안건명',
                (c['decision_subject'] ?? c['project_name'] ?? c['case_title'] ?? '-').toString(),
              ),
            ),
            if (c['decision_due_date'] != null)
              Expanded(child: _buildContentItem(context, '결정 목표일', c['decision_due_date'].toString())),
          ],
        ),
        if (c['financial_impact'] != null && num.tryParse(c['financial_impact'].toString()) != null && num.parse(c['financial_impact'].toString()) > 0)
          _buildContentItem(context, '재무적 영향 (비용)', _formatCurrency(c['financial_impact'])),
        _buildContentItem(
          context,
          '현안 배경 및 문제점',
          (c['background_issue'] ?? c['purpose'] ?? c['reason'] ?? c['content'] ?? c['body'] ?? '-').toString(),
          isMultiline: true,
        ),
        if (c['option_1'] != null && c['option_1'].toString().isNotEmpty)
          _buildContentItem(context, '대안 1 (원안)', c['option_1'].toString(), isMultiline: true),
        if (c['option_2'] != null && c['option_2'].toString().isNotEmpty)
          _buildContentItem(context, '대안 2 (추천안/변경안)', c['option_2'].toString(), isMultiline: true),
        if (c['option_3'] != null && c['option_3'].toString().isNotEmpty)
          _buildContentItem(context, '대안 3 (선택안)', c['option_3'].toString(), isMultiline: true),
        _buildContentItem(
          context,
          '주관부서 추천안 및 선정 사유',
          (c['recommendation'] ?? '-').toString(),
          isMultiline: true,
        ),
        if (c['action_plan'] != null && c['action_plan'].toString().isNotEmpty)
          _buildContentItem(context, '향후 조치 계획', c['action_plan'].toString()),
        if (c['enclosed_docs'] != null && c['enclosed_docs'].toString().isNotEmpty)
          _buildContentItem(context, '첨부 서류', c['enclosed_docs'].toString()),
        if (c['note'] != null && c['note'].toString().isNotEmpty && c['enclosed_docs'] == null)
          _buildContentItem(context, '비고', c['note'].toString()),
      ],
    );
  }

  Widget _buildBusinessApprovalContent(BuildContext context, Map<String, dynamic> c) {
    String apTypeName;
    final ap = c['approval_type'];
    if (ap == 'NEW_LAUNCH') {
      apTypeName = '사업 론칭 승인';
    } else if (ap == 'LAND_ACQUISITION') {
      apTypeName = '토지매매/계약금 집행';
    } else if (ap == 'SPC_ESTABLISH') {
      apTypeName = 'SPC/PFV 설립';
    } else if (ap == 'PF_EXECUTION') {
      apTypeName = '본PF약정/인출';
    } else if (ap == 'CONSTRUCTION_START') {
      apTypeName = '시공 도급/착공';
    } else {
      apTypeName = '주요 사업 승인';
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: _buildContentItem(
                context,
                '사업명 (프로젝트)',
                (c['project_name'] ?? c['case_title'] ?? '-').toString(),
              ),
            ),
            Expanded(child: _buildContentItem(context, '승인 의결 구분', apTypeName)),
          ],
        ),
        if (c['location'] != null || c['biz_scale_summary'] != null)
          Row(
            children: [
              if (c['location'] != null && c['location'].toString().isNotEmpty)
                Expanded(child: _buildContentItem(context, '사업 부지 위치', c['location'].toString())),
              if (c['biz_scale_summary'] != null && c['biz_scale_summary'].toString().isNotEmpty)
                Expanded(child: _buildContentItem(context, '사업 규모 / 용도', c['biz_scale_summary'].toString())),
            ],
          ),
        Row(
          children: [
            Expanded(
              child: _buildContentItem(
                context,
                '금회 승인 요청액',
                _formatCurrency(c['requested_amount'] ?? c['approval_budget'] ?? c['amount']),
              ),
            ),
            if (c['total_project_cost'] != null)
              Expanded(child: _buildContentItem(context, '전체 총사업비', _formatCurrency(c['total_project_cost']))),
          ],
        ),
        if (c['budget_usage_plan'] != null && c['budget_usage_plan'].toString().isNotEmpty)
          _buildContentItem(context, '금회 승인예산 집행 내역', c['budget_usage_plan'].toString()),
        _buildContentItem(
          context,
          '승인 의결 사항',
          (c['resolution_matters'] ?? c['purpose'] ?? c['reason'] ?? c['content'] ?? c['body'] ?? '-').toString(),
          isMultiline: true,
        ),
        if (c['pm_lead'] != null || c['target_schedule'] != null)
          Row(
            children: [
              if (c['pm_lead'] != null && c['pm_lead'].toString().isNotEmpty)
                Expanded(child: _buildContentItem(context, '총괄 PM / 담당', c['pm_lead'].toString())),
              if (c['target_schedule'] != null && c['target_schedule'].toString().isNotEmpty)
                Expanded(child: _buildContentItem(context, '향후 추진 일정', c['target_schedule'].toString())),
            ],
          ),
        if (c['expected_effects'] != null && c['expected_effects'].toString().isNotEmpty)
          _buildContentItem(context, '기대 효과 / 대책', c['expected_effects'].toString(), isMultiline: true),
        if (c['enclosed_docs'] != null && c['enclosed_docs'].toString().isNotEmpty)
          _buildContentItem(context, '첨부 서류', c['enclosed_docs'].toString()),
        if (c['note'] != null && c['note'].toString().isNotEmpty && c['enclosed_docs'] == null)
          _buildContentItem(context, '비고', c['note'].toString()),
      ],
    );
  }

  Widget _buildBusinessReviewContent(BuildContext context, Map<String, dynamic> c) {
    String bizTypeName;
    final bt = c['biz_type'];
    if (bt == 'DEV_SELF') {
      bizTypeName = '자체 개발사업';
    } else if (bt == 'DEV_TRUST') {
      bizTypeName = '토지신탁';
    } else if (bt == 'CONTRACT_CIVIL') {
      bizTypeName = '단순 도급(시공)';
    } else if (bt == 'REDEVELOPMENT') {
      bizTypeName = '재개발/재건축';
    } else if (bt == 'PF_INVEST') {
      bizTypeName = '지분투자/공동개발';
    } else {
      bizTypeName = '신규 사업';
    }

    final rev = num.tryParse(c['total_revenue']?.toString() ?? '') ?? 0;
    final cst = num.tryParse(c['total_cost']?.toString() ?? '') ?? 0;
    final net = c['net_profit'] ?? (rev - cst);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: _buildContentItem(
                context,
                '사업명 (프로젝트)',
                (c['project_name'] ?? c['case_title'] ?? '-').toString(),
              ),
            ),
            Expanded(child: _buildContentItem(context, '사업 유형', bizTypeName)),
          ],
        ),
        if (c['location'] != null && c['location'].toString().isNotEmpty)
          _buildContentItem(context, '사업 부지 위치', c['location'].toString()),
        if (c['building_scale'] != null || c['land_area'] != null || c['gross_floor_area'] != null)
          Row(
            children: [
              if (c['building_scale'] != null && c['building_scale'].toString().isNotEmpty)
                Expanded(child: _buildContentItem(context, '건축 규모', c['building_scale'].toString())),
              if (c['land_area'] != null || c['gross_floor_area'] != null)
                Expanded(
                  child: _buildContentItem(
                    context,
                    '대지 / 연면적',
                    '${c['land_area'] != null ? '대지: ${c['land_area']}㎡' : ''} ${c['gross_floor_area'] != null ? '연면적: ${c['gross_floor_area']}㎡' : ''}',
                  ),
                ),
            ],
          ),
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '총 매출/분양수입', _formatCurrency(c['total_revenue']))),
            Expanded(child: _buildContentItem(context, '총 사업비 (지출)', _formatCurrency(c['total_cost']))),
          ],
        ),
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '예상 세전 이익', _formatCurrency(net))),
            if (c['profit_rate'] != null)
              Expanded(child: _buildContentItem(context, '수익률 (ROI)', '${c['profit_rate']} %')),
          ],
        ),
        if (c['required_equity'] != null || c['pf_loan_amount'] != null)
          Row(
            children: [
              if (c['required_equity'] != null)
                Expanded(child: _buildContentItem(context, '자기자본 (Equity)', _formatCurrency(c['required_equity']))),
              if (c['pf_loan_amount'] != null)
                Expanded(child: _buildContentItem(context, 'PF 조달규모', _formatCurrency(c['pf_loan_amount']))),
            ],
          ),
        if (c['start_date'] != null || c['completion_date'] != null)
          _buildContentItem(
            context,
            '주요 일정',
            '착공/분양: ${c['start_date'] ?? '-'} ~ 준공/입주: ${c['completion_date'] ?? '-'}',
          ),
        if (c['market_analysis'] != null && c['market_analysis'].toString().isNotEmpty)
          _buildContentItem(context, '입지 및 분양성', c['market_analysis'].toString(), isMultiline: true),
        if (c['risk_factors'] != null && c['risk_factors'].toString().isNotEmpty)
          _buildContentItem(context, '리스크 및 대책', c['risk_factors'].toString(), isMultiline: true),
        _buildContentItem(
          context,
          '종합 검토의견',
          (c['recommendation'] ?? c['purpose'] ?? c['reason'] ?? c['content'] ?? c['body'] ?? '-').toString(),
          isMultiline: true,
        ),
        if (c['enclosed_docs'] != null && c['enclosed_docs'].toString().isNotEmpty)
          _buildContentItem(context, '첨부 서류', c['enclosed_docs'].toString()),
        if (c['note'] != null && c['note'].toString().isNotEmpty && c['enclosed_docs'] == null)
          _buildContentItem(context, '비고', c['note'].toString()),
      ],
    );
  }

  Widget _buildLegalReviewContent(BuildContext context, Map<String, dynamic> c) {
    String rtTypeName;
    final rt = c['review_type'];
    if (rt == 'CONTRACT_REVIEW') {
      rtTypeName = '계약서/협약서 검토';
    } else if (rt == 'LITIGATION_DISPUTE') {
      rtTypeName = '소송/분쟁 대응';
    } else if (rt == 'REGULATORY_COMPLIANCE') {
      rtTypeName = '법령해석/인허가';
    } else if (rt == 'INTERNAL_RULE') {
      rtTypeName = '사규/내부규정';
    } else if (rt == 'CLAIM_NOTICE') {
      rtTypeName = '내용증명/공문';
    } else {
      rtTypeName = '법률 자문';
    }

    String ugTypeName;
    final ug = c['urgency'];
    if (ug == 'VERY_URGENT') {
      ugTypeName = '당일 긴급';
    } else if (ug == 'URGENT') {
      ugTypeName = '긴급(1~2일)';
    } else {
      ugTypeName = '보통';
    }

    String rkTypeName;
    final rk = c['risk_level'];
    if (rk == 'HIGH') {
      rkTypeName = '높음 (중대 불리조항)';
    } else if (rk == 'MEDIUM') {
      rkTypeName = '중간 (수정 권고)';
    } else {
      rkTypeName = '낮음 (체결 가능)';
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '검토 분야 / 긴급도', '$rtTypeName ($ugTypeName)')),
            if (c['review_due_date'] != null && c['review_due_date'].toString().isNotEmpty)
              Expanded(child: _buildContentItem(context, '회신 희망일', c['review_due_date'].toString())),
          ],
        ),
        if (c['case_title'] != null && c['case_title'].toString().isNotEmpty)
          _buildContentItem(context, '의뢰 건명', c['case_title'].toString()),
        if (c['counterparty'] != null || c['dispute_amount'] != null)
          Row(
            children: [
              if (c['counterparty'] != null && c['counterparty'].toString().isNotEmpty)
                Expanded(child: _buildContentItem(context, '상대방 (당사자)', c['counterparty'].toString())),
              if (c['dispute_amount'] != null)
                Expanded(child: _buildContentItem(context, '관련 가액', _formatCurrency(c['dispute_amount']))),
            ],
          ),
        _buildContentItem(
          context,
          '사실관계 및 검토 배경',
          (c['background'] ?? c['purpose'] ?? c['reason'] ?? c['content'] ?? c['body'] ?? '-').toString(),
          isMultiline: true,
        ),
        if (c['key_issues'] != null && c['key_issues'].toString().isNotEmpty)
          _buildContentItem(context, '주요 쟁점 사항', c['key_issues'].toString(), isMultiline: true),
        if (c['legal_opinion'] != null && c['legal_opinion'].toString().isNotEmpty)
          _buildContentItem(context, '법무 검토 결과 (리스크: $rkTypeName)', c['legal_opinion'].toString(), isMultiline: true),
        if (c['enclosed_docs'] != null && c['enclosed_docs'].toString().isNotEmpty)
          _buildContentItem(context, '첨부 서류', c['enclosed_docs'].toString()),
        if (c['note'] != null && c['note'].toString().isNotEmpty && c['enclosed_docs'] == null)
          _buildContentItem(context, '비고', c['note'].toString()),
      ],
    );
  }

  Widget _buildContractChangeContent(BuildContext context, Map<String, dynamic> c) {
    String chgTypeName;
    final ct = c['change_type'];
    if (ct == 'TERMINATION') {
      chgTypeName = '계약 해지 / 합의 해제';
    } else if (ct == 'AMOUNT_CHANGE') {
      chgTypeName = '금액 변경 (증/감액)';
    } else if (ct == 'PERIOD_CHANGE') {
      chgTypeName = '기간 변경 (공기연장)';
    } else if (ct == 'SCOPE_CHANGE') {
      chgTypeName = '과업/조건 변경';
    } else {
      chgTypeName = '복합 변경 (금액+기간)';
    }

    final isTermination = ct == 'TERMINATION';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '변경/해지 구분', chgTypeName)),
            if (c['contractor_name'] != null && c['contractor_name'].toString().isNotEmpty)
              Expanded(child: _buildContentItem(context, '계약 상대방', c['contractor_name'].toString())),
          ],
        ),
        _buildContentItem(
          context,
          '원 계약 건명',
          '${c['original_contract_name'] ?? '-'}${c['original_contract_no'] != null && c['original_contract_no'].toString().isNotEmpty ? ' (계약번호: ${c['original_contract_no']})' : ''}',
        ),
        if (!isTermination) ...[
          Row(
            children: [
              Expanded(child: _buildContentItem(context, '원 계약 금액', _formatCurrency(c['original_amount']))),
              Expanded(
                child: _buildContentItem(
                  context,
                  '증감 금액',
                  '${(c['change_amount'] is num && (c['change_amount'] as num) >= 0) ? '+' : ''}${_formatCurrency(c['change_amount'])}',
                ),
              ),
            ],
          ),
          Row(
            children: [
              Expanded(
                child: _buildContentItem(
                  context,
                  '최종 변경 금액',
                  _formatCurrency(c['final_amount'] ?? ((c['original_amount'] ?? 0) + (c['change_amount'] ?? 0))),
                ),
              ),
              if (c['final_end_date'] != null || c['period_change_desc'] != null)
                Expanded(
                  child: _buildContentItem(
                    context,
                    '변경 후 종료일',
                    '${c['final_end_date'] ?? ''}${c['period_change_desc'] != null ? ' (${c['period_change_desc']})' : ''}',
                  ),
                ),
            ],
          ),
        ] else ...[
          Row(
            children: [
              if (c['termination_date'] != null)
                Expanded(child: _buildContentItem(context, '해지 기준일', c['termination_date'].toString())),
              Expanded(child: _buildContentItem(context, '타절 정산금액', _formatCurrency(c['settlement_amount']))),
            ],
          ),
          if (c['penalty_terms'] != null && c['penalty_terms'].toString().isNotEmpty)
            _buildContentItem(context, '위약 / 보증몰취', c['penalty_terms'].toString()),
        ],
        _buildContentItem(
          context,
          '변경 / 해지 사유',
          (c['change_reason'] ?? c['purpose'] ?? c['reason'] ?? c['content'] ?? c['body'] ?? '-').toString(),
          isMultiline: true,
        ),
        if (c['subsequent_plan'] != null && c['subsequent_plan'].toString().isNotEmpty)
          _buildContentItem(context, '후속 대책 / 비고', c['subsequent_plan'].toString(), isMultiline: true),
      ],
    );
  }

  Widget _buildContractContent(BuildContext context, Map<String, dynamic> c) {
    String ctTypeName;
    final ct = c['contract_type'];
    if (ct == 'CONSTRUCTION') {
      ctTypeName = '공사 도급/하도급';
    } else if (ct == 'SERVICE') {
      ctTypeName = '용역/설계/감리/PM';
    } else if (ct == 'PURCHASE') {
      ctTypeName = '물품/자재 구매';
    } else if (ct == 'LEASE') {
      ctTypeName = '부동산 임대차';
    } else if (ct == 'MOU_NDA') {
      ctTypeName = 'MOU/NDA';
    } else {
      ctTypeName = '일반 계약';
    }

    String ckTypeName;
    final ck = c['contract_kind'];
    if (ck == 'CHANGE') {
      ckTypeName = '변경 계약';
    } else if (ck == 'RENEWAL') {
      ckTypeName = '갱신 계약';
    } else {
      ckTypeName = '신규 계약';
    }

    String vatTypeName;
    final vt = c['vat_type'];
    if (vt == 'INCLUDED') {
      vatTypeName = 'VAT 포함';
    } else if (vt == 'ZERO_TAX') {
      vatTypeName = '면세';
    } else {
      vatTypeName = 'VAT 별도';
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '계약 구분 / 형태', '$ctTypeName ($ckTypeName)')),
            if (c['contract_name'] != null && c['contract_name'].toString().isNotEmpty)
              Expanded(child: _buildContentItem(context, '계약 건명', c['contract_name'].toString())),
          ],
        ),
        if (c['contractor_name'] != null && c['contractor_name'].toString().isNotEmpty)
          _buildContentItem(
            context,
            '계약 상대방',
            '${c['contractor_name']}${c['contractor_ceo'] != null && c['contractor_ceo'].toString().isNotEmpty ? ' (대표: ${c['contractor_ceo']})' : ''}${c['contractor_contact'] != null && c['contractor_contact'].toString().isNotEmpty ? ' | 연락처: ${c['contractor_contact']}' : ''}',
          ),
        Row(
          children: [
            Expanded(
              child: _buildContentItem(
                context,
                '계약 금액',
                '${_formatCurrency(c['contract_amount'] ?? c['amount'])} ($vatTypeName)',
              ),
            ),
            if (c['contract_start_date'] != null || c['contract_end_date'] != null)
              Expanded(
                child: _buildContentItem(
                  context,
                  '계약 기간',
                  '${c['contract_start_date'] ?? ''} ~ ${c['contract_end_date'] ?? ''}',
                ),
              ),
          ],
        ),
        if (c['payment_terms'] != null && c['payment_terms'].toString().isNotEmpty)
          _buildContentItem(context, '대금 지급 조건', c['payment_terms'].toString()),
        if (c['warranty_terms'] != null && c['warranty_terms'].toString().isNotEmpty)
          _buildContentItem(context, '이행 / 하자 보증', c['warranty_terms'].toString()),
        _buildContentItem(
          context,
          '계약 체결 사유 / 배경',
          (c['purpose_reason'] ?? c['purpose'] ?? c['reason'] ?? c['content'] ?? c['body'] ?? '-').toString(),
          isMultiline: true,
        ),
        if (c['special_terms'] != null && c['special_terms'].toString().isNotEmpty)
          _buildContentItem(context, '특약 / 비고', c['special_terms'].toString(), isMultiline: true),
        if (c['note'] != null && c['note'].toString().isNotEmpty && c['special_terms'] == null)
          _buildContentItem(context, '비고', c['note'].toString()),
      ],
    );
  }

  Widget _buildAdvancePaymentContent(BuildContext context, Map<String, dynamic> c) {
    String advTypeName;
    final at = c['advance_type'];
    if (at == 'PREPAYMENT') {
      advTypeName = '선급금 (계약상 선지급)';
    } else if (at == 'IMPREST_FUND') {
      advTypeName = '전도금 (상비 운영비)';
    } else if (at == 'EVENT_FUND') {
      advTypeName = '행사/프로젝트 진행비';
    } else if (at == 'OTHER') {
      advTypeName = '기타 선급금';
    } else {
      advTypeName = '가지급금 (업무용 선지급)';
    }

    final hasBank = c['bank_name'] != null && c['bank_name'].toString().isNotEmpty;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '신청 구분', advTypeName)),
            if (c['payment_due_date'] != null)
              Expanded(child: _buildContentItem(context, '지급 요청일', c['payment_due_date'].toString())),
          ],
        ),
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '신청 금액', _formatCurrency(c['advance_amount'] ?? c['amount']))),
            if (c['settlement_due_date'] != null)
              Expanded(child: _buildContentItem(context, '정산 예정일', c['settlement_due_date'].toString())),
          ],
        ),
        if (hasBank)
          _buildContentItem(
            context,
            '입금(수령) 계좌',
            '${c['receiver_type'] == 'VENDOR' ? '[거래처] ' : '[임직원] '}${c['bank_name']} ${c['account_number'] ?? ''} (예금주: ${c['account_holder'] ?? '-'})',
          ),
        _buildContentItem(
          context,
          '사용 목적 / 계획',
          (c['purpose'] ?? c['reason'] ?? c['content'] ?? c['body'] ?? '-').toString(),
          isMultiline: true,
        ),
        if (c['settlement_promise'] != false)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(
              children: [
                Icon(Icons.check_circle_outline, size: 15, color: context.colors.accentApproval),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    '정산 예정일까지 증빙 영수증을 첨부하여 전액 정산할 것을 확약함',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: context.colors.textPrimary),
                  ),
                ),
              ],
            ),
          ),
        if (c['note'] != null && c['note'].toString().isNotEmpty)
          _buildContentItem(context, '비고 / 특이사항', c['note'].toString()),
      ],
    );
  }

  Widget _buildExpenseSettlementContent(BuildContext context, Map<String, dynamic> c) {
    String stTypeName;
    final st = c['settlement_type'];
    if (st == 'PERSONAL_EXPENSE') {
      stTypeName = '개인경비 실비환급';
    } else if (st == 'BUSINESS_TRIP') {
      stTypeName = '출장경비 정산';
    } else if (st == 'ADVANCE_PAY') {
      stTypeName = '가지급금 정산';
    } else {
      stTypeName = '법인카드 사용정산';
    }

    final items = c['items'] as List?;
    final hasCard = c['card_number'] != null && c['card_number'].toString().isNotEmpty;
    final hasBank = c['bank_name'] != null && c['bank_name'].toString().isNotEmpty;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '정산 구분', stTypeName)),
            Expanded(child: _buildContentItem(context, '귀속 연월', c['target_month']?.toString() ?? '-')),
          ],
        ),
        if (hasCard)
          _buildContentItem(context, '법인카드 정보', c['card_number'].toString()),
        if (hasBank)
          _buildContentItem(
            context,
            '환급 입금계좌',
            '${c['bank_name']} ${c['account_number'] ?? ''} (예금주: ${c['account_holder'] ?? '-'})',
          ),
        _buildContentItem(context, '총 정산 합계 금액', _formatCurrency(c['total_amount'] ?? c['amount'])),
        _buildContentItem(context, '정산 사유 / 설명', (c['reason'] ?? c['purpose'] ?? c['content'] ?? c['body'] ?? '-').toString(), isMultiline: true),
        if (items != null && items.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(
            '영수증 / 세부 사용 내역',
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
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            (item['merchant'] ?? item['description'] ?? item['name'] ?? '-').toString(),
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                          ),
                          Text(
                            '${item['date'] ?? ''} | ${item['category'] ?? '경비'}',
                            style: TextStyle(fontSize: 11.5, color: context.colors.textMuted),
                          ),
                          if (item['purpose'] != null && item['purpose'].toString().isNotEmpty)
                            Text('용도: ${item['purpose']}', style: TextStyle(fontSize: 11.5, color: context.colors.textMuted)),
                        ],
                      ),
                    ),
                    Text(
                      _formatCurrency(item['amount']),
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: context.colors.textPrimary),
                    ),
                  ],
                ),
              ),
        ],
        if (c['note'] != null && c['note'].toString().isNotEmpty)
          _buildContentItem(context, '비고 / 증빙 안내', c['note'].toString()),
      ],
    );
  }

  Widget _buildHrRequestContent(BuildContext context, Map<String, dynamic> c) {
    String reqTypeName;
    final rt = c['request_type'];
    if (rt == 'CONGRATULATION_CONDOLENCE') {
      reqTypeName = '경조사 지원/경조금';
    } else if (rt == 'LEAVE_OF_ABSENCE') {
      reqTypeName = '휴직 신청';
    } else if (rt == 'REINSTATEMENT') {
      reqTypeName = '복직원 제출';
    } else if (rt == 'ACCOUNT_CHANGE') {
      reqTypeName = '계좌/정보 변경';
    } else {
      reqTypeName = '제증명서 발급';
    }

    final receiveMethod = c['receive_method'] == 'PRINT_DIRECT'
        ? '원본 직접 수령'
        : c['receive_method'] == 'POST'
            ? '우편(등기) 수령'
            : 'PDF 이메일 수신';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '신청 구분', reqTypeName)),
            Expanded(child: _buildContentItem(context, '수령 방법', receiveMethod)),
          ],
        ),
        if (rt == 'CERTIFICATE' || rt == null) ...[
          Row(
            children: [
              Expanded(child: _buildContentItem(context, '증명서 종류', '${c['cert_type'] ?? '재직증명서'} (${c['cert_language'] == 'ENGLISH' ? '영문' : '국문'}, ${c['cert_count'] ?? 1}부)')),
              Expanded(child: _buildContentItem(context, '제출처 / 용도', '${c['submit_to'] ?? '-'} / ${c['usage_purpose'] ?? '-'}')),
            ],
          ),
          _buildContentItem(context, '주민번호 표기', c['include_resident_num'] == true ? '뒷자리 전체 표기' : '생년월일만 표기'),
        ] else if (rt == 'CONGRATULATION_CONDOLENCE') ...[
          Row(
            children: [
              Expanded(child: _buildContentItem(context, '경조 구분', c['event_type']?.toString() ?? '-')),
              Expanded(child: _buildContentItem(context, '경조 일자', c['event_date']?.toString() ?? '-')),
            ],
          ),
          Row(
            children: [
              Expanded(child: _buildContentItem(context, '경조 장소', c['event_place']?.toString() ?? '-')),
              Expanded(child: _buildContentItem(context, '경조금 신청액', '${(c['congratulation_amount'] ?? c['amount'] ?? 0)} 원')),
            ],
          ),
          if (c['support_items'] != null && c['support_items'].toString().isNotEmpty)
            _buildContentItem(context, '물품 지원 요청', c['support_items'].toString()),
        ] else if (rt == 'LEAVE_OF_ABSENCE' || rt == 'REINSTATEMENT') ...[
          _buildContentItem(
            context,
            '기간 / 희망일',
            rt == 'LEAVE_OF_ABSENCE'
                ? '휴직: ${c['leave_start_date'] ?? '-'} ~ ${c['leave_end_date'] ?? '-'}'
                : '복직 희망일: ${c['reinstatement_date'] ?? '-'}',
          ),
        ],
        _buildContentItem(context, '신청 사유 / 상세', (c['reason'] ?? c['content'] ?? c['body'] ?? '-').toString(), isMultiline: true),
        if (c['note'] != null && c['note'].toString().isNotEmpty)
          _buildContentItem(context, '비고 / 특이사항', c['note'].toString()),
      ],
    );
  }

  Widget _buildHrAppointmentContent(BuildContext context, Map<String, dynamic> c) {
    final targets = c['targets'] as List?;
    final appType = c['appointment_type']?.toString() ?? '승진/전보';
    final effDate = c['effective_date']?.toString() ?? '-';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '발령 구분', appType)),
            Expanded(child: _buildContentItem(context, '발령 시행일', effDate)),
          ],
        ),
        _buildContentItem(context, '발령 사유 / 배경', (c['reason'] ?? c['content'] ?? c['body'] ?? '-').toString(), isMultiline: true),
        if (targets != null && targets.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(
            '발령 대상자 명단',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: context.colors.textPrimary),
          ),
          const SizedBox(height: 6),
          for (final t in targets)
            if (t is Map)
              Container(
                margin: const EdgeInsets.only(bottom: 6),
                padding: const EdgeInsets.all(8),
                color: context.colors.bgSurface,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(t['name']?.toString() ?? '', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          color: context.colors.accentApproval.withValues(alpha: 0.1),
                          child: Text(t['type_desc']?.toString() ?? '발령', style: TextStyle(fontSize: 11, color: context.colors.accentApproval, fontWeight: FontWeight.w600)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text('현직: ${t['current_dept'] ?? '-'} / ${t['current_position'] ?? '-'}', style: TextStyle(fontSize: 11.5, color: context.colors.textMuted)),
                    Text('발령: ${t['new_dept'] ?? '-'} / ${t['new_position'] ?? '-'}', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: context.colors.textPrimary)),
                    if (t['note'] != null && t['note'].toString().isNotEmpty)
                      Text('비고: ${t['note']}', style: TextStyle(fontSize: 11, color: context.colors.textMuted)),
                  ],
                ),
              ),
        ],
        if (c['note'] != null && c['note'].toString().isNotEmpty)
          _buildContentItem(context, '비고 / 특이사항', c['note'].toString()),
      ],
    );
  }

  Widget _buildOvertimeContent(BuildContext context, Map<String, dynamic> c) {
    String workTypeName;
    final wt = c['work_type'];
    if (wt == 'HOLIDAY') {
      workTypeName = '휴일 근무';
    } else if (wt == 'NIGHT') {
      workTypeName = '야간 근무';
    } else {
      workTypeName = '평일 연장근무';
    }

    final compTypeName = c['compensation_type'] == 'COMP_LEAVE' ? '대체휴무 (보상휴가) 적립' : '수당 지급';
    final timeStr = '${c['start_time'] ?? '-'} ~ ${c['end_time'] ?? '-'}';
    final breakHours = c['break_hours'];
    final breakStr = (breakHours != null && (breakHours is num ? breakHours > 0 : breakHours.toString() != '0'))
        ? ' (휴게: $breakHours시간)'
        : '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '근무 구분', workTypeName)),
            Expanded(child: _buildContentItem(context, '근무 일자', c['work_date']?.toString() ?? '-')),
          ],
        ),
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '근무 시간', '$timeStr$breakStr')),
            Expanded(child: _buildContentItem(context, '인정 시간', '${c['total_hours'] ?? '-'} 시간')),
          ],
        ),
        _buildContentItem(context, '보상 방식', compTypeName),
        _buildContentItem(context, '근무 사유 및 업무', (c['reason'] ?? c['content'] ?? c['body'] ?? '-').toString(), isMultiline: true),
        if (c['co_workers'] != null && c['co_workers'].toString().isNotEmpty)
          _buildContentItem(context, '동반 근무자', c['co_workers'].toString()),
        if (c['note'] != null && c['note'].toString().isNotEmpty)
          _buildContentItem(context, '비고 / 특이사항', c['note'].toString()),
      ],
    );
  }

  Widget _buildBusinessTripContent(BuildContext context, Map<String, dynamic> c) {
    final tripType = c['trip_type'] == 'OVERSEAS' ? '해외 출장' : '국내 출장';
    final sDate = c['start_date']?.toString() ?? '-';
    final eDate = c['end_date']?.toString() ?? '-';
    final days = '${c['nights_count'] ?? 0}박 ${c['days_count'] ?? c['days'] ?? 1}일';
    final total = c['total_cost'] ?? c['amount'] ?? 0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '출장 구분', tripType)),
            Expanded(child: _buildContentItem(context, '출장지', c['destination']?.toString() ?? '-')),
          ],
        ),
        _buildContentItem(context, '출장 기간', '$sDate ~ $eDate ($days)'),
        _buildContentItem(context, '출장 목적', c['purpose']?.toString() ?? '-'),
        if (c['companion'] != null && c['companion'].toString().isNotEmpty)
          _buildContentItem(context, '동행자', c['companion'].toString()),
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '업무 대행자', c['substitute_worker']?.toString() ?? '-')),
            Expanded(child: _buildContentItem(context, '교통편', c['transportation']?.toString() ?? '법인차량')),
          ],
        ),
        if (c['emergency_contact'] != null && c['emergency_contact'].toString().isNotEmpty)
          _buildContentItem(context, '비상 연락처', c['emergency_contact'].toString()),
        _buildContentItem(context, '총 예상 여비', _formatCurrency(total)),
        if (c['itinerary'] != null && c['itinerary'].toString().isNotEmpty)
          _buildContentItem(context, '세부 일정 계획', c['itinerary'].toString(), isMultiline: true),
      ],
    );
  }

  Widget _buildGeneralProposalContent(BuildContext context, Map<String, dynamic> c) {
    final amt = c['budget'] ?? c['amount'];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (c['purpose'] != null)
          _buildContentItem(context, '품의 목적', c['purpose'].toString()),
        if (c['schedule'] != null && c['schedule'].toString().isNotEmpty)
          _buildContentItem(context, '추진 일정', c['schedule'].toString()),
        if (c['budget_account'] != null && c['budget_account'].toString().isNotEmpty)
          _buildContentItem(context, '예산 과목', c['budget_account'].toString()),
        _buildContentItem(context, '소요 예산', _formatCurrency(amt)),
        _buildContentItem(context, '세부 품의 내용', (c['content'] ?? c['body'] ?? '-').toString(), isMultiline: true),
        if (c['expected_effect'] != null && c['expected_effect'].toString().isNotEmpty)
          _buildContentItem(context, '기대 효과', c['expected_effect'].toString(), isMultiline: true),
        if (c['note'] != null && c['note'].toString().isNotEmpty)
          _buildContentItem(context, '비고 / 특이사항', c['note'].toString()),
      ],
    );
  }

  Widget _buildOfficialLetterContent(BuildContext context, Map<String, dynamic> c) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildContentItem(context, '수신처', c['receiver']?.toString() ?? '-'),
        if (c['refer_to'] != null && c['refer_to'].toString().isNotEmpty)
          _buildContentItem(context, '참조처 (경유)', c['refer_to'].toString()),
        _buildContentItem(context, '발신 명의', c['sender_name']?.toString() ?? '대표이사'),
        if (c['doc_number_external'] != null && c['doc_number_external'].toString().isNotEmpty)
          _buildContentItem(context, '대외 공문번호', c['doc_number_external'].toString()),
        _buildContentItem(context, '공문 제목', c['letter_subject']?.toString() ?? '-'),
        _buildContentItem(context, '공문 본문 (요지)', c['letter_body']?.toString() ?? '-', isMultiline: true),
        if (c['enclosed_files_desc'] != null && c['enclosed_files_desc'].toString().isNotEmpty)
          _buildContentItem(context, '붙임 서류 내역', c['enclosed_files_desc'].toString(), isMultiline: true),
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '발송 방법', c['send_method']?.toString() ?? '이메일')),
            Expanded(child: _buildContentItem(context, '발송 희망일', c['send_due_date']?.toString() ?? '-')),
          ],
        ),
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '날인 인감', c['seal_type']?.toString() ?? '법인인감')),
            Expanded(child: _buildContentItem(context, '날인 부수', '${c['seal_count'] ?? 1} 부')),
          ],
        ),
      ],
    );
  }

  Widget _buildLeaveContent(BuildContext context, Map<String, dynamic> c) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildContentItem(context, '휴가 구분', c['leave_type']?.toString() ?? '-'),
        _buildContentItem(context, '시작일', c['start_date']?.toString() ?? '-'),
        _buildContentItem(context, '종료일', c['end_date']?.toString() ?? '-'),
        _buildContentItem(context, '휴가 일수', '${c['days_count'] ?? c['days'] ?? '-'} 일'),
        if (c['reason'] != null)
          _buildContentItem(context, '사유', c['reason'].toString(), isMultiline: true),
        if (c['substitute_worker'] != null && c['substitute_worker'].toString().isNotEmpty)
          _buildContentItem(context, '업무 대행자', c['substitute_worker'].toString()),
        if (c['emergency_contact'] != null && c['emergency_contact'].toString().isNotEmpty)
          _buildContentItem(context, '비상 연락처', c['emergency_contact'].toString()),
      ],
    );
  }

  Widget _buildExpenseContent(BuildContext context, Map<String, dynamic> c) {
    String expTypeName;
    final et = c['expense_type'];
    if (et == 'TAX_INVOICE') {
      expTypeName = '세금계산서';
    } else if (et == 'RECEIPT') {
      expTypeName = '현금/간이영수증';
    } else if (et == 'TRANSFER') {
      expTypeName = '일반 계좌이체';
    } else {
      expTypeName = '법인카드';
    }

    final items = c['items'] as List?;
    final hasBank = c['bank_name'] != null && c['bank_name'].toString().isNotEmpty;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '지출 구분', expTypeName)),
            if (c['payment_due_date'] != null)
              Expanded(child: _buildContentItem(context, '지급 요청일', c['payment_due_date'].toString())),
          ],
        ),
        if (hasBank)
          _buildContentItem(
            context,
            '입금 계좌',
            '${c['bank_name']} ${c['account_number'] ?? ''} (예금주: ${c['account_holder'] ?? '-'})',
          ),
        _buildContentItem(context, '총 지출 결의 금액', _formatCurrency(c['total_amount'] ?? c['amount'])),
        if (c['purpose'] != null)
          _buildContentItem(context, '지출 목적 / 사유', c['purpose'].toString(), isMultiline: true),
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
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            (item['description'] ?? item['name'] ?? '-').toString(),
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                          ),
                          if (item['date'] != null)
                            Text('일자: ${item['date']}', style: TextStyle(fontSize: 11.5, color: context.colors.textMuted)),
                          if (item['note'] != null && item['note'].toString().isNotEmpty)
                            Text('비고: ${item['note']}', style: TextStyle(fontSize: 11.5, color: context.colors.textMuted)),
                        ],
                      ),
                    ),
                    Text(
                      _formatCurrency(item['amount']),
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: context.colors.textPrimary),
                    ),
                  ],
                ),
              ),
        ],
      ],
    );
  }

  Widget _buildPurchaseContent(BuildContext context, Map<String, dynamic> c) {
    final items = c['items'] as List?;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: _buildContentItem(context, '총 품의 금액', _formatCurrency(c['total_amount'] ?? c['amount']))),
            if (c['vendor'] != null && c['vendor'].toString().isNotEmpty)
              Expanded(child: _buildContentItem(context, '거래처 / 공급업체', c['vendor'].toString())),
          ],
        ),
        if (c['delivery_due_date'] != null || c['delivery_location'] != null)
          Row(
            children: [
              if (c['delivery_due_date'] != null)
                Expanded(child: _buildContentItem(context, '납품 희망일', c['delivery_due_date'].toString())),
              if (c['delivery_location'] != null && c['delivery_location'].toString().isNotEmpty)
                Expanded(child: _buildContentItem(context, '납품 장소', c['delivery_location'].toString())),
            ],
          ),
        if (c['purpose'] != null)
          _buildContentItem(context, '구매 목적 / 사유', c['purpose'].toString(), isMultiline: true),
        if (items != null && items.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(
            '구매 품목 내역',
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
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(item['name']?.toString() ?? '', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                          if (item['spec'] != null && item['spec'].toString().isNotEmpty)
                            Text('규격: ${item['spec']}', style: TextStyle(fontSize: 11.5, color: context.colors.textMuted)),
                          Text(
                            '수량: ${item['quantity'] ?? 1} | 단가: ${_formatCurrency(item['unit_price'])}',
                            style: TextStyle(fontSize: 11.5, color: context.colors.textMuted),
                          ),
                        ],
                      ),
                    ),
                    Text(
                      _formatCurrency(item['supply_price'] ?? item['amount']),
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: context.colors.textPrimary),
                    ),
                  ],
                ),
              ),
        ],
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
              // 반려 버튼 (40%)
              Expanded(
                flex: 4,
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
                    label: const Text('반려', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
                  ),
                ),
              ),
              const SizedBox(width: 10),

              // 결재 승인 버튼 (60%)
              Expanded(
                flex: 6,
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
                    label: const Text('결재 승인', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    // 내가 기안자이고 임시저장(draft) 또는 반려(rejected) 상태인 경우 -> 상신/재상신 버튼
    if (isMyDraft && (doc.status == 'draft' || doc.status == 'rejected')) {
      final isRejected = doc.status == 'rejected';
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
        ),
        child: SafeArea(
          child: Row(
            children: [
              // 1. 내용 수정 버튼
              Expanded(
                flex: 4,
                child: SizedBox(
                  height: 44,
                  child: OutlinedButton.icon(
                    onPressed: () {
                      context.push('/approval/draft', extra: doc);
                    },
                    style: OutlinedButton.styleFrom(
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      side: BorderSide(color: context.colors.accentApprovalDeep),
                    ),
                    icon: Icon(Icons.edit_document, color: context.colors.accentApprovalDeep, size: 18),
                    label: Text(
                      '내용 수정',
                      style: TextStyle(color: context.colors.accentApprovalDeep, fontWeight: FontWeight.w700, fontSize: 13.5),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),

              // 2. 상신하기 버튼
              Expanded(
                flex: 6,
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
                    label: Text(
                      isRejected ? '결재 재상신' : '결재 상신',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    // 내가 기안자이고 결재 진행 중이며, 1차 결재자가 아직 승인하지 않은 경우 -> 회수 버튼
    final firstStep = doc.steps?.where((s) => s.stepOrder == 1).firstOrNull;
    final isFirstStepApproved = firstStep?.actions.any((a) => a.action == 'approved') ?? false;

    if (isMyDraft && doc.status == 'pending' && !isFirstStepApproved) {
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
