import 'dart:io';

class ApiConstants {
  // 로컬 개발 환경용 서버 URL (Android 에뮬레이터에서는 10.0.2.2가 PC의 localhost입니다)
  static String get baseUrl {
    if (Platform.isAndroid) {
      return 'http://10.0.2.2'; // Docker Nginx 포트 (80)
    }
    return 'http://localhost';
  }

  // API Endpoint 경로들 (Django _config/urls.py 정의 기준)
  static const String jwtCreate = '/api/v1/token/';
  static const String jwtRefresh = '/api/v1/token/refresh/';
  static const String jwtVerify = '/api/v1/token/verify/';
  static const String currentUser = '/api/v1/accounts/users/me/';
}
