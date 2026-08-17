import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/router/app_router.dart';
import '../../../core/theme/app_colors_extension.dart';

/// 홈 탭 — 3대 카테고리 히어로 카드 + 채널(공지/게시판) 퀵 카드
/// ── 배경색과 확연히 분리되면서도 눈이 편안한 프리미엄 서페이스 컬러 적용
class HomeTab extends ConsumerWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // ── 통합 검색 바 (모던 직사각형 스타일) ─────────────────────────
          InkWell(
            onTap: () => context.go(AppRoutes.search),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.zero,
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.search_rounded,
                    size: 20,
                    color: context.colors.accentWork,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      '통합 검색 (업무, 회의, 문서 등)...',
                      style: AppTextStyles.bodyMuted.copyWith(
                        color: context.colors.textMuted,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                    decoration: BoxDecoration(
                      color: context.colors.accentWork.withAlpha(25),
                      borderRadius: BorderRadius.circular(2),
                      border: Border.all(
                        color: context.colors.accentWork.withAlpha(60),
                        width: 0.6,
                      ),
                    ),
                    child: Text(
                      'Search',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.5,
                        color: context.colors.accentWork,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // ── 01. 업무 관리 (Work Core — Azure Blue) ──────────────────────
          _HeroCard(
            categoryNum: '01',
            title: '업무 관리',
            englishTitle: 'WORK CORE',
            description: '워크스페이스 회의, 업무, 액션아이템 등 협업 관리',
            icon: Icons.task_alt_rounded,
            accentColor: context.colors.accentWork,
            gradientColors: isDark
                ? const [Color(0xFF232D42), Color(0xFF1B2334)]
                : const [Color(0xFFFFFFFF), Color(0xFFF0F9FF)],
            badgeText: '협업 시스템',
            onTap: () => context.go(AppRoutes.work),
          ),
          const SizedBox(height: 12),

          // ── 02. 프로젝트 관리 (Project Core — Mint Emerald) ─────────────
          _HeroCard(
            categoryNum: '02',
            title: '프로젝트 관리',
            englishTitle: 'PROJECT CORE',
            description: '프로젝트 계약, 수납, 입출금, 부지 및 사업지 데이터',
            icon: Icons.business_center_rounded,
            accentColor: context.colors.accentProject,
            gradientColors: isDark
                ? const [Color(0xFF1F332E), Color(0xFF182824)]
                : const [Color(0xFFFFFFFF), Color(0xFFF0FDF4)],
            badgeText: '데이터 관리',
            onTap: () => context.go(AppRoutes.project),
          ),
          const SizedBox(height: 12),

          // ── 03. 전자 결재 (Approval Core — Honey Amber) ─────────────────
          _HeroCard(
            categoryNum: '03',
            title: '전자결재',
            englishTitle: 'APPROVAL CORE',
            description: '기안/미결함, 승인/반려/위임, 모바일 전자서명 및 알림',
            icon: Icons.draw_rounded,
            accentColor: context.colors.accentApproval,
            gradientColors: isDark
                ? const [Color(0xFF32281E), Color(0xFF261F17)]
                : const [Color(0xFFFFFFFF), Color(0xFFFFFBEB)],
            badgeText: '준비 중...',
            onTap: () => context.go(AppRoutes.approval),
          ),
          const SizedBox(height: 24),

          // ── 채널 섹션 헤더 ─────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(
              children: [
                Icon(
                  Icons.campaign_rounded,
                  size: 15,
                  color: context.colors.textMuted,
                ),
                const SizedBox(width: 6),
                Text(
                  '채널',
                  style: AppTextStyles.label.copyWith(
                    color: context.colors.textMuted,
                    letterSpacing: 1.0,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Divider(
                    color: context.colors.border,
                    thickness: 0.8,
                    height: 1,
                  ),
                ),
              ],
            ),
          ),

          // ── 채널 Quick Card: 공지사항 ──────────────────────────────────
          _ChannelQuickCard(
            title: '공지사항',
            subtitle: '워크스페이스 최신 공지 및 안내 사항',
            icon: Icons.notifications_active_outlined,
            accentColor: context.colors.accentCorp,
            onTap: () => context.go('${AppRoutes.channel}?tab=0'),
          ),
          const SizedBox(height: 8),

          // ── 채널 Quick Card: 게시판 ────────────────────────────────────
          _ChannelQuickCard(
            title: '게시판',
            subtitle: '팀/현장별 게시글 및 자유 토론 채널',
            icon: Icons.forum_outlined,
            accentColor: context.colors.accentProject,
            onTap: () => context.go('${AppRoutes.channel}?tab=1'),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

// ── 3대 카테고리 프리미엄 히어로 카드 (Left Accent Bar + 눈이 편안한 대비) ─────────
class _HeroCard extends StatelessWidget {
  final String categoryNum;
  final String title;
  final String englishTitle;
  final String description;
  final IconData icon;
  final Color accentColor;
  final List<Color> gradientColors;
  final String badgeText;
  final VoidCallback onTap;

  const _HeroCard({
    required this.categoryNum,
    required this.title,
    required this.englishTitle,
    required this.description,
    required this.icon,
    required this.accentColor,
    required this.gradientColors,
    required this.badgeText,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.zero,
      child: Container(
        height: 136,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: gradientColors,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.zero,
          border: Border.all(
            color: isDark
                ? accentColor.withAlpha(70)
                : context.colors.border,
            width: 1.0,
          ),
          boxShadow: [
            BoxShadow(
              color: isDark
                  ? Colors.black.withAlpha(45)
                  : accentColor.withAlpha(18),
              blurRadius: 10,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Stack(
          children: [
            // 1. 좌측 시그니처 액센트 인디케이터 바 (Left Indicator)
            Positioned(
              left: 0,
              top: 0,
              bottom: 0,
              child: Container(
                width: 3.5,
                color: accentColor,
              ),
            ),

            // 2. 배경 수치 워터마크 (우측 하단)
            Positioned(
              right: -6,
              bottom: -22,
              child: Text(
                categoryNum,
                style: TextStyle(
                  fontSize: 90,
                  fontWeight: FontWeight.w900,
                  color: isDark
                      ? accentColor.withAlpha(20)
                      : accentColor.withAlpha(22),
                  letterSpacing: -4,
                ),
              ),
            ),

            // 3. 카드 메인 컨텐츠
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 18, 18, 18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8.5),
                            decoration: BoxDecoration(
                              color: accentColor.withAlpha(28),
                              borderRadius: BorderRadius.circular(2),
                              border: Border.all(
                                color: accentColor.withAlpha(65),
                                width: 0.8,
                              ),
                            ),
                            child: Icon(icon, color: accentColor, size: 20),
                          ),
                          const SizedBox(width: 12),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                englishTitle,
                                style: AppTextStyles.label.copyWith(
                                  color: accentColor,
                                  letterSpacing: 1.4,
                                  fontWeight: FontWeight.w800,
                                  fontSize: 10.5,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                title,
                                style: AppTextStyles.titleLg.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: context.colors.textPrimary,
                                  letterSpacing: -0.3,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 3.5),
                        decoration: BoxDecoration(
                          color: accentColor.withAlpha(22),
                          borderRadius: BorderRadius.circular(2),
                          border: Border.all(
                            color: accentColor.withAlpha(60),
                            width: 0.8,
                          ),
                        ),
                        child: Text(
                          badgeText,
                          style: AppTextStyles.caption.copyWith(
                            color: accentColor,
                            fontWeight: FontWeight.bold,
                            fontSize: 10.5,
                            letterSpacing: -0.2,
                          ),
                        ),
                      ),
                    ],
                  ),
                  Text(
                    description,
                    style: AppTextStyles.bodySecond.copyWith(
                      color: context.colors.textSecond,
                      fontSize: 12.5,
                      letterSpacing: -0.15,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 채널 Quick Card (공지 / 게시판 진입 행 카드) ────────────────────────────────
class _ChannelQuickCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color accentColor;
  final VoidCallback onTap;

  const _ChannelQuickCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.accentColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.zero,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(color: context.colors.border, width: 0.8),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: accentColor.withAlpha(20),
                borderRadius: BorderRadius.circular(2),
                border: Border.all(
                  color: accentColor.withAlpha(45),
                  width: 0.6,
                ),
              ),
              child: Icon(icon, color: accentColor, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: AppTextStyles.titleSm.copyWith(
                      color: context.colors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: AppTextStyles.bodySm.copyWith(
                      color: context.colors.textMuted,
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.arrow_forward_ios_rounded,
              size: 13,
              color: context.colors.textMuted,
            ),
          ],
        ),
      ),
    );
  }
}
