import 'package:flutter/material.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/theme/app_colors_extension.dart';

/// 앱 최초 진입 시 푸시 알림 수신 동의를 유도하는 프리미엄 바텀시트 모달
class PushPermissionPromptModal extends StatelessWidget {
  final VoidCallback onAccept;
  final VoidCallback onDecline;

  const PushPermissionPromptModal({
    super.key,
    required this.onAccept,
    required this.onDecline,
  });

  /// 바텀시트로 표시하는 헬퍼 메서드
  static Future<bool?> show(BuildContext context) {
    return showModalBottomSheet<bool>(
      context: context,
      isDismissible: false,
      enableDrag: false,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => PushPermissionPromptModal(
        onAccept: () => Navigator.of(ctx).pop(true),
        onDecline: () => Navigator.of(ctx).pop(false),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bgColor = isDark ? const Color(0xFF1E293B) : Colors.white;

    return Align(
      alignment: Alignment.bottomCenter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 520),
        child: Container(
          decoration: BoxDecoration(
            color: bgColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.15),
                blurRadius: 20,
                offset: const Offset(0, -4),
              ),
            ],
          ),
          child: SafeArea(
            top: false,
            bottom: true,
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(24, 24, 24, 20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // 상단 아이콘 & 타이틀
                  Center(
                    child: Container(
                      width: 56,
                      height: 56,
                      decoration: BoxDecoration(
                        color:
                            (isDark
                                    ? const Color(0xFF0F766E)
                                    : const Color(0xFFCCFBF1))
                                .withValues(alpha: 0.8),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        Icons.notifications_active_rounded,
                        size: 28,
                        color: isDark
                            ? const Color(0xFF5EEAD4)
                            : const Color(0xFF0D9488),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  Text(
                    'IBS 알림을 켜고 주요 소식을 놓치지 마세요',
                    textAlign: TextAlign.center,
                    style: AppTextStyles.titleLg.copyWith(
                      fontWeight: FontWeight.w700,
                      color: context.colors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 10),

                  Text(
                    '전자결재 승인 요청, 프로젝트 업무 및 회의 변동사항,\n실시간 채팅 소식을 빠르게 알려드립니다.',
                    textAlign: TextAlign.center,
                    style: AppTextStyles.bodyMd.copyWith(
                      color: context.colors.textSecond,
                      height: 1.45,
                    ),
                  ),
                  const SizedBox(height: 24),

                  // 알림 혜택 리스트 박스
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 14,
                    ),
                    decoration: BoxDecoration(
                      color: isDark
                          ? const Color(0xFF0F172A)
                          : const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isDark
                            ? const Color(0xFF334155)
                            : const Color(0xFFE2E8F0),
                      ),
                    ),
                    child: Column(
                      children: [
                        _buildFeatureRow(
                          context,
                          Icons.assignment_turned_in_rounded,
                          '전자결재 결재 및 반려 실시간 알림',
                        ),
                        const SizedBox(height: 10),
                        _buildFeatureRow(
                          context,
                          Icons.chat_bubble_outline_rounded,
                          '사내 메신저 및 주요 채널 멘션 알림',
                        ),
                        const SizedBox(height: 10),
                        _buildFeatureRow(
                          context,
                          Icons.event_note_rounded,
                          '워크스페이스 업무 및 회의 소식',
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // 승인 버튼
                  ElevatedButton(
                    onPressed: onAccept,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: context.colors.accentChannel,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      elevation: 0,
                    ),
                    child: Text(
                      '알림 받기',
                      style: AppTextStyles.titleMd.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),

                  // 나중에 설정 버튼
                  TextButton(
                    onPressed: onDecline,
                    style: TextButton.styleFrom(
                      foregroundColor: context.colors.textMuted,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    child: Text(
                      '나중에 설정하기',
                      style: AppTextStyles.bodyMd.copyWith(
                        color: context.colors.textMuted,
                        fontWeight: FontWeight.w500,
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

  Widget _buildFeatureRow(BuildContext context, IconData icon, String text) {
    return Row(
      children: [
        Icon(icon, size: 18, color: context.colors.accentChannel),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            text,
            style: AppTextStyles.caption.copyWith(
              color: context.colors.textPrimary,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }
}
