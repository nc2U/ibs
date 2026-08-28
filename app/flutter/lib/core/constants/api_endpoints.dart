/// IBS 워크스페이스 API 엔드포인트 상수
/// Django _config/urls.py 기준
abstract class ApiEndpoints {
  // ── Auth & Users ──────────────────────────────────
  static const String jwtCreate      = '/api/v1/token/';
  static const String jwtRefresh     = '/api/v1/token/refresh/';
  static const String jwtVerify      = '/api/v1/token/verify/';
  static const String me             = '/api/v1/accounts/users/me/';
  static const String users          = '/api/v1/user/';
  static const String fcmToken       = '/api/v1/accounts/fcm-token/';
  static const String changePassword = '/api/v1/change-password/';
  static const String passwordReset  = '/api/v1/password-reset/';

  // ── Project ──────────────────────────────────────
  static const String projects           = '/api/v1/issue-project/';
  static const String projectDetail      = '/api/v1/issue-project/{slug}/';
  static const String projectMyProjects  = '/api/v1/issue-project/my_projects/';

  // ── Issue ────────────────────────────────────────────────────────────────
  static const String issues         = '/api/v1/issue/';
  static const String issueDetail    = '/api/v1/issue/{id}/';
  static const String issueComments  = '/api/v1/issue-comment/';
  static const String issueFiles     = '/api/v1/issue-file/';
  static const String issueLogs      = '/api/v1/log-entry/';
  static const String issueStatuses  = '/api/v1/issue-status/';
  static const String codePriorities = '/api/v1/code-priority/';

  // ── Meeting ──────────────────────────────────────
  static const String meetings          = '/api/v1/meeting/';
  static const String meetingDetail     = '/api/v1/meeting/{id}/';
  static const String meetingCategories = '/api/v1/meeting-category/';
  static const String members           = '/api/v1/member/';

  // ── Search ───────────────────────────────────────
  static const String issueSearchRun = '/api/v1/issue-search/run/';

  // ── Contract ─────────────────────────────────────
  static const String contracts     = '/api/v1/contract/';

  // ── Ledger ───────────────────────────────────────
  static const String ledgers       = '/api/v1/ledger/';

  // ── Approval ─────────────────────────────────────
  static const String approvalDocCategories    = '/api/v1/approval-doc-category/';
  static const String approvalDocTypes         = '/api/v1/approval-doc-type/';
  static const String approvalDocTypesForDraft = '/api/v1/approval-doc-type/for_draft/';
  static const String approvalDocuments        = '/api/v1/approval-document/';
  static const String approvalDocumentDetail   = '/api/v1/approval-document/{id}/';
  static const String approvalMyPending        = '/api/v1/approval-document/my_pending/';
  static const String approvalMyDrafted        = '/api/v1/approval-document/my_drafted/';
  static const String approvalMyApproved       = '/api/v1/approval-document/my_approved/';
  static const String approvalMyObserved       = '/api/v1/approval-document/my_observed/';
  static const String approvalAllDocuments     = '/api/v1/approval-document/all_documents/';
  static const String approvalMyAssignments    = '/api/v1/approval-document/my_assignments/';
  static const String approvalPreviewRoute     = '/api/v1/approval-document/preview_route/';
  static const String approvalSubmit           = '/api/v1/approval-document/{id}/submit/';
  static const String approvalAct              = '/api/v1/approval-document/{id}/act/';
  static const String approvalCancel           = '/api/v1/approval-document/{id}/cancel/';
  static const String approvalPrintPdf         = '/api/v1/approval-document/{id}/print_pdf/';
  static const String approvalAttachments      = '/api/v1/approval-attachment/';
  static const String approvalDelegations      = '/api/v1/approval-delegation/';
  static const String approvalDelegationDetail = '/api/v1/approval-delegation/{id}/';

  /// URL 패턴에서 {id}/{slug} 등을 실제 값으로 치환
  static String resolve(String pattern, Map<String, dynamic> params) {
    var url = pattern;
    params.forEach((key, value) {
      url = url.replaceAll('{$key}', value.toString());
    });
    return url;
  }
}
