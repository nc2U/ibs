import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/router/app_router.dart';
import '../../../core/services/biometric_service.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../services/auth_service.dart';

/// 🔐 IBS 워크스페이스 로그인 화면
/// - 이메일/비밀번호 기반 SimpleJWT 인증
/// - Face ID / 지문 인식 생체 간편 로그인
/// - 아이디(이메일) 저장 옵션
/// - 키보드 액션 및 포커스 자동 전환 지원
class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();

  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _rememberEmail = false;
  bool _canUseBiometrics = false;
  String _biometricLabel = 'Face ID';
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initAuthInfo();
    });
  }

  Future<void> _initAuthInfo() async {
    final authService = ref.read(authServiceProvider);
    final savedEmail = await authService.getSavedEmail();
    if (savedEmail != null && savedEmail.isNotEmpty && mounted) {
      _emailController.text = savedEmail;
      setState(() => _rememberEmail = true);
    }

    final canBio = await authService.canBiometricLogin();
    final label = await BiometricService.getBiometricLabel();
    if (mounted) {
      setState(() {
        _canUseBiometrics = canBio;
        _biometricLabel = label;
      });
    }
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _emailFocusNode.dispose();
    _passwordFocusNode.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final authService = ref.read(authServiceProvider);
    final result = await authService.login(
      email: _emailController.text.trim(),
      password: _passwordController.text,
      rememberEmail: _rememberEmail,
    );

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (result['success'] == true) {
      // 사용자 캐시 무효화 및 새 인증 토큰 반영
      ref.invalidate(currentUserProvider);
      ref.read(authProvider.notifier).setAuthenticated(result['access'] as String);
      if (mounted) context.go(AppRoutes.home);
    } else {
      setState(() => _errorMessage = result['message'] ?? '로그인에 실패했습니다.');
    }
  }

  Future<void> _handleBiometricLogin() async {
    FocusScope.of(context).unfocus();
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final authService = ref.read(authServiceProvider);
    final result = await authService.loginWithBiometrics();

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (result['success'] == true) {
      // 사용자 캐시 무효화 및 새 인증 토큰 반영
      ref.invalidate(currentUserProvider);
      ref.read(authProvider.notifier).setAuthenticated(result['access'] as String);
      if (mounted) context.go(AppRoutes.home);
    } else {
      setState(() => _errorMessage = result['message'] ?? '$_biometricLabel 로그인 실패');
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = context.isDarkMode;

    return GestureDetector(
      onTap: () => FocusScope.of(context).unfocus(),
      behavior: HitTestBehavior.translucent,
      child: Scaffold(
        backgroundColor: context.colors.bgPrimary,
        body: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // 로고
                  Center(
                    child: SvgPicture.asset(
                      isDark
                          ? 'assets/images/sygnet.svg'
                          : 'assets/images/sygnet_light.svg',
                      width: 80,
                      height: 80,
                    ),
                  ),
                  const SizedBox(height: 20),
                  Text(
                    'IBS 워크스페이스',
                    textAlign: TextAlign.center,
                    style: AppTextStyles.h1.copyWith(color: context.colors.textPrimary),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '(주)대영아이비에스 업무/프로젝트 관리시스템',
                    textAlign: TextAlign.center,
                    style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                  ),
                  const SizedBox(height: 36),

                  // 로그인 카드 (플랫 직각 스타일)
                  Container(
                    padding: const EdgeInsets.all(24.0),
                    decoration: BoxDecoration(
                      color: context.colors.bgCard,
                      borderRadius: BorderRadius.zero,
                      border: Border.all(color: context.colors.border, width: 1.2),
                      boxShadow: [
                        BoxShadow(
                          color: isDark
                              ? Colors.black.withAlpha(76)
                              : Colors.black.withAlpha(15),
                          blurRadius: 16,
                          offset: const Offset(0, 6),
                        ),
                      ],
                    ),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // 오류 배너
                          if (_errorMessage != null) ...[
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: context.colors.errorBg,
                                border: Border.all(color: context.colors.errorBorder),
                                borderRadius: BorderRadius.zero,
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(Icons.error_outline_rounded, color: context.colors.error, size: 20),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      _errorMessage!,
                                      style: AppTextStyles.bodySm.copyWith(color: context.colors.error),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 18),
                          ],

                          // 이메일 입력창
                          TextFormField(
                            controller: _emailController,
                            focusNode: _emailFocusNode,
                            keyboardType: TextInputType.emailAddress,
                            textInputAction: TextInputAction.next,
                            style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                            decoration: _inputDecoration(context, '이메일 주소', Icons.email_outlined),
                            validator: (v) {
                              if (v == null || v.trim().isEmpty) {
                                return '이메일 주소를 입력해주세요';
                              }
                              final email = v.trim();
                              final emailRegex = RegExp(r'^[^@]+@[^@]+\.[^@]+$');
                              if (!emailRegex.hasMatch(email)) {
                                return '올바른 이메일 형식을 입력해주세요';
                              }
                              return null;
                            },
                            onFieldSubmitted: (_) => _passwordFocusNode.requestFocus(),
                          ),
                          const SizedBox(height: 16),

                          // 비밀번호 입력창
                          TextFormField(
                            controller: _passwordController,
                            focusNode: _passwordFocusNode,
                            obscureText: _obscurePassword,
                            textInputAction: TextInputAction.done,
                            style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                            decoration: _inputDecoration(
                              context,
                              '비밀번호',
                              Icons.lock_outline,
                              suffix: IconButton(
                                icon: Icon(
                                  _obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                                  color: context.colors.textMuted,
                                  size: 20,
                                ),
                                onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                              ),
                            ),
                            validator: (v) =>
                                (v == null || v.isEmpty) ? '비밀번호를 입력해주세요' : null,
                            onFieldSubmitted: (_) => _handleLogin(),
                          ),
                          const SizedBox(height: 12),

                          // 아이디(이메일) 저장 체크박스
                          Row(
                            children: [
                              SizedBox(
                                width: 20,
                                height: 20,
                                child: Checkbox(
                                  value: _rememberEmail,
                                  activeColor: context.colors.accentWork,
                                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                                  onChanged: (val) => setState(() => _rememberEmail = val ?? false),
                                ),
                              ),
                              const SizedBox(width: 8),
                              GestureDetector(
                                onTap: () => setState(() => _rememberEmail = !_rememberEmail),
                                child: Text(
                                  '아이디(이메일) 저장',
                                  style: AppTextStyles.caption.copyWith(
                                    color: context.colors.textSecond,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 24),

                          // 생체 인증(Face ID / 지문) 간편 로그인 버튼
                          if (_canUseBiometrics) ...[
                            ElevatedButton.icon(
                              onPressed: _isLoading ? null : _handleBiometricLogin,
                              icon: Icon(
                                _biometricLabel == 'Face ID' ? Icons.face_rounded : Icons.fingerprint_rounded,
                                color: Colors.white,
                                size: 22,
                              ),
                              label: Text(
                                '$_biometricLabel 간편 로그인',
                                style: AppTextStyles.titleMd.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: isDark ? const Color(0xFF115E59) : context.colors.accentChannel,
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                side: BorderSide(
                                  color: isDark
                                      ? const Color(0xFF2DD4BF).withValues(alpha: 0.5)
                                      : const Color(0xFF0F766E).withValues(alpha: 0.7),
                                  width: 1.2,
                                ),
                                shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                                elevation: isDark ? 4 : 2,
                              ),
                            ),
                            const SizedBox(height: 12),
                          ],

                          // 일반 로그인 버튼
                          ElevatedButton(
                            onPressed: _isLoading ? null : _handleLogin,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: isDark ? const Color(0xFF075985) : context.colors.accentWork,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 16),
                              shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                              elevation: isDark ? 4 : 1,
                            ),
                            child: _isLoading
                                ? const SizedBox(
                                    height: 22,
                                    width: 22,
                                    child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white),
                                  )
                                : Text('로그인', style: AppTextStyles.titleMd.copyWith(color: Colors.white)),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(BuildContext context, String label, IconData icon, {Widget? suffix}) {
    return InputDecoration(
      labelText: label,
      labelStyle: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
      prefixIcon: Icon(icon, color: context.colors.accentWork),
      suffixIcon: suffix,
      filled: true,
      fillColor: context.colors.bgInput,
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: context.colors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: context.colors.accentWork, width: 1.5),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: context.colors.error),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: context.colors.error, width: 1.5),
      ),
    );
  }
}
