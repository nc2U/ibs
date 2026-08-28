import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/dio_provider.dart';
import '../../../core/providers/theme_provider.dart';
import '../../../core/router/app_router.dart';
import '../../../core/services/biometric_service.dart';
import '../../../core/services/fcm_service.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../../../core/widgets/user_avatar.dart';
import 'delegation_settings_screen.dart';
import 'email_notification_settings_screen.dart';

/// 내 설정 화면 — 프로필 / 알림 / 계정 관리
class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  bool _pushNotif = false;
  bool _isBiometricSupported = false;
  bool _biometricEnabled = false;
  String _biometricLabel = '생체 인증';
  late final AppLifecycleListener _lifecycleListener;

  @override
  void initState() {
    super.initState();
    _loadBiometricSettings();
    _loadPushSettings();

    // iOS/Android 시스템 설정 화면에서 알림 허용 후 앱으로 돌아왔을 때 상태 자동 갱신
    _lifecycleListener = AppLifecycleListener(
      onResume: _loadPushSettings,
      onShow: _loadPushSettings,
    );
  }

  @override
  void dispose() {
    _lifecycleListener.dispose();
    super.dispose();
  }

  Future<void> _loadPushSettings() async {
    final isEnabled = await FcmService.isPushEnabled();
    if (mounted) {
      setState(() => _pushNotif = isEnabled);
    }
  }

  Future<void> _togglePushNotification(bool value) async {
    final dio = ref.read(dioProvider);
    final success = await FcmService.setPushEnabled(dio, value);

    if (mounted) {
      setState(() => _pushNotif = value && success);
      if (value && !success) {
        // iOS/Android에서 시스템 알림 권한이 거부되어 있는 경우
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('기기 설정에서 IBS 웍스의 알림 권한을 허용해주세요.'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: context.colors.error,
            duration: const Duration(seconds: 5),
            action: SnackBarAction(
              label: '설정 열기',
              textColor: Colors.white,
              onPressed: () => FcmService.openNotificationSettings(),
            ),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              value
                  ? '모바일 푸시 알림이 활성화되었습니다.'
                  : '모바일 푸시 알림이 비활성화되었습니다.',
            ),
            behavior: SnackBarBehavior.floating,
            backgroundColor: value ? const Color(0xFF10B981) : context.colors.textPrimary,
          ),
        );
      }
    }
  }

  Future<void> _loadBiometricSettings() async {
    final canAuth = await BiometricService.canAuthenticate();
    if (canAuth) {
      final isEnabled = await BiometricService.isBiometricEnabled();
      final label = await BiometricService.getBiometricLabel();
      if (mounted) {
        setState(() {
          _isBiometricSupported = true;
          _biometricEnabled = isEnabled;
          _biometricLabel = label;
        });
      }
    }
  }

  Future<void> _toggleBiometric(bool value) async {
    if (value) {
      // 켤 때는 실제 생체 인증을 한번 확인
      final result = await BiometricService.authenticate(
        reason: '$_biometricLabel 사용을 위해 본인 인증을 진행합니다.',
      );
      if (result == BiometricAuthResult.success) {
        await BiometricService.setBiometricEnabled(true);
        if (mounted) setState(() => _biometricEnabled = true);
      }
    } else {
      await BiometricService.setBiometricEnabled(false);
      if (mounted) setState(() => _biometricEnabled = false);
    }
  }

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
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.zero,
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
            const SizedBox(height: 16),

            // ── 화면 설정 섹션 ────────────────────────────────────────────────
            const _SectionLabel(title: '화면 설정'),
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
            const SizedBox(height: 16),

            // ── 알림 설정 섹션 ────────────────────────────────────────────────
            const _SectionLabel(title: '알림 설정'),
            _SettingTile(
              leading: Icon(Icons.mark_email_read_outlined,
                  color: context.colors.accentWork, size: 22),
              title: '업무 및 이메일 알림 설정',
              subtitle: '회의 알림, 업무 자동 지켜보기, 구독 프로젝트',
              trailing: Icon(Icons.chevron_right_rounded,
                  color: context.colors.textDisabled),
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => const EmailNotificationSettingsScreen(),
                  ),
                );
              },
            ),
            const _Divider(),
            _SettingTile(
              leading: Icon(Icons.notifications_active_outlined,
                  color: context.colors.textSecond, size: 22),
              title: '푸시 알림',
              subtitle: _pushNotif ? '실시간 모바일 푸시 알림 수신 중' : '모바일 푸시 알림 꺼짐',
              trailing: Switch(
                value: _pushNotif,
                onChanged: _togglePushNotification,
                activeTrackColor: context.colors.accentWork,
                activeThumbColor: Colors.white,
              ),
            ),
            if (_pushNotif) ...[
              const _Divider(),
              _SettingTile(
                leading: Icon(Icons.science_outlined,
                    color: context.colors.textSecond, size: 22),
                title: '알림 및 뱃지 자가 진단',
                subtitle: '테스트 알림을 즉시 발송하여 수신 확인',
                trailing: Icon(Icons.send_rounded,
                    size: 18, color: context.colors.accentWork),
                onTap: () async {
                  await FcmService.showTestLocalNotification();
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('테스트 알림이 발송되었습니다. 상단 알림 배너를 확인하세요.'),
                        behavior: SnackBarBehavior.floating,
                        backgroundColor: Color(0xFF10B981),
                      ),
                    );
                  }
                },
              ),
            ],
            const SizedBox(height: 16),

            // ── 보안 및 인증 섹션 ────────────────────────────────────────────
            if (_isBiometricSupported) ...[
              const _SectionLabel(title: '보안 및 결재 인증'),
              _SettingTile(
                leading: Icon(
                  _biometricLabel == 'Face ID'
                      ? Icons.face_rounded
                      : Icons.fingerprint_rounded,
                  color: context.colors.accentApprovalDeep,
                  size: 24,
                ),
                title: '$_biometricLabel 결재 승인',
                subtitle: '결재 승인 시 본인 생체 인증 사용',
                trailing: Switch(
                  value: _biometricEnabled,
                  onChanged: _toggleBiometric,
                  activeTrackColor: context.colors.accentApproval,
                  activeThumbColor: Colors.white,
                ),
              ),
              const SizedBox(height: 16),
            ],

            // ── 전자결재 및 위임 관리 섹션 ─────────────────────────────────────
            const _SectionLabel(title: '전자결재 및 부재 설정'),
            _SettingTile(
              leading: Icon(Icons.shield_outlined,
                  color: context.colors.accentApprovalDeep, size: 24),
              title: '부재 및 결재 위임(대결)',
              subtitle: '휴가/출장 시 대결자 지정 및 권한 위임',
              trailing: Icon(Icons.chevron_right_rounded,
                  color: context.colors.textDisabled),
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const DelegationSettingsScreen()),
                );
              },
            ),
            const SizedBox(height: 16),

            // ── 계정 섹션 ─────────────────────────────────────────────────────
            const _SectionLabel(title: '계정'),
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
                  color: context.colors.error, size: 22),
              title: '로그아웃',
              titleColor: context.colors.error,
              trailing: Icon(Icons.chevron_right_rounded,
                  color: context.colors.textDisabled),
              onTap: _handleLogout,
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

// ── 섹션 라벨 (구분 헤더) ──────────────────────────────────────────────────────
class _SectionLabel extends StatelessWidget {
  final String title;
  const _SectionLabel({required this.title});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: context.colors.bgSurface,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Text(
        title,
        style: AppTextStyles.caption.copyWith(
          color: context.colors.textMuted,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

// ── 설정 타일 ────────────────────────────────────────────────────────────────
class _SettingTile extends StatelessWidget {
  final Widget leading;
  final String title;
  final Color? titleColor;
  final String? subtitle;
  final Widget? trailing;
  final VoidCallback? onTap;

  const _SettingTile({
    required this.leading,
    required this.title,
    this.titleColor,
    this.subtitle,
    this.trailing,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: context.colors.bgCard,
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
                        color: titleColor ?? context.colors.textPrimary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (subtitle != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        subtitle!,
                        style: AppTextStyles.bodySm
                            .copyWith(color: context.colors.textMuted),
                      ),
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
    return Divider(
      height: 1,
      thickness: 0.8,
      color: context.colors.border,
      indent: 52,
    );
  }
}
