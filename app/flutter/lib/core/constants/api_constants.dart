import '../api/api_client.dart';

class ApiConstants {
  // api_client.dart의 appBaseUrl과 단일화 (Web/Release/BASE_URL 환경 대응)
  static String get baseUrl => appBaseUrl;

  // API Endpoint 경로들 (Django _config/urls.py 정의 기준)
  static const String jwtCreate = '/api/v1/token/';
  static const String jwtRefresh = '/api/v1/token/refresh/';
  static const String jwtVerify = '/api/v1/token/verify/';
  static const String currentUser = '/api/v1/accounts/users/me/';
}
