import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/auth_provider.dart';

/// 내 설정 화면 — 프로필 / 알림 / 계정 관리
class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  bool _emailNotif = false;
  bool _pushNotif = false;

  Future<void> _handleLogout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: Text('로그아웃', style: AppTextStyles.titleLg),
        content: Text(
          'IBS 워크스페이스에서\n로그아웃 하시겠습니까?',
          style: AppTextStyles.bodySecond,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: AppTextStyles.bodyMuted),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text('로그아웃'),
          ),
        ],
      ),
    );
    if (confirm == true && mounted) {
      await ref.read(authProvider.notifier).logout();
    }
  }

  @override
  Widget build(BuildContext context) {
    // 추후 실제 user 정보 연동 시 authProvider에서 가져옴
    const username = '관리자';
    const email = '';
    const initial = 'A';

    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      appBar: AppBar(
        title: Text('내 설정', style: AppTextStyles.titleMd),
        backgroundColor: AppColors.bgPrimary,
        foregroundColor: AppColors.textPrimary,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppColors.textPrimary),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── 프로필 헤더 카드 ──────────────────────────────────────────────
            Container(
              color: AppColors.bgCard,
              padding: const EdgeInsets.symmetric(vertical: 28, horizontal: 20),
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 36,
                    backgroundColor: AppColors.accentWork.withAlpha(40),
                    child: Text(
                      initial,
                      style: AppTextStyles.h2.copyWith(
                          color: AppColors.accentWork),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Text(username, style: AppTextStyles.titleLg),
                  if (email.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(email, style: AppTextStyles.bodySecond),
                  ],
                  const SizedBox(height: 16),
                  OutlinedButton(
                    onPressed: null, // 준비 중
                    style: OutlinedButton.styleFrom(
                      shape: const RoundedRectangleBorder(
                          borderRadius: BorderRadius.zero),
                      side: const BorderSide(color: AppColors.border),
                      disabledForegroundColor: AppColors.textDisabled,
                    ),
                    child: const Text('프로필 수정 (준비 중)'),
                  ),
                ],
              ),
            ),

            // ── 알림 설정 섹션 ────────────────────────────────────────────────
            _SectionLabel(title: '알림 설정'),
            _SettingTile(
              leading: const Icon(Icons.email_outlined,
                  color: AppColors.textSecond, size: 22),
              title: '이메일 알림',
              subtitle: '업무 및 결재 이메일 알림',
              trailing: Switch(
                value: _emailNotif,
                onChanged: (v) => setState(() => _emailNotif = v),
                activeColor: AppColors.accentWork,
              ),
            ),
            const _Divider(),
            _SettingTile(
              leading: const Icon(Icons.notifications_active_outlined,
                  color: AppColors.textSecond, size: 22),
              title: '푸시 알림',
              subtitle: '모바일 푸시 알림 수신',
              trailing: Switch(
                value: _pushNotif,
                onChanged: (v) => setState(() => _pushNotif = v),
                activeColor: AppColors.accentWork,
              ),
            ),

            // ── 계정 섹션 ─────────────────────────────────────────────────────
            _SectionLabel(title: '계정'),
            _SettingTile(
              leading: const Icon(Icons.lock_outline_rounded,
                  color: AppColors.textSecond, size: 22),
              title: '비밀번호 변경',
              subtitle: '준비 중',
              trailing: const Icon(Icons.chevron_right_rounded,
                  color: AppColors.textDisabled),
              onTap: null,
            ),
            const _Divider(),
            _SettingTile(
              leading: const Icon(Icons.logout_rounded,
                  color: AppColors.error, size: 22),
              title: '로그아웃',
              titleColor: AppColors.error,
              trailing: const Icon(Icons.chevron_right_rounded,
                  color: AppColors.error),
              onTap: _handleLogout,
            ),
            const _Divider(),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

// ── 섹션 라벨 (회색 배경 구분자) ──────────────────────────────────────────────
class _SectionLabel extends StatelessWidget {
  final String title;
  const _SectionLabel({required this.title});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.bgSurface,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Text(title, style: AppTextStyles.bodyMuted),
    );
  }
}

// ── 설정 타일 ────────────────────────────────────────────────────────────────
class _SettingTile extends StatelessWidget {
  final Widget leading;
  final String title;
  final String? subtitle;
  final Color? titleColor;
  final Widget? trailing;
  final VoidCallback? onTap;

  const _SettingTile({
    required this.leading,
    required this.title,
    this.subtitle,
    this.titleColor,
    this.trailing,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.bgCard,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              leading,
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: AppTextStyles.bodyMd.copyWith(
                        color: titleColor ?? AppColors.textPrimary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    if (subtitle != null) ...[
                      const SizedBox(height: 2),
                      Text(subtitle!,
                          style: AppTextStyles.bodySm
                              .copyWith(color: AppColors.textMuted)),
                    ],
                  ],
                ),
              ),
              if (trailing != null) trailing!,
            ],
          ),
        ),
      ),
    );
  }
}

class _Divider extends StatelessWidget {
  const _Divider();

  @override
  Widget build(BuildContext context) {
    return const Divider(
        height: 1, thickness: 1, color: AppColors.border, indent: 52);
  }
}
