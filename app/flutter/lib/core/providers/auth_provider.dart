import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
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
