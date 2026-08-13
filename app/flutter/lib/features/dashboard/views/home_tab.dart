import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/router/app_router.dart';

/// 홈 탭 — 3대 카테고리 히어로 카드 + 공용문서 퀵바 (톤다운 그라데이션 적용)
class HomeTab extends ConsumerWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // ── 01. 업무 관리 (Work Core) ──────────────────────────────────
          _HeroCard(
            categoryNum: '01',
            title: '업무 관리',
            englishTitle: 'WORK CORE',
            description: '워크스페이스 업무 이슈, 회의록, 액션아이템 및 진척률',
            icon: Icons.task_alt_rounded,
            accentColor: AppColors.accentWork,
            gradientColors: const [Color(0xFF142642), Color(0xFF1A1D2E)],
            badgeText: '할당 업무',
            onTap: () => context.go(AppRoutes.work),
          ),
          const SizedBox(height: 12),

          // ── 02. 프로젝트 관리 (Project Core) ───────────────────────────
          _HeroCard(
            categoryNum: '02',
            title: '프로젝트 관리',
            englishTitle: 'PROJECT CORE',
            description: '프로젝트 선택, 계약 현황, 수납/입출금 및 상세 설정',
            icon: Icons.business_center_rounded,
            accentColor: AppColors.accentProject,
            gradientColors: const [Color(0xFF0F2E23), Color(0xFF1A1D2E)],
            badgeText: '계약 현황',
            onTap: () => context.go(AppRoutes.project),
          ),
          const SizedBox(height: 12),

          // ── 03. 전자 결재 (Approval Core) ──────────────────────────────
          _HeroCard(
            categoryNum: '03',
            title: '전자 결재',
            englishTitle: 'APPROVAL CORE',
            description: '미결함 결재 승인/반려, 기안함 및 모바일 서명',
            icon: Icons.draw_rounded,
            accentColor: AppColors.accentApproval,
            gradientColors: const [Color(0xFF332010), Color(0xFF1A1D2E)],
            badgeText: '준비 중',
            onTap: () => context.go(AppRoutes.approval),
          ),
          const SizedBox(height: 16),

          // ── 공용 문서 퀵 바 ───────────────────────────────────────────
          _DocsQuickBar(onTap: () => context.go(AppRoutes.docs)),
          const SizedBox(height: 12),
        ],
      ),
    );
  }
}

// ── 3대 카테고리 히어로 카드 (radius = 0, 톤다운 그라데이션 적용) ──────────────────
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
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.zero,
      child: Container(
        height: 136,
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: gradientColors,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.zero,
          border: Border.all(color: accentColor.withAlpha(45), width: 1.0),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withAlpha(40),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Stack(
          children: [
            // 배경 수치 워터마크
            Positioned(
              right: -10,
              bottom: -22,
              child: Text(
                categoryNum,
                style: TextStyle(
                  fontSize: 88,
                  fontWeight: FontWeight.w900,
                  color: Colors.white.withAlpha(10),
                  letterSpacing: -4,
                ),
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(9),
                          decoration: BoxDecoration(
                            color: accentColor.withAlpha(30),
                            borderRadius: BorderRadius.zero,
                            border: Border.all(color: accentColor.withAlpha(60)),
                          ),
                          child: Icon(icon, color: accentColor, size: 22),
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              englishTitle,
                              style: AppTextStyles.label.copyWith(
                                color: accentColor,
                                letterSpacing: 1.2,
                                fontSize: 10.5,
                              ),
                            ),
                            Text(title, style: AppTextStyles.titleLg),
                          ],
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: accentColor.withAlpha(25),
                        borderRadius: BorderRadius.zero,
                        border: Border.all(color: accentColor.withAlpha(60)),
                      ),
                      child: Text(
                        badgeText,
                        style: AppTextStyles.caption.copyWith(
                          color: accentColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ],
                ),
                Text(
                  description,
                  style: AppTextStyles.bodyMuted.copyWith(fontSize: 12.5),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// ── 공용 문서 퀵바 ─────────────────────────────────────────────────────────────
class _DocsQuickBar extends StatelessWidget {
  final VoidCallback onTap;

  const _DocsQuickBar({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.zero,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(color: AppColors.border, width: 0.8),
        ),
        child: Row(
          children: [
            const Icon(Icons.folder_shared_outlined,
                color: AppColors.accentCorp, size: 20),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                '공용 문서함 (사규/표준서식)',
                style: AppTextStyles.bodyMd.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            const Icon(Icons.arrow_forward_ios_rounded,
                size: 14, color: AppColors.textMuted),
          ],
        ),
      ),
    );
  }
}
