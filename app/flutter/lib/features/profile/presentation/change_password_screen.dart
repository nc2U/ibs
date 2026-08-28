import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/api_endpoints.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/auth_provider.dart';
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

  /// 현재 비밀번호를 잊은 사용자를 위한 이메일 재설정 링크 요청 모달
  Future<void> _showPasswordResetDialog() async {
    final user = ref.read(currentUserProvider).valueOrNull;
    final emailController = TextEditingController(text: user?.email ?? '');
    bool isSending = false;

    await showDialog(
      context: context,
      builder: (dialogCtx) {
        return StatefulBuilder(
          builder: (dialogCtx, setDialogState) {
            return AlertDialog(
              backgroundColor: context.colors.bgCard,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              title: Row(
                children: [
                  Icon(Icons.mark_email_read_outlined, color: context.colors.accentWork, size: 22),
                  const SizedBox(width: 8),
                  Text(
                    '비밀번호 재설정 링크 발송',
                    style: AppTextStyles.titleMd.copyWith(
                      fontWeight: FontWeight.w800,
                      color: context.colors.textPrimary,
                    ),
                  ),
                ],
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '가입된 이메일 주소로 비밀번호 재설정 링크가 포함된 메일을 발송합니다. 메일 수신 후 안내 링크를 통해 새로운 비밀번호를 설정하실 수 있습니다.',
                    style: TextStyle(
                      fontSize: 13,
                      color: context.colors.textSecond,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '이메일 주소',
                    style: TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w700,
                      color: context.colors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  TextField(
                    controller: emailController,
                    keyboardType: TextInputType.emailAddress,
                    decoration: InputDecoration(
                      hintText: '이메일 주소 입력',
                      hintStyle: TextStyle(color: context.colors.textMuted, fontSize: 13),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
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
                    ),
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: isSending ? null : () => Navigator.pop(dialogCtx),
                  child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
                ),
                ElevatedButton(
                  onPressed: isSending
                      ? null
                      : () async {
                          final email = emailController.text.trim();
                          if (email.isEmpty || !email.contains('@')) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('유효한 이메일 주소를 입력해주세요.'),
                                behavior: SnackBarBehavior.floating,
                                backgroundColor: Colors.redAccent,
                              ),
                            );
                            return;
                          }

                          setDialogState(() => isSending = true);

                          try {
                            final dio = ref.read(dioProvider);
                            final res = await dio.post(
                              ApiEndpoints.passwordReset,
                              data: {'email': email},
                            );

                            if (dialogCtx.mounted) Navigator.pop(dialogCtx);

                            if (mounted) {
                              final msg = (res.data is Map && res.data['detail'] != null)
                                  ? res.data['detail'].toString()
                                  : '비밀번호 재설정 이메일이 발송되었습니다.';

                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(msg),
                                  backgroundColor: context.colors.success,
                                  behavior: SnackBarBehavior.floating,
                                  duration: const Duration(seconds: 4),
                                ),
                              );
                            }
                          } on DioException catch (e) {
                            setDialogState(() => isSending = false);
                            String errorMsg = '이메일 발송에 실패했습니다.';
                            if (e.response?.data is Map && e.response!.data['detail'] != null) {
                              errorMsg = e.response!.data['detail'].toString();
                            }
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(errorMsg),
                                  backgroundColor: context.colors.error,
                                  behavior: SnackBarBehavior.floating,
                                ),
                              );
                            }
                          } catch (e) {
                            setDialogState(() => isSending = false);
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('오류가 발생했습니다: $e'),
                                  backgroundColor: context.colors.error,
                                  behavior: SnackBarBehavior.floating,
                                ),
                              );
                            }
                          }
                        },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: context.colors.accentWork,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                  ),
                  child: isSending
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('발송하기', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                ),
              ],
            );
          },
        );
      },
    );
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
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '현재 비밀번호',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: context.colors.textPrimary,
                    ),
                  ),
                  TextButton(
                    onPressed: _showPasswordResetDialog,
                    style: TextButton.styleFrom(
                      padding: EdgeInsets.zero,
                      minimumSize: const Size(50, 30),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: Text(
                      '비밀번호를 잊으셨나요?',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: context.colors.accentWork,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
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
