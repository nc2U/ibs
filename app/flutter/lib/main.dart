import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'core/providers/theme_provider.dart';
import 'core/router/app_router.dart';
import 'core/services/fcm_service.dart';
import 'core/theme/app_theme.dart';
import 'core/widgets/share_intent_listener.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

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

    return MaterialApp.router(
      title: 'IBS 웍스',
      debugShowCheckedModeBanner: false,
      routerConfig: router,
      builder: (context, child) => ShareIntentListener(child: child!),

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
