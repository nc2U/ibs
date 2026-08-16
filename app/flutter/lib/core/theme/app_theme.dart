import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_colors_extension.dart';

/// IBS 워크스페이스 전역 테마 설정 (Material 3)
class AppTheme {
  // ☀️ 라이트 테마
  static ThemeData get light {
    const colors = AppColorsExtension.light;

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: colors.bgPrimary,
      colorScheme: ColorScheme.light(
        primary: colors.accentWork,
        secondary: colors.accentProject,
        surface: colors.bgCard,
        onSurface: colors.textPrimary,
        error: colors.error,
        outline: colors.border,
      ),
      textTheme: GoogleFonts.notoSansKrTextTheme(
        ThemeData.light().textTheme,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: colors.bgSurface,
        foregroundColor: colors.textPrimary,
        elevation: 0,
        scrolledUnderElevation: 0.5,
        surfaceTintColor: Colors.transparent,
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: colors.bgSurface,
        selectedItemColor: colors.accentWork,
        unselectedItemColor: colors.textDisabled,
        elevation: 4,
      ),
      cardTheme: CardThemeData(
        color: colors.bgCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          side: BorderSide(color: colors.border, width: 0.8),
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: colors.border,
        thickness: 0.8,
        space: 1,
      ),
      extensions: const [colors],
    );
  }

  // 🌙 다크 테마
  static ThemeData get dark {
    const colors = AppColorsExtension.dark;

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: colors.bgPrimary,
      colorScheme: ColorScheme.dark(
        primary: colors.accentWork,
        secondary: colors.accentProject,
        surface: colors.bgCard,
        onSurface: colors.textPrimary,
        error: colors.error,
        outline: colors.border,
      ),
      textTheme: GoogleFonts.notoSansKrTextTheme(
        ThemeData.dark().textTheme,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: colors.bgPrimary,
        foregroundColor: colors.textPrimary,
        elevation: 0,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.transparent,
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: colors.bgSurface,
        selectedItemColor: colors.accentWork,
        unselectedItemColor: colors.textDisabled,
        elevation: 4,
      ),
      cardTheme: CardThemeData(
        color: colors.bgCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          side: BorderSide(color: colors.border, width: 0.8),
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: colors.border,
        thickness: 0.8,
        space: 1,
      ),
      extensions: const [colors],
    );
  }
}
