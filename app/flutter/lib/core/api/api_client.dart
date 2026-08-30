import 'package:dio/dio.dart';
import 'dart:io';
import '../storage/token_storage.dart';
import '../constants/api_endpoints.dart';

/// 개발/운영 환경별 Base URL
/// - 빌드 시 `--dart-define=BASE_URL=https://your-prod-api.com` 옵션으로 운영서버 주소 동적 주입 가능
/// - 미지정 시 기본값: 로컬 개발 환경 (localhost / 10.0.2.2)
String get appBaseUrl {
  const envUrl = String.fromEnvironment('BASE_URL');
  if (envUrl.isNotEmpty) {
    var url = envUrl.trim();
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://$url';
    }
    return url.endsWith('/') ? url.substring(0, url.length - 1) : url;
  }

  if (Platform.isAndroid) return 'http://10.0.2.2'; // 에뮬레이터 → localhost
  return 'http://localhost';
}

String get _baseUrl => appBaseUrl;

/// Dio 싱글톤 인스턴스 생성 함수
/// Riverpod dioProvider에서 호출
Dio createDio(TokenStorage tokenStorage) {
  final dio = Dio(
    BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ),
  );

  dio.interceptors.add(
    AuthInterceptor(dio: dio, tokenStorage: tokenStorage),
  );

  return dio;
}

/// JWT 토큰 자동 갱신 인터셉터
/// - 모든 요청에 Authorization 헤더 자동 삽입
/// - 401 응답 시 refresh_token으로 access_token 재발급 후 원요청 재시도
/// - 갱신 실패 시 토큰 삭제 (로그인 화면으로 go_router가 리다이렉트 처리)
class AuthInterceptor extends QueuedInterceptorsWrapper {
  final Dio dio;
  final TokenStorage tokenStorage;

  AuthInterceptor({required this.dio, required this.tokenStorage});

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // 로그인 및 토큰 갱신 요청에는 Authorization 헤더를 붙이지 않음
    final isAuthEndpoint = options.path.contains(ApiEndpoints.jwtCreate) ||
        options.path.contains(ApiEndpoints.jwtRefresh);

    if (!isAuthEndpoint) {
      final token = await tokenStorage.getAccessToken();
      if (token != null && token.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final isAuthEndpoint = err.requestOptions.path.contains(ApiEndpoints.jwtCreate) ||
        err.requestOptions.path.contains(ApiEndpoints.jwtRefresh);

    if (!isAuthEndpoint && err.response?.statusCode == 401) {
      // access_token 만료 → refresh 시도
      final refreshed = await _tryRefresh();
      if (refreshed) {
        // 원 요청 재시도 (새 access_token으로)
        final newToken = await tokenStorage.getAccessToken();
        final retryOptions = err.requestOptions;
        retryOptions.headers['Authorization'] = 'Bearer $newToken';
        try {
          final retryResponse = await dio.fetch(retryOptions);
          return handler.resolve(retryResponse);
        } catch (e) {
          // 재시도도 실패 → 토큰 삭제
          await tokenStorage.clearTokens();
        }
      } else {
        await tokenStorage.clearTokens();
      }
    }
    handler.next(err);
  }

  Future<bool> _tryRefresh() async {
    final refreshToken = await tokenStorage.getRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) return false;

    try {
      // 인터셉터 없는 별도 Dio 인스턴스로 refresh 요청 (무한루프 방지)
      final refreshDio = Dio(BaseOptions(baseUrl: _baseUrl));
      final response = await refreshDio.post(
        ApiEndpoints.jwtRefresh,
        data: {'refresh': refreshToken},
      );
      final newAccess = response.data['access'] as String?;
      if (newAccess != null) {
        await tokenStorage.saveAccessToken(newAccess);
        return true;
      }
    } catch (_) {}
    return false;
  }
}

/// DioException 또는 일반 예외로부터 서버가 전달한 한국어 상세 에러 메시지를 추출
String getDioErrorMessage(Object error) {
  if (error is DioException) {
    final response = error.response;
    if (response?.data != null) {
      final dynamic data = response!.data;
      if (data is Map<String, dynamic>) {
        if (data.containsKey('detail')) {
          return data['detail'].toString();
        }
        if (data.containsKey('message')) {
          return data['message'].toString();
        }
        if (data.containsKey('error')) {
          return data['error'].toString();
        }
        // 필드별 유효성 검사 에러 (예: {'category': ['이 필드는 null일 수 없습니다.']})
        final messages = <String>[];
        data.forEach((key, val) {
          if (val is List && val.isNotEmpty) {
            messages.add('$key: ${val.first}');
          } else if (val is String) {
            messages.add('$key: $val');
          }
        });
        if (messages.isNotEmpty) {
          return messages.join('\n');
        }
      } else if (data is String && data.isNotEmpty) {
        return data;
      }
    }
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      return '서버 응답 시간이 초과되었습니다.';
    }
    if (error.type == DioExceptionType.connectionError) {
      return '서버에 연결할 수 없습니다. 네트워크를 확인해 주세요.';
    }
  }
  return error.toString();
}
