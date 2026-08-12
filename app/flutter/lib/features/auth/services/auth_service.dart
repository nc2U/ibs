import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/dio_provider.dart';
import '../../../core/storage/token_storage.dart';
import '../../../core/constants/api_endpoints.dart';

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
