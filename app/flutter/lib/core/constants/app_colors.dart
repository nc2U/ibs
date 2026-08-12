import 'package:flutter/material.dart';

/// IBS 워크스페이스 브랜드 컬러 시스템
/// 웹(Vue) 다크 테마와 동일한 팔레트를 모바일에 적용
abstract class AppColors {
  // ── Background ──────────────────────────────────
  static const Color bgPrimary    = Color(0xFF202336); // 메인 배경
  static const Color bgCard       = Color(0xFF2A2E47); // 카드/컨테이너 배경
  static const Color bgSurface    = Color(0xFF191B2B); // 하단바/앱바
  static const Color bgInput      = Color(0xFF202336); // 입력 필드 배경

  // ── Border ──────────────────────────────────────
  static const Color border       = Color(0xFF3B4061);
  static const Color borderSubtle = Color(0xFF2E3256);

  // ── Text ────────────────────────────────────────
  static const Color textPrimary  = Colors.white;
  static const Color textSecond   = Color(0xFFCBD5E1);
  static const Color textMuted    = Color(0xFF94A3B8);
  static const Color textDisabled = Color(0xFF64748B);

  // ── Brand Accent (탭/카테고리 대응) ─────────────
  /// 업무관리 — Electric Blue
  static const Color accentWork     = Color(0xFF38BDF8);
  static const Color accentWorkDeep = Color(0xFF1E3A8A);

  /// 프로젝트관리 — Emerald Green
  static const Color accentProject     = Color(0xFF34D399);
  static const Color accentProjectDeep = Color(0xFF064E3B);

  /// 전자결재 — Amber Gold
  static const Color accentApproval     = Color(0xFFFBBF24);
  static const Color accentApprovalDeep = Color(0xFF78350F);

  /// 전사정보 — Purple
  static const Color accentCorp     = Color(0xFFA78BFA);
  static const Color accentCorpDeep = Color(0xFF4C1D95);

  // ── Status / Semantic ────────────────────────────
  static const Color success = Color(0xFF22C55E);
  static const Color warning = Color(0xFFF59E0B);
  static const Color error   = Color(0xFFEF4444);
  static const Color info    = Color(0xFF38BDF8);

  static const Color errorBg     = Color(0x26EF4444); // 16% opacity
  static const Color errorBorder = Color(0x66EF4444); // 40% opacity
}
