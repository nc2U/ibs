import 'package:dio/dio.dart';
import '../../../core/api/api_client.dart';
import '../../../core/constants/api_constants.dart';

class AuthService {
  final ApiClient _apiClient = ApiClient();

  // Django SimpleJWT 로그인 (/apiV1/jwt/create/)
  Future<Map<String, dynamic>> login({
    required String username,
    required String password,
  }) async {
    try {
      final response = await _apiClient.dio.post(
        ApiConstants.jwtCreate,
        data: {
          'username': username,
          'password': password,
        },
      );

      final data = response.data as Map<String, dynamic>;
      final accessToken = data['access'] as String;
      final refreshToken = data['refresh'] as String;

      // 토큰 보안 저장소에 저장
      await _apiClient.tokenStorage.saveAccessToken(accessToken);
      await _apiClient.tokenStorage.saveRefreshToken(refreshToken);

      return {
        'success': true,
        'access': accessToken,
        'refresh': refreshToken,
      };
    } on DioException catch (e) {
      String errorMessage = '로그인에 실패했습니다.';
      if (e.response != null && e.response?.data != null) {
        final data = e.response?.data;
        if (data is Map && data.containsKey('detail')) {
          errorMessage = data['detail'].toString();
        }
      }
      return {
        'success': false,
        'message': errorMessage,
      };
    } catch (e) {
      return {
        'success': false,
        'message': '서버와의 통신 중 오류가 발생했습니다: $e',
      };
    }
  }

  // 로그아웃
  Future<void> logout() async {
    await _apiClient.tokenStorage.clearTokens();
  }

  // 로그인 상태 확인 (AccessToken 존재 여부)
  Future<bool> isLoggedIn() async {
    final token = await _apiClient.tokenStorage.getAccessToken();
    return token != null && token.isNotEmpty;
  }
}
