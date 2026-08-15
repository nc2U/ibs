import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../models/user_model.dart';
import 'dio_provider.dart';

part 'auth_provider.freezed.dart';

// ── 인증 상태 모델 ─────────────────────────────────────────────────────────────
@freezed
class AuthState with _$AuthState {
  const factory AuthState.authenticated({required String accessToken}) = _Authenticated;
  const factory AuthState.unauthenticated() = _Unauthenticated;
  const factory AuthState.loading() = _Loading;
}

// ── AuthNotifier ───────────────────────────────────────────────────────────────
class AuthNotifier extends AsyncNotifier<AuthState> {
  @override
  Future<AuthState> build() async {
    final tokenStorage = ref.read(tokenStorageProvider);
    final token = await tokenStorage.getAccessToken();
    if (token != null && token.isNotEmpty) {
      return AuthState.authenticated(accessToken: token);
    }
    return const AuthState.unauthenticated();
  }

  Future<void> logout() async {
    final tokenStorage = ref.read(tokenStorageProvider);
    await tokenStorage.clearTokens();
    state = const AsyncData(AuthState.unauthenticated());
  }

  void setAuthenticated(String accessToken) {
    state = AsyncData(AuthState.authenticated(accessToken: accessToken));
  }
}

// ── 프로바이더 ──────────────────────────────────────────────────────────────────
final authProvider = AsyncNotifierProvider<AuthNotifier, AuthState>(
  AuthNotifier.new,
);

/// 간편 인증 여부 확인 (go_router 가드에서 사용)
final isAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(authProvider).maybeWhen(
    data: (state) => state.maybeWhen(
      authenticated: (_) => true,
      orElse: () => false,
    ),
    orElse: () => false,
  );
});

/// 현재 로그인 사용자 정보 프로바이더 (JWT payload의 user_id 파싱 후 /api/v1/user/{id}/ 조회)
final currentUserProvider = FutureProvider<UserModel?>((ref) async {
  final authState = ref.watch(authProvider).valueOrNull;
  if (authState == null) return null;

  final token = authState.maybeWhen(
    authenticated: (t) => t,
    orElse: () => null,
  );
  if (token == null || token.isEmpty) return null;

  try {
    // JWT base64 payload 디코딩 (user_id 추출)
    final parts = token.split('.');
    if (parts.length >= 2) {
      final normalized = base64Url.normalize(parts[1]);
      final payloadString = utf8.decode(base64Url.decode(normalized));
      final payload = jsonDecode(payloadString) as Map<String, dynamic>;
      final userId = payload['user_id'];

      if (userId != null) {
        final dio = ref.watch(dioProvider);
        final res = await dio.get('/api/v1/user/$userId/');
        return UserModel.fromJson(res.data as Map<String, dynamic>);
      }
    }
  } catch (_) {}
  return null;
});
