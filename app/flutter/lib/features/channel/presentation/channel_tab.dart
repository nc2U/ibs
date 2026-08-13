import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';

/// 채널 탭 — 공지사항 / 게시판
class ChannelTab extends StatelessWidget {
  const ChannelTab({super.key});

  static const _noticeColor = Color(0xFF1565C0);
  static const _forumColor  = Color(0xFF00695C);

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // ── 공지사항 ──────────────────────────────────────────────────────
          const _SectionHeader(
            title: '공지사항',
            icon: Icons.campaign_rounded,
            accentColor: _noticeColor,
          ),
          const SizedBox(height: 10),
          Text(
            '워크스페이스 공지사항 및 안내 사항이 연동됩니다.',
            style: AppTextStyles.bodyMuted,
          ),
          const SizedBox(height: 10),
          const _PlaceholderCard(text: '공지사항 API 연동 준비 중'),
          const SizedBox(height: 24),

          // ── 게시판 ────────────────────────────────────────────────────────
          const _SectionHeader(
            title: '게시판',
            icon: Icons.forum_outlined,
            accentColor: _forumColor,
          ),
          const SizedBox(height: 10),
          Text(
            '팀 게시판 및 자유 토론 채널입니다.',
            style: AppTextStyles.bodyMuted,
          ),
          const SizedBox(height: 10),
          const _PlaceholderCard(text: '게시판 API 연동 준비 중'),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

// ── 섹션 헤더 (왼쪽 컬러 보더 바) ─────────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color accentColor;

  const _SectionHeader({
    required this.title,
    required this.icon,
    required this.accentColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border(left: BorderSide(color: accentColor, width: 4.0)),
      ),
      child: Row(
        children: [
          Icon(icon, color: accentColor, size: 20),
          const SizedBox(width: 8),
          Text(
            title,
            style: AppTextStyles.titleMd.copyWith(color: AppColors.textPrimary),
          ),
        ],
      ),
    );
  }
}

// ── 준비 중 Placeholder 카드 ──────────────────────────────────────────────────
class _PlaceholderCard extends StatelessWidget {
  final String text;

  const _PlaceholderCard({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: AppColors.border, width: 0.8),
      ),
      child: Row(
        children: [
          const Icon(Icons.construction_rounded,
              color: AppColors.textDisabled, size: 18),
          const SizedBox(width: 10),
          Text(text, style: AppTextStyles.bodyMuted),
        ],
      ),
    );
  }
}
