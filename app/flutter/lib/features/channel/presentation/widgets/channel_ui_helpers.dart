import 'package:url_launcher/url_launcher.dart';
import '../../../../core/api/api_client.dart';
import '../../../../core/models/common_models.dart';

/// ISO 타임스탬프를 `YYYY-MM-DD HH:MM` 형식으로 안전하게 포맷
String formatChannelDateTime(String? raw) {
  if (raw == null || raw.isEmpty) return '';
  final normalized = raw.replaceAll('T', ' ');
  return normalized.length >= 16 ? normalized.substring(0, 16) : normalized;
}

/// 다운로드 파일명의 경로 순회 문자(`..`, `/`, `\`) 등 위험 문자 제거
String sanitizeChannelFileName(String rawName) {
  final stripped = rawName.split(RegExp(r'[/\\]')).last.trim();
  final safe = stripped
      .replaceAll('..', '_')
      .replaceAll(RegExp(r'[^a-zA-Z0-9가-힣._-]'), '_');
  return safe.isEmpty ? 'attachment' : safe;
}

/// 본문 HTML 내 상대/절대 링크를 안전하게 외부 브라우저로 열기
Future<bool> launchChannelHtmlUrl(String url) async {
  final trimmed = url.trim();
  if (trimmed.isEmpty) return true;
  final resolved = trimmed.startsWith('/') ? '$appBaseUrl$trimmed' : trimmed;
  final uri = Uri.tryParse(resolved);
  if (uri != null && uri.hasScheme && await canLaunchUrl(uri)) {
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }
  return true;
}

/// 작성자 표시 이름 (`name` 우선, 비어있으면 `username`, 둘 다 없으면 [fallback])
String resolveUserDisplayName(
  SimpleUserModel? user, {
  String fallback = '익명',
}) {
  if (user == null) return fallback;
  if (user.name.isNotEmpty) return user.name;
  if (user.username.isNotEmpty) return user.username;
  return fallback;
}
