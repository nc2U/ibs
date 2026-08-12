/// IBS 워크스페이스 API 엔드포인트 상수
/// Django _config/urls.py 기준
abstract class ApiEndpoints {
  // ── Auth ──────────────────────────────────────────
  static const String jwtCreate  = '/api/v1/token/';
  static const String jwtRefresh = '/api/v1/token/refresh/';
  static const String jwtVerify  = '/api/v1/token/verify/';
  static const String me         = '/api/v1/accounts/users/me/';
  static const String fcmToken   = '/api/v1/accounts/fcm-token/';

  // ── Project ──────────────────────────────────────
  static const String projects       = '/api/v1/work-projects/';
  static const String myProjects     = '/api/v1/work-projects/?my=true';
  static const String projectDetail  = '/api/v1/work-projects/{slug}/';

  // ── Issue ────────────────────────────────────────────────────────────────
  static const String issues        = '/api/v1/issues/';
  static const String issueDetail   = '/api/v1/issues/{id}/';
  static const String issueComments = '/api/v1/issue-comments/';
  static const String issueFiles    = '/api/v1/issue-files/';

  // ── Meeting ──────────────────────────────────────
  static const String meetings      = '/api/v1/meetings/';
  static const String meetingDetail = '/api/v1/meetings/{id}/';

  // ── Contract ─────────────────────────────────────
  static const String contracts     = '/api/v1/contracts/';

  // ── Ledger ───────────────────────────────────────
  static const String ledgers       = '/api/v1/ledgers/';

  /// URL 패턴에서 {id}/{slug} 등을 실제 값으로 치환
  static String resolve(String pattern, Map<String, dynamic> params) {
    var url = pattern;
    params.forEach((key, value) {
      url = url.replaceAll('{$key}', value.toString());
    });
    return url;
  }
}
