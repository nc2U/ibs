import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/dio_provider.dart';
import '../../../core/storage/token_storage.dart';
import '../../../core/constants/api_endpoints.dart';
import '../../../core/services/biometric_service.dart';

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
      await _tokenStorage.saveSavedEmail(email);

      return {'success': true, 'access': accessToken, 'refresh': refreshToken};
    } on DioException catch (e) {
      String errorMessage = '로그인에 실패했습니다.';
      final responseData = e.response?.data;
      if (responseData is Map && responseData.containsKey('detail')) {
        errorMessage = responseData['detail'].toString();
      } else if (responseData != null) {
        errorMessage = responseData.toString();
      }
      return {'success': false, 'message': errorMessage};
    } catch (e) {
      return {'success': false, 'message': '서버와의 통신 중 오류가 발생했습니다.'};
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
        await _tokenStorage.saveRefreshToken(data['refresh'] as String);
      }

      return {'success': true, 'access': accessToken};
    } on DioException catch (e) {
      String errorMessage = '인증 세션이 만료되었습니다. 비밀번호로 다시 로그인해 주세요.';
      final responseData = e.response?.data;
      if (responseData is Map && responseData.containsKey('detail')) {
        errorMessage = responseData['detail'].toString();
      }
      return {'success': false, 'message': errorMessage};
    } catch (e) {
      return {'success': false, 'message': '생체 로그인 처리 중 오류가 발생했습니다.'};
    }
  }

  /// 로그아웃 (토큰 삭제)
  Future<void> logout() async {
    await _tokenStorage.clearTokens();
  }

  /// 로그인 상태 확인
  Future<bool> isLoggedIn() async {
    final token = await _tokenStorage.getAccessToken();
    return token != null && token.isNotEmpty;
  }
}

/// AuthService Riverpod 프로바이더
final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(
    dio: ref.watch(dioProvider),
    tokenStorage: ref.watch(tokenStorageProvider),
  );
});
