import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
  final _storage = const FlutterSecureStorage();

  String? _cachedAccessToken;
  String? _cachedRefreshToken;

  static const _accessTokenKey = 'ACCESS_TOKEN';
  static const _refreshTokenKey = 'REFRESH_TOKEN';
  static const _biometricRefreshTokenKey = 'BIOMETRIC_REFRESH_TOKEN';
  static const _savedEmailKey = 'SAVED_EMAIL';
  static const _cachedUserKey = 'CACHED_USER_DATA';

  String? _inMemoryUserData;

  // Cached User Data (JSON string)
  Future<void> saveUserData(String userJson) async {
    _inMemoryUserData = userJson;
    await _storage.write(key: _cachedUserKey, value: userJson);
  }

  Future<String?> getUserData() async {
    if (_inMemoryUserData != null && _inMemoryUserData!.isNotEmpty) {
      return _inMemoryUserData;
    }
    _inMemoryUserData = await _storage.read(key: _cachedUserKey);
    return _inMemoryUserData;
  }

  // Access Token 저장/읽기/삭제
  Future<void> saveAccessToken(String token) async {
    _cachedAccessToken = token;
    await _storage.write(key: _accessTokenKey, value: token);
  }

  Future<String?> getAccessToken() async {
    if (_cachedAccessToken != null && _cachedAccessToken!.isNotEmpty) {
      return _cachedAccessToken;
    }
    _cachedAccessToken = await _storage.read(key: _accessTokenKey);
    return _cachedAccessToken;
  }

  // Refresh Token 저장/읽기/삭제
  Future<void> saveRefreshToken(String token) async {
    _cachedRefreshToken = token;
    await _storage.write(key: _refreshTokenKey, value: token);
    await _storage.write(key: _biometricRefreshTokenKey, value: token);
  }

  Future<String?> getRefreshToken() async {
    if (_cachedRefreshToken != null && _cachedRefreshToken!.isNotEmpty) {
      return _cachedRefreshToken;
    }
    _cachedRefreshToken = await _storage.read(key: _refreshTokenKey);
    return _cachedRefreshToken;
  }

  Future<String?> getBiometricRefreshToken() async {
    return await _storage.read(key: _biometricRefreshTokenKey);
  }

  Future<void> clearBiometricRefreshToken() async {
    await _storage.delete(key: _biometricRefreshTokenKey);
  }

  // 저장된 이메일
  Future<void> saveSavedEmail(String email) async {
    await _storage.write(key: _savedEmailKey, value: email);
  }

  Future<String?> getSavedEmail() async {
    return await _storage.read(key: _savedEmailKey);
  }

  // 모든 토큰 삭제 (로그아웃 시)
  Future<void> clearTokens() async {
    _cachedAccessToken = null;
    _cachedRefreshToken = null;
    _inMemoryUserData = null;
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
    await _storage.delete(key: _cachedUserKey);
  }
}
