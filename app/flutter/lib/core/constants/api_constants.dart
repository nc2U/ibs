import 'dart:io';

class ApiConstants {
  // 로컬 개발 환경용 서버 URL (Android 에뮬레이터에서는 10.0.2.2가 PC의 localhost입니다)
  static String get baseUrl {
    if (Platform.isAndroid) {
      return 'http://10.0.2.2:8000'; // Django dev server 포트
    }
    return 'http://localhost:8000';
  }

  // API Endpoint 경로들
  static const String jwtCreate = '/apiV1/jwt/create/';
  static const String jwtRefresh = '/apiV1/jwt/refresh/';
  static const String jwtVerify = '/apiV1/jwt/verify/';
  static const String currentUser = '/apiV1/accounts/users/me/';
}
