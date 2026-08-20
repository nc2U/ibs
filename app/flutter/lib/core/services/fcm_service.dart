import 'dart:io';
import 'package:dio/dio.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'app_badge_service.dart';

/// Firebase Cloud Messaging (FCM) 푸시 알림 서비스
class FcmService {
  static final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  static bool _isInitialized = false;

  /// FCM 초기화 및 백엔드 기기 등록
  static Future<void> initialize(Dio dio) async {
    if (_isInitialized) return;

    try {
      // 1. Firebase 앱 초기화 확인
      if (Firebase.apps.isEmpty) {
        await Firebase.initializeApp();
      }

      // 2. 푸시 알림 수신 권한 요청 (iOS 대응)
      NotificationSettings settings = await _messaging.requestPermission(
        alert: true,
        announcement: false,
        badge: true,
        carPlay: false,
        criticalAlert: false,
        provisional: false,
        sound: true,
      );

      if (settings.authorizationStatus == AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional) {
        debugPrint('🔔 [FCM] 푸시 알림 권한 승인됨: ${settings.authorizationStatus}');

        // 3. APNs 토큰 대기 (iOS인 경우)
        if (Platform.isIOS) {
          String? apnsToken = await _messaging.getAPNSToken();
          debugPrint('🍎 [FCM] APNs Token: $apnsToken');
        }

        // 4. 기기 고유 FCM 토큰 발급
        String? fcmToken = await _messaging.getToken();
        if (fcmToken != null && fcmToken.isNotEmpty) {
          debugPrint('🔑 [FCM] Device Token: $fcmToken');
          await _registerTokenToServer(dio, fcmToken);
        }

        // 5. 토큰 갱신 이벤트 리스너
        _messaging.onTokenRefresh.listen((newToken) {
          debugPrint('🔄 [FCM] Device Token Refreshed: $newToken');
          _registerTokenToServer(dio, newToken);
        });

        // 6. 포그라운드(앱 켜진 상태) 메시지 리스너
        FirebaseMessaging.onMessage.listen((RemoteMessage message) {
          debugPrint('📩 [FCM] 포그라운드 알림 수신: ${message.notification?.title} / ${message.notification?.body}');
          final badgeStr = message.data['badge'] ?? message.notification?.android?.count;
          if (badgeStr != null) {
            final badgeCount = int.tryParse(badgeStr.toString());
            if (badgeCount != null) {
              AppBadgeService.updateBadgeCount(badgeCount);
            }
          }
        });

        // 7. 백그라운드 푸시 탭하여 앱 진입 시 리스너
        FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
          debugPrint('🚀 [FCM] 백그라운드 푸시 탭으로 앱 진입: ${message.data}');
        });

        _isInitialized = true;
      } else {
        debugPrint('⚠️ [FCM] 푸시 알림 권한 거부됨');
      }
    } catch (e) {
      debugPrint('⚠️ [FCM] 초기화 중 예외 발생: $e');
    }
  }

  /// 백엔드 (/api/v1/fcm-device/)에 기기 토큰 등록/갱신
  static Future<void> _registerTokenToServer(Dio dio, String token) async {
    try {
      final deviceType = Platform.isIOS
          ? 'ios'
          : (Platform.isAndroid ? 'android' : 'web');

      await dio.post(
        '/api/v1/fcm-device/',
        data: {
          'registration_id': token,
          'device_type': deviceType,
          'is_active': true,
        },
      );
      debugPrint('✅ [FCM] 백엔드에 기기 토큰 등록 성공');
    } on DioException catch (e) {
      debugPrint('❌ [FCM] 기기 토큰 백엔드 등록 실패: ${e.response?.statusCode} ${e.response?.data}');
    } catch (e) {
      debugPrint('❌ [FCM] 기기 토큰 등록 오류: $e');
    }
  }
}
