import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';

class ChangePasswordScreen extends ConsumerStatefulWidget {
  const ChangePasswordScreen({super.key});

  @override
  ConsumerState<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends ConsumerState<ChangePasswordScreen> {
  final _formKey = GlobalKey<FormState>();

  final _oldPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  bool _obscureOldPassword = true;
  bool _obscureNewPassword = true;
  bool _obscureConfirmPassword = true;
  bool _isLoading = false;

  @override
  void dispose() {
    _oldPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final dio = ref.read(dioProvider);
      final response = await dio.post(
        ApiEndpoints.changePassword,
        data: {
          'old_password': _oldPasswordController.text.trim(),
          'new_password': _newPasswordController.text.trim(),
        },
      );

      if (!mounted) return;

      final msg = (response.data is Map && response.data['detail'] != null)
          ? response.data['detail'].toString()
          : '비밀번호가 성공적으로 변경되었습니다.';

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(msg),
          backgroundColor: context.colors.success,
          behavior: SnackBarBehavior.floating,
        ),
      );

      Navigator.of(context).pop();
    } on DioException catch (e) {
      if (!mounted) return;

      String errorMsg = '비밀번호 변경에 실패했습니다.';
      if (e.response?.data is Map) {
        final data = e.response!.data as Map;
        if (data['detail'] != null) {
          errorMsg = data['detail'].toString();
        } else if (data['old_password'] != null) {
          errorMsg = (data['old_password'] is List)
              ? (data['old_password'] as List).join('\n')
              : data['old_password'].toString();
        } else if (data['new_password'] != null) {
          errorMsg = (data['new_password'] is List)
              ? (data['new_password'] as List).join('\n')
              : data['new_password'].toString();
        }
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(errorMsg),
          backgroundColor: context.colors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('오류가 발생했습니다: $e'),
          backgroundColor: context.colors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        title: Text(
          '비밀번호 변경',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.w800,
            color: context.colors.textPrimary,
          ),
        ),
        backgroundColor: context.colors.bgCard,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 보안 안내 배너 ──────────────────────────────────────────────
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: context.colors.info.withAlpha(20),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: context.colors.info.withAlpha(60), width: 0.8),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.lock_reset_rounded, color: context.colors.info, size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '안전한 비밀번호 설정 안내',
                            style: TextStyle(
                              fontWeight: FontWeight.w700,
                              color: context.colors.info,
                              fontSize: 13.5,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '비밀번호는 영문, 숫자, 특수문자를 혼용하여 8자리 이상으로 설정하시는 것을 권장합니다.',
                            style: TextStyle(
                              color: context.colors.textSecond,
                              fontSize: 12,
                              height: 1.4,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // ── 1. 현재 비밀번호 ─────────────────────────────────────────────
              Text(
                '현재 비밀번호',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: context.colors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _oldPasswordController,
                obscureText: _obscureOldPassword,
                decoration: InputDecoration(
                  hintText: '현재 사용 중인 비밀번호를 입력하세요',
                  hintStyle: TextStyle(color: context.colors.textMuted, fontSize: 13),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  filled: true,
                  fillColor: context.colors.bgInput,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(6),
                    borderSide: BorderSide(color: context.colors.border),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(6),
                    borderSide: BorderSide(color: context.colors.border),
                  ),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscureOldPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                      size: 20,
                      color: context.colors.textMuted,
                    ),
                    onPressed: () => setState(() => _obscureOldPassword = !_obscureOldPassword),
                  ),
                ),
                validator: (val) {
                  if (val == null || val.trim().isEmpty) {
                    return '현재 비밀번호를 입력해주세요.';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 20),

              // ── 2. 새 비밀번호 ──────────────────────────────────────────────
              Text(
                '새 비밀번호',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: context.colors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _newPasswordController,
                obscureText: _obscureNewPassword,
                decoration: InputDecoration(
                  hintText: '새로 사용할 비밀번호를 입력하세요 (8자 이상 권장)',
                  hintStyle: TextStyle(color: context.colors.textMuted, fontSize: 13),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  filled: true,
                  fillColor: context.colors.bgInput,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(6),
                    borderSide: BorderSide(color: context.colors.border),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(6),
                    borderSide: BorderSide(color: context.colors.border),
                  ),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscureNewPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                      size: 20,
                      color: context.colors.textMuted,
                    ),
                    onPressed: () => setState(() => _obscureNewPassword = !_obscureNewPassword),
                  ),
                ),
                validator: (val) {
                  if (val == null || val.trim().isEmpty) {
                    return '새 비밀번호를 입력해주세요.';
                  }
                  if (val.trim().length < 6) {
                    return '비밀번호는 최소 6자 이상이어야 합니다.';
                  }
                  if (val.trim() == _oldPasswordController.text.trim()) {
                    return '현재 비밀번호와 다른 비밀번호를 설정해주세요.';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 20),

              // ── 3. 새 비밀번호 확인 ──────────────────────────────────────────
              Text(
                '새 비밀번호 확인',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: context.colors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _confirmPasswordController,
                obscureText: _obscureConfirmPassword,
                decoration: InputDecoration(
                  hintText: '새 비밀번호를 한 번 더 입력하세요',
                  hintStyle: TextStyle(color: context.colors.textMuted, fontSize: 13),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  filled: true,
                  fillColor: context.colors.bgInput,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(6),
                    borderSide: BorderSide(color: context.colors.border),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(6),
                    borderSide: BorderSide(color: context.colors.border),
                  ),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscureConfirmPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                      size: 20,
                      color: context.colors.textMuted,
                    ),
                    onPressed: () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
                  ),
                ),
                validator: (val) {
                  if (val == null || val.trim().isEmpty) {
                    return '새 비밀번호를 다시 입력해주세요.';
                  }
                  if (val.trim() != _newPasswordController.text.trim()) {
                    return '새 비밀번호가 일치하지 않습니다.';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 32),

              // ── 변경 완료 버튼 ──────────────────────────────────────────────
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _handleSubmit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: context.colors.accentWork,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                    elevation: 0,
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text(
                          '비밀번호 변경 완료',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: Colors.white,
                          ),
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
