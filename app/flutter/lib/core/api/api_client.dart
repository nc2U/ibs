import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'dart:io';
import '../services/biometric_service.dart';
import '../storage/token_storage.dart';
import '../constants/api_endpoints.dart';

// ─── 재시도 대상 DioException 유형 ───────────────────────────────────────────
const _retryableTypes = {
  DioExceptionType.connectionError,
  DioExceptionType.connectionTimeout,
  DioExceptionType.receiveTimeout,
  DioExceptionType.sendTimeout,
};

/// 개발/운영 환경별 Base URL
/// - CI/CD 빌드 시 `--dart-define=BASE_URL=https://...` 옵션으로 동적 주입 최우선 적용
/// - 릴리즈 빌드 미지정 시: 안전장치로 운영 서버(`https://ibs.dyibs.com`) 적용
/// - 로컬 디버그 모드(`flutter run`): 로컬 백엔드 서버(Android: 10.0.2.2:8000, iOS/Web: localhost:8000)
String get appBaseUrl {
  const envUrl = String.fromEnvironment('BASE_URL');
  if (envUrl.isNotEmpty) {
    var url = envUrl.trim();
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://$url';
    }
    return url.endsWith('/') ? url.substring(0, url.length - 1) : url;
  }

  // 릴리즈 빌드 시 안전 fallback: 운영 서버 도메인
  if (kReleaseMode) {
    return 'https://ibs.dyibs.com';
  }

  // 로컬 개발 디버그 모드 (flutter run)
  if (Platform.isAndroid) return 'http://10.0.2.2';
  return 'http://localhost';
}

String get _baseUrl => appBaseUrl;

/// Dio 싱글톤 인스턴스 생성 함수
/// Riverpod dioProvider에서 호출
Dio createDio(TokenStorage tokenStorage, {void Function()? onSessionExpired}) {
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

  // 1) 네트워크 오류 자동 재시도 (최대 2회, 지수 백오프)
  dio.interceptors.add(RetryInterceptor(dio: dio));

  // 2) JWT 토큰 자동 갱신
  dio.interceptors.add(
    AuthInterceptor(
      dio: dio,
      tokenStorage: tokenStorage,
      onSessionExpired: onSessionExpired,
    ),
  );

  return dio;
}

/// 네트워크 오류 자동 재시도 인터셉터
/// - 재시도 대상: connectionError, connectionTimeout, receiveTimeout, sendTimeout
/// - 최대 재시도 횟수: 2회
/// - 지수 백오프: 1초 → 2초
/// - 4xx/5xx 응답 오류는 재시도하지 않음 (서버 로직 오류)
/// - 이미 재시도한 요청은 extra['_retryCount']로 횟수 추적
class RetryInterceptor extends Interceptor {
  final Dio dio;
  final int maxRetries;
  final Duration initialDelay;

  RetryInterceptor({
    required this.dio,
    this.maxRetries = 2,
    this.initialDelay = const Duration(seconds: 1),
  });

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final options = err.requestOptions;
    final retryCount = (options.extra['_retryCount'] as int?) ?? 0;

    final shouldRetry = _retryableTypes.contains(err.type) &&
        retryCount < maxRetries &&
        // S3 Presigned URL 등 외부 URL은 재시도하지 않음
        !options.path.startsWith('http://') &&
        !options.path.startsWith('https://');

    if (!shouldRetry) {
      return handler.next(err);
    }

    final delay = initialDelay * (1 << retryCount); // 1s, 2s
    await Future<void>.delayed(delay);

    options.extra['_retryCount'] = retryCount + 1;

    try {
      final response = await dio.fetch<dynamic>(options);
      return handler.resolve(response);
    } on DioException catch (retryErr) {
      return handler.next(retryErr);
    }
  }
}

/// JWT 토큰 자동 갱신 인터셉터
/// - 모든 요청에 Authorization 헤더 자동 삽입
/// - 401 응답 시 동시 다발적 refresh 요청을 방지(Completer 락)하고 단 1회만 안전하게 갱신
/// - 큐 내부 데드락(Deadlock) 방지를 위해 독립 retry Dio 인스턴스로 원요청 재시도
/// - 갱신 실패 시(Refresh 토큰 만료)에만 토큰 삭제 및 세션 만료 알림(로그인 화면 이동)
class AuthInterceptor extends QueuedInterceptorsWrapper {
  final Dio dio;
  final TokenStorage tokenStorage;
  final void Function()? onSessionExpired;

  // 동시 401 발생 시 중복 리프레시 요청 방지 (Lock)
  Completer<bool>? _refreshCompleter;

  // QueuedInterceptorsWrapper 내부 데드락 방지를 위한 인터셉터 없는 독립 retry 전용 Dio
  late final Dio _retryDio;

  AuthInterceptor({
    required this.dio,
    required this.tokenStorage,
    this.onSessionExpired,
  }) {
    _retryDio = Dio(
      BaseOptions(
        baseUrl: dio.options.baseUrl,
        connectTimeout: dio.options.connectTimeout,
        receiveTimeout: dio.options.receiveTimeout,
        sendTimeout: dio.options.sendTimeout,
      ),
    );
  }

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // 로그인 및 토큰 갱신 요청 및 외부 스토리지(S3 등) Presigned URL에는 Authorization 헤더를 붙이지 않음
    final isAuthEndpoint = options.path.contains(ApiEndpoints.jwtCreate) ||
        options.path.contains(ApiEndpoints.jwtRefresh);

    final isExternalStorageUrl = options.path.startsWith('http://') || options.path.startsWith('https://');

    if (isExternalStorageUrl) {
      // S3 Presigned URL 서명 불일치(403 SignatureDoesNotMatch) 및 복수 인증 오류(400) 방지
      options.headers.remove('Authorization');
      options.headers.remove('Content-Type');
    } else if (!isAuthEndpoint) {
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
      // 1. 현재 저장된 최신 토큰 및 요청 시 전송했던 토큰 확인
      final currentToken = await tokenStorage.getAccessToken();
      final sentToken = err.requestOptions.headers['Authorization']
          ?.toString()
          .replaceFirst('Bearer ', '')
          .trim();

      bool refreshed = false;
      // 다른 동시 요청이나 로그인으로 인해 이미 최신 토큰으로 갱신된 상태라면 재갱신 불필요
      if (currentToken != null &&
          currentToken.isNotEmpty &&
          sentToken != null &&
          sentToken.isNotEmpty &&
          sentToken != currentToken) {
        refreshed = true;
      } else {
        // 현재 유효했던 토큰이 만료된 것이므로 1회만 안전하게 토큰 갱신
        refreshed = await _synchronizedRefresh();
      }

      if (refreshed) {
        // 새 access_token으로 원 요청 재시도
        final newToken = await tokenStorage.getAccessToken();
        if (newToken != null && newToken.isNotEmpty) {
          final retryOptions = err.requestOptions;
          retryOptions.headers['Authorization'] = 'Bearer $newToken';
          try {
            // 데드락 방지를 위해 인터셉터 없는 _retryDio로 재시도
            final retryResponse = await _retryDio.fetch<dynamic>(retryOptions);
            return handler.resolve(retryResponse);
          } on DioException catch (retryErr) {
            // 재시도한 요청마저 401인 경우에만 최종 세션 만료로 처리
            if (retryErr.response?.statusCode == 401) {
              await tokenStorage.clearTokens();
              onSessionExpired?.call();
            }
            return handler.reject(retryErr);
          } catch (e) {
            return handler.reject(
              DioException(
                requestOptions: err.requestOptions,
                error: e,
              ),
            );
          }
        }
      }

      // 리프레시 토큰까지 만료되어 갱신에 최종 실패한 경우에만 토큰 정리 및 세션 만료
      await tokenStorage.clearTokens();
      onSessionExpired?.call();
      return handler.next(err);
    }

    handler.next(err);
  }

  Future<bool> _synchronizedRefresh() async {
    if (_refreshCompleter != null) {
      return _refreshCompleter!.future;
    }

    final completer = Completer<bool>();
    _refreshCompleter = completer;
    try {
      final success = await _tryRefresh();
      completer.complete(success);
      return success;
    } catch (e) {
      completer.complete(false);
      return false;
    } finally {
      _refreshCompleter = null;
    }
  }

  Future<bool> _tryRefresh() async {
    final refreshToken = await tokenStorage.getRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) return false;

    try {
      // 인터셉터 없는 별도 Dio 인스턴스로 refresh 요청 (무한루프 방지 및 타임아웃 10초 설정)
      final refreshDio = Dio(
        BaseOptions(
          baseUrl: _baseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
        ),
      );
      final response = await refreshDio.post(
        ApiEndpoints.jwtRefresh,
        data: {'refresh': refreshToken},
      );
      final newAccess = response.data['access'] as String?;
      if (newAccess != null && newAccess.isNotEmpty) {
        await tokenStorage.saveAccessToken(newAccess);

        // 토큰 로테이션이 켜져 있는 경우 새로 발급된 refresh 토큰도 저장
        final newRefresh = response.data['refresh'] as String?;
        if (newRefresh != null && newRefresh.isNotEmpty) {
          await tokenStorage.saveRefreshToken(newRefresh);
          if (await BiometricService.isBiometricEnabled()) {
            await tokenStorage.saveBiometricRefreshToken(newRefresh);
          }
        }
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
