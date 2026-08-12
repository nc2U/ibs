import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/router/app_router.dart';

/// 홈 탭 — 3대 카테고리 히어로 카드 + 공용문서 퀵바
/// 기존 main_page.dart의 _buildHomeTab()을 독립 위젯으로 분리
class HomeTab extends ConsumerWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _HeroCard(
            categoryNum: '01',
            title: '업무 관리',
            englishTitle: 'WORK CORE',
            description: '현장 업무 이슈, 회의록, 액션아이템 및 공정 진척률',
            icon: Icons.task_alt_rounded,
            accentColor: AppColors.accentWork,
            gradientColors: [AppColors.accentWorkDeep, AppColors.bgCard],
            badgeText: '할당 업무',
            onTap: () => context.go(AppRoutes.work),
          ),
          const SizedBox(height: 12),
          _HeroCard(
            categoryNum: '02',
            title: '프로젝트 관리',
            englishTitle: 'PROJECT CORE',
            description: '현장 선택, 계약 현황, 수납/입출금 및 현장 설정',
            icon: Icons.business_center_rounded,
            accentColor: AppColors.accentProject,
            gradientColors: [AppColors.accentProjectDeep, AppColors.bgCard],
            badgeText: '계약 현황',
            onTap: () => context.go(AppRoutes.project),
          ),
          const SizedBox(height: 12),
          _HeroCard(
            categoryNum: '03',
            title: '전자 결재',
            englishTitle: 'APPROVAL CORE',
            description: '미결함 결재 승인/반려, 기안함 및 모바일 서명',
            icon: Icons.draw_rounded,
            accentColor: AppColors.accentApproval,
            gradientColors: [AppColors.accentApprovalDeep, AppColors.bgCard],
            badgeText: '준비 중',
            onTap: () => context.go(AppRoutes.approval),
          ),
          const SizedBox(height: 16),
          _DocsQuickBar(onTap: () => context.go(AppRoutes.docs)),
          const SizedBox(height: 12),
        ],
      ),
    );
  }
}

// ── 3대 카테고리 히어로 카드 ────────────────────────────────────────────────────
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
        height: 140,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: gradientColors,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.zero,
          border: Border.all(color: accentColor.withOpacity(0.3), width: 1.2),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.3),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Stack(
          children: [
            Positioned(
              right: -10,
              bottom: -20,
              child: Text(
                categoryNum,
                style: TextStyle(
                  fontSize: 90,
                  fontWeight: FontWeight.w900,
                  color: Colors.white.withOpacity(0.04),
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
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: accentColor.withOpacity(0.15),
                            borderRadius: BorderRadius.zero,
                            border: Border.all(color: accentColor.withOpacity(0.3)),
                          ),
                          child: Icon(icon, color: accentColor, size: 24),
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
                              ),
                            ),
                            Text(title, style: AppTextStyles.h3),
                          ],
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: accentColor.withOpacity(0.2),
                        borderRadius: BorderRadius.zero,
                        border: Border.all(color: accentColor.withOpacity(0.5)),
                      ),
                      child: Text(
                        badgeText,
                        style: AppTextStyles.label.copyWith(color: accentColor),
                      ),
                    ),
                  ],
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Expanded(
                      child: Text(
                        description,
                        style: AppTextStyles.bodySecond.copyWith(fontSize: 13),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Icon(Icons.arrow_forward_rounded, color: accentColor, size: 20),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// ── 공용 문서 퀵바 ──────────────────────────────────────────────────────────────
class _DocsQuickBar extends StatelessWidget {
  final VoidCallback onTap;
  const _DocsQuickBar({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.zero,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          borderRadius: BorderRadius.zero,
          border: Border.all(color: AppColors.border, width: 1),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFF334155),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.folder_shared_rounded, color: AppColors.textMuted, size: 22),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('공용 문서 섹션', style: AppTextStyles.titleSm),
                  const SizedBox(height: 2),
                  Text('전사 사규, 온보딩 가이드 및 공통 서식/도면 열람',
                      style: AppTextStyles.caption),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios_rounded, color: AppColors.textDisabled, size: 16),
          ],
        ),
      ),
    );
  }
}
