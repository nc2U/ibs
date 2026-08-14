import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'core/constants/app_colors.dart';
import 'core/router/app_router.dart';
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

    return MaterialApp.router(
      title: 'IBS 웍스',
      debugShowCheckedModeBanner: false,
      routerConfig: router,
      builder: (context, child) => ShareIntentListener(child: child!),

      // 전역 다크 테마 (브랜드 컬러 시스템 적용)
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: AppColors.bgPrimary,
        colorScheme: ColorScheme.dark(
          primary: AppColors.accentWork,
          secondary: AppColors.accentProject,
          surface: AppColors.bgCard,
          onSurface: AppColors.textPrimary,
        ),
        textTheme: GoogleFonts.notoSansKrTextTheme(
          ThemeData.dark().textTheme,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: AppColors.bgPrimary,
          foregroundColor: AppColors.textPrimary,
          elevation: 0,
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: AppColors.bgSurface,
          selectedItemColor: AppColors.accentWork,
          unselectedItemColor: AppColors.textDisabled,
        ),
        cardTheme: const CardThemeData(
          color: AppColors.bgCard,
          elevation: 0,
        ),
      ),
    );
  }
}
