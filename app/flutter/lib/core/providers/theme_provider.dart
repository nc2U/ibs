import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// 앱 테마 모드 옵션
enum AppThemeMode {
  light('라이트 모드', ThemeMode.light),
  dark('다크 모드', ThemeMode.dark),
  system('기기 설정', ThemeMode.system);

  final String label;
  final ThemeMode themeMode;
  const AppThemeMode(this.label, this.themeMode);
}

final themeModeProvider =
    StateNotifierProvider<ThemeNotifier, AppThemeMode>((ref) {
  return ThemeNotifier();
});

class ThemeNotifier extends StateNotifier<AppThemeMode> {
  static const _storageKey = 'APP_THEME_MODE';
  final _storage = const FlutterSecureStorage();

  ThemeNotifier() : super(AppThemeMode.dark) {
    _loadSavedTheme();
  }

  Future<void> _loadSavedTheme() async {
    try {
      final saved = await _storage.read(key: _storageKey);
      if (saved != null) {
        state = AppThemeMode.values.firstWhere(
          (e) => e.name == saved,
          orElse: () => AppThemeMode.dark,
        );
      }
    } catch (_) {}
  }

  Future<void> setTheme(AppThemeMode mode) async {
    state = mode;
    try {
      await _storage.write(key: _storageKey, value: mode.name);
    } catch (_) {}
  }
}
