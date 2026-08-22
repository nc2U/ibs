import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';

class BiometricService {
  static final LocalAuthentication _auth = LocalAuthentication();
  static const _storage = FlutterSecureStorage();
  static const _biometricEnabledKey = 'BIOMETRIC_AUTH_ENABLED';

  /// 기기 및 OS에서 생체 인증을 지원하고 등록된 정보가 있는지 여부
  static Future<bool> canAuthenticate() async {
    try {
      final bool canCheckBiometrics = await _auth.canCheckBiometrics;
      final bool isDeviceSupported = await _auth.isDeviceSupported();
      return canCheckBiometrics && isDeviceSupported;
    } on PlatformException {
      return false;
    }
  }

  /// 사용 가능한 생체 인증 수단 목록 조회 (지문, Face ID, 홍채 등)
  static Future<List<BiometricType>> getAvailableBiometrics() async {
    try {
      return await _auth.getAvailableBiometrics();
    } on PlatformException {
      return [];
    }
  }

  /// 생체 인증 유형 한글 명칭 (예: "Face ID", "지문 인식", "생체 인증")
  static Future<String> getBiometricLabel() async {
    final biometrics = await getAvailableBiometrics();
    if (biometrics.contains(BiometricType.face)) {
      return 'Face ID';
    } else if (biometrics.contains(BiometricType.fingerprint) ||
        biometrics.contains(BiometricType.strong) ||
        biometrics.contains(BiometricType.weak)) {
      return '지문 인식';
    } else if (biometrics.contains(BiometricType.iris)) {
      return '홍채 인식';
    }
    return '생체 인증';
  }

  /// 사용자가 앱 내에서 생체 인증 결재를 활성화했는지 여부 (기본값: 기기가 지원하면 true)
  static Future<bool> isBiometricEnabled() async {
    final value = await _storage.read(key: _biometricEnabledKey);
    if (value == null) {
      // 초기 설정이 없으면 기기 지원 여부에 따라 기본 활성화
      return await canAuthenticate();
    }
    return value == 'true';
  }

  /// 생체 인증 사용 설정 변경
  static Future<void> setBiometricEnabled(bool enabled) async {
    await _storage.write(key: _biometricEnabledKey, value: enabled.toString());
  }

  /// 생체 인증 실행
  static Future<BiometricAuthResult> authenticate({
    String reason = '전자결재 승인을 위해 본인 인증을 진행합니다.',
  }) async {
    try {
      final canAuth = await canAuthenticate();
      if (!canAuth) {
        return BiometricAuthResult.notAvailable;
      }

      final isEnabled = await isBiometricEnabled();
      if (!isEnabled) {
        // 사용자가 생체인증 기능을 비활성화한 경우 생체 인증 건너뜀
        return BiometricAuthResult.success;
      }

      final bool didAuthenticate = await _auth.authenticate(
        localizedReason: reason,
        options: const AuthenticationOptions(
          stickyAuth: true,
          biometricOnly: false, // 생체 인증 실패 시 디바이스 PIN/패턴 폴백 허용
          useErrorDialogs: true,
        ),
      );

      return didAuthenticate
          ? BiometricAuthResult.success
          : BiometricAuthResult.failed;
    } on PlatformException catch (e) {
      if (e.code == 'NotAvailable') {
        return BiometricAuthResult.notAvailable;
      } else if (e.code == 'LockedOut' || e.code == 'PermanentlyLockedOut') {
        return BiometricAuthResult.lockedOut;
      }
      return BiometricAuthResult.failed;
    } catch (_) {
      return BiometricAuthResult.failed;
    }
  }
}

enum BiometricAuthResult {
  success,
  failed,
  notAvailable,
  lockedOut,
}
