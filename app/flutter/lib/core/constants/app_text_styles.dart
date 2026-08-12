import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_colors.dart';

/// IBS 워크스페이스 타이포그래피 시스템 (Noto Sans KR)
/// 현장 근무자 가독성 최우선: 최소 14sp, 본문 16sp
abstract class AppTextStyles {
  static TextStyle get _base => GoogleFonts.notoSansKr(color: AppColors.textPrimary);

  // ── Headline ──────────────────────────────────────
  static TextStyle get h1 => _base.copyWith(fontSize: 26, fontWeight: FontWeight.w800, letterSpacing: -0.5);
  static TextStyle get h2 => _base.copyWith(fontSize: 22, fontWeight: FontWeight.w700, letterSpacing: -0.5);
  static TextStyle get h3 => _base.copyWith(fontSize: 18, fontWeight: FontWeight.bold);

  // ── Title ────────────────────────────────────────
  static TextStyle get titleLg => _base.copyWith(fontSize: 16, fontWeight: FontWeight.bold);
  static TextStyle get titleMd => _base.copyWith(fontSize: 15, fontWeight: FontWeight.w600);
  static TextStyle get titleSm => _base.copyWith(fontSize: 14, fontWeight: FontWeight.w600);

  // ── Body ─────────────────────────────────────────
  static TextStyle get bodyLg => _base.copyWith(fontSize: 16, fontWeight: FontWeight.normal);
  static TextStyle get bodyMd => _base.copyWith(fontSize: 14, fontWeight: FontWeight.normal);
  static TextStyle get bodySm => _base.copyWith(fontSize: 13, fontWeight: FontWeight.normal);

  // ── Muted / Caption ──────────────────────────────
  static TextStyle get caption => _base.copyWith(fontSize: 12, color: AppColors.textMuted);
  static TextStyle get label   => _base.copyWith(fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.8);

  // ── Variants (color overrides) ───────────────────
  static TextStyle get bodySecond   => bodyMd.copyWith(color: AppColors.textSecond);
  static TextStyle get bodyMuted    => bodyMd.copyWith(color: AppColors.textMuted);
  static TextStyle get bodyDisabled => bodyMd.copyWith(color: AppColors.textDisabled);
}
