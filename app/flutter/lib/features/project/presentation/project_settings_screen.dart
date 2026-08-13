import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';

/// 프로젝트 설정 (Settings) 화면 (Phase 2 스케일러블 플레이스홀더)
class ProjectSettingsScreen extends ConsumerWidget {
  final VoidCallback onBackToMain;

  const ProjectSettingsScreen({
    super.key,
    required this.onBackToMain,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      children: [
        // ── 1. 프로젝트 설정 모듈 헤더 배너 ──────────────────────────────────
        Container(
          color: AppColors.bgSurface,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: const Color(0xFF00796B).withAlpha(30),
                  borderRadius: BorderRadius.zero,
                ),
                child: const Icon(Icons.settings_outlined,
                    size: 20, color: Color(0xFF00796B)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('프로젝트 설정 (Settings)',
                        style: AppTextStyles.titleSm
                            .copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 2),
                    Text('사업지 기본 정보, 차수/동호수 배치 및 수납 약정 설정',
                        style: AppTextStyles.caption
                            .copyWith(color: AppColors.textMuted)),
                  ],
                ),
              ),
            ],
          ),
        ),
        const Divider(color: AppColors.border, height: 1),

        // ── 2. 설정 카테고리 스크롤 뷰 ───────────────────────────────────────
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _SettingGroupTile(
                title: '프로젝트 개요 및 기본 정보',
                subtitle: '사업지 명칭, 대표 주소, 대지면적, 연면적 및 사업 기간 설정',
                icon: Icons.info_outline_rounded,
                accentColor: const Color(0xFF00796B),
              ),
              const SizedBox(height: 12),
              _SettingGroupTile(
                title: '타입 및 유닛 (동·호수) 설정',
                subtitle: '분양 유닛 타입(A/B/C), 동/호수 배정 및 공급면적 관리',
                icon: Icons.domain_outlined,
                accentColor: const Color(0xFF1565C0),
              ),
              const SizedBox(height: 12),
              _SettingGroupTile(
                title: '차수 및 수납 약정금 설정',
                subtitle: '계약금, 중도금(1~6차), 잔금 비율 및 수납 계좌 지정',
                icon: Icons.payments_outlined,
                accentColor: const Color(0xFF2E7D32),
              ),
              const SizedBox(height: 12),
              _SettingGroupTile(
                title: '예산 및 지출 계정 설정',
                subtitle: '수입/지출 예산안 수립 및 세부 회계 계정 과목 매핑',
                icon: Icons.account_balance_wallet_outlined,
                accentColor: const Color(0xFFE65100),
              ),
              const SizedBox(height: 24),

              // 데이터 준비 중 안내 카드
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: AppColors.bgCard,
                  borderRadius: BorderRadius.zero,
                  border: Border.all(color: AppColors.border, width: 0.8),
                ),
                child: Column(
                  children: [
                    const Icon(Icons.admin_panel_settings_outlined,
                        size: 40, color: AppColors.textDisabled),
                    const SizedBox(height: 12),
                    Text('프로젝트 상세 설정 모듈 준비 중입니다.',
                        style: AppTextStyles.titleSm
                            .copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 6),
                    Text(
                      '관리자 권한에 따른 프로젝트 마스터 데이터 설정 페이지가 연동됩니다.',
                      style: AppTextStyles.bodySecond
                          .copyWith(color: AppColors.textMuted),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _SettingGroupTile extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color accentColor;

  const _SettingGroupTile({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.accentColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: AppColors.border, width: 0.8),
      ),
      child: ListTile(
        leading: Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: accentColor.withAlpha(25),
            borderRadius: BorderRadius.zero,
          ),
          child: Icon(icon, size: 20, color: accentColor),
        ),
        title: Text(title,
            style:
                AppTextStyles.bodyMd.copyWith(fontWeight: FontWeight.bold)),
        subtitle: Text(subtitle,
            style: AppTextStyles.caption.copyWith(color: AppColors.textMuted)),
        trailing: const Icon(Icons.chevron_right_rounded,
            size: 20, color: AppColors.textMuted),
        onTap: () {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('$title 상세 설정 준비 중입니다.')),
          );
        },
      ),
    );
  }
}
