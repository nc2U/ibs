import 'package:flutter/material.dart';

/// 테마별 색상 시스템 (ThemeExtension)
/// 라이트 모드와 다크 모드에 대응하는 색상 팔레트
@immutable
class AppColorsExtension extends ThemeExtension<AppColorsExtension> {
  // ── 배경 ──────────────────────────────────────────
  final Color bgPrimary;
  final Color bgCard;
  final Color bgSurface;
  final Color bgInput;

  // ── 테두리 ────────────────────────────────────────
  final Color border;
  final Color borderSubtle;

  // ── 텍스트 ────────────────────────────────────────
  final Color textPrimary;
  final Color textSecond;
  final Color textMuted;
  final Color textDisabled;

  // ── 브랜드 액센트 (카테고리/탭 대응) ─────────────
  final Color accentWork;
  final Color accentWorkDeep;
  final Color accentProject;
  final Color accentProjectDeep;
  final Color accentApproval;
  final Color accentApprovalDeep;
  final Color accentCorp;
  final Color accentCorpDeep;

  // ── 상태 ──────────────────────────────────────────
  final Color success;
  final Color warning;
  final Color error;
  final Color info;
  final Color errorBg;
  final Color errorBorder;

  const AppColorsExtension({
    required this.bgPrimary,
    required this.bgCard,
    required this.bgSurface,
    required this.bgInput,
    required this.border,
    required this.borderSubtle,
    required this.textPrimary,
    required this.textSecond,
    required this.textMuted,
    required this.textDisabled,
    required this.accentWork,
    required this.accentWorkDeep,
    required this.accentProject,
    required this.accentProjectDeep,
    required this.accentApproval,
    required this.accentApprovalDeep,
    required this.accentCorp,
    required this.accentCorpDeep,
    required this.success,
    required this.warning,
    required this.error,
    required this.info,
    required this.errorBg,
    required this.errorBorder,
  });

  // ☀️ 라이트 테마 팔레트 (Vue 웹 라이트 룩앤필과 100% 일치)
  static const light = AppColorsExtension(
    bgPrimary: Color(0xFFF1F5F9), // Slate 100
    bgCard: Color(0xFFFFFFFF), // White
    bgSurface: Color(0xFFFFFFFF), // White
    bgInput: Color(0xFFF8FAFC), // Slate 50
    border: Color(0xFFE2E8F0), // Slate 200
    borderSubtle: Color(0xFFF1F5F9),
    textPrimary: Color(0xFF0F172A), // Slate 900
    textSecond: Color(0xFF475569), // Slate 600
    textMuted: Color(0xFF64748B), // Slate 500
    textDisabled: Color(0xFF94A3B8), // Slate 400
    accentWork: Color(0xFF0284C7), // Sky 600
    accentWorkDeep: Color(0xFF0369A1),
    accentProject: Color(0xFF059669), // Emerald 600
    accentProjectDeep: Color(0xFF047857),
    accentApproval: Color(0xFFD97706), // Amber 600
    accentApprovalDeep: Color(0xFFB45309),
    accentCorp: Color(0xFF0284C7), // Sky/Azure 600 (청량하고 세련된 청색)
    accentCorpDeep: Color(0xFF0369A1),
    success: Color(0xFF16A34A),
    warning: Color(0xFFD97706),
    error: Color(0xFFDC2626),
    info: Color(0xFF0284C7),
    errorBg: Color(0x1FEF4444),
    errorBorder: Color(0x4DE2E8F0),
  );

  // 🌙 다크 테마 팔레트 (기존 AppColors 상수와 100% 일치)
  static const dark = AppColorsExtension(
    bgPrimary: Color(0xFF202336),
    bgCard: Color(0xFF2A2E47),
    bgSurface: Color(0xFF191B2B),
    bgInput: Color(0xFF202336),
    border: Color(0xFF3B4061),
    borderSubtle: Color(0xFF2E3256),
    textPrimary: Color(0xFFFFFFFF),
    textSecond: Color(0xFFCBD5E1),
    textMuted: Color(0xFF94A3B8),
    textDisabled: Color(0xFF64748B),
    accentWork: Color(0xFF38BDF8),
    accentWorkDeep: Color(0xFF1E3A8A),
    accentProject: Color(0xFF34D399),
    accentProjectDeep: Color(0xFF064E3B),
    accentApproval: Color(0xFFFBBF24),
    accentApprovalDeep: Color(0xFF78350F),
    accentCorp: Color(0xFF38BDF8), // Crisp Luminous Azure 400 (청량하고 세련된 청색)
    accentCorpDeep: Color(0xFF0369A1),
    success: Color(0xFF22C55E),
    warning: Color(0xFFF59E0B),
    error: Color(0xFFEF4444),
    info: Color(0xFF38BDF8),
    errorBg: Color(0x26EF4444),
    errorBorder: Color(0x66EF4444),
  );

  @override
  AppColorsExtension copyWith({
    Color? bgPrimary,
    Color? bgCard,
    Color? bgSurface,
    Color? bgInput,
    Color? border,
    Color? borderSubtle,
    Color? textPrimary,
    Color? textSecond,
    Color? textMuted,
    Color? textDisabled,
    Color? accentWork,
    Color? accentWorkDeep,
    Color? accentProject,
    Color? accentProjectDeep,
    Color? accentApproval,
    Color? accentApprovalDeep,
    Color? accentCorp,
    Color? accentCorpDeep,
    Color? success,
    Color? warning,
    Color? error,
    Color? info,
    Color? errorBg,
    Color? errorBorder,
  }) {
    return AppColorsExtension(
      bgPrimary: bgPrimary ?? this.bgPrimary,
      bgCard: bgCard ?? this.bgCard,
      bgSurface: bgSurface ?? this.bgSurface,
      bgInput: bgInput ?? this.bgInput,
      border: border ?? this.border,
      borderSubtle: borderSubtle ?? this.borderSubtle,
      textPrimary: textPrimary ?? this.textPrimary,
      textSecond: textSecond ?? this.textSecond,
      textMuted: textMuted ?? this.textMuted,
      textDisabled: textDisabled ?? this.textDisabled,
      accentWork: accentWork ?? this.accentWork,
      accentWorkDeep: accentWorkDeep ?? this.accentWorkDeep,
      accentProject: accentProject ?? this.accentProject,
      accentProjectDeep: accentProjectDeep ?? this.accentProjectDeep,
      accentApproval: accentApproval ?? this.accentApproval,
      accentApprovalDeep: accentApprovalDeep ?? this.accentApprovalDeep,
      accentCorp: accentCorp ?? this.accentCorp,
      accentCorpDeep: accentCorpDeep ?? this.accentCorpDeep,
      success: success ?? this.success,
      warning: warning ?? this.warning,
      error: error ?? this.error,
      info: info ?? this.info,
      errorBg: errorBg ?? this.errorBg,
      errorBorder: errorBorder ?? this.errorBorder,
    );
  }

  @override
  AppColorsExtension lerp(ThemeExtension<AppColorsExtension>? other, double t) {
    if (other is! AppColorsExtension) return this;
    return AppColorsExtension(
      bgPrimary: Color.lerp(bgPrimary, other.bgPrimary, t)!,
      bgCard: Color.lerp(bgCard, other.bgCard, t)!,
      bgSurface: Color.lerp(bgSurface, other.bgSurface, t)!,
      bgInput: Color.lerp(bgInput, other.bgInput, t)!,
      border: Color.lerp(border, other.border, t)!,
      borderSubtle: Color.lerp(borderSubtle, other.borderSubtle, t)!,
      textPrimary: Color.lerp(textPrimary, other.textPrimary, t)!,
      textSecond: Color.lerp(textSecond, other.textSecond, t)!,
      textMuted: Color.lerp(textMuted, other.textMuted, t)!,
      textDisabled: Color.lerp(textDisabled, other.textDisabled, t)!,
      accentWork: Color.lerp(accentWork, other.accentWork, t)!,
      accentWorkDeep: Color.lerp(accentWorkDeep, other.accentWorkDeep, t)!,
      accentProject: Color.lerp(accentProject, other.accentProject, t)!,
      accentProjectDeep: Color.lerp(accentProjectDeep, other.accentProjectDeep, t)!,
      accentApproval: Color.lerp(accentApproval, other.accentApproval, t)!,
      accentApprovalDeep: Color.lerp(accentApprovalDeep, other.accentApprovalDeep, t)!,
      accentCorp: Color.lerp(accentCorp, other.accentCorp, t)!,
      accentCorpDeep: Color.lerp(accentCorpDeep, other.accentCorpDeep, t)!,
      success: Color.lerp(success, other.success, t)!,
      warning: Color.lerp(warning, other.warning, t)!,
      error: Color.lerp(error, other.error, t)!,
      info: Color.lerp(info, other.info, t)!,
      errorBg: Color.lerp(errorBg, other.errorBg, t)!,
      errorBorder: Color.lerp(errorBorder, other.errorBorder, t)!,
    );
  }
}

/// BuildContext를 통한 테마 색상 확장 접근자
extension BuildContextThemeX on BuildContext {
  AppColorsExtension get colors =>
      Theme.of(this).extension<AppColorsExtension>() ?? AppColorsExtension.dark;

  bool get isDarkMode => Theme.of(this).brightness == Brightness.dark;
}
