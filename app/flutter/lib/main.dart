import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/providers/theme_provider.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'core/widgets/share_intent_listener.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
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

      // ── 3-Way 테마 시스템 (라이트 / 다크 / 기기설정) ────────────────
      themeMode: themeMode.themeMode,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
    );
  }
}
