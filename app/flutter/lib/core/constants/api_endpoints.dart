/// IBS 워크스페이스 API 엔드포인트 상수
/// Django _config/urls.py 기준
abstract class ApiEndpoints {
  // ── Auth & Users ──────────────────────────────────
  static const String jwtCreate  = '/api/v1/token/';
  static const String jwtRefresh = '/api/v1/token/refresh/';
  static const String jwtVerify  = '/api/v1/token/verify/';
  static const String me         = '/api/v1/accounts/users/me/';
  static const String users      = '/api/v1/user/';
  static const String fcmToken   = '/api/v1/accounts/fcm-token/';

  // ── Project ──────────────────────────────────────
  static const String projects       = '/api/v1/issue-project/';
  static const String projectDetail  = '/api/v1/issue-project/{slug}/';

  // ── Issue ────────────────────────────────────────────────────────────────
  static const String issues        = '/api/v1/issue/';
  static const String issueDetail   = '/api/v1/issue/{id}/';
  static const String issueComments = '/api/v1/issue-comment/';
  static const String issueFiles    = '/api/v1/issue-file/';
  static const String issueLogs     = '/api/v1/log-entry/';

  // ── Meeting ──────────────────────────────────────
  static const String meetings          = '/api/v1/meeting/';
  static const String meetingDetail     = '/api/v1/meeting/{id}/';
  static const String meetingCategories = '/api/v1/meeting-category/';
  static const String members           = '/api/v1/member/';

  // ── Contract ─────────────────────────────────────
  static const String contracts     = '/api/v1/contract/';

  // ── Ledger ───────────────────────────────────────
  static const String ledgers       = '/api/v1/ledger/';

  /// URL 패턴에서 {id}/{slug} 등을 실제 값으로 치환
  static String resolve(String pattern, Map<String, dynamic> params) {
    var url = pattern;
    params.forEach((key, value) {
      url = url.replaceAll('{$key}', value.toString());
    });
    return url;
  }
}
