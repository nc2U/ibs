import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/router/app_router.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../services/auth_service.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _isLoading = false;
  bool _obscurePassword = true;
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final authService = ref.read(authServiceProvider);
    final result = await authService.login(
      email: _emailController.text.trim(),
      password: _passwordController.text,
    );

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (result['success'] == true) {
      // Riverpod 인증 상태 업데이트 → go_router 가드가 자동으로 /home으로 리다이렉트
      ref.read(authProvider.notifier).setAuthenticated(result['access'] as String);
      if (mounted) context.go(AppRoutes.home);
    } else {
      setState(() => _errorMessage = result['message'] ?? '로그인 실패');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
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
                    context.isDarkMode
                        ? 'assets/images/sygnet.svg'
                        : 'assets/images/sygnet_light.svg',
                    width: 80,
                    height: 80,
                  ),
                ),
                const SizedBox(height: 20),
                Text('IBS 워크스페이스', textAlign: TextAlign.center, style: AppTextStyles.h1),
                const SizedBox(height: 8),
                Text('|주|대영아이비에스 업무/프로젝트 관리시스템',
                    textAlign: TextAlign.center, style: AppTextStyles.caption),
                const SizedBox(height: 40),

                // 로그인 카드
                Container(
                  padding: const EdgeInsets.all(24.0),
                  decoration: BoxDecoration(
                    color: AppColors.bgCard,
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: AppColors.border, width: 1.2),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.3),
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
                              color: AppColors.errorBg,
                              border: Border.all(color: AppColors.errorBorder),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.error_outline, color: Color(0xFFFCA5A5), size: 20),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(_errorMessage!,
                                      style: AppTextStyles.bodySm.copyWith(color: const Color(0xFFFCA5A5))),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 20),
                        ],

                        // 이메일
                        TextFormField(
                          controller: _emailController,
                          keyboardType: TextInputType.emailAddress,
                          style: AppTextStyles.bodyMd,
                          decoration: _inputDecoration('이메일 주소', Icons.email_outlined),
                          validator: (v) =>
                              (v == null || v.trim().isEmpty) ? '이메일 주소를 입력해주세요' : null,
                        ),
                        const SizedBox(height: 16),

                        // 비밀번호
                        TextFormField(
                          controller: _passwordController,
                          obscureText: _obscurePassword,
                          style: AppTextStyles.bodyMd,
                          decoration: _inputDecoration(
                            '비밀번호',
                            Icons.lock_outline,
                            suffix: IconButton(
                              icon: Icon(
                                _obscurePassword ? Icons.visibility_off : Icons.visibility,
                                color: AppColors.textMuted,
                                size: 20,
                              ),
                              onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                            ),
                          ),
                          validator: (v) =>
                              (v == null || v.isEmpty) ? '비밀번호를 입력해주세요' : null,
                          onFieldSubmitted: (_) => _handleLogin(),
                        ),
                        const SizedBox(height: 28),

                        // 로그인 버튼
                        ElevatedButton(
                          onPressed: _isLoading ? null : _handleLogin,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.accentWorkDeep,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                            elevation: 4,
                          ),
                          child: _isLoading
                              ? const SizedBox(
                                  height: 22,
                                  width: 22,
                                  child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white),
                                )
                              : Text('로그인', style: AppTextStyles.titleMd),
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
    );
  }

  InputDecoration _inputDecoration(String label, IconData icon, {Widget? suffix}) {
    return InputDecoration(
      labelText: label,
      labelStyle: AppTextStyles.bodyMuted,
      prefixIcon: Icon(icon, color: AppColors.accentWork),
      suffixIcon: suffix,
      filled: true,
      fillColor: AppColors.bgInput,
      enabledBorder: const OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: AppColors.border),
      ),
      focusedBorder: const OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: AppColors.accentWork, width: 1.5),
      ),
      errorBorder: const OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: AppColors.error),
      ),
      focusedErrorBorder: const OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: AppColors.error, width: 1.5),
      ),
    );
  }
}
