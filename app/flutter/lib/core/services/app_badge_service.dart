import 'package:app_badge_plus/app_badge_plus.dart';
import 'package:flutter/foundation.dart';

/// 앱 아이콘 알림 뱃지(Badge) 관리 서비스 (AGP 8+ / Android 14+ / iOS 대응)
class AppBadgeService {
  static bool? _isSupportedCache;

  /// 기기에서 앱 아이콘 뱃지를 지원하는지 여부 확인
  static Future<bool> isSupported() async {
    if (_isSupportedCache != null) return _isSupportedCache!;
    try {
      _isSupportedCache = await AppBadgePlus.isSupported();
    } catch (e) {
      debugPrint('⚠️ [AppBadge] 지원 여부 확인 오류: $e');
      _isSupportedCache = false;
    }
    return _isSupportedCache ?? false;
  }

  /// 뱃지 숫자 갱신 (0 이하면 뱃지 제거)
  static Future<void> updateBadgeCount(int count) async {
    try {
      final supported = await isSupported();
      if (!supported) return;

      if (count > 0) {
        await AppBadgePlus.updateBadge(count);
        debugPrint('🏷️ [AppBadge] 뱃지 카운트 갱신: $count');
      } else {
        await AppBadgePlus.updateBadge(0);
        debugPrint('🏷️ [AppBadge] 뱃지 제거');
      }
    } catch (e) {
      debugPrint('⚠️ [AppBadge] 뱃지 갱신 오류: $e');
    }
  }

  /// 뱃지 완전 제거
  static Future<void> removeBadge() async {
    try {
      final supported = await isSupported();
      if (supported) {
        await AppBadgePlus.updateBadge(0);
        debugPrint('🏷️ [AppBadge] 뱃지 제거 완료');
      }
    } catch (e) {
      debugPrint('⚠️ [AppBadge] 뱃지 제거 오류: $e');
    }
  }
}
