import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/theme/app_colors_extension.dart';

/// 사업 부지 관리 (Site) 메인 모듈 화면 (IBS Global - type == '2' 부동산 개발 전용)
/// 필지 목록 / 소유자 관리 / 부지 매매계약 / 협의 이력 관리 UI (radius = 0)
class SiteScreen extends ConsumerWidget {
  final VoidCallback onBackToMain;

  const SiteScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      children: [
        // ── 1. 사업 부지 모듈 헤더 배너 ──────────────────────────────────
        Container(
          color: context.colors.bgSurface,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: const Color(0xFF0D9488).withAlpha(30),
                  borderRadius: BorderRadius.zero,
                ),
                child: const Icon(
                  Icons.map_outlined,
                  size: 20,
                  color: Color(0xFF0D9488),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Text(
                          '부지 정보 관리',
                          style: AppTextStyles.titleSm.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                          decoration: BoxDecoration(
                            color: const Color(0xFF0D9488).withAlpha(20),
                            border: Border.all(color: const Color(0xFF0D9488).withAlpha(120), width: 0.8),
                            borderRadius: BorderRadius.circular(2),
                          ),
                          child: const Text(
                            'SITE',
                            style: TextStyle(
                              fontSize: 9.5,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF0D9488),
                              letterSpacing: 0.6,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '지번 목록 현황, 토지 소유자 정보 및 매입 계약 관리',
                      style: AppTextStyles.caption.copyWith(
                        color: context.colors.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        Divider(color: context.colors.border, height: 1),

        // ── 2. 부지 관리 세부 영역 목록 ────────────────────────────────────
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _SiteGroupTile(
                title: '필지 / 지번 목록',
                subtitle: '사업 대상 토지 지번, 지목, 면적(㎡·평) 및 매입 상태 현황',
                icon: Icons.pin_drop_outlined,
                badgeText: '지번·면적',
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('필지 목록 화면을 준비 중입니다.')),
                  );
                },
              ),
              const SizedBox(height: 10),
              _SiteGroupTile(
                title: '토지 소유자 관리',
                subtitle: '소유자 인적사항, 연락처, 소유 지분 및 권리관계 현황',
                icon: Icons.person_search_outlined,
                badgeText: '소유자·지분',
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('토지 소유자 화면을 준비 중입니다.')),
                  );
                },
              ),
              const SizedBox(height: 10),
              _SiteGroupTile(
                title: '부지 매매계약',
                subtitle: '토지 매매계약 체결 내역, 계약금/중도금/잔금 지급 일정 및 정산',
                icon: Icons.handshake_outlined,
                badgeText: '매매계약',
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('부지 매매계약 화면을 준비 중입니다.')),
                  );
                },
              ),
              const SizedBox(height: 10),
              _SiteGroupTile(
                title: '협의 / 상담 일지',
                subtitle: '토지 소유자별 매입 협의 이력, 상담 기록 및 동의율 현황',
                icon: Icons.speaker_notes_outlined,
                badgeText: '협의일지',
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('협의 일지 화면을 준비 중입니다.')),
                  );
                },
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _SiteGroupTile extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final String badgeText;
  final VoidCallback onTap;

  const _SiteGroupTile({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.badgeText,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.zero,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.zero,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D9488).withAlpha(20),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(
                      color: const Color(0xFF0D9488).withAlpha(60),
                      width: 0.8,
                    ),
                  ),
                  child: Icon(icon, size: 18, color: const Color(0xFF0D9488)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            title,
                            style: AppTextStyles.label.copyWith(
                              color: context.colors.textPrimary,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 5, vertical: 1.5),
                            decoration: BoxDecoration(
                              color: const Color(0xFF0D9488).withAlpha(20),
                              borderRadius: BorderRadius.zero,
                              border: Border.all(
                                color: const Color(0xFF0D9488).withAlpha(60),
                                width: 0.8,
                              ),
                            ),
                            child: Text(
                              badgeText,
                              style: AppTextStyles.caption.copyWith(
                                color: const Color(0xFF0D9488),
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 3),
                      Text(
                        subtitle,
                        style: AppTextStyles.caption
                            .copyWith(color: context.colors.textMuted),
                      ),
                    ],
                  ),
                ),
                Icon(
                  Icons.chevron_right_rounded,
                  size: 18,
                  color: context.colors.textMuted,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
