import 'dart:ui';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'core/providers/theme_provider.dart';
import 'core/router/app_router.dart';
import 'core/services/fcm_service.dart';
import 'core/services/network_monitor.dart';
import 'core/theme/app_theme.dart';
import 'core/widgets/offline_banner.dart';
import 'core/widgets/share_intent_listener.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // ── 전역 런타임 에러 바운더리 (Crash Shield & 로깅) ──────────────────────
  FlutterError.onError = (details) {
    FlutterError.presentError(details);
    debugPrint('🚨 [FlutterError] ${details.exceptionAsString()}');
  };

  PlatformDispatcher.instance.onError = (error, stack) {
    debugPrint('🚨 [PlatformDispatcher] Unhandled async error: $error\n$stack');
    return true; // 에러 흡수 및 비정상 프로세스 강제 종료 방지
  };

  // 렌더링 파이프라인 오류 발생 시 회색 화면(Grey Screen) 대신 사용자 안내 UI 제공
  ErrorWidget.builder = (FlutterErrorDetails details) {
    return Material(
      color: Colors.transparent,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline_rounded, color: Colors.amber, size: 40),
              const SizedBox(height: 12),
              const Text(
                '화면 요소를 불러오는 중 일시적인 오류가 발생했습니다.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
              ),
              if (!kReleaseMode) ...[
                const SizedBox(height: 8),
                Text(
                  details.exceptionAsString(),
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 11, color: Colors.red),
                  textAlign: TextAlign.center,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  };

  // 한국어 로케일 및 날짜 포맷 초기화
  await initializeDateFormatting('ko_KR', null);

  // Firebase 초기화 및 백그라운드 푸시 리스너 등록
  try {
    if (Firebase.apps.isEmpty) {
      await Firebase.initializeApp();
    }
    FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
  } catch (e) {
    debugPrint('⚠️ [Main] Firebase background init skipped: $e');
  }

  runApp(
    const ProviderScope(
      child: IBSApp(),
    ),
  );
}

class IBSApp extends ConsumerWidget {
  const IBSApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    final themeMode = ref.watch(themeModeProvider);

    // 앱 시작 시 네트워크 모니터를 초기화 (warm-up)
    ref.watch(networkMonitorProvider);

    return MaterialApp.router(
      title: 'IBS 웍스',
      debugShowCheckedModeBanner: false,
      routerConfig: router,
      builder: (context, child) => OfflineBanner(
        child: ShareIntentListener(child: child ?? const SizedBox.shrink()),
      ),

      // ── 한국어 로케일 설정 ──────────────────────────────────────────
      locale: const Locale('ko', 'KR'),
      supportedLocales: const [
        Locale('ko', 'KR'),
        Locale('en', 'US'),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],

      // ── 3-Way 테마 시스템 (라이트 / 다크 / 기기설정) ────────────────
      themeMode: themeMode.themeMode,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
    );
  }
}
