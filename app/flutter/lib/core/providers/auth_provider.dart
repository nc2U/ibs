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

/// 현재 로그인 사용자 정보 프로바이더 (로컬 캐시 즉시 반환 + 백그라운드 API 동기화)
final currentUserProvider = FutureProvider<UserModel?>((ref) async {
  final authState = ref.watch(authProvider).valueOrNull;
  if (authState == null) return null;

  final token = authState.maybeWhen(
    authenticated: (t) => t,
    orElse: () => null,
  );
  if (token == null || token.isEmpty) return null;

  final tokenStorage = ref.read(tokenStorageProvider);

  try {
    // 1. 로컬 캐시된 프로필이 있다면 캐시 데이터 로드 준비
    UserModel? cachedUser;
    final cachedJsonStr = await tokenStorage.getUserData();
    if (cachedJsonStr != null && cachedJsonStr.isNotEmpty) {
      try {
        final decoded = jsonDecode(cachedJsonStr) as Map<String, dynamic>;
        cachedUser = UserModel.fromJson(decoded);
      } catch (_) {}
    }

    // 2. JWT base64 payload 디코딩 (user_id 추출)
    final parts = token.split('.');
    if (parts.length >= 2) {
      final normalized = base64Url.normalize(parts[1]);
      final payloadString = utf8.decode(base64Url.decode(normalized));
      final payload = jsonDecode(payloadString) as Map<String, dynamic>;
      final userId = payload['user_id'];

      if (userId != null) {
        final dio = ref.watch(dioProvider);
        try {
          final res = await dio.get('/api/v1/user/$userId/');
          final user = UserModel.fromJson(res.data as Map<String, dynamic>);
          // 최신 사용자 정보 캐싱
          await tokenStorage.saveUserData(jsonEncode(user.toJson()));
          return user;
        } catch (_) {
          // 네트워크 실패/오프라인 시 캐시된 정보 반환
          if (cachedUser != null) return cachedUser;
          // 캐시도 없으면 JWT 페이로드 기반 최소 UserModel 생성
          final jwtUsername = payload['username'] as String? ?? '';
          if (jwtUsername.isNotEmpty) {
            return UserModel(
              pk: userId is int ? userId : int.tryParse('$userId') ?? 0,
              username: jwtUsername,
            );
          }
        }
      }
    }
    return cachedUser;
  } catch (_) {}
  return null;
});

/// 현재 로그인 사용자의 PK ID 즉시 반환 프로바이더 (네트워크 대기 없이 토큰에서 동기 추출)
final currentUserIdProvider = Provider<int?>((ref) {
  final authState = ref.watch(authProvider).valueOrNull;
  if (authState == null) return null;

  final token = authState.maybeWhen(
    authenticated: (t) => t,
    orElse: () => null,
  );
  if (token == null || token.isEmpty) return null;

  try {
    final parts = token.split('.');
    if (parts.length >= 2) {
      final normalized = base64Url.normalize(parts[1]);
      final payloadString = utf8.decode(base64Url.decode(normalized));
      final payload = jsonDecode(payloadString) as Map<String, dynamic>;
      final uid = payload['user_id'];
      if (uid is int) return uid;
      if (uid is num) return uid.toInt();
      if (uid is String) return int.tryParse(uid);
    }
  } catch (_) {}
  return null;
});

/// 전체 사용자/직원 목록 프로바이더 (대결자 지정, 업무 담당자 지정 등)
final usersListProvider = FutureProvider<List<UserModel>>((ref) async {
  final dio = ref.watch(dioProvider);
  final res = await dio.get('/api/v1/user/');
  final list = (res.data is List)
      ? res.data as List
      : ((res.data as Map<String, dynamic>)['results'] as List? ?? []);
  return list.map((e) => UserModel.fromJson(e as Map<String, dynamic>)).toList();
});
