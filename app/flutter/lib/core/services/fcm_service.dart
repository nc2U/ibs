import 'dart:io';
import 'package:dio/dio.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'app_badge_service.dart';

/// 백엔드(_utils/push_service.py)와 일치하는 중요 알림 채널 ID
const String kHighImportanceChannelId = 'ibs_high_importance_channel';

/// 안드로이드 고유 Notification Channel 정의 (소리, 진동, 헤드업 알림 및 뱃지 허용)
const AndroidNotificationChannel kAndroidNotificationChannel = AndroidNotificationChannel(
  kHighImportanceChannelId,
  'IBS 중요 알림',
  description: '전자결재, 업무, 회의 및 긴급 공지사항 알림',
  importance: Importance.max,
  playSound: true,
  enableVibration: true,
  showBadge: true,
);

/// 로컬 알림 플러그인 싱글톤 인스턴스
final FlutterLocalNotificationsPlugin kLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

/// 백그라운드 / 앱 종료 상태에서 FCM 메시지 수신 시 실행되는 글로벌 최상위 핸들러
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  if (Firebase.apps.isEmpty) {
    await Firebase.initializeApp();
  }
  debugPrint('🌙 [FCM Background] 알림 수신: ${message.messageId} / ${message.notification?.title}');

  final badgeStr = message.data['badge'] ?? message.notification?.android?.count;
  if (badgeStr != null) {
    final badgeCount = int.tryParse(badgeStr.toString());
    if (badgeCount != null) {
      await AppBadgeService.updateBadgeCount(badgeCount);
    }
  }
}

/// Firebase Cloud Messaging (FCM) 푸시 알림 및 로컬 알림 서비스
class FcmService {
  static final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  static const _storage = FlutterSecureStorage();
  static const _pushEnabledKey = 'PUSH_NOTIFICATION_ENABLED';
  static bool _isInitialized = false;

  /// 푸시 알림 활성화 여부 확인 (기본값: false - 최초 권한 유도 전까지 꺼짐 상태 유지)
  static Future<bool> isPushEnabled() async {
    final value = await _storage.read(key: _pushEnabledKey);
    if (value == null) {
      // 최초 사용 시 OS 권한 상태 확인
      final settings = await _messaging.getNotificationSettings();
      final hasOsPermission = settings.authorizationStatus == AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional;
      return hasOsPermission;
    }
    return value == 'true';
  }

  /// 푸시 알림 설정 변경 및 서버 동기화
  static Future<bool> setPushEnabled(Dio dio, bool enabled) async {
    await _storage.write(key: _pushEnabledKey, value: enabled.toString());

    if (enabled) {
      // 켤 때는 OS 권한 요청 및 토큰 등록 진행
      final settings = await _messaging.requestPermission(
        alert: true,
        announcement: false,
        badge: true,
        carPlay: false,
        criticalAlert: false,
        provisional: false,
        sound: true,
      );

      final isAuthorized = settings.authorizationStatus == AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional;

      if (isAuthorized) {
        String? fcmToken = await _messaging.getToken();
        if (fcmToken != null && fcmToken.isNotEmpty) {
          await _registerTokenToServer(dio, fcmToken, isActive: true);
        }
        return true;
      } else {
        // OS 권한이 거부된 경우 false 저장
        await _storage.write(key: _pushEnabledKey, value: 'false');
        return false;
      }
    } else {
      // 끌 때는 백엔드 기기 토큰을 is_active = false 로 업데이트
      try {
        String? fcmToken = await _messaging.getToken();
        if (fcmToken != null && fcmToken.isNotEmpty) {
          await _registerTokenToServer(dio, fcmToken, isActive: false);
        }
      } catch (e) {
        debugPrint('⚠️ [FCM] 토큰 비활성화 실패: $e');
      }
      return true;
    }
  }

  /// FCM 초기화, 알림 채널 등록 및 백엔드 기기 토큰 등록
  static Future<void> initialize(Dio dio) async {
    if (_isInitialized) return;

    try {
      // 1. Firebase 앱 초기화 확인
      if (Firebase.apps.isEmpty) {
        await Firebase.initializeApp();
      }

      // 2. 안드로이드 로컬 알림 플러그인 초기화 및 Notification Channel 등록
      const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
      const iosInit = DarwinInitializationSettings(
        requestAlertPermission: true,
        requestBadgePermission: true,
        requestSoundPermission: true,
      );
      const initSettings = InitializationSettings(android: androidInit, iOS: iosInit);

      await kLocalNotificationsPlugin.initialize(
        initSettings,
        onDidReceiveNotificationResponse: (response) {
          debugPrint('👆 [LocalNotification] 알림 탭: ${response.payload}');
        },
      );

      // 안드로이드 시스템에 'ibs_high_importance_channel' 채널 공식 등록
      final androidImplementation = kLocalNotificationsPlugin
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>();
      if (androidImplementation != null) {
        await androidImplementation.createNotificationChannel(kAndroidNotificationChannel);
        debugPrint('📢 [FCM] Android Notification Channel 등록 완료 ($kHighImportanceChannelId)');
      }

      // 3. 사용자 설정 확인
      final enabled = await isPushEnabled();
      if (!enabled) {
        debugPrint('ℹ️ [FCM] 사용자가 푸시 알림을 비활성화했거나 아직 켜지 않았습니다.');
        _isInitialized = true;
        return;
      }

      // 3. 푸시 알림 수신 권한 요청 (Android 13+ 및 iOS)
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

        // 4. APNs 토큰 대기 (iOS인 경우)
        if (Platform.isIOS) {
          String? apnsToken;
          int retryCount = 0;
          while (apnsToken == null && retryCount < 10) {
            apnsToken = await _messaging.getAPNSToken();
            if (apnsToken == null) {
              await Future.delayed(const Duration(milliseconds: 500));
              retryCount++;
            }
          }
          debugPrint('🍎 [FCM] APNs Token: $apnsToken (retries: $retryCount)');
        }

        // 5. 기기 고유 FCM 토큰 발급
        String? fcmToken = await _messaging.getToken();
        if (fcmToken != null && fcmToken.isNotEmpty) {
          debugPrint('🔑 [FCM] Device Token: $fcmToken');
          await _registerTokenToServer(dio, fcmToken);
        } else {
          debugPrint('⚠️ [FCM] FCM Token 발급 실패 (null 또는 empty)');
        }

        // 6. 토큰 갱신 이벤트 리스너
        _messaging.onTokenRefresh.listen((newToken) {
          debugPrint('🔄 [FCM] Device Token Refreshed: $newToken');
          _registerTokenToServer(dio, newToken);
        });

        // 7. 포그라운드(앱 켜진 상태) 메시지 리스너
        FirebaseMessaging.onMessage.listen((RemoteMessage message) {
          debugPrint('📩 [FCM] 포그라운드 알림 수신: ${message.notification?.title} / ${message.notification?.body}');

          final notification = message.notification;
          final android = message.notification?.android;

          // 포그라운드에서도 상단 헤드업 팝업 및 상태바 알림 생성 (OS 뱃지 자동 연동)
          if (notification != null && !kIsWeb) {
            kLocalNotificationsPlugin.show(
              notification.hashCode,
              notification.title,
              notification.body,
              NotificationDetails(
                android: AndroidNotificationDetails(
                  kAndroidNotificationChannel.id,
                  kAndroidNotificationChannel.name,
                  channelDescription: kAndroidNotificationChannel.description,
                  importance: Importance.max,
                  priority: Priority.high,
                  icon: android?.smallIcon ?? '@mipmap/ic_launcher',
                  playSound: true,
                  enableVibration: true,
                  number: android?.count,
                ),
                iOS: const DarwinNotificationDetails(
                  presentAlert: true,
                  presentBadge: true,
                  presentSound: true,
                ),
              ),
              payload: message.data.toString(),
            );
          }

          // 뱃지 카운트 갱신
          final badgeStr = message.data['badge'] ?? message.notification?.android?.count;
          if (badgeStr != null) {
            final badgeCount = int.tryParse(badgeStr.toString());
            if (badgeCount != null) {
              AppBadgeService.updateBadgeCount(badgeCount);
            }
          }
        });

        // 8. 백그라운드 푸시 탭하여 앱 진입 시 리스너
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
  static Future<void> _registerTokenToServer(Dio dio, String token, {bool isActive = true}) async {
    try {
      final deviceType = Platform.isIOS
          ? 'ios'
          : (Platform.isAndroid ? 'android' : 'web');

      await dio.post(
        '/api/v1/fcm-device/',
        data: {
          'registration_id': token,
          'platform': deviceType,
          'device_type': deviceType,
          'is_active': isActive,
        },
      );
      debugPrint('✅ [FCM] 백엔드에 기기 토큰 등록 성공 ($deviceType, is_active: $isActive)');
    } on DioException catch (e) {
      debugPrint('❌ [FCM] 기기 토큰 백엔드 등록 실패: ${e.response?.statusCode} ${e.response?.data}');
    } catch (e) {
      debugPrint('❌ [FCM] 기기 토큰 등록 오류: $e');
    }
  }

  /// 클라이언트 자체 알림 채널 및 뱃지 자가 진단용 로컬 알림 발송
  static Future<void> showTestLocalNotification() async {
    await kLocalNotificationsPlugin.show(
      9999,
      '[IBS 웍스] 알림 시스템 자가 진단',
      '알림 채널(ibs_high_importance_channel) 및 배지 연동이 정상 작동합니다.',
      NotificationDetails(
        android: AndroidNotificationDetails(
          kAndroidNotificationChannel.id,
          kAndroidNotificationChannel.name,
          channelDescription: kAndroidNotificationChannel.description,
          importance: Importance.max,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
          playSound: true,
          enableVibration: true,
          number: 1,
        ),
        iOS: const DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
          badgeNumber: 1,
        ),
      ),
    );
    await AppBadgeService.updateBadgeCount(1);
    debugPrint('🧪 [FCM] 자가 진단 로컬 알림 및 배지(1) 테스트 완료');
  }
}
