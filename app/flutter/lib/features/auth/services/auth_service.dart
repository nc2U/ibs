import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/api_endpoints.dart';
import '../../../core/providers/dio_provider.dart';
import '../../../core/services/biometric_service.dart';
import '../../../core/storage/token_storage.dart';

class AuthService {
  final Dio _dio;
  final TokenStorage _tokenStorage;

  AuthService({required Dio dio, required TokenStorage tokenStorage})
      : _dio = dio,
        _tokenStorage = tokenStorage;

  /// Django SimpleJWT 로그인 (/api/v1/token/)
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
    bool rememberEmail = true,
  }) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.jwtCreate,
        data: {'email': email, 'password': password},
      );

      final data = response.data as Map<String, dynamic>;
      final accessToken  = data['access']  as String;
      final refreshToken = data['refresh'] as String;

      await _tokenStorage.saveAccessToken(accessToken);
      await _tokenStorage.saveRefreshToken(refreshToken);

      // 생체 인증 사용 설정이 켜져 있는 경우에만 생체 인증용 토큰 보관
      final isBioEnabled = await BiometricService.isBiometricEnabled();
      if (isBioEnabled) {
        await _tokenStorage.saveBiometricRefreshToken(refreshToken);
      }

      // 이메일 기억하기 설정 여부에 따라 저장 또는 삭제
      if (rememberEmail) {
        await _tokenStorage.saveSavedEmail(email);
      } else {
        await _tokenStorage.clearSavedEmail();
      }

      return {'success': true, 'access': accessToken, 'refresh': refreshToken};
    } on DioException catch (e) {
      return {'success': false, 'message': _parseDioError(e, defaultMessage: '로그인에 실패했습니다.')};
    } catch (_) {
      return {'success': false, 'message': '서버와의 통신 중 예기치 않은 오류가 발생했습니다.'};
    }
  }

  /// 생체 인증(Face ID / 지문)으로 로그인 가능 여부
  Future<bool> canBiometricLogin() async {
    final canAuth = await BiometricService.canAuthenticate();
    if (!canAuth) return false;
    final isEnabled = await BiometricService.isBiometricEnabled();
    if (!isEnabled) return false;
    final refreshToken = await _tokenStorage.getBiometricRefreshToken();
    return refreshToken != null && refreshToken.isNotEmpty;
  }

  /// 저장된 이메일 조회
  Future<String?> getSavedEmail() async {
    return await _tokenStorage.getSavedEmail();
  }

  /// 생체 인증(Face ID / 지문) 로그인 수행
  Future<Map<String, dynamic>> loginWithBiometrics() async {
    try {
      final label = await BiometricService.getBiometricLabel();
      final bioResult = await BiometricService.authenticate(
        reason: 'IBS 워크스페이스 로그인을 위해 $label 본인 인증을 진행합니다.',
      );

      if (bioResult != BiometricAuthResult.success) {
        if (bioResult == BiometricAuthResult.lockedOut) {
          return {'success': false, 'message': '생체 인증 시도 횟수를 초과했습니다. 비밀번호로 로그인해 주세요.'};
        }
        return {'success': false, 'message': '생체 인증에 실패했습니다.'};
      }

      final refreshToken = await _tokenStorage.getBiometricRefreshToken();
      if (refreshToken == null || refreshToken.isEmpty) {
        return {'success': false, 'message': '저장된 인증 정보가 없습니다. 비밀번호로 먼저 로그인해 주세요.'};
      }

      final response = await _dio.post(
        ApiEndpoints.jwtRefresh,
        data: {'refresh': refreshToken},
      );

      final data = response.data as Map<String, dynamic>;
      final accessToken = data['access'] as String;
      await _tokenStorage.saveAccessToken(accessToken);

      if (data.containsKey('refresh') && data['refresh'] != null) {
        final newRefresh = data['refresh'] as String;
        await _tokenStorage.saveRefreshToken(newRefresh);
        await _tokenStorage.saveBiometricRefreshToken(newRefresh);
      }

      return {'success': true, 'access': accessToken};
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        // 리프레시 토큰 만료 또는 폐기 시 로컬 생체 토큰 삭제
        await _tokenStorage.clearBiometricRefreshToken();
        return {'success': false, 'message': '인증 세션이 만료되었습니다. 비밀번호로 다시 로그인해 주세요.'};
      }
      return {'success': false, 'message': _parseDioError(e, defaultMessage: '생체 인증 로그인에 실패했습니다.')};
    } catch (_) {
      return {'success': false, 'message': '생체 로그인 처리 중 오류가 발생했습니다.'};
    }
  }

  /// 로그아웃 (일반 세션 토큰 삭제, 생체 로그인 세션은 유지)
  Future<void> logout() async {
    await _tokenStorage.clearTokens(clearBiometric: false);
  }

  /// 로그인 상태 확인
  Future<bool> isLoggedIn() async {
    final token = await _tokenStorage.getAccessToken();
    return token != null && token.isNotEmpty;
  }

  /// DioException 에러 파싱 유틸리티
  String _parseDioError(DioException e, {required String defaultMessage}) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return '서버 응답 시간이 초과되었습니다. 네트워크 연결을 확인하고 다시 시도해 주세요.';
      case DioExceptionType.connectionError:
        return '서버와 연결할 수 없습니다. 인터넷 상태를 확인해 주세요.';
      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode;
        final responseData = e.response?.data;

        if (statusCode == 401) {
          final detail = (responseData is Map) ? responseData['detail']?.toString() : null;
          if (detail != null && detail.contains('No active account found')) {
            return '등록되지 않은 이메일이거나 비밀번호가 일치하지 않습니다.';
          }
          return '이메일 또는 비밀번호가 일치하지 않습니다.';
        }

        if (responseData is Map) {
          if (responseData.containsKey('detail')) {
            return responseData['detail'].toString();
          }
          final messages = <String>[];
          responseData.forEach((key, value) {
            if (value is List) {
              messages.addAll(value.map((v) => '$v'));
            } else if (value is String) {
              messages.add(value);
            }
          });
          if (messages.isNotEmpty) {
            return messages.join('\n');
          }
        }
        return defaultMessage;
      default:
        return defaultMessage;
    }
  }
}

/// AuthService Riverpod 프로바이더
final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(
    dio: ref.watch(dioProvider),
    tokenStorage: ref.watch(tokenStorageProvider),
  );
});
