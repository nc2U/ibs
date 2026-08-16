import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/theme_provider.dart';
import '../../../core/router/app_router.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../../core/widgets/user_avatar.dart';

/// 내 설정 화면 — 프로필 / 알림 / 계정 관리
class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  bool _emailNotif = false;
  bool _pushNotif = false;

  void _showThemeSelector(BuildContext context) {
    final currentMode = ref.read(themeModeProvider);

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.only(left: 8, bottom: 12),
              child: Text(
                '화면 테마 설정',
                style: AppTextStyles.titleLg.copyWith(color: context.colors.textPrimary),
              ),
            ),
            ...AppThemeMode.values.map((mode) {
              final isSelected = currentMode == mode;
              final icon = switch (mode) {
                AppThemeMode.light => Icons.light_mode_outlined,
                AppThemeMode.dark => Icons.dark_mode_outlined,
                AppThemeMode.system => Icons.settings_brightness_outlined,
              };

              return ListTile(
                leading: Icon(
                  icon,
                  color: isSelected
                      ? context.colors.accentWork
                      : context.colors.textSecond,
                ),
                title: Text(
                  mode.label,
                  style: AppTextStyles.bodyMd.copyWith(
                    color: isSelected
                        ? context.colors.accentWork
                        : context.colors.textPrimary,
                    fontWeight:
                        isSelected ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
                trailing: isSelected
                    ? Icon(Icons.check_rounded,
                        color: context.colors.accentWork)
                    : null,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
                onTap: () {
                  ref.read(themeModeProvider.notifier).setTheme(mode);
                  Navigator.pop(ctx);
                },
              );
            }),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  Future<void> _handleLogout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: Text('로그아웃', style: AppTextStyles.titleLg.copyWith(color: context.colors.textPrimary)),
        content: Text(
          'IBS 워크스페이스에서\n로그아웃 하시겠습니까?',
          style: AppTextStyles.bodyMd.copyWith(color: context.colors.textSecond),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(
              '취소',
              style: AppTextStyles.bodyMd
                  .copyWith(color: context.colors.textMuted),
            ),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: context.colors.error,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(6)),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('로그아웃'),
          ),
        ],
      ),
    );

    if (confirm == true && mounted) {
      await ref.read(authProvider.notifier).logout();
      if (mounted) context.go(AppRoutes.login);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(currentUserProvider).valueOrNull;
    final themeMode = ref.watch(themeModeProvider);

    final username = user?.username ?? '';
    final email = user?.email ?? '';
    final cellPhone = user?.profile?.cellPhone;
    final hasRealName = user?.nameOrUsername != null && user!.nameOrUsername.isNotEmpty;
    final displayName = user?.nameOrUsername ?? username;

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        backgroundColor: context.colors.bgPrimary,
        elevation: 0,
        title: Text(
          '내 설정',
          style: AppTextStyles.titleLg.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        centerTitle: false,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 프로필 헤더 카드 ───────────────────────────────────────────
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Column(
                children: [
                  UserAvatar(
                    user: user,
                    radius: 36,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    displayName,
                    style: AppTextStyles.titleLg.copyWith(
                      fontWeight: FontWeight.bold,
                      color: context.colors.textPrimary,
                    ),
                  ),
                  if (hasRealName) ...[
                    const SizedBox(height: 3),
                    Text('@$username',
                        style: AppTextStyles.caption
                            .copyWith(color: context.colors.textMuted)),
                  ],
                  if (email.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(email, style: AppTextStyles.bodySecond.copyWith(color: context.colors.textSecond)),
                  ],
                  if (cellPhone != null && cellPhone.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(cellPhone,
                        style: AppTextStyles.caption
                            .copyWith(color: context.colors.textMuted)),
                  ],
                ],
              ),
            ),

            // ── 화면 설정 섹션 ────────────────────────────────────────────────
            _SectionLabel(title: '화면 설정'),
            _SettingTile(
              leading: Icon(
                switch (themeMode) {
                  AppThemeMode.light => Icons.light_mode_outlined,
                  AppThemeMode.dark => Icons.dark_mode_outlined,
                  AppThemeMode.system => Icons.settings_brightness_outlined,
                },
                color: context.colors.textSecond,
                size: 22,
              ),
              title: '화면 테마',
              subtitle: themeMode.label,
              trailing: Icon(Icons.chevron_right_rounded,
                  color: context.colors.textDisabled),
              onTap: () => _showThemeSelector(context),
            ),
            const _Divider(),

            // ── 알림 설정 섹션 ────────────────────────────────────────────────
            _SectionLabel(title: '알림 설정'),
            _SettingTile(
              leading: Icon(Icons.email_outlined,
                  color: context.colors.textSecond, size: 22),
              title: '이메일 알림',
              subtitle: '업무 및 결재 이메일 알림',
              trailing: Switch(
                value: _emailNotif,
                onChanged: (v) => setState(() => _emailNotif = v),
                activeColor: context.colors.accentWork,
                activeThumbColor: Colors.white,
              ),
            ),
            const _Divider(),
            _SettingTile(
              leading: Icon(Icons.notifications_active_outlined,
                  color: context.colors.textSecond, size: 22),
              title: '푸시 알림',
              subtitle: '모바일 푸시 알림 수신',
              trailing: Switch(
                value: _pushNotif,
                onChanged: (v) => setState(() => _pushNotif = v),
                activeColor: context.colors.accentWork,
                activeThumbColor: Colors.white,
              ),
            ),

            // ── 계정 섹션 ─────────────────────────────────────────────────────
            _SectionLabel(title: '계정'),
            _SettingTile(
              leading: Icon(Icons.lock_outline_rounded,
                  color: context.colors.textSecond, size: 22),
              title: '비밀번호 변경',
              subtitle: '준비 중',
              trailing: Icon(Icons.chevron_right_rounded,
                  color: context.colors.textDisabled),
              onTap: null,
            ),
            const _Divider(),
            _SettingTile(
              leading: Icon(Icons.logout_rounded,
                  color: context.colors.textSecond, size: 22),
              title: '로그아웃',
              trailing: const Icon(Icons.chevron_right_rounded,
                  color: AppColors.textDisabled),
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
  final Widget? trailing;
  final VoidCallback? onTap;

  const _SettingTile({
    required this.leading,
    required this.title,
    this.subtitle,
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
                        color: AppColors.textPrimary,
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
